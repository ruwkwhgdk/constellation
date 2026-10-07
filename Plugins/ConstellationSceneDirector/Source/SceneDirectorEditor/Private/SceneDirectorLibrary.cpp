#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "AssetToolsModule.h"
#include "Factories/BlueprintFactory.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Engine/Blueprint.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
#include "AssetRegistry/AssetRegistryModule.h"

namespace
{
bool SaveDirectorPackage(UObject* Object)
{
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    FString Filename=FPackageName::LongPackageNameToFilename(Object->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension());
    return UPackage::SavePackage(Object->GetOutermost(),Object,*Filename,Args);
}
}
bool USceneDirectorLibrary::CompileDirector(USceneDirectorAsset* Asset,FString& Message)
{
    if(!Asset){Message=TEXT("연출 에셋이 없습니다.");return false;}
    return FSceneDirectorCompiler::Compile(*Asset,Message);
}
USceneDirectorAsset* USceneDirectorLibrary::CreateExample()
{
    const TCHAR* AssetPath=TEXT("/Game/SceneDirector/Examples/DA_FirstScene.DA_FirstScene");
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,AssetPath,nullptr,LOAD_NoWarn))return Existing;
    auto* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/SceneDirector/Examples/BP_DirectorStandIn.BP_DirectorStandIn"),nullptr,LOAD_NoWarn);
    if(!BP)
    {
        auto* Factory=NewObject<UBlueprintFactory>();Factory->ParentClass=AStaticMeshActor::StaticClass();
        BP=Cast<UBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().CreateAsset(TEXT("BP_DirectorStandIn"),TEXT("/Game/SceneDirector/Examples"),UBlueprint::StaticClass(),Factory));
        if(!BP)return nullptr;
        auto* Default=Cast<AStaticMeshActor>(BP->GeneratedClass->GetDefaultObject());
        Default->GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
        Default->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
        FKismetEditorUtilities::CompileBlueprint(BP);BP->MarkPackageDirty();if(!SaveDirectorPackage(BP))return nullptr;
    }
    UPackage* Package=CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_FirstScene"));
    auto* Asset=NewObject<USceneDirectorAsset>(Package,TEXT("DA_FirstScene"),RF_Public|RF_Standalone|RF_Transactional);
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::SpawnNPC,EDirectorNodeType::Camera,EDirectorNodeType::End})
    {
        FDirectorStep S;S.Type=Type;S.EditorPosition=FVector2D(Asset->Steps.Num()*280,0);
        if(Type==EDirectorNodeType::SpawnNPC){S.ActorClass=BP->GeneratedClass;S.Transform=FTransform(FRotator::ZeroRotator,FVector(0,0,90),FVector(.6,.6,1.8));}
        if(Type==EDirectorNodeType::Camera){S.Transform.SetLocation(FVector(-450,150,200));S.Duration=5.f;}
        Asset->Steps.Add(S);
    }
    for(int32 I=0;I<Asset->Steps.Num()-1;++I)Asset->Steps[I].NextNodes={Asset->Steps[I+1].Id};
    FString Message;if(!FSceneDirectorCompiler::Compile(*Asset,Message)){UE_LOG(LogTemp,Error,TEXT("Scene Director: %s"),*Message);return nullptr;}
    FAssetRegistryModule::AssetCreated(Asset);Asset->MarkPackageDirty();if(!SaveDirectorPackage(Asset))return nullptr;
    return Asset;
}


#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
USceneDirectorAsset* USceneDirectorLibrary::CreateConversationExample()
{
    const TCHAR* Path=TEXT("/Game/SceneDirector/Examples/DA_Conversation.DA_Conversation");
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,Path,nullptr,LOAD_NoWarn))return Existing;
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview"));
    if(!Mesh)return nullptr;
    auto* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/SceneDirector/Examples/BP_ConversationActor.BP_ConversationActor"),nullptr,LOAD_NoWarn);
    if(!BP)
    {
        auto* Factory=NewObject<UBlueprintFactory>();Factory->ParentClass=ASkeletalMeshActor::StaticClass();
        BP=Cast<UBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().CreateAsset(TEXT("BP_ConversationActor"),TEXT("/Game/SceneDirector/Examples"),UBlueprint::StaticClass(),Factory));
        if(!BP)return nullptr;
        auto* Component=CastChecked<ASkeletalMeshActor>(BP->GeneratedClass->GetDefaultObject())->GetSkeletalMeshComponent();Component->SetSkeletalMeshAsset(Mesh);
        FKismetEditorUtilities::CompileBlueprint(BP);
        Component=CastChecked<ASkeletalMeshActor>(BP->GeneratedClass->GetDefaultObject())->GetSkeletalMeshComponent();
        auto* Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Shared/Animations/Idle.Idle"));
        if(Idle&&Idle->GetSkeleton()->IsCompatibleForEditor(Mesh->GetSkeleton()))Component->OverrideAnimationData(Idle,true,true,0,1);
        else if(auto* Pose=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Walk_Timid.AS_player_heroine_new_Walk_Timid")))Component->OverrideAnimationData(Pose,false,true,.3f,0);
        BP->MarkPackageDirty();if(!SaveDirectorPackage(BP))return nullptr;
    }
    auto* Profile=LoadObject<USceneDirectorCharacterProfile>(nullptr,TEXT("/Game/SceneDirector/Examples/DA_ConversationProfile.DA_ConversationProfile"),nullptr,LOAD_NoWarn);
    if(!Profile)
    {
        auto* P=CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_ConversationProfile"));
        Profile=NewObject<USceneDirectorCharacterProfile>(P,TEXT("DA_ConversationProfile"),RF_Public|RF_Standalone|RF_Transactional);
        Profile->AimHeight=150;Profile->HeadBone=TEXT("head");
        const auto& Ref=Mesh->GetRefSkeleton();int32 Bone=Ref.FindBoneIndex(Profile->HeadBone);FTransform Head=FTransform::Identity;
        while(Bone!=INDEX_NONE){Head=Head*Ref.GetRefBonePose()[Bone];Bone=Ref.GetParentIndex(Bone);}
        Profile->HeadForwardAxis=Head.GetRotation().UnrotateVector(FVector::ForwardVector);
        FAssetRegistryModule::AssetCreated(Profile);if(!SaveDirectorPackage(Profile))return nullptr;
    }
    auto* Package=CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_Conversation"));
    auto* A=NewObject<USceneDirectorAsset>(Package,TEXT("DA_Conversation"),RF_Public|RF_Standalone|RF_Transactional);A->EventKey=TEXT("Conversation");
    auto Add=[&](EDirectorNodeType Type,FName Role=TEXT("Hero"))->int32{FDirectorStep S;S.Type=Type;S.Role=Role;S.Duration=3;S.EditorPosition=FVector2D(A->Steps.Num()*220,0);return A->Steps.Add(S);};
    Add(EDirectorNodeType::Start);Add(EDirectorNodeType::SpawnNPC);Add(EDirectorNodeType::SpawnNPC,TEXT("Partner"));Add(EDirectorNodeType::CinematicMode);
    Add(EDirectorNodeType::CameraPreset);Add(EDirectorNodeType::LookAt);Add(EDirectorNodeType::Dialogue);
    Add(EDirectorNodeType::CameraPreset,TEXT("Partner"));Add(EDirectorNodeType::CameraSwitch);Add(EDirectorNodeType::LookAt,TEXT("Partner"));Add(EDirectorNodeType::Dialogue,TEXT("Partner"));Add(EDirectorNodeType::GameplayReturn);Add(EDirectorNodeType::End);
    for(int32 I=0;I<A->Steps.Num()-1;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
    for(int32 I:{1,2}){auto& S=A->Steps[I];S.ActorClass=BP->GeneratedClass;S.Profile=Profile;S.Transform=FTransform(FRotator(0,I==1?0:180,0),FVector(I==1?0:220,0,0));}
    A->Steps[4].CameraKey=TEXT("HeroClose");A->Steps[4].Framing=EDirectorFraming::CloseUp;A->Steps[4].ShotYaw=35;A->Steps[4].bWaitForCompletion=false;
    A->Steps[5].TargetRole=TEXT("Partner");A->Steps[5].bWaitForCompletion=false;
    A->Steps[6].SpeakerName=FText::FromString(TEXT("주인공"));A->Steps[6].DialogueText=FText::FromString(TEXT("여기에서 잠깐 이야기할 수 있을까요?"));A->Steps[6].DialogueAdvance=EDirectorDialogueAdvance::Click;
    A->Steps[7].CameraKey=TEXT("PartnerClose");A->Steps[7].Framing=EDirectorFraming::CloseUp;A->Steps[7].ShotYaw=-35;A->Steps[7].bActivateCamera=false;A->Steps[7].bWaitForCompletion=false;
    A->Steps[8].CameraKey=TEXT("PartnerClose");A->Steps[8].BlendSeconds=.5f;A->Steps[8].bWaitForCompletion=false;
    A->Steps[9].TargetRole=TEXT("Hero");A->Steps[9].bWaitForCompletion=false;
    A->Steps[10].SpeakerName=FText::FromString(TEXT("동료"));A->Steps[10].DialogueText=FText::FromString(TEXT("물론이죠. 무슨 일이 있었나요?"));A->Steps[10].DialogueAdvance=EDirectorDialogueAdvance::Click;
    A->Steps[11].Duration=.5f;
    // Break the long line into three readable rows while preserving exact execution links.
    for(int32 I=4;I<=6;++I)A->Steps[I].EditorPosition=FVector2D((I-4)*250,220);
    for(int32 I=7;I<=12;++I)A->Steps[I].EditorPosition=FVector2D((I-7)*250,440);
    FString Message;if(!FSceneDirectorCompiler::Compile(*A,Message)){UE_LOG(LogTemp,Error,TEXT("Conversation example: %s"),*Message);return nullptr;}
    auto* Bound=DuplicateObject<USceneDirectorAsset>(A,A,TEXT("ExistingActors"));Bound->EventKey=TEXT("ExistingActors");
    for(auto& S:Bound->Steps)if(S.Type==EDirectorNodeType::SpawnNPC){S.Type=EDirectorNodeType::BindNPC;S.ActorSource=EDirectorActorSource::Tag;S.ActorTag=S.Role;}
    if(!FSceneDirectorCompiler::Compile(*Bound,Message))return nullptr;A->EventGraphs.Add(Bound);
    FAssetRegistryModule::AssetCreated(A);A->MarkPackageDirty();if(!SaveDirectorPackage(A))return nullptr;return A;
}

USceneDirectorAsset* USceneDirectorLibrary::CreateBranchingExample()
{
    const TCHAR* Path=TEXT("/Game/SceneDirector/Examples/DA_Branching.DA_Branching");
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,Path,nullptr,LOAD_NoWarn))return Existing;
    auto* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/SceneDirector/Examples/BP_ConversationActor.BP_ConversationActor"),nullptr,LOAD_NoWarn);
    auto* Profile=LoadObject<USceneDirectorCharacterProfile>(nullptr,TEXT("/Game/SceneDirector/Examples/DA_ConversationProfile.DA_ConversationProfile"),nullptr,LOAD_NoWarn);
    if(!BP||!BP->GeneratedClass){UE_LOG(LogTemp,Error,TEXT("Branching example requires BP_ConversationActor; create the conversation example first."));return nullptr;}
    auto* Package=CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_Branching"));
    auto* A=NewObject<USceneDirectorAsset>(Package,TEXT("DA_Branching"),RF_Public|RF_Standalone|RF_Transactional);A->EventKey=TEXT("Branching");
    FDirectorBoolEntry Variable;Variable.Key=TEXT("HelpAccepted");Variable.Value=false;A->BoolVariables.Add(Variable);
    auto Add=[&](EDirectorNodeType Type,int32 X,int32 Y)->int32
    {FDirectorStep S;S.Type=Type;S.Role=TEXT("Hero");S.Duration=1;S.EditorPosition=FVector2D(X,Y);return A->Steps.Add(S);};
    Add(EDirectorNodeType::Start,0,0);Add(EDirectorNodeType::SpawnNPC,240,0);Add(EDirectorNodeType::CinematicMode,520,0);
    Add(EDirectorNodeType::CameraPreset,800,0);Add(EDirectorNodeType::Dialogue,1100,0);
    Add(EDirectorNodeType::SetBool,1480,-160);Add(EDirectorNodeType::SetBool,1480,160);
    Add(EDirectorNodeType::Condition,1800,0);Add(EDirectorNodeType::Dialogue,2120,-160);Add(EDirectorNodeType::Dialogue,2120,160);
    Add(EDirectorNodeType::GameplayReturn,2500,0);Add(EDirectorNodeType::End,2780,0);
    for(int32 I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
    auto& NPC=A->Steps[1];NPC.ActorClass=BP->GeneratedClass;NPC.Profile=Profile;NPC.Transform=FTransform::Identity;
    auto& Camera=A->Steps[3];Camera.CameraKey=TEXT("HeroClose");Camera.Framing=EDirectorFraming::CloseUp;Camera.ShotYaw=25;Camera.bWaitForCompletion=false;
    auto& Prompt=A->Steps[4];Prompt.SpeakerName=FText::FromString(TEXT("주인공"));Prompt.DialogueText=FText::FromString(TEXT("길을 잃은 동료를 도와줄까요?"));Prompt.DialogueAdvance=EDirectorDialogueAdvance::Click;Prompt.PreviewChoiceIndex=1;
    FDirectorChoice Yes;Yes.Key=TEXT("Help");Yes.Text=FText::FromString(TEXT("네, 함께 길을 찾아볼게요."));Prompt.Choices.Add(Yes);
    FDirectorChoice No;No.Key=TEXT("Decline");No.Text=FText::FromString(TEXT("미안하지만 지금은 먼저 가야 해요."));Prompt.Choices.Add(No);
    Prompt.ChoiceTargets.Add(Yes.Key,A->Steps[5].Id);Prompt.ChoiceTargets.Add(No.Key,A->Steps[6].Id);
    for(int32 I:{5,6}){A->Steps[I].BoolKey=Variable.Key;A->Steps[I].BoolValue=I==5;A->Steps[I].NextNodes={A->Steps[7].Id};}
    A->Steps[7].BoolKey=Variable.Key;A->Steps[7].TrueTarget=A->Steps[8].Id;A->Steps[7].FalseTarget=A->Steps[9].Id;
    for(int32 I:{8,9}){A->Steps[I].SpeakerName=FText::FromString(TEXT("주인공"));A->Steps[I].DialogueAdvance=EDirectorDialogueAdvance::Click;A->Steps[I].NextNodes={A->Steps[10].Id};}
    A->Steps[8].DialogueText=FText::FromString(TEXT("같이 가면 금방 찾을 수 있을 거예요."));
    A->Steps[9].DialogueText=FText::FromString(TEXT("다음에 만나면 꼭 도와드릴게요."));
    A->Steps[10].Duration=.5f;A->Steps[10].NextNodes={A->Steps[11].Id};
    FString Message;if(!FSceneDirectorCompiler::Compile(*A,Message)){UE_LOG(LogTemp,Error,TEXT("Branching example: %s"),*Message);return nullptr;}
    FAssetRegistryModule::AssetCreated(A);A->MarkPackageDirty();if(!SaveDirectorPackage(A))return nullptr;return A;
}
#include "LevelSequence.h"
UBlueprint* USceneDirectorLibrary::GetSequenceDirectorBlueprint(ULevelSequence* Source)
{
    return Source ? Source->GetDirectorBlueprint() : nullptr;
}

bool USceneDirectorLibrary::CompileAuthoringEvents(USceneDirectorAsset* Asset,FString& Report)
{
 if(!Asset){Report=TEXT("Missing asset");return false;}
 TArray<USceneDirectorAsset*> Events{Asset};for(auto E:Asset->EventGraphs)if(E)Events.Add(E);int32 Count=0;
 for(auto* E:Events)
 {
  if(!FSceneDirectorCompiler::Compile(*E,Report))return false;
  for(const auto& S:E->Steps)if(S.Type==EDirectorNodeType::CinematicMode||S.Type==EDirectorNodeType::GameplayReturn){Report=TEXT("Legacy controls remain");return false;}
  Count+=E->Steps.Num();
 }
 Report=FString::Printf(TEXT("%d events, %d nodes compiled"),Events.Num(),Count);return true;
}
