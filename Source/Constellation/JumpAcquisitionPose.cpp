#include "JumpAcquisitionPose.h"
#include "Animation/AnimBlueprintGeneratedClass.h"
#include "Animation/AnimInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/UnrealType.h"
#include "TwoBoneIK.h"

struct FJumpPoseProxy : FAnimInstanceProxy
{
 explicit FJumpPoseProxy(UAnimInstance* Instance):FAnimInstanceProxy(Instance){}
 FAnimNode_LinkedInputPose* Input=nullptr;
 int32 Indices[6]={};
 FVector Hand,Look,Forward;float HandAlpha=0,LookAlpha=0;
 virtual void Initialize(UAnimInstance* I)override{Input=&CastChecked<UJumpAcquisitionPose>(I)->InputPose;FAnimInstanceProxy::Initialize(I);}
 virtual void PreUpdate(UAnimInstance* I,float Dt)override
 {
  FAnimInstanceProxy::PreUpdate(I,Dt);auto* P=CastChecked<UJumpAcquisitionPose>(I);auto* M=P->GetSkelMeshComponent();
  const FName Names[]={TEXT("upperarm_r"),TEXT("upperarm_twist_01_r"),TEXT("lowerarm_r"),TEXT("lowerarm_twist_01_r"),TEXT("hand_r"),TEXT("head")};
  for(int32 N=0;N<6;N++)Indices[N]=M->GetBoneIndex(Names[N]);
  Hand=M->GetComponentTransform().InverseTransformPosition(P->HandTarget);Look=M->GetComponentTransform().InverseTransformPosition(P->LookTarget);
  Forward=P->HeadForward;HandAlpha=P->HandWeight;LookAlpha=P->LookWeight;
 }
 virtual bool Evaluate(FPoseContext& Output)override
 {
  Input->Evaluate_AnyThread(Output);const auto& Bones=Output.Pose.GetBoneContainer();
  FCompactPoseBoneIndex B[6];for(int32 I=0;I<6;I++)B[I]=Indices[I]==INDEX_NONE?FCompactPoseBoneIndex(INDEX_NONE):Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(Indices[I]));
  FCSPose<FCompactPose> CS;CS.InitPose(Output.Pose);
  if(HandAlpha>0&&B[0]!=INDEX_NONE&&B[1]!=INDEX_NONE&&B[2]!=INDEX_NONE&&B[3]!=INDEX_NONE&&B[4]!=INDEX_NONE)
  {
   FTransform U=CS.GetComponentSpaceTransform(B[0]),L=CS.GetComponentSpaceTransform(B[2]),H=CS.GetComponentSpaceTransform(B[4]);
   const auto UT=CS.GetComponentSpaceTransform(B[1]).GetRelativeTransform(U),LT=CS.GetComponentSpaceTransform(B[3]).GetRelativeTransform(L);
   const FQuat BeforeU=U.GetRotation(),BeforeL=L.GetRotation(),BeforeH=H.GetRotation();
   // Only anatomical shoulder/elbow articulate; preserve each twist segment's local transform.
   AnimationCore::SolveTwoBoneIK(U,L,H,U.GetLocation()+FVector(0,25,-100),Hand,false,1,1);
   H.SetRotation((L.GetRotation()*BeforeL.Inverse()*BeforeH).GetNormalized());
   TArray<FBoneTransform> Changed{{B[0],U},{B[1],UT*U},{B[2],L},{B[3],LT*L},{B[4],H}};Changed.Sort(FCompareBoneTransformIndex());
   CS.LocalBlendCSBoneTransforms(Changed,FMath::Clamp(HandAlpha,0.f,1.f));
  }
  if(LookAlpha>0&&B[5]!=INDEX_NONE)
  {
   FTransform H=CS.GetComponentSpaceTransform(B[5]);const FVector Desired=(Look-H.GetLocation()).GetSafeNormal();
   FQuat Delta=FQuat::FindBetweenNormals(H.GetRotation().RotateVector(Forward).GetSafeNormal(),Desired);
   const float Angle=Delta.GetAngle(),Limit=FMath::DegreesToRadians(25.f);
   Delta=FQuat::Slerp(FQuat::Identity,Delta,LookAlpha*(Angle>Limit?Limit/Angle:1));H.SetRotation((Delta*H.GetRotation()).GetNormalized());
   TArray<FBoneTransform> Head{{B[5],H}};CS.LocalBlendCSBoneTransforms(Head,1);
  }
  FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(CS,Output.Pose);return true;
 }
};
FAnimInstanceProxy* UJumpAcquisitionPose::CreateAnimInstanceProxy(){return new FJumpPoseProxy(this);}
void UJumpAcquisitionPose::DestroyAnimInstanceProxy(FAnimInstanceProxy* P){delete P;}
bool UJumpAcquisitionPose::Install(USkeletalMeshComponent* M)
{
 if(!M||M->GetPostProcessAnimBPClassToBeUsed()||!M->GetSkeletalMeshAsset())return false;
 for(FName B:{FName("upperarm_r"),FName("upperarm_twist_01_r"),FName("lowerarm_r"),FName("lowerarm_twist_01_r"),FName("hand_r"),FName("head")})if(M->GetBoneIndex(B)==INDEX_NONE)return false;
 M->CompleteParallelAnimationEvaluation(true);
 auto* Class=NewObject<UAnimBlueprintGeneratedClass>(GetTransientPackage(),NAME_None,RF_Transient);Class->SetSuperStruct(StaticClass());Class->ClassFlags|=CLASS_Transient;Class->Bind();Class->StaticLink(true);
 FAnimBlueprintFunction Function(TEXT("AnimGraph"));Function.InputPoseNames.Add(FAnimNode_LinkedInputPose::DefaultInputPoseName);Function.InputPoseNodeProperties.Add(FindFProperty<FStructProperty>(StaticClass(),GET_MEMBER_NAME_CHECKED(UJumpAcquisitionPose,InputPose)));Class->AnimBlueprintFunctions.Add(Function);Class->GetDefaultObject();Class->UpdateCustomPropertyListForPostConstruction();
 M->SetOverridePostProcessAnimBP(Class,false);M->SetDisablePostProcessBlueprint(false);
 auto* Instance=NewObject<UJumpAcquisitionPose>(M,Class);M->PostProcessAnimInstance=Instance;Instance->InitializeAnimation();if(M->HasBegunPlay()){Instance->NativeBeginPlay();Instance->BlueprintBeginPlay();}
 if(auto* Input=Instance->GetLinkedInputPoseNode()){const auto& Bones=Instance->GetRequiredBones();if(Bones.IsValid())Input->CachedInputPose.SetBoneContainer(&Bones);Input->bIsCachedInputPoseInitialized=false;}
 const auto& Ref=M->GetSkeletalMeshAsset()->GetRefSkeleton();int32 Index=Ref.FindBoneIndex(TEXT("head"));FTransform Head=Ref.GetRefBonePose()[Index];while((Index=Ref.GetParentIndex(Index))!=INDEX_NONE)Head=Head*Ref.GetRefBonePose()[Index];
 // Mesh reference faces component +Y (heroine uses actor-relative yaw -90).
 Instance->HeadForward=Head.GetRotation().Inverse().RotateVector(FVector::RightVector);return true;
}
void UJumpAcquisitionPose::Remove(USkeletalMeshComponent* M)
{
 if(!M||!Cast<UJumpAcquisitionPose>(M->GetPostProcessInstance()))return;
 M->CompleteParallelAnimationEvaluation(true);M->PostProcessAnimInstance->UninitializeAnimation();M->PostProcessAnimInstance=nullptr;M->SetOverridePostProcessAnimBP(nullptr,false);
}
