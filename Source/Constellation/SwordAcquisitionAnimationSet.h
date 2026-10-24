#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SwordAcquisitionAnimationSet.generated.h"
class UAnimMontage;
USTRUCT(BlueprintType)
struct FSwordAcquisitionClip
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere) TObjectPtr<UAnimMontage> Montage;
 UPROPERTY(EditAnywhere) bool bLoop=false;
 UPROPERTY(EditAnywhere) TArray<FTransform> SwordSamples;
};
UCLASS(BlueprintType)
class CONSTELLATION_API USwordAcquisitionAnimationSet : public UDataAsset
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere) TMap<FName,FSwordAcquisitionClip> Clips;
 UPROPERTY(EditAnywhere) float SampleRate=30.f;
 // Production mesh local coordinates to the delivered guard-centred prop.
 UPROPERTY(EditAnywhere) FTransform MeshToGuard;
};
