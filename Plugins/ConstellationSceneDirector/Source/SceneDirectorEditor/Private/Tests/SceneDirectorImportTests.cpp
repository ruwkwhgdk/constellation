#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorLibrary.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportContractTest,"Constellation.SceneDirector.ImportContract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportContractTest::RunTest(const FString&)
{
    TestNotNull(TEXT("Editable movement points"),FDirectorStep::StaticStruct()->FindPropertyByName(TEXT("MotionPoints")));
    TestNotNull(TEXT("Animation blend in"),FDirectorStep::StaticStruct()->FindPropertyByName(TEXT("AnimationBlendIn")));
    TestNotNull(TEXT("Sequence import API"),USceneDirectorLibrary::StaticClass()->FindFunctionByName(TEXT("ImportSequence")));
    return true;
}


#include "SceneDirectorImporter.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "MovieScene.h"
static ULevelSequence* ImportExampleSequence(USceneDirectorAsset* A)
{for(const auto& S:A->Steps)if(S.Type==EDirectorNodeType::Sequence&&S.SourceSequence)return S.SourceSequence;return nullptr;}
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Tracks/MovieSceneEventTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Animation/AnimSequence.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportFidelityTest,"Constellation.SceneDirector.ImportFidelity",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportFidelityTest::RunTest(const FString&)
{
    auto* Example=USceneDirectorLibrary::CreateSequenceExample();if(!Example||!TestNotNull(TEXT("Reusable clip"),ImportExampleSequence(Example)))return false;
    auto* Source=DuplicateObject<ULevelSequence>(ImportExampleSequence(Example),GetTransientPackage());auto* M=Source->GetMovieScene();
    UMovieScene3DTransformTrack* OriginalTrack=nullptr;
    for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())if(auto* T=M->FindTrack<UMovieScene3DTransformTrack>(B.GetObjectGuid())){OriginalTrack=T;break;}
    if(!OriginalTrack)return false;auto* Sec=OriginalTrack->GetAllSections()[0];auto C=Sec->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    C[0]->Reset();FMovieSceneTangentData Tangent;Tangent.ArriveTangent=3;Tangent.LeaveTangent=8;
    C[0]->AddCubicKey(0,0,RCTM_Break,Tangent);C[0]->AddCubicKey(30,100,RCTM_Break,Tangent);
    C[5]->Reset();C[5]->AddLinearKey(0,0);C[5]->AddLinearKey(60,450);
    FString Report;auto* Imported=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);
    if(!TestNotNull(TEXT("Supported source converts"),Imported)){AddError(Report);return false;}
    TestEqual(TEXT("Original key count unchanged"),C[0]->GetNumKeys(),2);TestEqual(TEXT("Original binding count unchanged"),M->GetSpawnableCount(),2);
    auto* Move=Imported->Steps.FindByPredicate([](const FDirectorStep& S){return S.bUseMotionPath;});if(!Move)return false;
    TestTrue(TEXT("Editable points preserve source curve mode"),Move->MotionPoints.Num()>=3&&Move->MotionPoints[0].Interpolation==EDirectorPathInterpolation::Original);
    const FGuid ID=Move->Type==EDirectorNodeType::CameraMove?Imported->CameraBindings.FindRef(Move->CameraKey):Imported->NPCBindings.FindRef(Move->Role);
    auto* T=Imported->GeneratedSequence->GetMovieScene()->FindTrack<UMovieScene3DTransformTrack>(ID);auto D=T->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    for(double Frame:{0.,3.25,15.5,29.9,30.,40.,59.9})for(int32 Axis=0;Axis<9;++Axis)
    {double A=0,B=0;C[Axis]->Evaluate(FFrameTime::FromDecimal(Frame),A);D[Axis]->Evaluate(FFrameTime::FromDecimal(Frame),B);TestTrue(FString::Printf(TEXT("Curve axis %d frame %.2f"),Axis,Frame),FMath::IsNearlyEqual(A,B,1.e-5));}
    Move->MotionPoints[1].Position.X+=50;TestTrue(TEXT("Imported graph remains editable"),FSceneDirectorCompiler::Compile(*Imported,Report));
    double Old=0;C[0]->Evaluate(FFrameTime(30),Old);TestEqual(TEXT("Editing imported point preserves original"),Old,100.);
    Source->GetMovieScene()->AddTrack<UMovieSceneEventTrack>();TestNull(TEXT("Unsupported tracks abort instead of partial conversion"),FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report));TestTrue(TEXT("Failure report explains preservation"),Report.Contains(TEXT("변경하지 않았습니다")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorPathBlendTest,"Constellation.SceneDirector.PathAndBlend",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorPathBlendTest::RunTest(const FString&)
{
    auto* Example=USceneDirectorLibrary::CreateSequenceExample();if(!Example||!TestNotNull(TEXT("Reusable clip"),ImportExampleSequence(Example)))return false;FString Error;
    auto* A=FSceneDirectorImporter::Convert(ImportExampleSequence(Example),GetTransientPackage(),Error);if(!TestNotNull(TEXT("Base source converts"),A)){AddError(Error);return false;}
    auto* Step=A->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::Animation;});if(!Step)return false;
    Step->Duration=2;Step->bExplicitAnimationRate=true;Step->AnimationRate=.75;Step->AnimationBlendIn=.3;Step->AnimationBlendOut=.4;Step->AnimationWeight=.6;Step->AnimationEaseIn=EMovieSceneBuiltInEasing::Linear;
    TestTrue(TEXT("Blend parameters compile"),FSceneDirectorCompiler::Compile(*A,Error));
    auto* Track=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSkeletalAnimationTrack>(A->NPCBindings.FindChecked(Step->Role));auto* S=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[0]);
    TestEqual(TEXT("Blend in duration"),S->Easing.GetEaseInDuration(),9);TestEqual(TEXT("Blend out duration"),S->Easing.GetEaseOutDuration(),12);TestEqual(TEXT("Explicit speed"),S->Params.PlayRate.AsFixedPlayRate(),.75);TestTrue(TEXT("Linear blend midpoint"),FMath::IsNearlyEqual(S->EvaluateEasing(FFrameTime::FromDecimal(4.5)),.5f,.001f));
    auto* Last=A->GeneratedSequence.Get();Step->AnimationBlendIn=3;TestFalse(TEXT("Invalid blend rejected"),FSceneDirectorCompiler::Compile(*A,Error));TestEqual(TEXT("Last valid sequence retained"),A->GeneratedSequence.Get(),Last);Step->AnimationBlendIn=.3;
    auto* Move=A->Steps.FindByPredicate([](const FDirectorStep& P){return P.Type==EDirectorNodeType::CharacterMove;});if(!Move)return false;Move->MotionPoints[1].Time=0;TestFalse(TEXT("Duplicate path time rejected"),FSceneDirectorCompiler::Compile(*A,Error));return true;
}


#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Components/SkeletalMeshComponent.h"
#include "UObject/SavePackage.h"
#include "PackageTools.h"
#include "Misc/Paths.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportPlaybackTest,"Constellation.SceneDirector.ImportPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportPlaybackTest::RunTest(const FString&)
{
    auto* Example=USceneDirectorLibrary::CreateSequenceExample();if(!Example||!TestNotNull(TEXT("Reusable clip"),ImportExampleSequence(Example)))return false;
    auto* Source=DuplicateObject<ULevelSequence>(ImportExampleSequence(Example),GetTransientPackage());auto* M=Source->GetMovieScene();FGuid ActorID;
    auto* Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));
    for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())for(auto* T:B.GetTracks())if(auto* Track=Cast<UMovieSceneSkeletalAnimationTrack>(T))
    {
        ActorID=B.GetObjectGuid();auto* S=CastChecked<UMovieSceneSkeletalAnimationSection>(T->GetAllSections()[0]);S->Params.Animation=Run;S->Params.PlayRate.Set(1.0);S->Params.StartFrameOffset=3;S->Easing.bManualEaseIn=true;S->Easing.ManualEaseInDuration=9;
        auto* Other=DuplicateObject<UMovieSceneSkeletalAnimationSection>(S,Track);Other->SetRange(TRange<FFrameNumber>(15,60));Other->Params.bReverse=true;Other->Params.Weight.SetDefault(.35);Track->AddSection(*Other);
    }
    FString Report;auto* A=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);if(!TestNotNull(TEXT("Overlapping clips import"),A)){AddError(Report);return false;}
    FName Role;for(const auto& S:A->Steps)if(S.Type==EDirectorNodeType::SpawnNPC)Role=S.Role;
    auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
    auto Sample=[&](ULevelSequence* Seq,FGuid ID,double Time)
    {
        ALevelSequenceActor* Actor=nullptr;auto* Player=ULevelSequencePlayer::CreateLevelSequencePlayer(W,Seq,FMovieSceneSequencePlaybackSettings(),Actor);TArray<FTransform> Bones;
        Player->Play();Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(float(Time),EUpdatePositionMethod::Jump));
        for(auto* O:Player->GetBoundObjects(UE::MovieScene::FRelativeObjectBindingID(ID)))if(auto* NPC=Cast<AActor>(O))if(auto* Mesh=NPC->FindComponentByClass<USkeletalMeshComponent>())
        {Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();Bones=Mesh->GetComponentSpaceTransforms();}
        Player->Stop();Actor->Destroy();return Bones;
    };
    for(double Time:{.1,.4,.75,1.3,1.9})
    {
        const auto Before=Sample(Source,ActorID,Time),After=Sample(A->GeneratedSequence,A->NPCBindings.FindChecked(Role),Time);
        TestTrue(TEXT("Bones evaluated"),Before.Num()>0);TestEqual(TEXT("Skeleton count matches"),After.Num(),Before.Num());
        bool Equal=Before.Num()==After.Num();for(int32 I=0;I<FMath::Min(Before.Num(),After.Num());++I)if(!Before[I].Equals(After[I],.001)){Equal=false;break;}
        TestTrue(FString::Printf(TEXT("Actual blended pose matches at %.2f sec"),Time),Equal);
    }
    GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportSaveTest,"Constellation.SceneDirector.ImportSaveReopen",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportSaveTest::RunTest(const FString&)
{
    auto* Example=USceneDirectorLibrary::CreateSequenceExample();if(!Example||!TestNotNull(TEXT("Reusable clip"),ImportExampleSequence(Example)))return false;FString Report;
    UPackage* Package=CreatePackage(*(TEXT("/Temp/DirectorImport_")+FGuid::NewGuid().ToString(EGuidFormats::Digits)));
    auto* Temp=FSceneDirectorImporter::Convert(ImportExampleSequence(Example),GetTransientPackage(),Report);if(!Temp){AddError(Report);return false;}
    auto* A=DuplicateObject<USceneDirectorAsset>(Temp,Package,TEXT("Imported"));A->SetFlags(RF_Public|RF_Standalone);
    const FString File=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("SceneDirector-import-roundtrip.uasset"));FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    if(!TestTrue(TEXT("Save import including Actor templates"),UPackage::SavePackage(Package,A,*File,Args)))return false;
    Package->SetDirtyFlag(false);A=nullptr;TArray<UPackage*> Packages{Package};if(!TestTrue(TEXT("Unload imported asset"),UPackageTools::UnloadPackages(Packages)))return false;
    auto* Reloaded=LoadPackage(nullptr,*File,LOAD_None);A=FindObject<USceneDirectorAsset>(Reloaded,TEXT("Imported"));if(!TestNotNull(TEXT("Reopen import"),A))return false;
    TestNotNull(TEXT("Source reference preserved"),A->ImportedFrom.Get());TestTrue(TEXT("Reopened graph compiles"),FSceneDirectorCompiler::Compile(*A,Report));
    for(const auto& S:A->Steps)if(S.Type==EDirectorNodeType::SpawnNPC)TestNotNull(TEXT("Spawnable customization persisted"),S.ImportedTemplate.Get());return true;
}


#include "Camera/CameraActor.h"
#include "Tracks/MovieSceneSpawnTrack.h"
#include "Sections/MovieSceneSpawnSection.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportPrecisionTest,"Constellation.SceneDirector.ImportPrecision",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportPrecisionTest::RunTest(const FString&)
{
    auto* Source=NewObject<ULevelSequence>();Source->Initialize();auto* M=Source->GetMovieScene();M->SetTickResolutionDirectly(FFrameRate(6000,1));M->SetPlaybackRange(6000,12000);
    auto* Template=NewObject<ACameraActor>(Source);auto ID=M->AddSpawnable(TEXT("Camera"),*Template);
    auto* Spawn=M->AddTrack<UMovieSceneSpawnTrack>(ID);auto* SpawnSection=CastChecked<UMovieSceneSpawnSection>(Spawn->CreateNewSection());SpawnSection->SetRange(TRange<FFrameNumber>(6000,18000));SpawnSection->GetChannel().SetDefault(true);Spawn->AddSection(*SpawnSection);
    auto* T=M->AddTrack<UMovieScene3DTransformTrack>(ID);T->SetPropertyNameAndPath(TEXT("Transform"),TEXT("Transform"));auto* S=CastChecked<UMovieScene3DTransformSection>(T->CreateNewSection());S->SetRange(TRange<FFrameNumber>(6000,18000));T->AddSection(*S);auto C=S->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    for(int32 I=0;I<9;++I)C[I]->SetDefault(I>=6?1:0);
    TArray<FFrameNumber> Times={FFrameNumber(6000),FFrameNumber(9000),FFrameNumber(15000)};TArray<FMovieSceneDoubleValue> Values;
    for(double V:{0.,100.,30.}){FMovieSceneDoubleValue Key(V);Key.InterpMode=RCIM_Cubic;Key.TangentMode=RCTM_Auto;Key.Tangent.ArriveTangent=.04;Key.Tangent.LeaveTangent=.01;Values.Add(Key);}C[0]->Set(Times,Values);C[0]->SetTickResolution(FFrameRate(6000,1));
    for(auto& V:Values){V.Tangent.TangentWeightMode=RCTWM_WeightedBoth;V.Tangent.ArriveTangentWeight=.5;V.Tangent.LeaveTangentWeight=.3;}C[1]->Set(Times,Values);C[1]->SetTickResolution(FFrameRate(6000,1));
    FString Report;auto* A=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);if(!TestNotNull(TEXT("6000 tick source with nonzero start imports"),A)){AddError(Report);return false;}
    auto* Out=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieScene3DTransformTrack>(A->CameraBindings.CreateConstIterator()->Value);auto D=Out->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    for(double Seconds:{0.,.12,.25,.49,.5,.8,1.2,1.6,1.9})for(int32 Axis=0;Axis<2;++Axis){double Before=0,After=0;C[Axis]->Evaluate(FFrameTime::FromDecimal(6000+Seconds*6000),Before);D[Axis]->Evaluate(FFrameTime::FromDecimal(Seconds*30),After);TestTrue(FString::Printf(TEXT("Auto tangent/timebase fidelity at %.2f"),Seconds),FMath::IsNearlyEqual(Before,After,.0001));}
    C[0]->AddLinearKey(9001,20);TestNull(TEXT("Unrepresentable subframe fails explicitly"),FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorImportGuardTest,"Constellation.SceneDirector.ImportGuards",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorImportGuardTest::RunTest(const FString&)
{
    auto* Example=USceneDirectorLibrary::CreateSequenceExample();if(!Example||!TestNotNull(TEXT("Reusable clip"),ImportExampleSequence(Example)))return false;
    auto* Source=DuplicateObject<ULevelSequence>(ImportExampleSequence(Example),GetTransientPackage());UMovieSceneSkeletalAnimationTrack* Track=nullptr;
    for(const auto& B:static_cast<const UMovieScene*>(Source->GetMovieScene())->GetBindings())for(auto* T:B.GetTracks())if(auto* Found=Cast<UMovieSceneSkeletalAnimationTrack>(T))Track=Found;if(!Track)return false;
    auto* Section=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[0]);FString Report;
    Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::KeepState;TestNull(TEXT("KeepState is not silently discarded"),FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report));Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;
    Track->EvalOptions.bEvalNearestSection=true;TestNull(TEXT("Nearest section is not silently discarded"),FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report));Track->EvalOptions.bEvalNearestSection=false;
    Section->Params.PlayRate.Set(1.000000000123);Section->Params.bForceCustomMode=false;
    auto* A=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);if(!TestNotNull(TEXT("Precise play rate imports"),A)){AddError(Report);return false;}
    auto* Step=A->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::Animation;});TestEqual(TEXT("Double rate retains precision"),Step->AnimationRate,Section->Params.PlayRate.AsFixedPlayRate());TestFalse(TEXT("Animation blueprint mode retained"),Step->bForceCustomAnimation);return true;
}
#endif
