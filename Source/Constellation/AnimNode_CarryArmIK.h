#pragma once
#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "AnimNode_CarryArmIK.generated.h"

// Solve anatomical joints; interleaved twist bones remain on rigid arm segments.
USTRUCT(BlueprintInternalUseOnly)
struct CONSTELLATION_API FAnimNode_CarryArmIK : public FAnimNode_SkeletalControlBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=Target, meta=(PinShownByDefault))
    FTransform EffectorTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, Category=Target) bool bUseTargetRotation=false;
    UPROPERTY(EditAnywhere, Category=Solver) FBoneReference UpperArm;
    UPROPERTY(EditAnywhere, Category=Solver) FBoneReference UpperTwist;
    UPROPERTY(EditAnywhere, Category=Solver) FBoneReference Forearm;
    UPROPERTY(EditAnywhere, Category=Solver) FBoneReference ForearmTwist;
    UPROPERTY(EditAnywhere, Category=Solver) FBoneReference Hand;
    // None means component space; otherwise target is relative to this bone.
    UPROPERTY(EditAnywhere, Category=Target) FBoneReference TargetReference;
    virtual bool HasPreUpdate() const override { return true; }
    virtual void PreUpdate(const UAnimInstance* InAnimInstance) override;
    virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
    virtual bool IsValidToEvaluate(const USkeleton*, const FBoneContainer& Bones) override;
    virtual void InitializeBoneReferences(const FBoneContainer& Bones) override;
private:
    bool bPlaceTargetInComponentSpace=false;
};
