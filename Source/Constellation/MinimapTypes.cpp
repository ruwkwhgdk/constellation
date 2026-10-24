#include "MinimapTypes.h"
bool FMinimapFloorData::IsValid()const{return Width>0&&Height>0&&int64(Width)*Height<=4000000&&Cells.Num()==int64(Width)*Height&&CellSize>=10&&FMath::IsFinite(CellSize)&&!Origin.ContainsNaN();}
int32 FMinimapFloorData::IndexAt(FVector2D P)const
{
 if(!IsValid()||P.ContainsNaN())return INDEX_NONE;const FVector2D C=(P-Origin)/CellSize;const int32 X=FMath::FloorToInt(C.X),Y=FMath::FloorToInt(C.Y);return X>=0&&Y>=0&&X<Width&&Y<Height?Y*Width+X:INDEX_NONE;
}
FVector2D FMinimapFloorData::Center(int32 I)const{return Width>0?Origin+FVector2D(I%Width+.5,I/Width+.5)*CellSize:Origin;}
FIntPoint FMinimapFloorData::GlobalCell(int32 I)const{const FVector2D P=Center(I)/CellSize;return FIntPoint(FMath::FloorToInt(P.X),FMath::FloorToInt(P.Y));}
bool FMinimapFloorData::HasSight(int32 A,int32 B)const
{
 if(!IsValid()||!Cells.IsValidIndex(A)||!Cells.IsValidIndex(B)||Cells[A]!=1||Cells[B]==0)return false;
 if(A==B)return true;
 int32 X=A%Width,Y=A/Width;const int32 TX=B%Width,TY=B/Width,DX=FMath::Abs(TX-X),DY=FMath::Abs(TY-Y),SX=TX>X?1:-1,SY=TY>Y?1:-1;int32 IX=0,IY=0;
 auto Clear=[&](int32 PX,int32 PY){return PX>=0&&PY>=0&&PX<Width&&PY<Height&&Cells[PY*Width+PX]==1;};
 // Supercover traversal includes both neighboring cells at diagonal corners.
 while(IX<DX||IY<DY)
 {
  const int64 Cross=int64(1+2*IX)*DY-int64(1+2*IY)*DX;
  if(Cross==0){if(!Clear(X+SX,Y)||!Clear(X,Y+SY))return false;X+=SX;Y+=SY;++IX;++IY;}
  else if(Cross<0){X+=SX;++IX;}else{Y+=SY;++IY;}
  if(X==TX&&Y==TY)return true;if(!Clear(X,Y))return false;
 }
 return true;
}
TArray<int32> FMinimapFloorData::VisibleCells(FVector2D Position,float Radius)const
{
 TArray<int32> Out;const int32 Start=IndexAt(Position);if(Start==INDEX_NONE||!FMath::IsFinite(Radius)||Radius<=0)return Out;
 const int32 R=FMath::CeilToInt(FMath::Min(Radius,10000.f)/CellSize);const int32 X=Start%Width,Y=Start/Width;
 for(int32 J=FMath::Max(0,Y-R);J<=FMath::Min(Height-1,Y+R);++J)for(int32 I=FMath::Max(0,X-R);I<=FMath::Min(Width-1,X+R);++I){const int32 N=J*Width+I;if(FVector2D::DistSquared(Center(N),Position)<=FMath::Square(Radius)&&HasSight(Start,N))Out.Add(N);}return Out;
}
int32 UMinimapRegionData::FindFloor(FVector P,int32 Previous,float Hysteresis,float MaxHeightDifference)const
{
 float Best=FLT_MAX;int32 Result=INDEX_NONE;
 for(int32 I=0;I<Floors.Num();++I)
 {
  const auto& F=Floors[I];int32 Cell=F.IndexAt(FVector2D(P));if(Cell==INDEX_NONE||F.Cells[Cell]!=1)continue;
  const float Z=F.SurfaceZ.IsValidIndex(Cell)?F.SurfaceZ[Cell]:F.ReferenceZ;float Dist=FMath::Abs(P.Z-Z);
  if(Dist>MaxHeightDifference)continue;if(I==Previous)Dist=FMath::Max(0.f,Dist-Hysteresis);if(Dist<Best){Best=Dist;Result=I;}
 }
 return Result;
}
int32 UMinimapRegionData::FindNearbyFloor(FVector Ground,int32 Previous,TFunctionRef<bool(FVector)> IsConnected)const
{
 if(Ground.ContainsNaN())return INDEX_NONE;
 float Best=FLT_MAX;int32 Result=INDEX_NONE;
 for(int32 I=0;I<Floors.Num();++I)
 {
  const auto& F=Floors[I];const int32 Center=F.IndexAt(FVector2D(Ground));
  if(Center==INDEX_NONE||F.Cells[Center]==2)continue;
  const int32 X=Center%F.Width,Y=Center/F.Width;
  for(int32 DY=-1;DY<=1;++DY)for(int32 DX=-1;DX<=1;++DX)
  {
   const int32 NX=X+DX,NY=Y+DY;if(NX<0||NY<0||NX>=F.Width||NY>=F.Height)continue;
   const int32 N=NY*F.Width+NX;if(F.Cells[N]!=1)continue;
   // Do not bridge diagonal wall corners, even when the center is a raster hole.
   if(DX&&DY&&(F.Cells[Y*F.Width+NX]==2||F.Cells[NY*F.Width+X]==2))continue;
   const FVector2D XY=F.Center(N);const float Z=F.SurfaceZ.IsValidIndex(N)?F.SurfaceZ[N]:F.ReferenceZ;
   const float Height=FMath::Abs(Ground.Z-Z),Distance=FVector2D::Distance(XY,FVector2D(Ground));
   if(Height>75||Distance>75)continue;
   const float Score=Height+Distance*.5f-(I==Previous?15.f:0.f);
   if(Score<Best&&IsConnected(FVector(XY,Z))){Best=Score;Result=I;}
  }
 }
 return Result;
}
TArray<FMinimapMarkerData> UMinimapRegionData::ResolveMarkers()const
{
 TArray<FMinimapMarkerData> Result;TSet<FString> Seen;
 for(const auto& List:{&GeneratedMarkers,&ManualMarkers})for(auto M:*List)
 {
  if(M.SourceId.IsEmpty()||Seen.Contains(M.SourceId))continue;Seen.Add(M.SourceId);
  for(const auto& O:MarkerOverrides)if(O.SourceId==M.SourceId){M.Position+=O.Offset;M.bHidden=O.bHidden;if(O.bOverrideKind)M.Kind=O.Kind;if(!O.FloorId.IsNone())M.FloorId=O.FloorId;if(!O.ConnectedFloorId.IsNone()){M.ConnectedFloorId=O.ConnectedFloorId;M.bConnectionVerified=true;}break;}
  Result.Add(M);
 }
 return Result;
}
