#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Animation/AnimSequence.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
USceneDirectorAsset* USceneDirectorLibrary::CreateImportExample()
{
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/Examples/DA_ImportedPerformance.DA_ImportedPerformance"),nullptr,LOAD_NoWarn))return Existing;
    auto* Reuse=CreateSequenceExample();if(!Reuse)return nullptr;
    const auto* Clip=Reuse->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::Sequence&&S.SourceSequence;});if(!Clip)return nullptr;
    const FString Path=TEXT("/Game/SceneDirector/Examples/LS_GraphConversionDemo");auto* Source=LoadObject<ULevelSequence>(nullptr,*(Path+TEXT(".LS_GraphConversionDemo")),nullptr,LOAD_NoWarn);
    if(!Source)
    {
        Source=DuplicateObject<ULevelSequence>(Clip->SourceSequence,CreatePackage(*Path),TEXT("LS_GraphConversionDemo"));Source->SetFlags(RF_Public|RF_Standalone|RF_Transactional);auto* M=Source->GetMovieScene();
        auto* Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));if(!Run)return nullptr;
        for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())if(auto* Track=M->FindTrack<UMovieSceneSkeletalAnimationTrack>(B.GetObjectGuid()))
        {
            auto* First=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[0]);auto* Second=DuplicateObject<UMovieSceneSkeletalAnimationSection>(First,Track);
            First->Params.Animation=Run;First->Params.PlayRate.Set(1.0);First->SetRange(TRange<FFrameNumber>(0,45));First->Easing.bManualEaseOut=true;First->Easing.ManualEaseOutDuration=15;
            Second->SetRange(TRange<FFrameNumber>(30,60));Second->Easing.bManualEaseIn=true;Second->Easing.ManualEaseInDuration=15;Track->AddSection(*Second);
            if(auto* Move=M->FindTrack<UMovieScene3DTransformTrack>(B.GetObjectGuid()))
            {auto C=Move->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();C[0]->Reset();C[0]->AddCubicKey(0,0);C[0]->AddCubicKey(15,25);C[0]->AddCubicKey(35,0);C[0]->AddCubicKey(60,0);C[1]->Reset();C[1]->AddCubicKey(0,-25);C[1]->AddCubicKey(35,0);C[1]->AddCubicKey(60,0);}
        }
        FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;if(!UPackage::SavePackage(Source->GetOutermost(),Source,*FPackageName::LongPackageNameToFilename(Path,FPackageName::GetAssetPackageExtension()),Args))return nullptr;FAssetRegistryModule::AssetCreated(Source);
    }
    FString Report;auto* Result=ImportSequence(Source,TEXT("/Game/SceneDirector/Examples/DA_ImportedPerformance"),Report);if(!Result)UE_LOG(LogTemp,Error,TEXT("Import example: %s"),*Report);return Result;
}
