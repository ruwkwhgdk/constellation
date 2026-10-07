#include "CombatLabCharacter.h"
#include "CombatWorkbenchSubsystem.h"
#include "Engine/GameInstance.h"
#include "CombatAbilitySystem.h"
#include "CombatVFXComponent.h"
#include "CombatHitReactionComponent.h"
#include "CombatActionDefinition.h"
#include "CombatAttackInput.h"
#include "CombatPatternProfile.h"
#include "CombatEnemyAgent.h"
#include "CombatEncounterProfile.h"
#include "BTTask_CombatAction.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/Composites/BTComposite_Sequence.h"
#include "BehaviorTree/Tasks/BTTask_Wait.h"
#include "AIController.h"
#include "BrainComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "InputCoreTypes.h"
ACombatLabCharacter::ACombatLabCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    bUseControllerRotationYaw = false;
    EnemyAgent=CreateDefaultSubobject<UCombatEnemyAgent>(TEXT("EnemyAgent"));
    Combat = CreateDefaultSubobject<UCombatAbilitySystem>(TEXT("Combat"));
    CombatVFX = CreateDefaultSubobject<UCombatVFXComponent>(TEXT("CombatVFX"));
    HitReaction = CreateDefaultSubobject<UCombatHitReactionComponent>(TEXT("HitReaction"));
    Sword = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Sword"));
    Sword->SetupAttachment(GetMesh());
    Sword->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Sword->SetCastShadow(false);
    AttackInput = CreateDefaultSubobject<UCombatAttackInput>(TEXT("AttackInput"));
    Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraArm"));
    Arm->SetupAttachment(GetRootComponent()); Arm->TargetArmLength = 450.f;
    Arm->bUsePawnControlRotation = true; Arm->SetRelativeLocation(FVector(0,0,10));
    Arm->bEnableCameraLag = true; Arm->CameraLagSpeed = 10.f; Arm->CameraLagMaxDistance = 60.f;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(Arm);
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    GetCharacterMovement()->MaxWalkSpeed = 500.f;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0,360,0);
}
UAbilitySystemComponent* ACombatLabCharacter::GetAbilitySystemComponent() const { return Combat; }
void ACombatLabCharacter::BeginPlay()
{
    Super::BeginPlay();
    if(auto* GI=GetGameInstance()) GI->GetSubsystem<UCombatWorkbenchSubsystem>()->PrepareActor(this);
    Combat->InitializeCombat(this);
    CombatVFX->Initialize(Combat);
    HitReaction->Initialize(Combat);
    AttackInput->Initialize(Combat);
    Arm->SetUsingAbsoluteRotation(false); Arm->bUsePawnControlRotation = true;
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
    Combat->TeamId = bTrainingEnemy ? 1 : 0;
    Combat->OnDied.AddWeakLambda(this, [this]()
    {
        if (auto* AI = Cast<AAIController>(GetController()))
            if (AI->BrainComponent) AI->BrainComponent->StopLogic(TEXT("Dead"));
        GetCharacterMovement()->DisableMovement();
        GetMesh()->SetVisibility(false, true);
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    });
    if (bTrainingEnemy)
    {
        auto* AI = Cast<AAIController>(GetController());
        if (!AI) { AI = GetWorld()->SpawnActor<AAIController>(); AI->Possess(this); }
        EnemyAgent->Initialize(EncounterProfile);
        UBehaviorTree* Tree = NewObject<UBehaviorTree>(this);
        Tree->BlackboardAsset = NewObject<UBlackboardData>(Tree);
        auto* Root = NewObject<UBTComposite_Sequence>(Tree);
        auto* Wait = NewObject<UBTTask_Wait>(Tree);
        Wait->WaitTime = .6f; Wait->RandomDeviation = 0.f;
        auto* Strike = NewObject<UBTTask_CombatAction>(Tree);
        Strike->Action = Action; Strike->PatternProfile=PatternProfile;
        FBTCompositeChild PauseChild; PauseChild.ChildTask = Wait;
        FBTCompositeChild StrikeChild; StrikeChild.ChildTask = Strike;
        Root->Children.Add(PauseChild); Root->Children.Add(StrikeChild);
        Tree->RootNode = Root;
        AI->RunBehaviorTree(Tree);
    }
#if !UE_BUILD_SHIPPING
    ConfigureAutomatedReview();
#endif
}
void ACombatLabCharacter::Attack()
{
    if(bWorkbenchOpen) return;
    if (Combat->IsActing() || Combat->IsDodging() || Combat->IsHitReacting()) { AttackInput->RequestAttack(Action); return; }
    if (CanLockTarget(LockedTarget.Get(),1100.f))
        SetActorRotation(FRotator(0,(LockedTarget->GetActorLocation()-GetActorLocation()).Rotation().Yaw,0));
    AttackInput->RequestAttack(Action);
}
void ACombatLabCharacter::Dodge()
{
    if(bWorkbenchOpen) return;
    auto* PC=Cast<APlayerController>(Controller);
    if(!PC) return;
    const FVector Input(PC->IsInputKeyDown(EKeys::W)-PC->IsInputKeyDown(EKeys::S),PC->IsInputKeyDown(EKeys::D)-PC->IsInputKeyDown(EKeys::A),0);
    Combat->TryDodge(FRotator(0,PC->GetControlRotation().Yaw,0).RotateVector(Input));
    AttackInput->LastInputReason=Combat->LastReason;
}
void ACombatLabCharacter::Cancel() { if(bWorkbenchOpen) return; AttackInput->Clear(); Combat->CancelAction(); }
void ACombatLabCharacter::ResetReview()
{
    if(bWorkbenchOpen) return;
    if (auto* PC = Cast<APlayerController>(Controller)) PC->ConsoleCommand(TEXT("RestartLevel"));
}
void ACombatLabCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    if(auto* PC=Cast<APlayerController>(Controller))
    {
        PC->SetControlRotation(FRotator(-25,-60,0));
        PC->bShowMouseCursor=false;
        PC->SetInputMode(FInputModeGameOnly());
    }
    SetupProjectControls(Input);

    Input->BindKey(EKeys::F1, IE_Pressed, this, &ACombatLabCharacter::ToggleWorkbench).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::SpaceBar, IE_Pressed, this, &ACombatLabCharacter::Dodge);
    Input->BindKey(EKeys::Q, IE_Pressed, this, &ACombatLabCharacter::UseSkill);
    Input->BindKey(EKeys::E, IE_Pressed, this, &ACombatLabCharacter::UseUltimate);
    Input->BindKey(EKeys::Tab, IE_Pressed, this, &ACombatLabCharacter::ToggleTargetLock);
    Input->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &ACombatLabCharacter::Attack);
    Input->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &ACombatLabCharacter::Cancel);
    Input->BindKey(EKeys::R, IE_Pressed, this, &ACombatLabCharacter::ResetReview);
}
void ACombatLabCharacter::Tick(float Delta)
{
    Super::Tick(Delta);
    EnsureWorkbench();
    if(bWorkbenchOpen) return;
    if (Combat->IsActing() || Combat->IsHitReacting())
    {
        ConsumeMovementInputVector();
        GetCharacterMovement()->StopMovementImmediately();
    }
    UpdateTargetLock(Delta);
    UpdateLocomotion();
    if (!bTrainingEnemy) if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        FVector Input(PC->IsInputKeyDown(EKeys::W) - PC->IsInputKeyDown(EKeys::S),
                     PC->IsInputKeyDown(EKeys::D) - PC->IsInputKeyDown(EKeys::A), 0);
        const FRotator ViewYaw(0, PC->GetControlRotation().Yaw, 0);
        const FVector Move = ViewYaw.RotateVector(Input).GetSafeNormal();
        if (Combat->GetHealth()>0 && !Combat->IsActing() && !Combat->IsHitReacting() && !Combat->IsDodging() && !Move.IsNearlyZero())
        {
            AddMovementInput(Move.GetSafeNormal());
        }

    }
}
float ACombatLabCharacter::TakeDamage(float Amount, const FDamageEvent&, AController*, AActor* Causer)
{
    const float Before = Combat->GetHealth();
    return Combat->ReceiveCombatDamage(Amount, Causer) ? Before - Combat->GetHealth() : 0.f;
}
















bool ACombatLabCharacter::UseSpecialAction(bool Ultimate)
{
    if(bWorkbenchOpen) return false;
    auto* Slot=Ultimate?UltimateAction.Get():SkillAction.Get();
    if(!Slot){AttackInput->LastInputReason=Ultimate?TEXT("Ultimate slot empty"):TEXT("Skill slot empty");return false;}
    FString Reason;
    if(!Combat->CanStart(Slot,Reason)){AttackInput->LastInputReason=Reason;return false;}
    if(CanLockTarget(LockedTarget.Get(),1100.f))
    {
        const FVector Direction=LockedTarget->GetActorLocation()-GetActorLocation();
        SetActorRotation(FRotator(0,Direction.Rotation().Yaw,0));
    }
    const bool Started=Combat->TryStartAction(Slot);
    if(Started) AttackInput->Clear();
    AttackInput->LastInputReason=Started?(Ultimate?TEXT("Ultimate started"):TEXT("Skill started")):Combat->LastReason;
    return Started;
}
void ACombatLabCharacter::UseSkill(){UseSpecialAction(false);}
void ACombatLabCharacter::UseUltimate(){UseSpecialAction(true);}
