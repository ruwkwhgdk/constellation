#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "InteractionPromptComponent.h"
#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInteractionPromptCarryTest,"Constellation.InteractionPrompt.CarryAvailability",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FInteractionPromptCarryTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    ACharacter* Player=World->SpawnActor<ACharacter>(FVector(0,0,100),FRotator::ZeroRotator);
    UCarryComponent* Carry=NewObject<UCarryComponent>(Player); Player->AddInstanceComponent(Carry); Carry->RegisterComponent();
    UInteractionPromptComponent* Prompt=NewObject<UInteractionPromptComponent>(Player); Player->AddInstanceComponent(Prompt); Prompt->RegisterComponent();
    AActor* Target=nullptr;
    TestEqual(TEXT("Empty space has no prompt"),Prompt->QueryAction(Target),EInteractionAction::None);
    AActor* Item=World->SpawnActor<AActor>();
    UStaticMeshComponent* Mesh=NewObject<UStaticMeshComponent>(Item); Item->SetRootComponent(Mesh);
    Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Mesh->SetWorldScale3D(FVector(.4)); Mesh->SetMobility(EComponentMobility::Movable);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); Mesh->SetCollisionResponseToAllChannels(ECR_Block);
    Mesh->RegisterComponent(); Mesh->SetMassOverrideInKg(NAME_None,5,true); Item->SetActorLocation(FVector(90,0,60));
    UHoldableComponent* Hold=NewObject<UHoldableComponent>(Item); Item->AddInstanceComponent(Hold); Hold->RegisterComponent();
    TestEqual(TEXT("Reachable item previews pickup before pressing F"),Prompt->QueryAction(Target),EInteractionAction::PickUp);
    TestEqual(TEXT("Prompt identifies exact input target"),Target,Item);
    TestEqual(TEXT("Preview does not pick item up"),Carry->State,ECarryState::Idle);
    APlayerController* PC=World->SpawnActor<APlayerController>(); PC->Possess(Player); PC->bShowMouseCursor=true;
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestEqual(TEXT("Visible cursor in gameplay does not suppress interaction"),Prompt->QueryAction(Target),EInteractionAction::PickUp);
    PC->SetIgnoreMoveInput(true);
    TestEqual(TEXT("Blocked gameplay does suppress interaction"),Prompt->QueryAction(Target),EInteractionAction::None);
    PC->ResetIgnoreMoveInput();
    Mesh->SetMassOverrideInKg(NAME_None,100,true);
    TestEqual(TEXT("Too heavy has no executable prompt"),Prompt->QueryAction(Target),EInteractionAction::None);
    Mesh->SetMassOverrideInKg(NAME_None,1,true);
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    TestEqual(TEXT("Airborne cannot pick up"),Prompt->QueryAction(Target),EInteractionAction::None);
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Input accepts the previewed pickup"),Carry->HandleInteract());
    TestEqual(TEXT("Pickup transition hides prompt"),Prompt->QueryAction(Target),EInteractionAction::None);
    Carry->OnPickupContact(); Carry->FinishAction();
    TestEqual(TEXT("No floor cannot advertise placement"),Prompt->QueryAction(Target),EInteractionAction::None);
    Carry->BeginAim();
    TestEqual(TEXT("Aim interaction cancels aiming"),Prompt->QueryAction(Target),EInteractionAction::CancelAim);
    Carry->AbortCarry();
    World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInteractionPromptStateTest,"Constellation.InteractionPrompt.AuthoredStateRules",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FInteractionPromptStateTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    ACharacter* Player=World->SpawnActor<ACharacter>();
    UInteractionPromptComponent* Prompt=NewObject<UInteractionPromptComponent>(Player);
    auto Spawn=[World](const TCHAR* Path) { return World->SpawnActor<AActor>(LoadClass<AActor>(nullptr,Path)); };
    auto SetBool=[](AActor* A,FName N,bool V) { auto* P=FindFProperty<FBoolProperty>(A->GetClass(),N); if(P) P->SetPropertyValue_InContainer(A,V); };
    AActor* Chest=Spawn(TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Chest.BP_Chest_C"));
    if(!TestNotNull(TEXT("Chest fixture loads"),Chest)) { World->DestroyWorld(false); return false; }
    FInteractionPromptRule Rule; Rule.ActorClass=Chest->GetClass(); Rule.Action=EInteractionAction::Open; Rule.CompletedProperty=TEXT("IsOpened"); Prompt->Rules.Add(Rule);
    SetBool(Chest,TEXT("IsOpened"),false);
    TestEqual(TEXT("Unopened chest offers Open"),Prompt->GetTargetAction(Chest),EInteractionAction::Open);
    SetBool(Chest,TEXT("IsOpened"),true);
    TestEqual(TEXT("Opened chest disappears"),Prompt->GetTargetAction(Chest),EInteractionAction::None);
    AActor* Door=Spawn(TEXT("/Game/Constellation/Environments/School/Blueprints/BP_School_Door.BP_School_Door_C"));
    if(!TestNotNull(TEXT("Door fixture loads"),Door)) { World->DestroyWorld(false); return false; }
    Rule=FInteractionPromptRule(); Rule.ActorClass=Door->GetClass(); Rule.Action=EInteractionAction::Open; Rule.AlternateAction=EInteractionAction::Close; Rule.ToggleProperty=TEXT("IsOpen"); Prompt->Rules.Insert(Rule,0);
    SetBool(Door,TEXT("IsOpen"),false);
    TestEqual(TEXT("Closed door offers Open"),Prompt->GetTargetAction(Door),EInteractionAction::Open);
    SetBool(Door,TEXT("IsOpen"),true);
    TestEqual(TEXT("Open door offers Close"),Prompt->GetTargetAction(Door),EInteractionAction::Close);
    Door->SetActorHiddenInGame(true);
    TestEqual(TEXT("Hidden actor has no prompt"),Prompt->GetTargetAction(Door),EInteractionAction::None);
    TestEqual(TEXT("Destroyed or missing actor is safe"),Prompt->GetTargetAction(nullptr),EInteractionAction::None);
    AActor* Ladder=World->SpawnActor<AActor>();
    UBoxComponent* Top=NewObject<UBoxComponent>(Ladder); Top->ComponentTags.Add(TEXT("LadderTop"));
    Rule=FInteractionPromptRule(); Rule.ActorClass=AActor::StaticClass(); Rule.Action=EInteractionAction::Climb;
    Rule.AlternateAction=EInteractionAction::Descend; Rule.AlternateComponentTag=TEXT("LadderTop");
    Prompt->Rules.Empty(); Prompt->Rules.Add(Rule);
    TestEqual(TEXT("Ladder bottom offers ascent"),Prompt->GetTargetAction(Ladder),EInteractionAction::Climb);
    TestEqual(TEXT("Ladder top offers descent"),Prompt->GetTargetAction(Ladder,Top),EInteractionAction::Descend);
    World->DestroyWorld(false); return true;
}
#endif
