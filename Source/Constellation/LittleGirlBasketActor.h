#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LittleGirlBasketActor.generated.h"
class UStaticMeshComponent;
class UStaticMesh;
class AStaticMeshActor;
/** Level-owned prop: attaching to a hand does not transfer ownership to the girl. */
UCLASS(BlueprintType)
class CONSTELLATION_API ALittleGirlBasketActor : public AActor
{
 GENERATED_BODY()
public:
 ALittleGirlBasketActor();
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Basket") TObjectPtr<UStaticMeshComponent> BasketMesh;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Basket") TArray<TObjectPtr<UStaticMesh>> MushroomMeshes;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Basket") TArray<FTransform> MushroomTransforms;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Basket") FTransform GripOffset;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Basket") bool bDropped=false;
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="Basket") TArray<TObjectPtr<AStaticMeshActor>> Mushrooms;
 UFUNCTION(BlueprintCallable,Category="Basket") bool AttachToCarrier(USceneComponent* Carrier,FName HandBone=TEXT("hand_l"));
 UFUNCTION(BlueprintCallable,Category="Basket") void Drop(FVector ReleaseVelocity=FVector::ZeroVector);
};
