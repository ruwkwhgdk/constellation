#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "GameFramework/Actor.h"
#include "MinimapTypes.h"
#include "MinimapWorldSubsystem.generated.h"
class UMinimapWidget;
UCLASS(Blueprintable) class CONSTELLATION_API AMinimapRegionActor:public AActor
{
 GENERATED_BODY()
public:
 AMinimapRegionActor();
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Minimap") TObjectPtr<UMinimapRegionData> Data;
};
USTRUCT(BlueprintType) struct FMinimapObjectiveView
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) bool bValid=false;
 UPROPERTY(BlueprintReadOnly) bool bSameFloor=false;
 UPROPERTY(BlueprintReadOnly) FVector Position=FVector::ZeroVector;
 UPROPERTY(BlueprintReadOnly) FName FloorId;
 UPROPERTY(BlueprintReadOnly) FText FloorLabel;
};
UCLASS() class CONSTELLATION_API UMinimapWorldSubsystem:public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual bool DoesSupportWorldType(EWorldType::Type T)const override{return T==EWorldType::Game||T==EWorldType::PIE;}
 virtual void Tick(float Delta)override;
 virtual void Deinitialize()override;
 virtual TStatId GetStatId()const override{RETURN_QUICK_DECLARE_CYCLE_STAT(UMinimapWorldSubsystem,STATGROUP_Tickables);}
 UMinimapRegionData* GetRegion()const{return Region;}
 UMinimapWidget* GetHUDWidget()const{return Widget;}
 const FMinimapFloorData* GetFloor()const{return Region&&Region->Floors.IsValidIndex(FloorIndex)?&Region->Floors[FloorIndex]:nullptr;}
 FVector GetPawnPosition()const{return PawnPosition;}
 float GetHeadingYaw()const{return HeadingYaw;}
 float GetCameraYaw()const{return CameraYaw;}
 float GetCameraFOV()const{return CameraFOV;}
 const FMinimapObjectiveView& GetObjective()const{return Objective;}
 const TArray<FMinimapMarkerData>& GetMarkers()const{return Markers;}
 bool IsDiscovered(const FMinimapFloorData& Floor,int32 Index)const;
 UFUNCTION(BlueprintCallable,Category="Minimap") void RevealNearby(float Radius);
 UFUNCTION(BlueprintCallable,Category="Minimap") void UnlockRegion(FName RegionId);
 UFUNCTION(BlueprintCallable,Category="Minimap") void SetObjectiveOverride(FName RegionId,FName FloorId,FVector Position);
 UFUNCTION(BlueprintCallable,Category="Minimap") void ClearObjectiveOverride();
 UFUNCTION(BlueprintPure,Category="Minimap") FName GetCurrentFloorId()const;
 UFUNCTION(BlueprintPure,Category="Minimap") int32 GetDiscoveredCellCount()const;
private:
 UPROPERTY() TObjectPtr<UMinimapRegionData> Region;
 UPROPERTY() TObjectPtr<UMinimapWidget> Widget;
 TArray<FMinimapMarkerData> Markers;
 FVector PawnPosition=FVector::ZeroVector;
 float HeadingYaw=0,CameraYaw=0,CameraFOV=70,Accumulator=0;
 int32 FloorIndex=INDEX_NONE;
 float UnresolvedSeconds=0;
 bool bCanReveal=false;
 FVector ConfirmedGround=FVector::ZeroVector;
 FMinimapObjectiveView Objective;
 bool bOverride=false;
 FName OverrideRegion,OverrideFloor;
 FVector OverridePosition=FVector::ZeroVector;
 void UpdateObjective();
};
