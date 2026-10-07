#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "SceneEventSubsystem.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneEventTrack.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/SkeletalMeshComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolMigrationContract,"Constellation.SceneDirector.SchoolMigrationContract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolMigrationContract::RunTest(const FString&)
{
 for(const TCHAR* Name:{TEXT("Appear_Slime_Event"),TEXT("Dump_Slime_Star_Obj_Get_Event"),TEXT("Little_Girl_Event_Mushroom_Cave")})
 {
  const FString Path=FString(TEXT("/Game/SceneDirector/School/DA_"))+Name;auto* A=LoadObject<USceneDirectorAsset>(nullptr,*Path);if(!TestNotNull(*Path,A))continue;
  TestNotNull(TEXT("Source preserved"),A->ImportedFrom.Get());TestFalse(TEXT("Compiled asset"),A->bNeedsCompile);FString Error;if(!TestTrue(TEXT("Recompile migrated graph"),FSceneDirectorCompiler::Compile(*A,Error)))AddError(Error);
  int Actions=0,Dialogue=0;const FDirectorStep* Clip=nullptr;
  for(const auto& S:A->Steps){if(S.Type==EDirectorNodeType::GameAction)++Actions;if(S.Type==EDirectorNodeType::Dialogue)++Dialogue;if(S.Type==EDirectorNodeType::Sequence)Clip=&S;}
  TestTrue(TEXT("Native game actions migrated"),Actions>=2);TestEqual(TEXT("Native dialogue count"),Dialogue,FString(Name).Contains(TEXT("Little_Girl"))?4:0);
  if(TestNotNull(TEXT("Retained visual layer"),Clip))
  {
   TestNotEqual(TEXT("Visual copy is distinct from source"),Clip->SourceSequence.Get(),A->ImportedFrom.Get());
   auto* M=Clip->SourceSequence->GetMovieScene();auto Check=[&](const TArray<UMovieSceneTrack*>& Tracks){for(auto* T:Tracks)TestFalse(TEXT("No legacy event side effects in visual layer"),T->IsA<UMovieSceneEventTrack>());};Check(M->GetTracks());for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())Check(B.GetTracks());
  }
 }
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolMigrationPlayback,"Constellation.SceneDirector.SchoolMigrationPlayback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolMigrationPlayback::RunTest(const FString&)
{
 for(const TCHAR* Name:{TEXT("Appear_Slime_Event"),TEXT("Dump_Slime_Star_Obj_Get_Event"),TEXT("Little_Girl_Event_Mushroom_Cave")})
 {
  auto* A=LoadObject<USceneDirectorAsset>(nullptr,*(FString(TEXT("/Game/SceneDirector/School/DA_"))+Name));if(!TestNotNull(TEXT("Migrated scene"),A))continue;
  auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());W->SetGameInstance(NewObject<UGameInstance>(W));
  auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);const FRotator OriginalLook(-17,73,0);PC->SetControlRotation(OriginalLook);auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;
  for(const auto& O:A->Objects){auto* Actor=W->SpawnActor<AActor>(O.ActorClass);R->ObjectBindings.Add(O.Key,Actor);}
  AActor* Hero=R->ObjectBindings.FindRef(TEXT("Heroine"));auto* HeroMesh=Hero?Hero->FindComponentByClass<USkeletalMeshComponent>():nullptr;if(HeroMesh)HeroMesh->SetVisibility(false);if(Hero)Hero->SetActorHiddenInGame(true);
  TestTrue(TEXT("Native graph starts"),R->PlayDirector());int Dialogues=0;bool WasWaiting=false;
  for(int I=0;I<1500&&R->IsDirectorPlaying();++I){if(R->IsWaitingForDialogue()){++Dialogues;R->AdvanceDialogue();}R->Tick(1.f/30);}
  TestFalse(TEXT("Scene reaches end"),R->IsDirectorPlaying());TestTrue(*R->LastError,R->LastError.IsEmpty());TestEqual(TEXT("All dialogue prompts reached"),Dialogues,FString(Name).Contains(TEXT("Little_Girl"))?4:0);
  for(const auto& Action:R->ActionResults)TestTrue(*Action.Message,Action.bSucceeded);
  if(Hero)TestTrue(TEXT("Bound stand-in stays hidden after completion"),Hero->IsHidden());if(HeroMesh)TestFalse(TEXT("Bound stand-in remains deactivated after completion"),HeroMesh->IsVisible());
  if(HeroMesh){R->PlayDirector();R->Tick(.5f);R->StopDirector();TestFalse(TEXT("Bound stand-in restored on early cancellation"),HeroMesh->IsVisible());TestTrue(TEXT("Bound stand-in hidden on cancellation"),Hero->IsHidden());}
  TestTrue(TEXT("Gameplay camera preserves pre-scene look direction"),PC->GetControlRotation().Equals(OriginalLook,.01f));
  TestFalse(TEXT("Controls restored"),PC->IsMoveInputIgnored());TestFalse(TEXT("Player visible"),Pawn->IsHidden());
  GEngine->DestroyWorldContext(W);W->DestroyWorld(false);
 }
 return true;
}
#endif
#if WITH_DEV_AUTOMATION_TESTS
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolVisualParity,"Constellation.SceneDirector.SchoolVisualParity",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolVisualParity::RunTest(const FString&)
{
 for(const TCHAR* Name:{TEXT("Appear_Slime_Event"),TEXT("Dump_Slime_Star_Obj_Get_Event"),TEXT("Little_Girl_Event_Mushroom_Cave")})
 {
  auto* A=LoadObject<USceneDirectorAsset>(nullptr,*(FString(TEXT("/Game/SceneDirector/School/DA_"))+Name));if(!TestNotNull(TEXT("Migrated scene"),A))continue;
  auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());W->SetGameInstance(NewObject<UGameInstance>(W));auto* PC=W->SpawnActor<APlayerController>();PC->Possess(W->SpawnActor<APawn>());
  auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;
  for(const auto& O:A->Objects){FTransform Pose;for(const auto& S:A->Steps)if(S.Type==EDirectorNodeType::BindNPC&&S.ObjectKey==O.Key)Pose=S.Transform;for(const auto& C:A->Cameras)if(C.ObjectKey==O.Key)Pose=C.Transform;R->ObjectBindings.Add(O.Key,W->SpawnActor<AActor>(O.ActorClass,Pose));}
  const auto* Cue=A->Cues.FindByPredicate([](const FDirectorCue& C){return C.Step.Type==EDirectorNodeType::Sequence;});if(!Cue){AddError(TEXT("Missing retained clip"));GEngine->DestroyWorldContext(W);W->DestroyWorld(false);continue;}
  TestTrue(TEXT("Play native visual"),R->PlayDirector());R->Tick(1.f);TMap<FGuid,FTransform> Poses;TMap<FGuid,float> FOVs;
  for(const auto& Role:Cue->Step.SequenceRoles)if(Role.Target!=EDirectorSequenceTarget::Original)if(auto* Target=Role.Target==EDirectorSequenceTarget::Camera?R->FindCamera(Role.Key):R->FindNPC(Role.Key)){Poses.Add(Role.Binding,Target->GetActorTransform());if(auto* C=Cast<ACameraActor>(Target))FOVs.Add(Role.Binding,C->GetCameraComponent()->FieldOfView);}
  const auto Objects=R->ObjectBindings;R->StopDirector();ALevelSequenceActor* RawActor=nullptr;FMovieSceneSequencePlaybackSettings Settings;Settings.FinishCompletionStateOverride=EMovieSceneCompletionModeOverride::ForceRestoreState;auto* Raw=ULevelSequencePlayer::CreateLevelSequencePlayer(W,Cue->Step.SourceSequence,Settings,RawActor);
  for(const auto& Role:Cue->Step.SequenceRoles)if(auto Target=Objects.FindRef(Role.Key))RawActor->SetBinding(UE::MovieScene::FRelativeObjectBindingID(Role.Binding),{Target},false);
  Raw->Play();Raw->Pause();Raw->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(1.f-Cue->StartFrame/30.f,EUpdatePositionMethod::Play));
  for(const auto& Pair:Poses){auto Found=Raw->GetBoundObjects(UE::MovieScene::FRelativeObjectBindingID(Pair.Key));AActor* Target=Found.Num()?Cast<AActor>(Found[0]):nullptr;if(TestNotNull(TEXT("Original visual role resolves"),Target)){TestTrue(*FString::Printf(TEXT("%s pose matches source %s native=%s source=%s"),Name,*Target->GetName(),*Pair.Value.ToString(),*Target->GetActorTransform().ToString()),Target->GetActorTransform().Equals(Pair.Value,.1));if(auto* C=Cast<ACameraActor>(Target);C&&FOVs.Contains(Pair.Key))TestTrue(TEXT("Lens matches source"),FMath::IsNearlyEqual(C->GetCameraComponent()->FieldOfView,FOVs[Pair.Key],.01f));}}
  Raw->Stop();RawActor->Destroy();GEngine->DestroyWorldContext(W);W->DestroyWorld(false);
 }
 return true;
}
#endif
