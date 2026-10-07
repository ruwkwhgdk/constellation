#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "Engine/Blueprint.h"
#include "Animation/AnimSequence.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
namespace
{
bool SaveReuseAsset(UObject* A)
{
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    return UPackage::SavePackage(A->GetOutermost(),A,*FPackageName::LongPackageNameToFilename(A->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension()),Args);
}
}
USceneDirectorAsset* USceneDirectorLibrary::CreateSequenceExample()
{
    const TCHAR* Path=TEXT("/Game/SceneDirector/Examples/DA_SequenceReuse.DA_SequenceReuse");
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,Path,nullptr,LOAD_NoWarn))return Existing;
    auto* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/SceneDirector/Examples/BP_ConversationActor.BP_ConversationActor"));
    auto* Profile=LoadObject<USceneDirectorCharacterProfile>(nullptr,TEXT("/Game/SceneDirector/Examples/DA_ConversationProfile.DA_ConversationProfile"));
    auto* Anim=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed.AS_player_heroine_new_PreviewRelaxed"));
    if(!BP||!Profile||!Anim)return nullptr;
    auto* Source=LoadObject<ULevelSequence>(nullptr,TEXT("/Game/SceneDirector/Examples/LS_ReusablePerformance.LS_ReusablePerformance"),nullptr,LOAD_NoWarn);
    FString Error;
    if(!Source)
    {
        auto* Temporary=NewObject<USceneDirectorAsset>();Temporary->Steps.SetNum(5);auto& S=Temporary->Steps;
        S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Performer");S[1].ActorClass=BP->GeneratedClass;S[1].Profile=Profile;
        S[2].Type=EDirectorNodeType::Animation;S[2].Role=TEXT("Performer");S[2].Animation=Anim;S[2].Duration=2;S[2].bWaitForCompletion=false;
        S[3].Type=EDirectorNodeType::CameraPreset;S[3].Role=TEXT("Performer");S[3].CameraKey=TEXT("OriginalShot");S[3].Duration=2;S[3].Framing=EDirectorFraming::Medium;
        S[4].Type=EDirectorNodeType::End;for(int32 I=0;I<4;++I)S[I].NextNodes={S[I+1].Id};
        if(!FSceneDirectorCompiler::Compile(*Temporary,Error)){UE_LOG(LogTemp,Error,TEXT("Reusable source: %s"),*Error);return nullptr;}
        Source=DuplicateObject<ULevelSequence>(Temporary->GeneratedSequence,CreatePackage(TEXT("/Game/SceneDirector/Examples/LS_ReusablePerformance")),TEXT("LS_ReusablePerformance"));Source->SetFlags(RF_Public|RF_Standalone|RF_Transactional);FAssetRegistryModule::AssetCreated(Source);if(!SaveReuseAsset(Source))return nullptr;
    }
    auto* A=NewObject<USceneDirectorAsset>(CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_SequenceReuse")),TEXT("DA_SequenceReuse"),RF_Public|RF_Standalone|RF_Transactional);A->EventKey=TEXT("SequenceReuse");A->Steps.SetNum(8);auto& S=A->Steps;
    S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::SpawnNPC;S[1].Role=TEXT("Hero");S[1].ActorClass=BP->GeneratedClass;S[1].Profile=Profile;
    S[2].Type=EDirectorNodeType::CinematicMode;S[3].Type=EDirectorNodeType::Sequence;S[3].SourceSequence=Source;DirectorSequence::RefreshRoles(S[3]);
    for(auto& R:S[3].SequenceRoles)if(R.Label==TEXT("Performer")){R.Target=EDirectorSequenceTarget::NPC;R.Key=TEXT("Hero");}
    S[4].Type=EDirectorNodeType::CameraPreset;S[4].Role=TEXT("Hero");S[4].CameraKey=TEXT("ReturnShot");S[4].Framing=EDirectorFraming::CloseUp;S[4].Duration=2;S[4].bWaitForCompletion=false;
    S[5].Type=EDirectorNodeType::Dialogue;S[5].Role=TEXT("Hero");S[5].SpeakerName=FText::FromString(TEXT("주인공"));S[5].DialogueText=FText::FromString(TEXT("준비됐어요. 이제 함께 출발해 볼까요?"));S[5].Duration=2;S[5].DialogueAdvance=EDirectorDialogueAdvance::Click;
    S[6].Type=EDirectorNodeType::GameplayReturn;S[6].Duration=.5;S[7].Type=EDirectorNodeType::End;
    for(int32 I=0;I<8;++I){S[I].EditorPosition=FVector2D(I*290,0);if(I<7)S[I].NextNodes={S[I+1].Id};}
    if(!FSceneDirectorCompiler::Compile(*A,Error)){UE_LOG(LogTemp,Error,TEXT("Sequence example: %s"),*Error);return nullptr;}
    FAssetRegistryModule::AssetCreated(A);A->MarkPackageDirty();return SaveReuseAsset(A)?A:nullptr;
}
