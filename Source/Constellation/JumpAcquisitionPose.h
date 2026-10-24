#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimNode_LinkedInputPose.h"
#include "JumpAcquisitionPose.generated.h"
class USkeletalMeshComponent;
// Temporary post-process over the live idle pose. Never replaces the player's ABP.
UCLASS(Transient,NotBlueprintable)
class CONSTELLATION_API UJumpAcquisitionPose : public UAnimInstance
{
 GENERATED_BODY()
public:
 UPROPERTY(Transient) FAnimNode_LinkedInputPose InputPose;
 FVector HandTarget=FVector::ZeroVector,LookTarget=FVector::ZeroVector;
 FVector HeadForward=FVector::ForwardVector;
 float HandWeight=0,LookWeight=0;
 virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
 virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) override;
 static bool Install(USkeletalMeshComponent* Mesh);
 static void Remove(USkeletalMeshComponent* Mesh);
};
