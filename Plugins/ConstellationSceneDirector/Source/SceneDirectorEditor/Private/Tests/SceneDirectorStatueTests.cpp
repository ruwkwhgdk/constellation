#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorBranching.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneVisibilityTrack.h"
#include "Sections/MovieSceneVisibilitySection.h"
#include "Tracks/MovieSceneFadeTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Sections/MovieSceneFadeSection.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Channels/MovieSceneDoubleChannel.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorStatueTrackTest,"Constellation.SceneDirector.StatueTracks",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorStatueTrackTest::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(6);auto& S=A->Steps;S[0].Type=EDirectorNodeType::Start;S[1].Type=EDirectorNodeType::SpawnNPC;S[1].ActorClass=AActor::StaticClass();S[2].Type=EDirectorNodeType::Visibility;S[2].bVisible=false;S[3].Type=EDirectorNodeType::Fade;S[3].Duration=1;S[4].Type=EDirectorNodeType::Visibility;S[4].bVisible=true;S[5].Type=EDirectorNodeType::End;for(int I=0;I<5;++I)S[I].NextNodes={S[I+1].Id};FString Error;
 if(!TestTrue(*Error,FSceneDirectorCompiler::Compile(*A,Error)))return false;
 auto* M=A->GeneratedSequence->GetMovieScene();auto* V=M->FindTrack<UMovieSceneVisibilityTrack>(A->NPCBindings.FindChecked(S[1].Role));if(!TestNotNull(TEXT("Visibility track"),V))return false;bool Visible=true;auto* Section=CastChecked<UMovieSceneVisibilitySection>(V->GetAllSections()[0]);Section->GetChannel().Evaluate(0,Visible);TestFalse(TEXT("False visibility means hidden"),Visible);Section->GetChannel().Evaluate(30,Visible);TestTrue(TEXT("True visibility means shown"),Visible);
 auto* Fade=M->FindTrack<UMovieSceneFadeTrack>();if(!TestNotNull(TEXT("Fade track"),Fade))return false;float Value=0;CastChecked<UMovieSceneFadeSection>(Fade->GetAllSections()[0])->FloatCurve.Evaluate(15,Value);TestEqual(TEXT("Linear fade midpoint"),Value,.5f);
 S[3].FadeTo=2;TestFalse(TEXT("Out of range fade rejected"),FSceneDirectorCompiler::Compile(*A,Error));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorStatueContentTest,"Constellation.SceneDirector.StatueContent",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorStatueContentTest::RunTest(const FString&)
{
 auto* Original=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction.DA_StatueInteraction"));if(!TestNotNull(TEXT("Statue content installed"),Original))return false;
 TArray<USceneDirectorAsset*> Events{Original};for(auto E:Original->EventGraphs)Events.Add(E.Get());TestEqual(TEXT("First and repeat events"),Events.Num(),2);
 for(auto* Event:Events)for(FName Choice:{FName(TEXT("Rest")),FName(TEXT("Leave"))})
 {
  auto* A=NewObject<USceneDirectorAsset>();TMap<FGuid,FName> Decisions;for(const auto& S:Event->Steps)if(!S.ChoiceTargets.IsEmpty())Decisions.Add(S.Id,Choice);FGuid Pending;FString Error;
  if(!TestTrue(TEXT("Resolve both choices"),DirectorBranching::Resolve(*Event,Decisions,{},*A,Pending,Error))||!TestTrue(*Error,FSceneDirectorCompiler::Compile(*A,Error)))return false;
  TestFalse(TEXT("No opaque original sequence playback"),A->Steps.ContainsByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::Sequence;}));
  int Animations=0,Recovery=0;for(const auto& S:A->Steps){if(S.Type==EDirectorNodeType::Animation)++Animations;if(S.Type==EDirectorNodeType::GameAction&&S.ActionKey==TEXT("RestoreHP"))++Recovery;}
  TestEqual(TEXT("Original five animation sections only on rest path"),Animations,Choice==TEXT("Rest")?5:0);TestEqual(TEXT("HP recovery only on rest path"),Recovery,Choice==TEXT("Rest")?1:0);
  const auto& FirstMove=*A->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::CameraMove;});auto* Track=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieScene3DTransformTrack>(A->CameraBindings.FindChecked(TEXT("StatueCamera")));auto Generated=Track->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();auto* Source=Event->ImportedFrom->GetMovieScene();bool Compared=false;
  for(const auto& B:static_cast<const UMovieScene*>(Source)->GetBindings())if(Source->FindPossessable(B.GetObjectGuid())&&Source->FindPossessable(B.GetObjectGuid())->GetName().Contains(TEXT("CineCameraActor")))if(auto* T=Source->FindTrack<UMovieScene3DTransformTrack>(B.GetObjectGuid()))
  {auto Channels=T->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();const FVector Offset(-34550,-16750,1650);for(int Frame=0;Frame<FirstMove.MotionPoints.Last().Time*30;++Frame)for(int Axis=0;Axis<9;++Axis){double X=0,Y=0;Channels[Axis]->Evaluate(FFrameTime::FromDecimal((Frame+.25)*Source->GetTickResolution().AsDecimal()/30),X);Generated[Axis]->Evaluate(FFrameTime::FromDecimal(Frame+.25),Y);if(Axis<3)X+=Offset[Axis];if(!TestTrue(TEXT("Source camera curve equals generated at subframes"),FMath::IsNearlyEqual(X,Y,.001)))return false;}Compared=true;}
  TestTrue(TEXT("Original camera comparison performed"),Compared);
  if(Choice==TEXT("Rest"))
  {
   auto* SourceYes=LoadObject<ULevelSequence>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/LevelSequences/LS_AbandonedSchool_Checkpoint_Event_Choice_Yes.LS_AbandonedSchool_Checkpoint_Event_Choice_Yes"));
   auto* GT=A->GeneratedSequence->GetMovieScene()->FindTrack<UMovieSceneSkeletalAnimationTrack>(A->NPCBindings.FindChecked(TEXT("Heroine")));UMovieSceneSkeletalAnimationTrack* ST=nullptr;
   for(const auto& B:static_cast<const UMovieScene*>(SourceYes->GetMovieScene())->GetBindings())if(auto* T=SourceYes->GetMovieScene()->FindTrack<UMovieSceneSkeletalAnimationTrack>(B.GetObjectGuid()))ST=T;
   if(!TestNotNull(TEXT("Original animation track"),ST)||!TestNotNull(TEXT("Generated animation track"),GT))return false;
   TestEqual(TEXT("Animation section count preserved"),GT->GetAllSections().Num(),ST->GetAllSections().Num());
   for(int I=0;I<ST->GetAllSections().Num();++I){auto* O=CastChecked<UMovieSceneSkeletalAnimationSection>(ST->GetAllSections()[I]);auto* G=CastChecked<UMovieSceneSkeletalAnimationSection>(GT->GetAllSections()[I]);TestEqual(TEXT("Animation asset preserved"),G->Params.Animation.Get(),O->Params.Animation.Get());for(double Fraction:{.01,.2,.5,.8,.99}){const auto OT=FFrameTime::FromDecimal(O->GetInclusiveStartFrame().Value+Fraction*(O->GetExclusiveEndFrame()-O->GetInclusiveStartFrame()).Value);const auto NT=FFrameTime::FromDecimal(G->GetInclusiveStartFrame().Value+Fraction*(G->GetExclusiveEndFrame()-G->GetInclusiveStartFrame()).Value);TestTrue(TEXT("Original animation clip time matches"),FMath::IsNearlyEqual(O->MapTimeToAnimation(OT,SourceYes->GetMovieScene()->GetTickResolution()),G->MapTimeToAnimation(NT,FFrameRate(30,1)),.00001));TestTrue(TEXT("Original blend weight matches including overlapping ease"),FMath::IsNearlyEqual(O->EvaluateEasing(OT),G->EvaluateEasing(NT),.00001f));}}
  }

 }
 return true;
}

#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorStatueControlTest,"Constellation.SceneDirector.StatuePlayerRestore",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorStatueControlTest::RunTest(const FString&)
{
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;
 auto* A=NewObject<USceneDirectorAsset>();for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::CinematicMode,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.bHidePlayer=true;A->Steps.Add(S);}for(int I=0;I<3;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};Runner->Director=A;FString Error;TestTrue(TEXT("Compile control fixture"),FSceneDirectorCompiler::Compile(*A,Error));
 for(bool Hidden:{false,true}){Pawn->SetActorHiddenInGame(Hidden);TestTrue(TEXT("Cinematic starts"),Runner->PlayDirector());TestTrue(TEXT("Player hidden during cinematic"),Pawn->IsHidden());Runner->StopDirector();TestEqual(TEXT("Original player visibility restored on stop"),Pawn->IsHidden(),Hidden);TestFalse(TEXT("Input restored on stop"),PC->IsMoveInputIgnored());}
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
