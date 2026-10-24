#include "MinimapEditorLibrary.h"
#include "MinimapTypes.h"
#include "QuestDefinition.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SplineComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "StaticMeshResources.h"
#include "Misc/AutomationTest.h"
#include "CollisionQueryParams.h"
#include "CollisionShape.h"

namespace SchoolMinimap
{
constexpr double Cell=50.;
constexpr int64 MaxCells=12000000;
constexpr int64 MaxWork=150000000;
struct FTriangle { FVector A,B,C; bool bCheckClearance=false; UStaticMeshComponent* CollisionSurface=nullptr; };
struct FSample { float Z=0; };
struct FLayer { int32 Height=0; TMap<FIntPoint,FSample> Samples; };

// These assets are single-surface terrain. Their playable collision footprint can
// differ from render LOD triangles. Composite room shells still use per-triangle
// sampling so a downward trace cannot discard floors underneath another storey.
bool UsesCollisionFloorRaster(const FString& Path)
{
 const FString P=Path.ToLower();
 return P.Contains(TEXT("/luoscaves/meshes/props_floors/"))||P.Contains(TEXT("/luoscaves/meshes/props_mesas/"))||P.Contains(TEXT("/shared/architecture/dummy/sm_dummy_ramp_default."));
}

// These are structural families present in the maintained school. Generic cubes require
// a structural actor label; a furniture/decor mesh never becomes floor by its bounds.
bool IsStructure(const FString& Label,const FString& Path)
{
 const FString L=Label.ToLower(), P=Path.ToLower();
 if(P.Contains(TEXT("/shared/architecture/dummy/sm_dummy_ramp_default.")))return true;
 if(L.Contains(TEXT("collision"))||P.Contains(TEXT("nocollision"))||L.Contains(TEXT("crack"))||(L.Contains(TEXT("slime"))&&L.Contains(TEXT("pool")))||L.Contains(TEXT("splitfloorboard"))) return false;
 if(L.Contains(TEXT("roof"))||L.Contains(TEXT("ceiling"))) return false;
 if(P.Contains(TEXT("/buildingmodules/floor/"))||P.Contains(TEXT("/buildingmodules/walls/"))||P.Contains(TEXT("/buildingmodules/interiorwalls/"))||P.Contains(TEXT("/buildingmodules/toplevelwalls/"))||P.Contains(TEXT("sm_gymfloor"))) return true;
 if(P.Contains(TEXT("sm_cutroof_348"))||P.Contains(TEXT("sm_cutroof_369"))) return true;
 if(P.Contains(TEXT("/luoscaves/meshes/"))) return P.Contains(TEXT("/props_floors/"))||P.Contains(TEXT("/props_mesas/"))||P.Contains(TEXT("/rock_walls/"));
 if(P.Contains(TEXT("sm_school_corridor_dummy"))) return true;
 if(P.Contains(TEXT("/environments/cave/sets/"))) return P.Contains(TEXT("shell"))||P.Contains(TEXT("rock"))||P.Contains(TEXT("passage"))||P.Contains(TEXT("floor"))||P.Contains(TEXT("wall"));
 if(P.Contains(TEXT("/environments/school/sets/"))) return P.Contains(TEXT("shell"))||P.Contains(TEXT("mainfloor"))||P.Contains(TEXT("rockplatform"))||P.Contains(TEXT("closedstair"))||P.Contains(TEXT("squarelanding"))||P.Contains(TEXT("centeredspiral"))||P.Contains(TEXT("classroompassage"));
 return L.StartsWith(TEXT("floor"))||L.StartsWith(TEXT("wall"))||L.Contains(TEXT("_floor_"))||L.Contains(TEXT("_wall_"))||L.Contains(TEXT("woodfloor"))||L.Contains(TEXT("floorcontinuation"))||L.Contains(TEXT("spiral_stair"))||L==TEXT("lower_floor")||L==TEXT("upper_floor")||L.Contains(TEXT("clocktower_stair"));
}
bool IsFloorSource(const FString& Label,const FString& Path)
{
 if(!IsStructure(Label,Path))return false;
 const FString L=Label.ToLower(),P=Path.ToLower();
 if(P.Contains(TEXT("/shared/architecture/dummy/sm_dummy_ramp_default.")))return true;
 // A wall's upper edge is not a floor, even though its triangle normal points up.
 if(P.Contains(TEXT("/walls/"))||P.Contains(TEXT("/interiorwalls/"))||P.Contains(TEXT("/toplevelwalls/"))||P.Contains(TEXT("/rock_walls/"))||P.Contains(TEXT("wallline")))return false;
 if(L.StartsWith(TEXT("wall"))||L.Contains(TEXT("_wall_"))||L.Contains(TEXT("stair_wall")))return false;
 if(P.Contains(TEXT("/buildingmodules/floor/"))||P.Contains(TEXT("sm_gymfloor"))||P.Contains(TEXT("sm_school_corridor_dummy")))return true;
 if(P.Contains(TEXT("/props_floors/"))||P.Contains(TEXT("/props_mesas/")))return true;
 if(P.Contains(TEXT("sm_cutroof_348"))||P.Contains(TEXT("sm_cutroof_369")))return true;
 if(P.Contains(TEXT("mainfloor"))||P.Contains(TEXT("rockplatform"))||P.Contains(TEXT("closedstair"))||P.Contains(TEXT("squarelanding"))||P.Contains(TEXT("centeredspiral"))||P.Contains(TEXT("classroompassage")))return true;
 if(P.Contains(TEXT("shell")))return true;
 return L.StartsWith(TEXT("floor"))||L.Contains(TEXT("_floor_"))||L.Contains(TEXT("woodfloor"))||L.Contains(TEXT("floorcontinuation"))||L==TEXT("lower_floor")||L==TEXT("upper_floor")||L==TEXT("large_cave_main")||L.Contains(TEXT("clocktower_stair"));
}
double Cross(FVector2D A,FVector2D B) {return A.X*B.Y-A.Y*B.X;}
FORCENOINLINE bool SurfaceAt(const FTriangle& T,FVector2D P,double& Z)
{
 const FVector2D A(T.A.X,T.A.Y), B(T.B.X,T.B.Y), C(T.C.X,T.C.Y);
 const double D=Cross(B-A,C-A); if(FMath::Abs(D)<.001) return false;
 const double U=Cross(P-A,C-A)/D,V=Cross(B-A,P-A)/D;
 if(U<-.0001||V<-.0001||U+V>1.0001) return false;
 Z=T.A.Z+U*(T.B.Z-T.A.Z)+V*(T.C.Z-T.A.Z); return true;
}
bool SegmentInCell(FVector2D A,FVector2D B,FVector2D Min)
{
 double T0=0,T1=1; const FVector2D D=B-A;
 for(int32 Axis=0;Axis<2;++Axis)
 {
  const double V=Axis?D.Y:D.X, P=Axis?A.Y:A.X, Lo=Axis?Min.Y:Min.X;
  if(FMath::Abs(V)<.00001) {if(P<Lo||P>Lo+Cell)return false;continue;}
  double A0=(Lo-P)/V,A1=(Lo+Cell-P)/V; if(A0>A1)Swap(A0,A1);
  T0=FMath::Max(T0,A0);T1=FMath::Min(T1,A1);if(T0>T1)return false;
 }
 return true;
}

bool WallAt(const FTriangle& T,double Z,FVector2D Min);
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolMinimapGeometryTest,"Constellation.Minimap.GeometryRaster",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolMinimapGeometryTest::RunTest(const FString&)
{
 using namespace SchoolMinimap;
 TestTrue(TEXT("Rock ramp uses its playable collision footprint"),UsesCollisionFloorRaster(TEXT("/Game/LuosCaves/Meshes/Props_Floors/SM_LCave_P_Free_Floor_02.SM_LCave_P_Free_Floor_02")));
 // User-captured repro: StaticMeshActor_767 at (2744.542,-1463.560,159.772).
 // Its Mesa_09 render surface omitted the ground that character collision uses.
 TestTrue(TEXT("Walkable mesa ramp uses its playable collision footprint"),UsesCollisionFloorRaster(TEXT("/Game/LuosCaves/Meshes/Props_Mesas/SM_LCave_P_Mesa_09.SM_LCave_P_Mesa_09")));
 TestFalse(TEXT("Multilevel shell keeps independent floor surfaces"),UsesCollisionFloorRaster(TEXT("/Game/Constellation/Environments/School/Sets/SM_SchoolShell")));
 TestFalse(TEXT("Decorative rock is not collision floor terrain"),UsesCollisionFloorRaster(TEXT("/Game/LuosCaves/Meshes/Props_Rocks/SM_Rock")));
 TestTrue(TEXT("Maintained school ramp is a floor source"),IsFloorSource(TEXT("ramp_1"),TEXT("/Game/Constellation/Environments/Shared/Architecture/Dummy/SM_Dummy_Ramp_Default.SM_Dummy_Ramp_Default")));
 double Z=-1;
 const FTriangle Ramp{FVector(0,0,0),FVector(100,0,100),FVector(0,100,0)};
 TestTrue(TEXT("Ramp interior has actual interpolated height"),SurfaceAt(Ramp,FVector2D(25,25),Z));
 TestEqual(TEXT("Ramp sample is not AABB top"),Z,25.);
 TestFalse(TEXT("Triangle bounding box corner is not floor"),SurfaceAt(Ramp,FVector2D(90,90),Z));
 const FTriangle Riser{FVector(0,0,0),FVector(0,100,0),FVector(0,0,300)};
 TestFalse(TEXT("Vertical floor module cannot raster as floor"),SurfaceAt(Riser,FVector2D(0,25),Z));
 TestTrue(TEXT("Thin wall blocks its intersected cell"),WallAt(Riser,60,FVector2D(-25,0)));
 TestFalse(TEXT("Wall does not block above its geometry"),WallAt(Riser,400,FVector2D(-25,0)));
 TestFalse(TEXT("Wall does not fill its distant neighbour"),WallAt(Riser,60,FVector2D(50,0)));
 TestFalse(TEXT("Roof made from floor modules is excluded"),IsStructure(TEXT("classroom_start_roof_1"),TEXT("/Game/ModulAbandJPSchool/Meshes/BuildingModules/Floor/SM_Floor_4x4")));
 TestFalse(TEXT("No-collision hollow proxy does not plug real hole"),IsStructure(TEXT("upper_floor_hollow"),TEXT("/Game/SM_Dummy_Cube_Default_NoCollision")));
 TestFalse(TEXT("Decorative rock does not become walkable terrain"),IsStructure(TEXT("EHG_BreachDebris1"),TEXT("/Game/LuosCaves/Meshes/Props_Rocks/SM_Rock")));
 TestTrue(TEXT("Maintained cut floor remains included"),IsStructure(TEXT("classroom_start_floor_28"),TEXT("/Game/Constellation/Environments/School/Sets/SM_CutRoof_348")));
 TestFalse(TEXT("Wall top never seeds floor layers"),IsFloorSource(TEXT("classroom_start_wall_up_1"),TEXT("/Game/ModulAbandJPSchool/Meshes/BuildingModules/Walls/SM_Wall_SB04x6")));
 TestTrue(TEXT("Actual floor module remains a floor source"),IsFloorSource(TEXT("classroom_start_floor_1"),TEXT("/Game/ModulAbandJPSchool/Meshes/BuildingModules/Floor/SM_Floor_4x4")));
 return true;
}
#endif
bool WallAt(const FTriangle& T,double Z,FVector2D Min)
{
 const FVector V[]={T.A,T.B,T.C}; TArray<FVector2D,TInlineAllocator<3>> P;
 for(int32 I=0;I<3;++I)
 {
  const FVector A=V[I],B=V[(I+1)%3];
  if((A.Z<=Z&&B.Z>Z)||(B.Z<=Z&&A.Z>Z))
  {const FVector Q=A+(B-A)*((Z-A.Z)/(B.Z-A.Z));P.Add(FVector2D(Q.X,Q.Y));}
 }
 return P.Num()==2&&SegmentInCell(P[0],P[1],Min);
}
int32 NearestLayer(const TArray<FLayer>& Layers,double Z)
{
 int32 Best=0;double Distance=DBL_MAX;
 for(int32 I=0;I<Layers.Num();++I){const double D=FMath::Abs(Z-Layers[I].Height);if(D<Distance){Distance=D;Best=I;}}
 return Best;
}
int32 ResolveFloor(const TArray<FMinimapFloorData>& Floors,FVector P,double Radius=250)
{
 int32 Best=INDEX_NONE;double Score=DBL_MAX;
 for(int32 F=0;F<Floors.Num();++F)
 {
  const auto& Floor=Floors[F]; const int32 X=FMath::FloorToInt((P.X-Floor.Origin.X)/Cell),Y=FMath::FloorToInt((P.Y-Floor.Origin.Y)/Cell);
  const int32 R=FMath::CeilToInt(Radius/Cell);
  for(int32 DY=-R;DY<=R;++DY)for(int32 DX=-R;DX<=R;++DX)
  {
   if(X+DX<0||Y+DY<0||X+DX>=Floor.Width||Y+DY>=Floor.Height)continue;
   const int32 I=(Y+DY)*Floor.Width+X+DX;if(Floor.Cells[I]!=1)continue;
   const double Dz=FMath::Abs(Floor.SurfaceZ[I]-P.Z);if(Dz>450)continue;
   const double S=Dz+FMath::Sqrt(double(DX*DX+DY*DY))*Cell;
   if(S<Score){Best=F;Score=S;}
  }
 }
 return Best;
}
}

FString UMinimapEditorLibrary::DescribeFloorSamples(UMinimapRegionData* Data,FVector Position)
{
 FString Report=Position.ToString();if(!Data)return Report;
 for(const auto& F:Data->Floors)
 {
  const int32 I=F.IndexAt(FVector2D(Position));if(I==INDEX_NONE)continue;
  if(FMath::Abs(F.ReferenceZ-Position.Z)<500)Report+=FString::Printf(TEXT(" %s=%d@%.1f"),*F.FloorId.ToString(),F.Cells[I],F.SurfaceZ.IsValidIndex(I)?F.SurfaceZ[I]:F.ReferenceZ);
 }
 return Report;
}
FString UMinimapEditorLibrary::DescribePawnGround(UObject* WorldContext)
{
 const auto* W=WorldContext?WorldContext->GetWorld():nullptr;
 const auto* PC=W?W->GetFirstPlayerController():nullptr;
 const auto* C=PC?Cast<ACharacter>(PC->GetPawn()):nullptr;if(!C)return TEXT("No character");
 const auto& Hit=C->GetCharacterMovement()->CurrentFloor.HitResult;
 return FString::Printf(TEXT("%s %s at %s"),*GetNameSafe(Hit.GetActor()),*GetNameSafe(Hit.GetComponent()),*Hit.ImpactPoint.ToString());
}
bool UMinimapEditorLibrary::GenerateSchoolMap(UObject* WorldContext,UMinimapRegionData* Data,FString& Report)
{
 using namespace SchoolMinimap;
 UWorld* World=WorldContext?WorldContext->GetWorld():nullptr;
 if(!World||!Data||!World->GetPackage()->GetName().EndsWith(TEXT("/AbandonedSchool"))) {Report=TEXT("Expected maintained AbandonedSchool world and data asset.");return false;}
 TArray<FTriangle> Surfaces,Walls;TMap<int32,double> HeightAreas;int32 Components=0,Missing=0;
 TArray<AActor*> Actors;for(TActorIterator<AActor> It(World);It;++It)Actors.Add(*It);
 Actors.Sort([](const AActor& A,const AActor& B){return A.GetPathName()<B.GetPathName();});
 for(AActor* A:Actors)
 {
  TInlineComponentArray<UStaticMeshComponent*> Meshes(A);
  for(UStaticMeshComponent* C:Meshes)
  {
   UStaticMesh* M=C->GetStaticMesh();if(!M||!IsStructure(A->GetActorLabel(),M->GetPathName()))continue;
   const FStaticMeshRenderData* Render=M->GetRenderData();if(!Render||Render->LODResources.IsEmpty()){++Missing;continue;}
   const auto& LOD=Render->LODResources[0];const auto& Vert=LOD.VertexBuffers.PositionVertexBuffer;
   if(!Vert.GetNumVertices()||!LOD.IndexBuffer.GetNumIndices()){++Missing;continue;}
   const bool FloorSource=IsFloorSource(A->GetActorLabel(),M->GetPathName());
   const FString MeshPath=M->GetPathName().ToLower();
   // A whole-component top trace cannot preserve vertically stacked instances.
   const bool CollisionFloor=FloorSource&&UsesCollisionFloorRaster(MeshPath)&&!Cast<UInstancedStaticMeshComponent>(C);
   if(CollisionFloor)
   {
    if(!C->IsQueryCollisionEnabled()||C->GetCollisionResponseToChannel(ECC_Pawn)!=ECR_Block)continue;
    // Bounds only enumerate probe locations. A cell becomes floor exclusively
    // when the component's simple collision confirms a walkable surface below.
    const FBox B=C->Bounds.GetBox();
    const FVector P0(B.Min.X,B.Min.Y,B.Max.Z),P1(B.Max.X,B.Min.Y,B.Max.Z);
    const FVector P2(B.Max.X,B.Max.Y,B.Max.Z),P3(B.Min.X,B.Max.Y,B.Max.Z);
    Surfaces.Add(FTriangle{P0,P1,P2,false,C});
    Surfaces.Add(FTriangle{P0,P2,P3,false,C});
   }
   const bool CheckClearance=MeshPath.Contains(TEXT("shell"))||MeshPath.Contains(TEXT("/environments/cave/"))||MeshPath.Contains(TEXT("/props_mesas/"))||MeshPath.Contains(TEXT("sm_school_corridor_dummy"));
   ++Components;TArray<FTransform> Transforms;
   if(auto* ISM=Cast<UInstancedStaticMeshComponent>(C)){for(int32 I=0;I<ISM->GetInstanceCount();++I){FTransform T;if(ISM->GetInstanceTransform(I,T,true))Transforms.Add(T);}}
   else Transforms.Add(C->GetComponentTransform());
   const FIndexArrayView Indices=LOD.IndexBuffer.GetArrayView();
   for(const FTransform& Transform:Transforms)for(int32 I=0;I+2<Indices.Num();I+=3)
   {
    FTriangle T{Transform.TransformPosition(FVector(Vert.VertexPosition(Indices[I]))),Transform.TransformPosition(FVector(Vert.VertexPosition(Indices[I+1]))),Transform.TransformPosition(FVector(Vert.VertexPosition(Indices[I+2])))};
    FVector N=FVector::CrossProduct(T.B-T.A,T.C-T.A);const double Area=N.Size()*.5;if(Area<1)continue;
    // Mirrored instances reverse triangle winding.
    if(Transform.GetDeterminant()<0)N=-N;
    const double NZ=N.Z/(Area*2);
    if(FloorSource&&NZ>.7)
    {
     T.bCheckClearance=CheckClearance;
     if(!CollisionFloor)Surfaces.Add(T);
     if(NZ>.985){const int32 H=FMath::RoundToInt((T.A.Z+T.B.Z+T.C.Z)/300.)*100;HeightAreas.FindOrAdd(H)+=Area;}
    }
    else if(!CollisionFloor&&FMath::Abs(NZ)<.55)Walls.Add(T);
   }
  }
 }
 TArray<int32> Heights;for(const auto& H:HeightAreas)if(H.Value>=20000)Heights.Add(H.Key);Heights.Sort();
 if(Heights.IsEmpty()||Heights.Num()>256||Surfaces.IsEmpty()||Missing){Report=FString::Printf(TEXT("Rejected: layers=%d surfaces=%d unavailable structural meshes=%d"),Heights.Num(),Surfaces.Num(),Missing);return false;}
 TArray<FLayer> Layers;for(int32 H:Heights){FLayer L;L.Height=H;Layers.Add(MoveTemp(L));}
 int64 Work=0,SampleCount=0;int32 ClearanceRejected=0;
 FCollisionObjectQueryParams StaticObjects;StaticObjects.AddObjectTypesToQuery(ECC_WorldStatic);
 const FCollisionQueryParams ClearanceParams(SCENE_QUERY_STAT(MinimapHeadroom),false);
 TMap<FIntVector,bool> ClearanceCache;
 for(const FTriangle& T:Surfaces)
 {
  const int32 X0=FMath::FloorToInt(FMath::Min3(T.A.X,T.B.X,T.C.X)/Cell),X1=FMath::FloorToInt(FMath::Max3(T.A.X,T.B.X,T.C.X)/Cell);
  const int32 Y0=FMath::FloorToInt(FMath::Min3(T.A.Y,T.B.Y,T.C.Y)/Cell),Y1=FMath::FloorToInt(FMath::Max3(T.A.Y,T.B.Y,T.C.Y)/Cell);
  Work+=int64(X1-X0+1)*(Y1-Y0+1);if(Work>MaxWork){Report=TEXT("Rejected: surface raster work limit exceeded; partition geometry, do not coarsen cells.");return false;}
  for(int32 Y=Y0;Y<=Y1;++Y)for(int32 X=X0;X<=X1;++X)
  {
   double Z;if(!SurfaceAt(T,FVector2D((X+.5)*Cell,(Y+.5)*Cell),Z))continue;
   if(T.CollisionSurface)
   {
    FHitResult Hit;const auto Bounds=T.CollisionSurface->Bounds;
    const FVector Top((X+.5)*Cell,(Y+.5)*Cell,Bounds.Origin.Z+Bounds.BoxExtent.Z+100);
    const FVector Bottom(Top.X,Top.Y,Bounds.Origin.Z-Bounds.BoxExtent.Z-100);
    if(!T.CollisionSurface->LineTraceComponent(Hit,Top,Bottom,FCollisionQueryParams(SCENE_QUERY_STAT(MinimapRampGround),false))||Hit.ImpactNormal.Z<.7)continue;
    Z=Hit.ImpactPoint.Z;
   }
   if(T.bCheckClearance)
   {
    const FIntVector K(X,Y,FMath::RoundToInt(Z));bool* Cached=ClearanceCache.Find(K);bool Blocked=false;
    if(Cached)Blocked=*Cached;
    // Test torso/head clearance, leaving the feet region to the sampled slope.
    // A full capsule rooted at triangle Z would incorrectly reject uphill ground.
    else {Blocked=World->OverlapAnyTestByObjectType(FVector((X+.5)*Cell,(Y+.5)*Cell,Z+120),FQuat::Identity,StaticObjects,FCollisionShape::MakeCapsule(28,60),ClearanceParams);ClearanceCache.Add(K,Blocked);}
    if(Blocked){++ClearanceRejected;continue;}
   }
   auto& L=Layers[NearestLayer(Layers,Z)];const FIntPoint Key(X,Y);FSample* Old=L.Samples.Find(Key);
   if(!Old){L.Samples.Add(Key,FSample{float(Z)});++SampleCount;}
   else if(FMath::Abs(Z-L.Height)<FMath::Abs(Old->Z-L.Height))Old->Z=Z;
  }
  if(SampleCount>MaxCells){Report=TEXT("Rejected: occupied cell memory limit exceeded.");return false;}
 }
 TArray<FMinimapFloorData> Floors;int64 GridCells=0;int32 FloorCells=0,WallCells=0;
 for(const FLayer& L:Layers)
 {
  if(L.Samples.Num()<8)continue;
  FIntPoint Min(MAX_int32,MAX_int32),Max(MIN_int32,MIN_int32);
  for(const auto& S:L.Samples){Min.X=FMath::Min(Min.X,S.Key.X);Min.Y=FMath::Min(Min.Y,S.Key.Y);Max.X=FMath::Max(Max.X,S.Key.X);Max.Y=FMath::Max(Max.Y,S.Key.Y);}
  Min-=FIntPoint(1,1);Max+=FIntPoint(1,1);
  FMinimapFloorData F;F.FloorId=FName(*FString::Printf(TEXT("Height_%d"),L.Height));F.Label=FText::FromString(FString::Printf(TEXT("높이 %.1fm"),L.Height/100.));F.ReferenceZ=L.Height;
  F.Origin=FVector2D(Min.X*Cell,Min.Y*Cell);F.CellSize=Cell;F.Width=Max.X-Min.X+1;F.Height=Max.Y-Min.Y+1;
  const int64 Count=int64(F.Width)*F.Height;GridCells+=Count;if(GridCells>MaxCells){Report=TEXT("Rejected: cropped grids exceed memory cap. Split regions; 50cm cells retained.");return false;}
  F.Cells.Init(0,int32(Count));F.SurfaceZ.Init(L.Height,int32(Count));F.MinZ=FLT_MAX;F.MaxZ=-FLT_MAX;
  for(const auto& S:L.Samples){const int32 I=(S.Key.Y-Min.Y)*F.Width+S.Key.X-Min.X;F.Cells[I]=1;F.SurfaceZ[I]=S.Value.Z;F.MinZ=FMath::Min(F.MinZ,S.Value.Z);F.MaxZ=FMath::Max(F.MaxZ,S.Value.Z);}
  for(const FTriangle& T:Walls)
  {
   if(FMath::Max3(T.A.Z,T.B.Z,T.C.Z)<F.MinZ+60||FMath::Min3(T.A.Z,T.B.Z,T.C.Z)>F.MaxZ+60)continue;
   const int32 X0=FMath::Max(Min.X,FMath::FloorToInt(FMath::Min3(T.A.X,T.B.X,T.C.X)/Cell)),X1=FMath::Min(Max.X,FMath::FloorToInt(FMath::Max3(T.A.X,T.B.X,T.C.X)/Cell));
   const int32 Y0=FMath::Max(Min.Y,FMath::FloorToInt(FMath::Min3(T.A.Y,T.B.Y,T.C.Y)/Cell)),Y1=FMath::Min(Max.Y,FMath::FloorToInt(FMath::Max3(T.A.Y,T.B.Y,T.C.Y)/Cell));
   if(X1<X0||Y1<Y0)continue;Work+=int64(X1-X0+1)*(Y1-Y0+1);if(Work>MaxWork){Report=TEXT("Rejected: wall raster work limit exceeded.");return false;}
   for(int32 Y=Y0;Y<=Y1;++Y)for(int32 X=X0;X<=X1;++X)
   {
    const int32 I=(Y-Min.Y)*F.Width+X-Min.X;
    // Only barriers touching known floor are retained. Slice at each sampled surface,
    // so sloped floor corridors do not inherit a distant layer's wall height.
    bool Near=F.Cells[I]!=0;double Z=F.SurfaceZ[I];
    if(!Near)for(int32 DY=-1;DY<=1&&!Near;++DY)for(int32 DX=-1;DX<=1;++DX)
    {const auto* S=L.Samples.Find(FIntPoint(X+DX,Y+DY));if(S){Near=true;Z=S->Z;break;}}
    if(Near&&WallAt(T,Z+60,FVector2D(X*Cell,Y*Cell)))F.Cells[I]=2;
   }
  }
  for(uint8 V:F.Cells){FloorCells+=V==1;WallCells+=V==2;}
  F.MinZ-=100;F.MaxZ+=200;Floors.Add(MoveTemp(F));
 }
 if(Floors.IsEmpty()||FloorCells<100||WallCells<10){Report=TEXT("Rejected: empty/implausible floor or wall raster.");return false;}
 // Validate the current spawn's real collision ground, not an obsolete fixed Z=0.
 bool StartSupported=false;FVector StartGround=FVector::ZeroVector;bool HasStartGround=false;
 for(TActorIterator<APlayerStart> It(World);It;++It)
 {
  FHitResult Hit;const FVector Start=It->GetActorLocation();
  if(World->LineTraceSingleByChannel(Hit,Start,Start-FVector(0,0,2000),ECC_Visibility))
  {
   StartGround=Hit.ImpactPoint;HasStartGround=true;
   for(const auto& F:Floors){const int32 I=F.IndexAt(FVector2D(StartGround));if(I!=INDEX_NONE&&F.Cells[I]==1&&FMath::Abs(F.SurfaceZ[I]-StartGround.Z)<=75)StartSupported=true;}
  }
  break;
 }
 if(!StartSupported)
 {
  Report=FString::Printf(TEXT("Rejected: current PlayerStart lacks supported ground (hit=%d, %s). Samples:"),HasStartGround,*StartGround.ToString());
  for(const auto& F:Floors){const int32 I=F.IndexAt(FVector2D(StartGround));if(I!=INDEX_NONE&&F.Cells[I])Report+=FString::Printf(TEXT(" %s:%d@%.1f"),*F.FloorId.ToString(),F.Cells[I],F.SurfaceZ[I]);}
  return false;
 }
 TArray<FMinimapMarkerData> Markers;int32 Unresolved=0;
 auto AddMarker=[&](AActor* A,const FString& Role,FVector P,EMinimapMarkerKind Kind,FVector Other,bool Connection)
 {
  FMinimapMarkerData M;M.SourceId=A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens)+TEXT(":")+Role;M.Position=P;M.Kind=Kind;
  const int32 F=ResolveFloor(Floors,P),To=Connection?ResolveFloor(Floors,Other):INDEX_NONE;
  if(F!=INDEX_NONE)M.FloorId=Floors[F].FloorId;
  if(To!=INDEX_NONE)M.ConnectedFloorId=Floors[To].FloorId;
  M.bConnectionVerified=Kind==EMinimapMarkerKind::Door||(Connection&&F!=INDEX_NONE&&To!=INDEX_NONE&&F!=To);
  M.bHidden=F==INDEX_NONE||!M.bConnectionVerified;if(M.bHidden)++Unresolved;Markers.Add(MoveTemp(M));
 };
 for(AActor* A:Actors)
 {
  const FString C=A->GetClass()->GetName(),L=A->GetActorLabel();const FVector P=A->GetActorLocation();
  if(C==TEXT("BP_School_Door_C")||C==TEXT("BP_School_Gate_C")||C==TEXT("BP_BattleGate_C")||C==TEXT("BP_Suzume_Door_C"))AddMarker(A,TEXT("door"),P,EMinimapMarkerKind::Door,P,false);
  else if(C==TEXT("BP_Ladder_C"))
  {
   const USplineComponent* S=A->FindComponentByClass<USplineComponent>();
   if(S&&S->GetNumberOfSplinePoints()>1){const FVector Bottom=S->GetLocationAtSplinePoint(0,ESplineCoordinateSpace::World),Top=S->GetLocationAtSplinePoint(S->GetNumberOfSplinePoints()-1,ESplineCoordinateSpace::World);AddMarker(A,TEXT("ladder-bottom"),Bottom,EMinimapMarkerKind::Stairs,Top,true);AddMarker(A,TEXT("ladder-top"),Top,EMinimapMarkerKind::Stairs,Bottom,true);}
   else AddMarker(A,TEXT("ladder-candidate"),P,EMinimapMarkerKind::Stairs,P,false);
  }
  else if(C==TEXT("BP_School_Trapdoor_C")||C==TEXT("BP_FallingElevator_C"))AddMarker(A,TEXT("connection-candidate"),P,EMinimapMarkerKind::Stairs,P,false);
  else if(L==TEXT("spiral_stair_1")||L==TEXT("spiral_stair_2")||L==TEXT("SM_AbandonedSchool_ClockTower_SpiralStair"))
  {
   // Static mesh names prove a stair candidate, not arrival positions. Preserve as an
   // editable candidate instead of inventing connectivity from an AABB extremum.
   AddMarker(A,TEXT("stair-assembly-candidate"),P,EMinimapMarkerKind::Stairs,P,false);
  }
 }
 Data->Modify();Data->RegionId=TEXT("AbandonedSchool");Data->RegionLabel=FText::FromString(TEXT("폐교"));Data->Floors=MoveTemp(Floors);Data->GeneratedMarkers=MoveTemp(Markers);
 int32 BoundObjectives=0,UnboundObjectives=0;
 if(const UQuestDefinition* Q=LoadObject<UQuestDefinition>(nullptr,TEXT("/Game/Constellation/Gameplay/Quests/Data/DA_MainQuest_ExitSchool.DA_MainQuest_ExitSchool")))
 {
  for(int32 Step=0;Step<Q->ProgressSteps.Num();++Step)for(int32 Inner=0;Inner<Q->ProgressSteps[Step].TargetPositions.Num();++Inner)
  {
   if(Data->Objectives.ContainsByPredicate([&](const FMinimapObjectiveBinding& B){return B.QuestId==Q->QuestID&&B.Progress==Step+1&&B.InnerProgress==Inner;}))continue;
   const FVector P=Q->ProgressSteps[Step].TargetPositions[Inner];const int32 F=ResolveFloor(Data->Floors,P);
   FMinimapObjectiveBinding B;B.bGenerated=true;B.QuestId=Q->QuestID;B.Progress=Step+1;B.InnerProgress=Inner;
   if(F==INDEX_NONE)++UnboundObjectives;else B.FloorId=Data->Floors[F].FloorId;
   Data->Objectives.Add(B);++BoundObjectives;
  }
 }
 Data->MarkPackageDirty();
 Report=FString::Printf(TEXT("components=%d upward_triangles=%d wall_triangles=%d layers=%d grid_cells=%lld floor_cells=%d wall_cells=%d markers=%d hidden_candidates=%d objectives_added=%d objectives_unresolved=%d clearance_rejected=%d; cell_size=50cm; overrides/manual/objectives preserved; floor labels describe height, not architectural floor numbers"),Components,Surfaces.Num(),Walls.Num(),Data->Floors.Num(),GridCells,FloorCells,WallCells,Data->GeneratedMarkers.Num(),Unresolved,BoundObjectives,UnboundObjectives,ClearanceRejected);
 return true;
}

FString UMinimapEditorLibrary::BuildSchoolMap(UObject* WorldContext,UMinimapRegionData* Data){FString Report;bool Ok=GenerateSchoolMap(WorldContext,Data,Report);return (Ok?TEXT("OK "):TEXT("ERROR "))+Report;}

