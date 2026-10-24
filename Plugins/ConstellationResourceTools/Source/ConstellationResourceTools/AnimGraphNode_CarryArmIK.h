#pragma once
#include "CoreMinimal.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "AnimNode_CarryArmIK.h"
#include "AnimGraphNode_CarryArmIK.generated.h"

UCLASS()
class CONSTELLATIONRESOURCETOOLS_API UAnimGraphNode_CarryArmIK : public UAnimGraphNode_SkeletalControlBase
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category=Settings) FAnimNode_CarryArmIK Node;
    virtual FText GetNodeTitle(ENodeTitleType::Type) const override { return FText::FromString(TEXT("Carry Anatomical Arm IK")); }
protected:
    virtual FText GetControllerDescription() const override { return FText::FromString(TEXT("Carry Anatomical Arm IK")); }
    virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &Node; }
};
