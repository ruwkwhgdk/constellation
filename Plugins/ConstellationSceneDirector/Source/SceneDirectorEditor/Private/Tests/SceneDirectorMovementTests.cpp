#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorCompiler.h"
#include "ScopedTransaction.h"
#include "Editor.h"
#include "SceneDirectorTestFixture.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorMovementScheduleTest,"Constellation.SceneDirector.MovementSchedule",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorMovementScheduleTest::RunTest(const FString&)
{
    auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Fixture"),A))return false;
    auto& M=A->Steps[2];M.Type=EDirectorNodeType::CharacterMove;M.bAutoLocomotion=false;M.Destination.Value=FVector(300,0,0);M.MoveSpeed=150;
    FDirectorSchedule S;FString Error;
    if(!TestTrue(TEXT("Movement supported"),FSceneDirectorCompiler::Schedule(*A,S,Error))){AddInfo(Error);return false;}
    TestEqual(TEXT("Distance / speed = 2 sec"),S.FinishFrames[2],60);
    TestEqual(TEXT("Destination"),S.ToPoses[2].GetLocation(),FVector(300,0,0));
    A->Steps[1].Transform.SetLocation(FVector(100,0,0));
    FDirectorVectorEntry V;V.Key=TEXT("Destination");V.Value=FVector(500,0,0);A->Vectors.Add(V);
    M.Destination.Mode=EDirectorValueMode::Key;M.Destination.Key=V.Key;M.Destination.Offset=FVector(50,0,0);
    TestTrue(TEXT("Named destination"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("Stored + offset"),S.ToPoses[2].GetLocation(),FVector(550,0,0));
    M.Destination.bAddCurrent=true;TestTrue(TEXT("Current relative"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("Current + stored + offset"),S.ToPoses[2].GetLocation(),FVector(650,0,0));
    M.Destination.Mode=EDirectorValueMode::Current;M.Destination.Key=TEXT("NotRequired");
    TestTrue(TEXT("Current mode does not need a stored key"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("Current + offset"),S.ToPoses[2].GetLocation(),FVector(150,0,0));
    M.Destination.Mode=EDirectorValueMode::Key;M.Destination.Key=V.Key;
    M.MoveTiming=EDirectorMoveTiming::Duration;M.Duration=1;M.MoveSpeed=-1;
    A->Steps[1].WalkAnimation=M.Animation;A->Steps[1].RunAnimation=DuplicateObject<UAnimSequence>(M.Animation,GetTransientPackage());M.bAutoLocomotion=true;
    TestTrue(TEXT("Time mode ignores unused speed"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("550 cm/s selects run"),S.Animations[2],A->Steps[1].RunAnimation.Get());
    M.Duration=4;TestTrue(TEXT("Slower time"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("137.5 cm/s selects walk"),S.Animations[2],A->Steps[1].WalkAnimation.Get());
    M.Destination.Key=TEXT("Missing");TestFalse(TEXT("Unknown vector rejected"),FSceneDirectorCompiler::Schedule(*A,S,Error));M.Destination.Key=V.Key;
    M.MoveTiming=EDirectorMoveTiming::Speed;TestFalse(TEXT("Negative active speed rejected"),FSceneDirectorCompiler::Schedule(*A,S,Error));M.MoveSpeed=150;
    FDirectorStep Next=M;Next.Id=FGuid::NewGuid();Next.Destination.Offset=FVector::ZeroVector;Next.Destination.bAddCurrent=true;
    Next.NextNodes={A->Steps[4].Id};M.NextNodes={Next.Id};A->Steps.Add(Next);
    TestTrue(TEXT("Sequential movement"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestEqual(TEXT("Second move begins at first destination"),S.FromPoses.Last().GetLocation(),FVector(650,0,0));TestEqual(TEXT("Second relative endpoint"),S.ToPoses.Last().GetLocation(),FVector(1150,0,0));
    A->Steps[2].bWaitForCompletion=false;TestFalse(TEXT("Overlapping same NPC moves rejected"),FSceneDirectorCompiler::Schedule(*A,S,Error));
    return true;
}
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "Channels/MovieSceneChannelProxy.h"
#include "SceneDirectorPlayer.h"
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Camera/CameraActor.h"
static USceneDirectorAsset* MakeCameraMoveTestAsset()
{
    auto* A=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::CameraMove,EDirectorNodeType::Wait,EDirectorNodeType::CameraMove,EDirectorNodeType::End})
    {FDirectorStep S;S.Type=Type;S.CameraKey=TEXT("Main");S.Duration=2;A->Steps.Add(S);}
    for(int32 I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
    A->Steps[1].Destination.Value=FVector(100,0,0);A->Steps[1].Rotation.Value=FVector(0,0,90);
    A->Steps[3].Destination.Mode=EDirectorValueMode::Key;A->Steps[3].Destination.Key=TEXT("Delta");A->Steps[3].Destination.bAddCurrent=true;
    A->Steps[3].Rotation.Mode=EDirectorValueMode::Key;A->Steps[3].Rotation.Key=TEXT("Turn");A->Steps[3].Rotation.Offset=FVector(0,0,10);A->Steps[3].Rotation.bAddCurrent=true;
    FDirectorVectorEntry V;V.Key=TEXT("Delta");V.Value=FVector(200,0,0);A->Vectors.Add(V);
    V.Id=FGuid::NewGuid();V.Key=TEXT("Turn");V.Value=FVector(0,0,80);A->Vectors.Add(V);return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorCameraMoveTest,"Constellation.SceneDirector.CameraMovementPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorCameraMoveTest::RunTest(const FString&)
{
    auto* A=MakeCameraMoveTestAsset();FString Error;FDirectorSchedule S;
    if(!TestTrue(TEXT("Camera move schedule"),FSceneDirectorCompiler::Schedule(*A,S,Error))){AddError(Error);return false;}
    TestEqual(TEXT("Reused camera start"),S.FromPoses[3].GetLocation(),FVector(100,0,0));TestEqual(TEXT("Relative endpoint"),S.ToPoses[3].GetLocation(),FVector(300,0,0));
    TestTrue(TEXT("Relative rotation"),S.ToPoses[3].Rotator().Equals(FRotator(0,180,0),.01));
    const auto SavedRotation=A->Steps[3].Rotation;
    A->Steps[3].Rotation.Mode=EDirectorValueMode::Current;A->Steps[3].Rotation.Key=TEXT("NotRequired");A->Steps[3].Rotation.Offset=FVector(0,0,30);
    TestTrue(TEXT("Current camera rotation mode"),FSceneDirectorCompiler::Schedule(*A,S,Error));TestTrue(TEXT("Current rotation plus offset"),S.ToPoses[3].Rotator().Equals(FRotator(0,120,0),.01));
    A->Steps[3].Rotation=SavedRotation;
    if(!TestTrue(TEXT("Camera compile"),FSceneDirectorCompiler::Compile(*A,Error)))return false;
    TestEqual(TEXT("Missing camera auto registered once"),A->Cameras.Num(),1);TestEqual(TEXT("Same camera binding reused"),A->GeneratedSequence->GetMovieScene()->GetSpawnableCount(),1);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=A;TestTrue(TEXT("Play"),Runner->PlayDirector());
    ULevelSequencePlayer* Player=nullptr;for(TActorIterator<ALevelSequenceActor> It(World);It;++It)Player=It->GetSequencePlayer();
    if(TestNotNull(TEXT("Sequence player"),Player))
    {
        Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(1.f,EUpdatePositionMethod::Jump));AActor* Camera=Runner->FindCamera(TEXT("Main"));
        if(TestNotNull(TEXT("Camera resolves"),Camera))
        {
            TestTrue(TEXT("Midpoint position"),Camera->GetActorLocation().Equals(FVector(50,0,0),.1));TestTrue(TEXT("Midpoint rotation"),Camera->GetActorRotation().Equals(FRotator(0,45,0),.1));
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(3.f,EUpdatePositionMethod::Jump));TestTrue(TEXT("Holds destination between moves"),Camera->GetActorLocation().Equals(FVector(100,0,0),.1));
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(5.f,EUpdatePositionMethod::Jump));TestEqual(TEXT("Camera object reused"),Runner->FindCamera(TEXT("Main")),Camera);TestTrue(TEXT("Second midpoint"),Camera->GetActorLocation().Equals(FVector(200,0,0),.1));TestTrue(TEXT("Second rotation midpoint"),Camera->GetActorRotation().Equals(FRotator(0,135,0),.1));
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(.5f,EUpdatePositionMethod::Jump));TestTrue(TEXT("Backward scrub deterministic"),Camera->GetActorLocation().Equals(FVector(25,0,0),.1));
        }
    }
    Runner->StopDirector();TestNull(TEXT("Camera cleaned after stop"),Runner->FindCamera(TEXT("Main")));GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorRegistryTest,"Constellation.SceneDirector.RegistryRename",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorRegistryTest::RunTest(const FString&)
{
    auto* A=MakeCameraMoveTestAsset();A->EnsureCameraDefinitions();A->PreEditChange(nullptr);
    A->Cameras[0].Key=TEXT("Renamed");A->Vectors[0].Key=TEXT("NewDelta");FPropertyChangedEvent Event(nullptr);A->PostEditChangeProperty(Event);
    TestEqual(TEXT("Camera references follow rename"),A->Steps[1].CameraKey,FName(TEXT("Renamed")));TestEqual(TEXT("Other camera reference follows"),A->Steps[3].CameraKey,FName(TEXT("Renamed")));TestEqual(TEXT("Vector reference follows"),A->Steps[3].Destination.Key,FName(TEXT("NewDelta")));
    FDirectorSchedule S;FString Error;TestTrue(TEXT("Renamed graph valid"),FSceneDirectorCompiler::Schedule(*A,S,Error));
    A->PreEditChange(nullptr);const auto VectorCopy=A->Vectors[0];const auto CameraCopy=A->Cameras[0];A->Vectors.Add(VectorCopy);A->Cameras.Add(CameraCopy);A->PostEditChangeProperty(Event);
    TestTrue(TEXT("Duplicate vector gets own identity"),A->Vectors[0].Id!=A->Vectors.Last().Id);TestTrue(TEXT("Duplicate camera gets own identity"),A->Cameras[0].Id!=A->Cameras.Last().Id);
    TestFalse(TEXT("Duplicate keys rejected"),FSceneDirectorCompiler::Schedule(*A,S,Error));
    A->PreEditChange(nullptr);A->Cameras.Last().Key=TEXT("CopyCamera");A->Vectors.Last().Key=TEXT("CopyVector");A->PostEditChangeProperty(Event);
    TestEqual(TEXT("Naming copy does not steal original camera references"),A->Steps[1].CameraKey,FName(TEXT("Renamed")));
    TestEqual(TEXT("Naming copy does not steal original vector references"),A->Steps[3].Destination.Key,FName(TEXT("NewDelta")));
    A->Steps[1].CameraKey=TEXT("CopyCamera");A->Steps[1].Destination.Key=TEXT("CopyVector");A->SetFlags(RF_Transactional);
    {
        const FScopedTransaction Tx(FText::FromString(TEXT("Rename registry test")));A->Modify();A->PreEditChange(nullptr);
        A->Cameras[0].Key=TEXT("FinalCamera");A->Vectors[0].Key=TEXT("FinalVector");A->PostEditChangeProperty(Event);
    }
    TestEqual(TEXT("Original reference renamed"),A->Steps[3].CameraKey,FName(TEXT("FinalCamera")));TestEqual(TEXT("Copy camera unchanged"),A->Steps[1].CameraKey,FName(TEXT("CopyCamera")));TestEqual(TEXT("Copy vector unchanged"),A->Steps[1].Destination.Key,FName(TEXT("CopyVector")));
    GEditor->UndoTransaction();TestEqual(TEXT("Undo registry rename"),A->Steps[3].CameraKey,FName(TEXT("Renamed")));TestEqual(TEXT("Undo vector reference"),A->Steps[3].Destination.Key,FName(TEXT("NewDelta")));
    GEditor->RedoTransaction();TestEqual(TEXT("Redo registry rename"),A->Steps[3].CameraKey,FName(TEXT("FinalCamera")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorCharacterMovePlaybackTest,"Constellation.SceneDirector.CharacterMovementPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorCharacterMovePlaybackTest::RunTest(const FString&)
{
    auto* A=MakeAnimationTestAsset();if(!TestNotNull(TEXT("Fixture"),A))return false;
    A->Steps[2].Type=EDirectorNodeType::CharacterMove;A->Steps[2].bAutoLocomotion=false;A->Steps[2].Destination.Value=FVector(300,0,0);A->Steps[2].MoveSpeed=150;
    A->Steps[3].Duration=4;FString Error;if(!TestTrue(TEXT("Compile moving character"),FSceneDirectorCompiler::Compile(*A,Error)))return false;
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
    auto* Runner=World->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=A;Runner->PlayDirector();
    ULevelSequencePlayer* Player=nullptr;for(TActorIterator<ALevelSequenceActor> It(World);It;++It)Player=It->GetSequencePlayer();
    if(TestNotNull(TEXT("Player"),Player))
    {
        Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(.2f,EUpdatePositionMethod::Jump));auto* NPC=Runner->FindNPC(TEXT("Heroine"));
        if(TestNotNull(TEXT("NPC"),NPC))
        {
            auto* Mesh=NPC->FindComponentByClass<USkeletalMeshComponent>();Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto First=Mesh->GetComponentSpaceTransforms();
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(.7f,EUpdatePositionMethod::Jump));Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto Second=Mesh->GetComponentSpaceTransforms();
            bool Changed=false;for(int32 I=0;I<FMath::Min(First.Num(),Second.Num());++I)if(!First[I].Equals(Second[I],.001f)){Changed=true;break;}
            TestTrue(TEXT("Moves and animates simultaneously"),Changed&&NPC->GetActorLocation().Equals(FVector(105,0,0),.1));
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(3.f,EUpdatePositionMethod::Jump));TestTrue(TEXT("NPC remains at destination"),NPC->GetActorLocation().Equals(FVector(300,0,0),.1));
            Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(1.f,EUpdatePositionMethod::Jump));TestTrue(TEXT("NPC scrubs backward"),NPC->GetActorLocation().Equals(FVector(150,0,0),.1));
        }
    }
    Runner->StopDirector();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
#endif
