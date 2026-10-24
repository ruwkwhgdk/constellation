#include "AnimNode_CarryArmIK.h"
#include "TwoBoneIK.h"
#include "Animation/AnimInstance.h"
#include "CarryComponent.h"
#include "GameFramework/Actor.h"

void FAnimNode_CarryArmIK::PreUpdate(const UAnimInstance* Instance)
{
    const AActor* Owner=Instance?Instance->GetOwningActor():nullptr;
    const UCarryComponent* Carry=Owner?Owner->FindComponentByClass<UCarryComponent>():nullptr;
    bPlaceTargetInComponentSpace=Carry&&Carry->GetFittedPlaceAlpha()>0.f;
}

void FAnimNode_CarryArmIK::InitializeBoneReferences(const FBoneContainer& Bones)
{
    for(FBoneReference* B : {&UpperArm,&UpperTwist,&Forearm,&ForearmTwist,&Hand,&TargetReference}) B->Initialize(Bones);
}
bool FAnimNode_CarryArmIK::IsValidToEvaluate(const USkeleton*, const FBoneContainer& Bones)
{
    for(const FBoneReference* B : {&UpperArm,&UpperTwist,&Forearm,&ForearmTwist,&Hand})
        if(!B->IsValidToEvaluate(Bones)) return false;
    return TargetReference.BoneName.IsNone() || TargetReference.IsValidToEvaluate(Bones);
}
void FAnimNode_CarryArmIK::EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& Out)
{
    const FBoneContainer& Bones=Output.Pose.GetPose().GetBoneContainer();
    const auto U=UpperArm.GetCompactPoseIndex(Bones), UT=UpperTwist.GetCompactPoseIndex(Bones);
    const auto F=Forearm.GetCompactPoseIndex(Bones), FT=ForearmTwist.GetCompactPoseIndex(Bones), H=Hand.GetCompactPoseIndex(Bones);
    FTransform Upper=Output.Pose.GetComponentSpaceTransform(U), Lower=Output.Pose.GetComponentSpaceTransform(F), Wrist=Output.Pose.GetComponentSpaceTransform(H);
    const FTransform UpperRelative=Output.Pose.GetComponentSpaceTransform(UT).GetRelativeTransform(Upper);
    const FTransform LowerRelative=Output.Pose.GetComponentSpaceTransform(FT).GetRelativeTransform(Lower);
    FVector Target=EffectorTransform.GetLocation();
    if(!TargetReference.BoneName.IsNone()&&!bPlaceTargetInComponentSpace) Target=Output.Pose.GetComponentSpaceTransform(TargetReference.GetCompactPoseIndex(Bones)).TransformPosition(Target);
    const FVector Shoulder=Upper.GetLocation(), Elbow=Lower.GetLocation();
    // Keep the authored bend plane. A distant pole avoids numerical instability.
    const FVector Axis=(Wrist.GetLocation()-Shoulder).GetSafeNormal();
    FVector Bend=(Elbow-Shoulder)-Axis*FVector::DotProduct(Elbow-Shoulder,Axis);
    if(!Bend.Normalize()) Bend=Upper.GetRotation().GetAxisY();
    // Carry arm targets support the underside of furniture. Keep elbows below
    // the grip plane instead of inheriting the generic pickup's raised elbow.
    const bool FurnitureArm=UpperArm.BoneName==TEXT("upperarm_l")||UpperArm.BoneName==TEXT("upperarm_r");
    const FVector Pole=FurnitureArm?Shoulder+FVector(0,UpperArm.BoneName==TEXT("upperarm_l")?-15.0:15.0,-100.0):Elbow+Bend*100.0;
    const FQuat HandRotation=Wrist.GetRotation();
    AnimationCore::SolveTwoBoneIK(Upper,Lower,Wrist,Pole,Target,false,1.0,1.0);
    Wrist.SetRotation(bUseTargetRotation?EffectorTransform.GetRotation():HandRotation);
    Out.Add(FBoneTransform(U,Upper)); Out.Add(FBoneTransform(UT,UpperRelative*Upper));
    Out.Add(FBoneTransform(F,Lower)); Out.Add(FBoneTransform(FT,LowerRelative*Lower)); Out.Add(FBoneTransform(H,Wrist));
    Out.Sort(FCompareBoneTransformIndex());
}
