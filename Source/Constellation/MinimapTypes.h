#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MinimapTypes.generated.h"

UENUM(BlueprintType) enum class EMinimapRevealMode:uint8 { Exploration, ObjectUnlock };
UENUM(BlueprintType) enum class EMinimapMarkerKind:uint8 { Door, Stairs };
USTRUCT(BlueprintType) struct CONSTELLATION_API FMinimapFloorData
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName FloorId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FText Label;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FVector2D Origin=FVector2D::ZeroVector;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float CellSize=50;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) int32 Width=0;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) int32 Height=0;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float ReferenceZ=0;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float MinZ=-100;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float MaxZ=100;
 // 0 = absent, 1 = real floor, 2 = structural wall. Height is actual sampled surface Z.
 UPROPERTY() TArray<uint8> Cells;
 UPROPERTY() TArray<float> SurfaceZ;
 bool IsValid()const;
 int32 IndexAt(FVector2D World)const;
 FVector2D Center(int32 Index)const;
 FIntPoint GlobalCell(int32 Index)const;
 bool HasSight(int32 From,int32 To)const;
 TArray<int32> VisibleCells(FVector2D Position,float Radius)const;
};
USTRUCT(BlueprintType) struct FMinimapMarkerData
{
 GENERATED_BODY()
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) FString SourceId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FVector Position=FVector::ZeroVector;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName FloorId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName ConnectedFloorId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) EMinimapMarkerKind Kind=EMinimapMarkerKind::Door;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bHidden=false;
 // Unverified connections are retained for authoring, never silently presented as confirmed stairs.
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bConnectionVerified=true;
};
USTRUCT(BlueprintType) struct FMinimapMarkerOverride
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString SourceId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FVector Offset=FVector::ZeroVector;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bHidden=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bOverrideKind=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) EMinimapMarkerKind Kind=EMinimapMarkerKind::Door;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName FloorId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName ConnectedFloorId;
};
USTRUCT(BlueprintType) struct FMinimapObjectiveBinding
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bGenerated=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName QuestId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) int32 Progress=1;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) int32 InnerProgress=0;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName FloorId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bOverridePosition=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FVector Position=FVector::ZeroVector;
};
UCLASS(BlueprintType) class CONSTELLATION_API UMinimapRegionData:public UDataAsset
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FName RegionId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FText RegionLabel;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) EMinimapRevealMode RevealMode=EMinimapRevealMode::Exploration;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float RevealRadius=600;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float ViewRadius=1800;
 // North = world +X by default. Screen right = +Y.
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float NorthYaw=0;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FMinimapFloorData> Floors;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TArray<FMinimapMarkerData> GeneratedMarkers;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FMinimapMarkerOverride> MarkerOverrides;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FMinimapMarkerData> ManualMarkers;
 // Explicit region association; do not infer target map from coordinates alone.
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FMinimapObjectiveBinding> Objectives;
 int32 FindFloor(FVector Position,int32 Previous=INDEX_NONE,float Hysteresis=40,float MaxHeightDifference=250)const;
 // Grounded-only recovery of a small raster gap. Caller verifies physical connectivity.
 int32 FindNearbyFloor(FVector Ground,int32 Previous,TFunctionRef<bool(FVector)> IsConnected)const;
 TArray<FMinimapMarkerData> ResolveMarkers()const;
};
USTRUCT() struct FMinimapExploredFloor
{
 GENERATED_BODY()
 UPROPERTY() FName RegionId;
 UPROPERTY() FName FloorId;
 UPROPERTY() int32 CellSize=50;
 UPROPERTY() TArray<FIntPoint> Cells;
};
USTRUCT() struct CONSTELLATION_API FMinimapSaveData
{
 GENERATED_BODY()
 UPROPERTY() int32 Version=1;
 UPROPERTY() TArray<FMinimapExploredFloor> Floors;
 UPROPERTY() TArray<FName> UnlockedRegions;
 void Merge(const FMinimapSaveData& Other);
};
