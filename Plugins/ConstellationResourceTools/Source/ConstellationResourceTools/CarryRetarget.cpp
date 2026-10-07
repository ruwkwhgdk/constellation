#include "CarryEditorLibrary.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AnimationBlueprintLibrary.h"

namespace
{
TArray<FTransform> ReferenceWorld(const FReferenceSkeleton& Ref)
{
    TArray<FTransform> World;
    for(int32 I=0;I<Ref.GetNum();++I)
        World.Add(Ref.GetParentIndex(I)>=0?Ref.GetRefBonePose()[I]*World[Ref.GetParentIndex(I)]:Ref.GetRefBonePose()[I]);
    return World;
}
FQuat BodyFrame(const FReferenceSkeleton& Ref,const TArray<FTransform>& World,FName Hip,FName Neck,FName Left,FName Right)
{
    const FVector Up=(World[Ref.FindBoneIndex(Neck)].GetLocation()-World[Ref.FindBoneIndex(Hip)].GetLocation()).GetSafeNormal();
    const FVector Side=(World[Ref.FindBoneIndex(Left)].GetLocation()-World[Ref.FindBoneIndex(Right)].GetLocation()).GetSafeNormal();
    return FRotationMatrix::MakeFromYZ(Side,Up).ToQuat();
}
}
UAnimSequence* UCarryEditorLibrary::RetargetCarrySequence(UAnimSequence* Source,USkeleton* Target,const FString& PackagePath,const FString& AssetName)
{
    if(!Source||!Source->GetSkeleton()||!Target||!Source->GetDataModel()) return nullptr;
    const FReferenceSkeleton& Src=Source->GetSkeleton()->GetReferenceSkeleton(); const FReferenceSkeleton& Dst=Target->GetReferenceSkeleton();
    for(FName Bone:{FName("pelvis"),FName("neck_01"),FName("clavicle_l"),FName("clavicle_r"),FName("foot_l")})
        if(Src.FindBoneIndex(Bone)==INDEX_NONE) return nullptr;
    for(FName Bone:{FName("Hips"),FName("Neck"),FName("LeftShoulder"),FName("RightShoulder"),FName("LeftFoot")})
        if(Dst.FindBoneIndex(Bone)==INDEX_NONE) return nullptr;
    const TArray<FTransform> SrcRef=ReferenceWorld(Src), DstRef=ReferenceWorld(Dst);
    // The current Mixamo player uses an animated hip origin above the mesh pivot.
    // Match its maintained idle height instead of the centered mesh's reference hip height.
    float HipHeightOffset=0;
    if(UAnimSequence* Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Shared/Animations/Idle.Idle")))
    {
        FTransform IdleHip;
        PRAGMA_DISABLE_DEPRECATION_WARNINGS
        UAnimationBlueprintLibrary::GetBonePoseForTime(Idle,TEXT("Hips"),0.f,false,IdleHip);
        PRAGMA_ENABLE_DEPRECATION_WARNINGS
        HipHeightOffset=IdleHip.GetLocation().Z-Dst.GetRefBonePose()[Dst.FindBoneIndex(TEXT("Hips"))].GetLocation().Z;
        UE_LOG(LogTemp,Display,TEXT("Carry retarget hip baseline=%f offset=%f"),IdleHip.GetLocation().Z,HipHeightOffset);
    }
    const FQuat Align=BodyFrame(Dst,DstRef,"Hips","Neck","LeftShoulder","RightShoulder")*BodyFrame(Src,SrcRef,"pelvis","neck_01","clavicle_l","clavicle_r").Inverse();
    const float Ratio=(DstRef[Dst.FindBoneIndex("Hips")].GetLocation()-DstRef[Dst.FindBoneIndex("LeftFoot")].GetLocation()).Size()
        / (SrcRef[Src.FindBoneIndex("pelvis")].GetLocation()-SrcRef[Src.FindBoneIndex("foot_l")].GetLocation()).Size();
    TMap<FName,FName> Mapping={{"Hips","pelvis"},{"Spine","spine_01"},{"Spine1","spine_02"},{"Spine2","spine_03"},{"Neck","neck_01"},{"Head","head"}};
    for(const FString Side:{FString(TEXT("Left")),FString(TEXT("Right"))})
    {
        const FString Suffix=Side==TEXT("Left")?TEXT("_l"):TEXT("_r");
        for(const auto& Pair:TMap<FString,FString>{{"Shoulder","clavicle"},{"Arm","upperarm"},{"ForeArm","lowerarm"},{"Hand","hand"},{"UpLeg","thigh"},{"Leg","calf"},{"Foot","foot"},{"ToeBase","ball"}})
            Mapping.Add(FName(*(Side+Pair.Key)),FName(*(Pair.Value+Suffix)));
        for(const auto& Finger:TMap<FString,FString>{{"Thumb","thumb"},{"Index","index"},{"Middle","middle"},{"Ring","ring"},{"Pinky","pinky"}})
            for(int32 J=1;J<=3;++J) Mapping.Add(FName(*(Side+TEXT("Hand")+Finger.Key+FString::FromInt(J))),FName(*FString::Printf(TEXT("%s_%02d%s"),*Finger.Value,J,*Suffix)));
    }
    IAnimationDataModel* Model=Source->GetDataModel(); const int32 Frames=Model->GetNumberOfFrames();
    TArray<TArray<FTransform>> SrcKeys; SrcKeys.SetNum(Src.GetNum());
    for(int32 I=0;I<Src.GetNum();++I) if(Model->IsValidBoneTrackName(Src.GetBoneName(I))) Model->GetBoneTrackTransforms(Src.GetBoneName(I),SrcKeys[I]);
    TArray<TArray<FVector>> Positions,Scales; TArray<TArray<FQuat>> Rotations;
    Positions.SetNum(Dst.GetNum()); Scales.SetNum(Dst.GetNum()); Rotations.SetNum(Dst.GetNum());
    FVector SourceHipStart=FVector::ZeroVector;
    for(int32 Frame=0;Frame<=Frames;++Frame)
    {
        TArray<FTransform> SrcWorld,DstWorld;
        for(int32 I=0;I<Src.GetNum();++I)
        {
            const FTransform Local=SrcKeys[I].IsEmpty()?Src.GetRefBonePose()[I]:SrcKeys[I][FMath::Min(Frame,SrcKeys[I].Num()-1)];
            SrcWorld.Add(Src.GetParentIndex(I)>=0?Local*SrcWorld[Src.GetParentIndex(I)]:Local);
        }
        if(Frame==0) SourceHipStart=SrcWorld[Src.FindBoneIndex(TEXT("pelvis"))].GetLocation();
        for(int32 I=0;I<Dst.GetNum();++I)
        {
            const int32 Parent=Dst.GetParentIndex(I); FTransform Local=Dst.GetRefBonePose()[I];
            const FName* SrcName=Mapping.Find(Dst.GetBoneName(I)); const int32 Index=SrcName?Src.FindBoneIndex(*SrcName):INDEX_NONE;
            if(Index>=0)
            {
                const FQuat Delta=Align*(SrcWorld[Index].GetRotation()*SrcRef[Index].GetRotation().Inverse())*Align.Inverse();
                const FQuat WorldRot=(Delta*DstRef[I].GetRotation()).GetNormalized();
                Local.SetRotation(Parent>=0?(DstWorld[Parent].GetRotation().Inverse()*WorldRot).GetNormalized():WorldRot);
                if(Dst.GetBoneName(I)==TEXT("Hips")) Local.AddToTranslation(Align.RotateVector(SrcWorld[Index].GetLocation()-SourceHipStart)*Ratio+FVector(0,0,HipHeightOffset));
            }
            Positions[I].Add(Local.GetTranslation()); Rotations[I].Add(Local.GetRotation()); Scales[I].Add(Local.GetScale3D());
            DstWorld.Add(Parent>=0?Local*DstWorld[Parent]:Local);
        }
    }
    const FString Full=PackagePath/AssetName;
    UPackage* Package=CreatePackage(*Full);
    UAnimSequence* Result=FindObject<UAnimSequence>(Package,*AssetName);
    const bool bNew=Result==nullptr;
    if(bNew) { Result=NewObject<UAnimSequence>(Package,*AssetName,RF_Public|RF_Standalone); FAssetRegistryModule::AssetCreated(Result); }
    Result->WaitOnExistingCompression();
    Result->SetSkeleton(Target); IAnimationDataController& Controller=Result->GetController();
    Controller.OpenBracket(NSLOCTEXT("Carry","Retarget","Retarget carry animation"),false);
    if(bNew) Controller.InitializeModel();
    Controller.SetFrameRate(Model->GetFrameRate(),false); Controller.SetNumberOfFrames(FFrameNumber(Frames),false);
    for(int32 I=0;I<Dst.GetNum();++I)
    { if(!Result->GetDataModel()->IsValidBoneTrackName(Dst.GetBoneName(I))) Controller.AddBoneCurve(Dst.GetBoneName(I),false); Controller.SetBoneTrackKeys(Dst.GetBoneName(I),Positions[I],Rotations[I],Scales[I],false); }
    Controller.NotifyPopulated(); Controller.CloseBracket(false); Result->WaitOnExistingCompression(); Result->MarkPackageDirty();
    TArray<FTransform> DebugHip;
    Result->GetDataModel()->GetBoneTrackTransforms(TEXT("Hips"),DebugHip);
    UE_LOG(LogTemp,Display,TEXT("Carry retarget stored hip=%s requested=%s mode=%d"),*DebugHip[0].GetLocation().ToString(),*Positions[Dst.FindBoneIndex(TEXT("Hips"))][0].ToString(),Target->GetBoneTranslationRetargetingMode(Dst.FindBoneIndex(TEXT("Hips"))));
    Result->CacheDerivedDataForCurrentPlatform(); Result->WaitOnExistingCompression();
    FTransform RawHip,CompressedHip;
    Result->GetBoneTransform(RawHip,FSkeletonPoseBoneIndex(Dst.FindBoneIndex(TEXT("Hips"))),FAnimExtractContext(0.),true);
    Result->GetBoneTransform(CompressedHip,FSkeletonPoseBoneIndex(Dst.FindBoneIndex(TEXT("Hips"))),FAnimExtractContext(0.),false);
    UE_LOG(LogTemp,Display,TEXT("Carry sampled raw=%s compressed=%s"),*RawHip.GetLocation().ToString(),*CompressedHip.GetLocation().ToString());
    return Result;
}
