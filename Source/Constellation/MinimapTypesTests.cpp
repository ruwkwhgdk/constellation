#if WITH_DEV_AUTOMATION_TESTS
#include "MinimapTypes.h"
#include "Misc/AutomationTest.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMinimapGridTest,"Constellation.Minimap.GridOcclusion",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMinimapGridTest::RunTest(const FString&)
{
 FMinimapFloorData F;F.Width=5;F.Height=5;F.CellSize=50;F.Cells.Init(1,25);F.SurfaceZ.Init(0,25);
 for(int Y=0;Y<5;++Y)F.Cells[Y*5+2]=2;
 TestTrue(TEXT("Near wall is visible"),F.HasSight(10,12));TestFalse(TEXT("Far room blocked"),F.HasSight(10,14));
 TestFalse(TEXT("Outside is not visible"),F.HasSight(0,25));
 F.Cells.Init(1,25);F.Cells[1]=2;F.Cells[5]=2;TestFalse(TEXT("No diagonal corner leak"),F.HasSight(0,6));
 TestEqual(TEXT("Negative world coordinate stays outside"),F.IndexAt(FVector2D(-1,1)),INDEX_NONE);
 TestEqual(TEXT("Global cells independent of cropped origin"),F.GlobalCell(0),FIntPoint(0,0));F.Origin=FVector2D(-100,50);TestEqual(TEXT("Global origin handles negative coordinates"),F.GlobalCell(0),FIntPoint(-2,1));
 auto* Data=NewObject<UMinimapRegionData>();F.Origin=FVector2D::ZeroVector;F.ReferenceZ=0;F.FloorId="Lower";F.Cells.Init(1,25);Data->Floors.Add(F);F.ReferenceZ=500;F.SurfaceZ.Init(500,25);F.MinZ=400;F.MaxZ=600;F.FloorId="Upper";Data->Floors.Add(F);
 TestEqual(TEXT("Overlapping XY uses height"),Data->FindFloor(FVector(25,25,500)),1);
 FMinimapMarkerData M;M.SourceId="Stable";M.Position=FVector(1,2,3);Data->GeneratedMarkers.Add(M);FMinimapMarkerOverride O;O.SourceId="Stable";O.Offset=FVector(10,0,0);O.bHidden=true;Data->MarkerOverrides.Add(O);
 auto Resolved=Data->ResolveMarkers();TestTrue(TEXT("Manual exclusion retained"),Resolved[0].bHidden);TestEqual(TEXT("Manual offset retained"),Resolved[0].Position.X,11.0);TestEqual(TEXT("Repeated resolution does not duplicate"),Data->ResolveMarkers().Num(),1);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMinimapSlopeRecoveryTest,"Constellation.Minimap.SlopeRecovery",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMinimapSlopeRecoveryTest::RunTest(const FString&)
{
 auto* Data=NewObject<UMinimapRegionData>();
 FMinimapFloorData F;F.Width=5;F.Height=5;F.CellSize=50;F.Cells.Init(1,25);F.SurfaceZ.Init(0,25);
 F.Cells[12]=0;Data->Floors.Add(F);
 const FVector Ground(125,125,20);
 TestEqual(TEXT("Missing center cell fails strict lookup"),Data->FindFloor(Ground),INDEX_NONE);
 TestEqual(TEXT("Connected nearby surface bridges raster gap"),Data->FindNearbyFloor(Ground,INDEX_NONE,[](FVector){return true;}),0);
 TestEqual(TEXT("Collision barrier rejects nearby floor"),Data->FindNearbyFloor(Ground,INDEX_NONE,[](FVector){return false;}),INDEX_NONE);
 Data->Floors[0].SurfaceZ.Init(300,25);
 TestEqual(TEXT("Overhead floor never fills gap"),Data->FindNearbyFloor(Ground,INDEX_NONE,[](FVector){return true;}),INDEX_NONE);
 Data->Floors[0].Cells[12]=1;Data->Floors[0].SurfaceZ.Init(200,25);
 TestEqual(TEXT("Ground contact rejects another platform within legacy height tolerance"),Data->FindFloor(Ground,INDEX_NONE,40,75),INDEX_NONE);
 Data->Floors[0].SurfaceZ.Init(0,25);Data->Floors[0].Cells[12]=2;
 TestEqual(TEXT("Wall cell cannot seed recovery"),Data->FindNearbyFloor(Ground,INDEX_NONE,[](FVector){return true;}),INDEX_NONE);
 TestEqual(TEXT("Outside map cannot snap to remote floor"),Data->FindNearbyFloor(FVector(900,900,0),INDEX_NONE,[](FVector){return true;}),INDEX_NONE);
 return true;
}
#endif
