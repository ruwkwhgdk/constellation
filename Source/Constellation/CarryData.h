#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "CarryData.generated.h"

class UAnimMontage;
class UMaterialInterface;
class UStringTable;

USTRUCT(BlueprintType)
struct CONSTELLATION_API FCarrySettingsRow : public FTableRowBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float CharacterWeightKg = 50.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float LiftWeightRatio = .2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float Reach = 160.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float MaxThrowDistance = 800.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float MinFlightTime = .4f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float MaxFlightTime = 1.3f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FName CarrySocket = TEXT("spine_03");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FName WeaponComponentName = TEXT("Sword");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FTransform ReleaseOffset = FTransform(FRotator::ZeroRotator,FVector(65,0,30));
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UAnimMontage> PickupMontage = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UAnimMontage> PlaceMontage = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UAnimMontage> ThrowMontage = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UAnimMontage> HoldMontage = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UAnimMontage> AimMontage = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UMaterialInterface> PreviewMaterial = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PickupPlayRate = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PlacePlayRate = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float ThrowPlayRate = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PickupContactTime = .45f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PickupDuration = .9f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PlaceContactTime = .55f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float PlaceDuration = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float ThrowContactTime = .25f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float ThrowDuration = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings", meta=(ClampMin="0.01"))
    float NoticeDuration = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    TObjectPtr<UStringTable> Messages = nullptr;
};

USTRUCT(BlueprintType)
struct CONSTELLATION_API FHoldableItemRow : public FTableRowBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FTransform CarryOffset = FTransform(FRotator::ZeroRotator,FVector(32,0,30));
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FTransform LeftHandGrip = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FTransform RightHandGrip = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    bool bCanThrow = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Settings")
    FRotator PlaceRotation = FRotator::ZeroRotator;
};
