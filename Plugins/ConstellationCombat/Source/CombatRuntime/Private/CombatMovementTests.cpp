#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputKeyEventArgs.h"
#include "Engine/World.h"
#include "CombatActionDefinition.h"
#include "Components/BoxComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "GameFramework/CharacterMovementComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatCameraMovementTest,"Constellation.CombatCore.CameraRelativeMovement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatCameraMovementTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=World->SpawnActor<ACombatLabCharacter>();
    auto* PC=World->SpawnActor<APlayerController>();
    PC->Possess(Actor); PC->PlayerInput=NewObject<UPlayerInput>(PC);
    Actor->Combat->InitializeCombat(Actor);
    for(float Yaw : {90.f,-60.f,180.f})
    {
        PC->SetControlRotation(FRotator(-25,Yaw,0));
        Actor->Arm->SetWorldRotation(FRotator(-25,Yaw,0));
        PC->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1.f));
        TArray<UInputComponent*> Stack;
        PC->PlayerInput->ProcessInputStack(Stack,.016f,false);
        TestTrue(TEXT("W reaches PlayerInput"),PC->IsInputKeyDown(EKeys::W));
        Actor->Tick(.016f);
        FVector Movement=Actor->ConsumeMovementInputVector();
        TestTrue(TEXT("W follows camera forward on ground"),
            FVector::DotProduct(Movement.GetSafeNormal(),FRotator(0,Yaw,0).Vector())>.99f);
        PC->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0.f));
        PC->PlayerInput->ProcessInputStack(Stack,.016f,false);
    }
    World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatLockTest,"Constellation.CombatCore.TargetLockLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatLockTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Actor=World->SpawnActor<ACombatLabCharacter>(FVector(0,0,100),FRotator::ZeroRotator,Spawn);
    auto* Target=World->SpawnActor<ACombatLabCharacter>(FVector(0,250,100),FRotator::ZeroRotator,Spawn);
    auto* Behind=World->SpawnActor<ACombatLabCharacter>(FVector(0,-150,100),FRotator::ZeroRotator,Spawn);
    for(auto* Pawn : {Actor,Target,Behind}) Pawn->Combat->InitializeCombat(Pawn);
    Target->Combat->TeamId=1; Behind->Combat->TeamId=1;
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Actor);
    PC->SetControlRotation(FRotator(-20,90,0)); PC->PlayerInput=NewObject<UPlayerInput>(PC);
    Actor->ToggleTargetLock();
    TestTrue(TEXT("Select visible enemy in front of camera"),Actor->GetLockedTarget()==Target);
    Actor->ToggleTargetLock(); TestNull(TEXT("Second press unlocks"),Actor->GetLockedTarget());
    Actor->ToggleTargetLock();
    AActor* Wall=World->SpawnActor<AActor>();
    auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(100,10,100)); Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent();
    Wall->SetActorLocation(FVector(0,125,100));
    Actor->Tick(.016f); TestNull(TEXT("New wall releases existing lock"),Actor->GetLockedTarget());
    Actor->ToggleTargetLock(); TestNull(TEXT("No lock through wall"),Actor->GetLockedTarget());
    Wall->Destroy(); Actor->ToggleTargetLock();
    Target->SetActorLocation(FVector(0,2000,100)); Actor->Tick(.016f);
    TestNull(TEXT("Out of range target releases lock"),Actor->GetLockedTarget());
    Target->SetActorLocation(FVector(0,250,100)); Actor->ToggleTargetLock();
    Target->Combat->ReceiveCombatDamage(100,Actor); Actor->Tick(.016f);
    TestNull(TEXT("Dead target releases lock"),Actor->GetLockedTarget());
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatLocomotionTest,"Constellation.CombatCore.LocomotionAndAttackRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatLocomotionTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=World->SpawnActor<ACombatLabCharacter>();
    Actor->GetMesh()->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview")));
    Actor->GetMesh()->InitAnim(true); Actor->Combat->InitializeCombat(Actor);
    Actor->IdleAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed"));
    Actor->MoveAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft"));
    Actor->Tick(.016f);
    auto* Single=Actor->GetMesh()->GetSingleNodeInstance();
    TestTrue(TEXT("Idle plays while stationary"),Single && Single->GetCurrentAsset()==Actor->IdleAnimation);
    Actor->GetCharacterMovement()->Velocity=FVector(168,0,0); Actor->Tick(.016f);
    TestTrue(TEXT("Run plays at movement speed"),Single && Single->GetCurrentAsset()==Actor->MoveAnimation);
    Actor->GetCharacterMovement()->Velocity=FVector(500,0,0); Actor->Tick(.016f);
    TestEqual(TEXT("Run tempo follows project speed"),Single->GetPlayRate(),500.f/168.f);
    auto* Action=LoadObject<UCombatActionDefinition>(nullptr,TEXT("/Game/Constellation/Review/CombatCore/DA_PlayerSlash"));
    TestTrue(TEXT("Attack starts while moving"),Actor->Combat->TryStartAction(Action));
    TestTrue(TEXT("Movement stops at commit, before next pawn tick"),Actor->GetVelocity().IsNearlyZero());
    Actor->Tick(.016f);
    TestTrue(TEXT("Attack stops residual movement"),Actor->GetVelocity().IsNearlyZero());
    TestTrue(TEXT("Locomotion cannot replace active montage"),Single && Single->GetCurrentAsset()==Action->Montage);
    Actor->Combat->CancelAction(); Actor->GetCharacterMovement()->Velocity=FVector(168,0,0); Actor->Tick(.016f);
    TestTrue(TEXT("Movement animation returns after cancellation"),Single && Single->GetCurrentAsset()==Actor->MoveAnimation);
    World->DestroyWorld(false); return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatMouseCameraTest,"Constellation.CombatCore.MouseCameraInput",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatMouseCameraTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=World->SpawnActor<ACombatLabCharacter>();
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Actor);
    PC->PlayerInput=NewObject<UPlayerInput>(PC);
    auto* Input=NewObject<UInputComponent>(Actor);
    Actor->SetupPlayerInputComponent(Input);
    PC->SetAsLocalPlayerController();
    PC->RotationInput=FRotator::ZeroRotator;
    Actor->ApplyProjectLook(FInputActionValue(FVector2D(2,-3)));
    TestEqual(TEXT("Project yaw controller scale"),PC->RotationInput.Yaw,5.0);
    TestEqual(TEXT("Project pitch controller scale"),PC->RotationInput.Pitch,7.5);
    TestFalse(TEXT("Camera cannot force actor yaw"),Actor->bUseControllerRotationYaw);
    TestTrue(TEXT("Spring arm follows control rotation"),Actor->Arm->bUsePawnControlRotation);
    World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatProjectDefaultsTest,"Constellation.CombatCore.ProjectControlDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatProjectDefaultsTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=World->SpawnActor<ACombatLabCharacter>();
    TestEqual(TEXT("Project runtime walk speed"),Actor->GetCharacterMovement()->MaxWalkSpeed,500.f);
    TestTrue(TEXT("Project camera position lag enabled"),Actor->Arm->bEnableCameraLag);
    TestEqual(TEXT("Project camera follow speed"),Actor->Arm->CameraLagSpeed,10.f);
    TestEqual(TEXT("Project camera lag distance"),Actor->Arm->CameraLagMaxDistance,60.f);
    TestEqual(TEXT("Project camera mount height"),Actor->Arm->GetRelativeLocation().Z,10.0);
    World->DestroyWorld(false); return true;
}

#endif
