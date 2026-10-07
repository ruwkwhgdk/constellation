#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorInteractionComponent.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorAsset.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/HUD.h"
#include "Camera/CameraActor.h"
static USceneDirectorAsset* IntegrationFixture(bool Bind=false)
{
 auto* A=NewObject<USceneDirectorAsset>();A->EventKey=TEXT("First");
 for(auto T:{EDirectorNodeType::Start,Bind?EDirectorNodeType::BindNPC:EDirectorNodeType::SpawnNPC,EDirectorNodeType::CinematicMode,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.ActorClass=ACameraActor::StaticClass();S.Role=TEXT("Prop");S.bHidePlayer=true;S.Duration=1;S.ActorSource=EDirectorActorSource::Object;S.ObjectKey=TEXT("ExistingProp");S.Transform=FTransform(FVector(10,20,30));A->Steps.Add(S);}for(int I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};FDirectorObjectEntry E;E.Key=TEXT("ExistingProp");E.ActorClass=ACameraActor::StaticClass();A->Objects.Add(E);return A;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorIntegrationLifecycle,"Constellation.SceneDirector.IntegrationLifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorIntegrationLifecycle::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);
 auto* Owner=W->SpawnActor<ACameraActor>();auto* C=NewObject<USceneDirectorInteractionComponent>(Owner);Owner->AddInstanceComponent(C);C->RegisterComponent();C->Director=IntegrationFixture();FString Error;TestTrue(TEXT("Compile"),FSceneDirectorCompiler::Compile(*C->Director,Error));
 C->HandleInteraction(Pawn);if(TestNotNull(TEXT("Runner created"),C->ActivePlayer.Get())){auto* R=C->ActivePlayer.Get();C->HandleInteraction(Pawn);TestEqual(TEXT("No duplicate"),C->ActivePlayer.Get(),R);C->Cancel();TestNull(TEXT("Cancel cleanup"),C->ActivePlayer.Get());TestFalse(TEXT("Visibility restored"),Pawn->IsHidden());}
 C->Director=nullptr;TestTrue(TEXT("Missing asset handled"),C->HandleInteraction(Pawn));TestFalse(TEXT("Error exposed"),C->LastError.IsEmpty());GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorIntegrationOrigin,"Constellation.SceneDirector.IntegrationOriginObjects",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorIntegrationOrigin::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=IntegrationFixture();FString Error;TestTrue(TEXT("Compile"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));Runner->bUseOrigin=true;Runner->OriginTransform=FTransform(FRotator(0,90,0),FVector(100,200,0));TestTrue(TEXT("Origin play"),Runner->PlayDirector());auto* Prop=Runner->FindNPC(TEXT("Prop"));if(TestNotNull(TEXT("Prop spawned"),Prop))TestTrue(TEXT("Native sequence applies rotated translated origin"),Prop->GetActorLocation().Equals(FVector(80,210,30),.01));Runner->StopDirector();
 auto* Existing=W->SpawnActor<ACameraActor>();Existing->SetActorLocation(FVector(700,800,900));Runner->Director=IntegrationFixture(true);TestTrue(TEXT("Compile binding"),FSceneDirectorCompiler::Compile(*Runner->Director,Error));TestFalse(TEXT("Missing object refused before playback"),Runner->PlayDirector());Runner->ObjectBindings.Add(TEXT("ExistingProp"),Existing);TestTrue(TEXT("Bound object play"),Runner->PlayDirector());TestEqual(TEXT("Uses actual existing actor"),Runner->FindNPC(TEXT("Prop")),static_cast<AActor*>(Existing));Runner->StopDirector();TestTrue(TEXT("Bound world pose restored"),Existing->GetActorLocation().Equals(FVector(700,800,900),.01));
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}


#include "UObject/StructOnScope.h"
#include "GameFramework/Character.h"
#include "Engine/GameInstance.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorStatueRoute,"Constellation.SceneDirector.StatueInteractionRoute",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorStatueRoute::RunTest(const FString&)
{
 auto* Class=LoadClass<AActor>(nullptr,TEXT("/Game/SceneDirector/Statue/BP_StatueDirector.BP_StatueDirector_C"));
 auto* HeroClass=LoadClass<ACharacter>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine.BP_Player_Heroine_C"));
 if(!TestNotNull(TEXT("Installed statue child BP"),Class)||!TestNotNull(TEXT("Original heroine BP"),HeroClass))return false;
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<ACharacter>(HeroClass);PC->Possess(Pawn);
 W->SetGameInstance(NewObject<UGameInstance>(W));
 const FTransform StatuePose(FRotator(0,90,0),FVector(-34550,-16750,1750),FVector(3));auto* Statue=W->SpawnActor<AActor>(Class,StatuePose);
 auto* C=Statue->FindComponentByClass<USceneDirectorInteractionComponent>();auto* Interact=Statue->FindFunction(TEXT("Interact"));auto* Visited=FindFProperty<FBoolProperty>(Class,TEXT("HasInteracted"));
 if(TestNotNull(TEXT("Interaction component"),C)&&TestNotNull(TEXT("BP override Interact"),Interact)&&TestNotNull(TEXT("Original first/repeat state"),Visited))
 {
  FStructOnScope Args(Interact);FindFProperty<FObjectPropertyBase>(Interact,TEXT("Interactor"))->SetObjectPropertyValue_InContainer(Args.GetStructMemory(),Pawn);
  for(FName Choice:{FName(TEXT("Leave")),FName(TEXT("Rest"))})
  {
   Statue->ProcessEvent(Interact,Args.GetStructMemory());auto* R=C->ActivePlayer.Get();
   if(!TestNotNull(TEXT("Real BP Interact routes to tool"),R))break;
   AddInfo(FString::Printf(TEXT("Authoring=%s Owner=%s Spawn=%s NPC=%s"),*C->Director->AuthoringOrigin.ToString(),*Statue->GetActorTransform().ToString(),*C->Director->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::SpawnNPC;})->Transform.ToString(),R->FindNPC(TEXT("Heroine"))?*R->FindNPC(TEXT("Heroine"))->GetActorTransform().ToString():TEXT("missing")));
   if(auto* NPC=R->FindNPC(TEXT("Heroine")))TestTrue(TEXT("Original statue origin does not shift original cast"),NPC->GetActorLocation().Equals(C->Director->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::SpawnNPC;})->Transform.GetLocation(),.1));
   int Choices=0;
   for(int I=0;I<1000&&C->ActivePlayer;++I)
   {R=C->ActivePlayer;if(R->IsWaitingForChoice()){TestTrue(TEXT("Select real statue choice"),R->SelectDialogueChoice(Choice));++Choices;}else if(R->IsWaitingForDialogue())R->AdvanceDialogue();R->Tick(.1f);}
   TestEqual(TEXT("One choice presented"),Choices,1);TestNull(TEXT("Full interaction completes"),C->ActivePlayer.Get());TestTrue(*C->LastError,C->LastError.IsEmpty());
   TestFalse(TEXT("Legacy Actor state is not modified"),Visited->GetPropertyValue_InContainer(Statue));TestFalse(TEXT("Player visible after finish"),Pawn->IsHidden());TestFalse(TEXT("Player controls restored"),PC->IsMoveInputIgnored());
  }
  Statue->ProcessEvent(Interact,Args.GetStructMemory());if(TestNotNull(TEXT("Repeat route starts"),C->ActivePlayer.Get()))TestEqual(TEXT("Rest completion selects repeat event"),C->ActivePlayer->EventKey,FName(TEXT("석상_재상호작용")));C->Cancel();
 }
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorExternalCameraBinding,"Constellation.SceneDirector.ExternalCameraBinding",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorExternalCameraBinding::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* Existing=W->SpawnActor<ACameraActor>();Existing->SetActorLocation(FVector(700,800,900));
 auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->ObjectBindings.Add(TEXT("ExistingProp"),Existing);
 auto* A=NewObject<USceneDirectorAsset>();
 for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::Camera,EDirectorNodeType::Wait,EDirectorNodeType::Camera,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.Duration=1;A->Steps.Add(S);}for(int I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};A->Steps[1].CameraKey=TEXT("One");A->Steps[3].CameraKey=TEXT("Two");A->Steps[1].bLookAtTarget=A->Steps[3].bLookAtTarget=false;
 FDirectorObjectEntry Object;Object.Key=TEXT("ExistingProp");Object.ActorClass=ACameraActor::StaticClass();A->Objects.Add(Object);
 FDirectorCameraEntry Camera;Camera.Key=TEXT("One");Camera.ObjectKey=Object.Key;A->Cameras.Add(Camera);Camera.Key=TEXT("Two");A->Cameras.Add(Camera);
 FString Error;TestTrue(TEXT("External camera graph compiles"),FSceneDirectorCompiler::Compile(*A,Error));Runner->Director=A;TestFalse(TEXT("Same camera under different keys rejected"),Runner->PlayDirector());
 A->Cameras[1].ObjectKey=NAME_None;TestTrue(TEXT("Unique camera compiles"),FSceneDirectorCompiler::Compile(*A,Error));TestTrue(TEXT("Existing camera plays"),Runner->PlayDirector());TestEqual(TEXT("Existing camera bound"),Runner->FindCamera(TEXT("One")),static_cast<AActor*>(Existing));Runner->StopDirector();TestTrue(TEXT("Camera pose restored"),Existing->GetActorLocation().Equals(FVector(700,800,900),.01));
 A->Cameras[0].ObjectKey=TEXT("Missing");TestFalse(TEXT("Missing object key rejected at compile"),FSceneDirectorCompiler::Compile(*A,Error));
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorConditionalEvents,"Constellation.SceneDirector.ConditionalEvents",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorConditionalEvents::RunTest(const FString&)
{
 auto* A=IntegrationFixture();FDirectorBoolEntry B;B.Key=TEXT("Seen");A->BoolVariables.Add(B);FDirectorIntEntry N;N.Key=TEXT("Count");A->IntVariables.Add(N);
 FDirectorEventCondition C;C.Key=B.Key;C.BoolValue=false;A->EntryConditions={C};auto* Repeat=DuplicateObject<USceneDirectorAsset>(A,A);Repeat->EventKey=TEXT("Repeat");Repeat->EntryConditions[0].BoolValue=true;A->EventGraphs.Add(Repeat);
 FDirectorEventCondition Limit;Limit.Type=EDirectorVariableType::Integer;Limit.Key=N.Key;Limit.Comparison=EDirectorComparison::GreaterEqual;Limit.IntValue=2;Repeat->EntryConditions.Add(Limit);
 FString Error;TestEqual(TEXT("False selects first"),A->SelectEvent({{B.Key,false}},{{N.Key,0}},Error),A);TestNull(TEXT("No matching event is explicit"),A->SelectEvent({{B.Key,true}},{{N.Key,1}},Error));TestEqual(TEXT("Bool plus int threshold selects repeat"),A->SelectEvent({{B.Key,true}},{{N.Key,2}},Error),Repeat);
 for(auto Op:{EDirectorComparison::Equal,EDirectorComparison::NotEqual,EDirectorComparison::Greater,EDirectorComparison::GreaterEqual,EDirectorComparison::Less,EDirectorComparison::LessEqual}){Repeat->EntryConditions[1].Comparison=Op;int V=Op==EDirectorComparison::Greater||Op==EDirectorComparison::NotEqual?3:Op==EDirectorComparison::Less?1:2;TestEqual(TEXT("Integer comparator matches"),A->SelectEvent({{B.Key,true}},{{N.Key,V}},Error),Repeat);}
 Repeat->EntryConditions[1].Key=TEXT("Missing");TestFalse(TEXT("Invalid event condition fails compile"),FSceneDirectorCompiler::Compile(*Repeat,Error));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorDialogueContinuity,"Constellation.SceneDirector.DialogueContinuity",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorDialogueContinuity::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);
 auto* A=NewObject<USceneDirectorAsset>();for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::SpawnNPC,EDirectorNodeType::CinematicMode,EDirectorNodeType::Dialogue,EDirectorNodeType::Wait,EDirectorNodeType::Dialogue,EDirectorNodeType::Wait,EDirectorNodeType::GameplayReturn,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.ActorClass=ACameraActor::StaticClass();S.Role=TEXT("Actor");S.Duration=1;S.bHidePlayer=true;S.SpeakerName=FText::FromString(TEXT(" "));S.DialogueText=FText::FromString(TEXT("Continued"));A->Steps.Add(S);}for(int I=0;I<A->Steps.Num()-1;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};A->Steps[5].DialoguePosition=EDirectorDialoguePosition::Center;A->Steps[1].bPlayerStandIn=true;A->Steps[2].bHideHUD=false;PC->ClientSetHUD(AHUD::StaticClass());
 auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;FString Error;TestTrue(TEXT("Compile dialogue gap"),FSceneDirectorCompiler::Compile(*A,Error));TestTrue(TEXT("Play"),R->PlayDirector());if(PC->GetHUD())TestFalse(TEXT("Control lock hides AHUD even with optional hide disabled"),PC->GetHUD()->bShowHUD);TestTrue(TEXT("Whitespace speaker has no nameplate"),R->CurrentSpeaker.IsEmpty());R->Tick(1.1);TestFalse(TEXT("Default keeps dialogue across gap"),R->CurrentDialogue.IsEmpty());R->Tick(1);TestEqual(TEXT("Next dialogue moves to center"),R->CurrentDialoguePosition,EDirectorDialoguePosition::Center);
 auto* NPC=R->FindNPC(TEXT("Actor"));R->Tick(1.85f);TestTrue(TEXT("Player still hidden before handoff"),Pawn->IsHidden());if(NPC)TestFalse(TEXT("NPC remains visible until handoff"),NPC->IsHidden());R->Tick(.1f);TestFalse(TEXT("Player restored on handoff frame"),Pawn->IsHidden());if(PC->GetHUD())TestTrue(TEXT("HUD restored at handoff"),PC->GetHUD()->bShowHUD);if(NPC)TestTrue(TEXT("NPC hidden on same handoff frame"),NPC->IsHidden());TestTrue(TEXT("Gameplay return closes held dialogue"),R->CurrentDialogue.IsEmpty());R->Tick(.1f);if(NPC)TestTrue(TEXT("NPC does not flash back next frame"),NPC->IsHidden());R->StopDirector();
 A->Steps[3].bKeepDialogueOpen=false;FSceneDirectorCompiler::Compile(*A,Error);R->PlayDirector();R->Tick(1.1f);TestTrue(TEXT("Explicit close hides dialogue in gap"),R->CurrentDialogue.IsEmpty());R->StopDirector();
 A->Steps[8].Type=EDirectorNodeType::CinematicMode;FDirectorStep Wait;Wait.Type=EDirectorNodeType::Wait;Wait.Duration=1;FDirectorStep End;End.Type=EDirectorNodeType::End;A->Steps[8].NextNodes={Wait.Id};Wait.NextNodes={End.Id};A->Steps.Add(Wait);A->Steps.Add(End);
 FDirectorStep Friend;Friend.Type=EDirectorNodeType::SpawnNPC;Friend.ActorClass=ACameraActor::StaticClass();Friend.Role=TEXT("Friend");Friend.NextNodes=A->Steps[1].NextNodes;A->Steps[1].NextNodes={Friend.Id};A->Steps.Add(Friend);
 TestTrue(TEXT("Compile cinematic re-entry"),FSceneDirectorCompiler::Compile(*A,Error));TestTrue(TEXT("Play cinematic re-entry"),R->PlayDirector());R->Tick(4.1f);NPC=R->FindNPC(TEXT("Actor"));auto* FriendActor=R->FindNPC(TEXT("Friend"));if(NPC)TestTrue(TEXT("Stand-in hidden after first return"),NPC->IsHidden());if(FriendActor)TestFalse(TEXT("Non-stand-in NPC remains visible"),FriendActor->IsHidden());R->Tick(1.1f);TestTrue(TEXT("Re-entry hides player"),Pawn->IsHidden());if(NPC)TestFalse(TEXT("Re-entry restores stand-in visibility"),NPC->IsHidden());R->StopDirector();
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorConditionalState,"Constellation.SceneDirector.ConditionalEventState",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorConditionalState::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();PC->Possess(Pawn);auto* Owner=W->SpawnActor<ACameraActor>();auto* C=NewObject<USceneDirectorInteractionComponent>(Owner);Owner->AddInstanceComponent(C);C->RegisterComponent();
 auto* A=NewObject<USceneDirectorAsset>();A->EventKey=TEXT("First");FDirectorBoolEntry B;B.Key=TEXT("Seen");A->BoolVariables.Add(B);FDirectorIntEntry N;N.Key=TEXT("Count");A->IntVariables.Add(N);FDirectorEventCondition Initial;Initial.Key=B.Key;Initial.BoolValue=false;A->EntryConditions={Initial};
 for(auto T:{EDirectorNodeType::Start,EDirectorNodeType::SetBool,EDirectorNodeType::SetInt,EDirectorNodeType::Wait,EDirectorNodeType::End}){FDirectorStep S;S.Type=T;S.BoolKey=B.Key;S.BoolValue=true;S.IntKey=N.Key;S.IntValue=2;S.Duration=1;A->Steps.Add(S);}for(int I=0;I<4;++I)A->Steps[I].NextNodes={A->Steps[I+1].Id};
 auto* Repeat=DuplicateObject<USceneDirectorAsset>(A,A);Repeat->EventKey=TEXT("Repeat");Repeat->EntryConditions[0].BoolValue=true;FDirectorEventCondition Enough;Enough.Type=EDirectorVariableType::Integer;Enough.Key=N.Key;Enough.Comparison=EDirectorComparison::GreaterEqual;Enough.IntValue=2;Repeat->EntryConditions.Add(Enough);A->EventGraphs.Add(Repeat);C->Director=A;
 FString Error;TestTrue(TEXT("Compile first"),FSceneDirectorCompiler::Compile(*A,Error));TestTrue(TEXT("Compile repeat"),FSceneDirectorCompiler::Compile(*Repeat,Error));
 C->HandleInteraction(Pawn);if(TestNotNull(TEXT("First runner"),C->ActivePlayer.Get())){TestTrue(TEXT("SetBool executed"),C->ActivePlayer->BoolValues.FindRef(B.Key));TestEqual(TEXT("SetInt executed"),C->ActivePlayer->IntValues.FindRef(N.Key),2);C->Cancel();}
 C->HandleInteraction(Pawn);if(TestNotNull(TEXT("Replay after cancel"),C->ActivePlayer.Get())){TestEqual(TEXT("Cancel did not commit state"),C->ActivePlayer->EventKey,A->EventKey);C->ActivePlayer->Tick(2);}
 C->HandleInteraction(Pawn);if(TestNotNull(TEXT("Replay after finish"),C->ActivePlayer.Get())){TestEqual(TEXT("Bool and int committed and select repeat"),C->ActivePlayer->EventKey,Repeat->EventKey);C->Cancel();}
 auto* Other=NewObject<USceneDirectorInteractionComponent>(Pawn);Pawn->AddInstanceComponent(Other);Other->RegisterComponent();Other->Director=A;Other->HandleInteraction(Pawn);if(TestNotNull(TEXT("Another instance"),Other->ActivePlayer.Get()))TestEqual(TEXT("State isolated per component"),Other->ActivePlayer->EventKey,A->EventKey);Other->Cancel();
 TestFalse(TEXT("Asset bool default not mutated"),A->BoolVariables[0].Value);TestEqual(TEXT("Asset int default not mutated"),A->IntVariables[0].Value,0);GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
