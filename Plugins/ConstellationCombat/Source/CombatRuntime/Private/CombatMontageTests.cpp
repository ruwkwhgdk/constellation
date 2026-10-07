#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatAttackInput.h"
#include "TimerManager.h"
#include "CombatActionDefinition.h"
#include "CombatPatternProfile.h"
#include "CombatEnemyAgent.h"
#include "CombatEncounterProfile.h"
#include "CombatAttributes.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "CombatHitWindow.h"
#include "CombatVFXComponent.h"
#include "ConstellationFXActor.h"
#include "EngineUtils.h"
#include "NiagaraSystem.h"
#include "NiagaraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "CombatLabCharacter.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "BTTask_CombatAction.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/Composites/BTComposite_Sequence.h"
namespace CombatTest
{
    UCombatActionDefinition* Action(UObject* Outer)
    {
        auto* Definition = NewObject<UCombatActionDefinition>(Outer);
        UAnimMontage* Source = LoadObject<UAnimMontage>(nullptr,
            TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AM_player_heroine_new_Attack01_Horizontal.AM_player_heroine_new_Attack01_Horizontal"));
        if (!Source) return Definition;
        Definition->Montage = DuplicateObject<UAnimMontage>(Source, Definition);
        Definition->Montage->Notifies.Reset();
        auto* Window = NewObject<UCombatHitWindow>(Definition->Montage);
        FAnimNotifyEvent Event;
        Event.NotifyStateClass = Window; Event.NotifyName = TEXT("CombatHit");
        Event.Link(Definition->Montage, .35f); Event.SetDuration(.15f);
        Event.EndLink.Link(Definition->Montage, .50f);
        Definition->Montage->Notifies.Add(Event);
        Definition->Cooldown = 0.f;
        return Definition;
    }
    ACombatLabCharacter* Actor(UWorld* World, FVector Location, int32 Team)
    {
        FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Actor = World->SpawnActor<ACombatLabCharacter>(Location, FRotator::ZeroRotator, Params);
        Actor->GetMesh()->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,
            TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview")));
        Actor->GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
        Actor->GetMesh()->InitAnim(true);
        Actor->Combat->InitializeCombat(Actor); Actor->Combat->TeamId = Team;
        return Actor;
    }
    int32 Instance(ACombatLabCharacter* Actor, UCombatActionDefinition* Action)
    {
        auto* Montage = Actor->GetMesh()->GetAnimInstance()->GetActiveInstanceForMontage(Action->Montage);
        return Montage ? Montage->GetInstanceID() : INDEX_NONE;
    }
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatLifecycleTest,"Constellation.CombatCore.MontageLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatLifecycleTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    auto* Actor = CombatTest::Actor(World, FVector(0,0,100), 0);
    auto* Victim = CombatTest::Actor(World, FVector(100,0,100), 1);
    auto* Action = CombatTest::Action(Actor);
    int32 Ends = 0;
    Actor->Combat->OnActionEnded.AddLambda([&Ends](uint64, ECombatActionResult) { ++Ends; });
    if (!TestTrue(TEXT("Real montage activates through GAS"), Actor->Combat->TryStartAction(Action)))
    {
        AddError(Actor->Combat->LastReason);
        World->DestroyWorld(false); return false;
    }
    TestEqual(TEXT("Cost charged once"), Actor->Combat->GetStamina(), 90.f);
    TestFalse(TEXT("Concurrent action refused"), Actor->Combat->TryStartAction(Action));
    TestEqual(TEXT("Refused action has no extra cost"), Actor->Combat->GetStamina(), 90.f);
    const int32 OldInstance = CombatTest::Instance(Actor, Action);
    Actor->Combat->OpenHitWindow("Swing", OldInstance);
    Actor->Combat->ApplyHit("Swing", Victim);
    TestEqual(TEXT("Opening overlap and extra contacts still give one hit"), Victim->Combat->GetHealth(), 80.f);
    Actor->Combat->CancelAction(); Actor->Combat->CancelAction();
    TestEqual(TEXT("Cancel ends exactly once"), Ends, 1);
    TestFalse(TEXT("Cancel clears active action"), Actor->Combat->IsActing());
    TestFalse(TEXT("Cancel clears damage window"), Actor->Combat->ApplyHit("Swing", Victim));
    TestTrue(TEXT("Same action can restart"), Actor->Combat->TryStartAction(Action));
    Actor->Combat->OpenHitWindow("Swing", OldInstance);
    TestFalse(TEXT("Late notify from old montage cannot reopen new attack"), Actor->Combat->ApplyHit("Swing", Victim));
    Actor->Combat->ReceiveCombatDamage(100.f, Victim);
    TestFalse(TEXT("Death cancels active GAS action"), Actor->Combat->IsActing());
    TestEqual(TEXT("Death triggers one more end"), Ends, 2);
    TestFalse(TEXT("Dead owner cannot restart"), Actor->Combat->TryStartAction(Action));
    World->DestroyWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatResourceTest,"Constellation.CombatCore.CostCooldownAndValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatResourceTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(Actor);
    FString Reason;
    TestTrue(TEXT("Valid montage window"),Action->Validate(Reason));
    Action->StaminaCost=101.f;
    TestFalse(TEXT("Insufficient resource rejects"),Actor->Combat->TryStartAction(Action));
    TestEqual(TEXT("No partial spending"),Actor->Combat->GetStamina(),100.f);
    Action->StaminaCost=10.f; Action->Cooldown=10.f;
    TestTrue(TEXT("Attack starts"),Actor->Combat->TryStartAction(Action));
    Actor->Combat->CancelAction();
    TestFalse(TEXT("Cancellation does not evade committed cooldown"),Actor->Combat->TryStartAction(Action));
    Action->Damage=-1.f;
    TestFalse(TEXT("Negative damage definition rejected"),Action->Validate(Reason));
    Action->Damage=20.f; const FAnimNotifyEvent Duplicate=Action->Montage->Notifies[0]; Action->Montage->Notifies.Add(Duplicate);
    TestFalse(TEXT("Duplicate window names rejected"),Action->Validate(Reason));
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatNaturalEndTest,"Constellation.CombatCore.NaturalMontageCompletion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatNaturalEndTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(Actor);
    int32 Ends=0; ECombatActionResult Result=ECombatActionResult::Failed;
    Actor->Combat->OnActionEnded.AddLambda([&](uint64,ECombatActionResult InResult){++Ends;Result=InResult;});
    TestTrue(TEXT("Action starts"),Actor->Combat->TryStartAction(Action));
    for(int32 i=0;i<50;++i)
    {
        Actor->GetMesh()->TickAnimation(.05f,false);
        Actor->GetMesh()->RefreshBoneTransforms();
        Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents();
    }
    TestFalse(TEXT("Animation completion releases action without fixed Delay"),Actor->Combat->IsActing());
    TestEqual(TEXT("Exactly one natural completion"),Ends,1);
    TestEqual(TEXT("Success differs from interruption"),Result,ECombatActionResult::Succeeded);
    World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatReentrantCostTest,"Constellation.CombatCore.ReentrantCostCancellation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatReentrantCostTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(Actor); Action->Cooldown=10.f;
    const FDelegateHandle Listener=Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute())
        .AddLambda([Actor](const FOnAttributeChangeData& Change)
        {
            if(Change.NewValue < Change.OldValue) Actor->Combat->CancelAllAbilities();
        });
    TestFalse(TEXT("Cancelled during cost is not reported active"),Actor->Combat->TryStartAction(Action));
    TestFalse(TEXT("Reentrant cancellation leaves no action"),Actor->Combat->IsActing());
    TestEqual(TEXT("Committed cost stays spent"),Actor->Combat->GetStamina(),90.f);
    Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).Remove(Listener);
    TestFalse(TEXT("Committed cooldown survives reentrant cancel"),Actor->Combat->TryStartAction(Action));
    World->DestroyWorld(false); return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatWindowTraceTest,"Constellation.CombatCore.AutomaticWindowsAndOcclusion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatWindowTraceTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Victim=CombatTest::Actor(World,FVector(200,0,100),1);
    auto* Action=CombatTest::Action(Actor); Action->Reach=240.f;
    AActor* Wall=World->SpawnActor<AActor>();
    auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(10,100,100)); Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent();
    Wall->SetActorLocation(FVector(100,0,100));
    TestTrue(TEXT("Action starts behind wall"),Actor->Combat->TryStartAction(Action));
    const int32 Id=CombatTest::Instance(Actor,Action);
    Actor->Combat->OpenHitWindow("Swing",Id);
    TestEqual(TEXT("World blocker prevents damage through wall"),Victim->Combat->GetHealth(),100.f);
    Actor->Combat->CancelAction(); Wall->Destroy();
    TestTrue(TEXT("Next attack starts without wall"),Actor->Combat->TryStartAction(Action));
    for(int32 i=0;i<50;++i)
    {
        Actor->GetMesh()->TickAnimation(.05f,false);
        Actor->GetMesh()->RefreshBoneTransforms();
        Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents();
    }
    TestEqual(TEXT("Actual montage notify gives exactly one hit"),Victim->Combat->GetHealth(),80.f);
    World->DestroyWorld(false); return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatReplacementTest,"Constellation.CombatCore.ReentrantReplacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatReplacementTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* First=CombatTest::Action(Actor);
    auto* Next=CombatTest::Action(Actor); Next->StaminaCost=0.f;
    TestTrue(TEXT("Pregrant replacement"),Actor->Combat->TryStartAction(Next));
    Actor->Combat->CancelAction();
    const uint64 Expected=Actor->Combat->GetExecutionId()+1;
    const auto End=Actor->Combat->OnActionEnded.AddLambda([&](uint64 Id,ECombatActionResult)
    { if(Id==Expected) Actor->Combat->TryStartAction(Next); });
    const auto Cost=Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute())
        .AddLambda([Actor](const FOnAttributeChangeData& Change)
        { if(Change.NewValue<Change.OldValue) Actor->Combat->CancelAllAbilities(); });
    TestFalse(TEXT("Replacement B cannot report cancelled A as started"),Actor->Combat->TryStartAction(First));
    TestTrue(TEXT("Replacement is independently active"),Actor->Combat->IsActing());
    TestTrue(TEXT("Replacement has a different execution"),Actor->Combat->GetExecutionId()>Expected);
    Actor->Combat->OnActionEnded.Remove(End);
    Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).Remove(Cost);
    Actor->Combat->CancelAction();
    World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatBTAbortTest,"Constellation.CombatCore.BehaviorTreeAbortAndDestroy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatBTAbortTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    World->CreateAISystem();
    Actor->DispatchBeginPlay();
    auto* AI=World->SpawnActor<AAIController>(); AI->Possess(Actor);
    auto* Tree=NewObject<UBehaviorTree>(AI);
    Tree->BlackboardAsset=NewObject<UBlackboardData>(Tree);
    auto* Root=NewObject<UBTComposite_Sequence>(Tree);
    auto* Task=NewObject<UBTTask_CombatAction>(Tree);
    Task->Action=CombatTest::Action(Actor); Task->PlayerRange=0;
    FBTCompositeChild Child; Child.ChildTask=Task; Root->Children.Add(Child); Tree->RootNode=Root;
    TestTrue(TEXT("Behavior tree starts"),AI->RunBehaviorTree(Tree));
    auto* Brain=Cast<UBehaviorTreeComponent>(AI->BrainComponent);
    if(!TestNotNull(TEXT("Behavior tree component"),Brain)) { World->DestroyWorld(false); return false; }
    for(int32 i=0;i<3;++i) Brain->TickComponent(.05f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("BT task waits while montage runs"),Actor->Combat->IsActing());
    Brain->StopTree(EBTStopMode::Safe);
    TestFalse(TEXT("BT abort cancels its montage"),Actor->Combat->IsActing());
    TestFalse(TEXT("BT is stopped"),Brain->IsRunning());
    TestTrue(TEXT("Tree restarts after abort"),AI->RunBehaviorTree(Tree));
    for(int32 i=0;i<3;++i) Brain->TickComponent(.05f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("BT is waiting again before destruction"),Actor->Combat->IsActing());
    int32 Ends=0;
    Actor->Combat->OnActionEnded.AddLambda([&](uint64,ECombatActionResult){++Ends;});
    Actor->Destroy();
    TestFalse(TEXT("Pawn destruction cancels active action"),Actor->Combat->IsActing());
    TestEqual(TEXT("Destruction ends exactly once"),Ends,1);
    World->DestroyWorld(false); return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatBufferedFollowUpTest,"Constellation.CombatCore.BufferedFollowUp",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatBufferedFollowUpTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->AttackInput->Initialize(Actor->Combat);
    auto* First=CombatTest::Action(Actor); auto* Next=CombatTest::Action(Actor);
    First->NextAction=Next;
    TestTrue(TEXT("First request starts action"),Actor->AttackInput->RequestAttack(First));
    auto* Anim=Actor->GetMesh()->GetAnimInstance();
    Anim->Montage_SetPosition(First->Montage,.49f);
    TestFalse(TEXT("Input before window rejected"),Actor->AttackInput->RequestAttack(First));
    Anim->Montage_SetPosition(First->Montage,.55f);
    TestTrue(TEXT("Input in window queued"),Actor->AttackInput->RequestAttack(First));
    TestTrue(TEXT("Repeated input shares one queue slot"),Actor->AttackInput->RequestAttack(First));
    Anim->Montage_SetPosition(First->Montage,.66f);
    TestFalse(TEXT("Input after window rejected"),Actor->AttackInput->RequestAttack(First));
    for(int32 i=0;i<40;++i) { Actor->GetMesh()->TickAnimation(.05f,false); Actor->GetMesh()->RefreshBoneTransforms(); Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents(); }
    TestTrue(TEXT("Extra press during handoff keeps queued action"),Actor->AttackInput->RequestAttack(First));
    World->GetTimerManager().Tick(.01f);
    TestTrue(TEXT("Next data-defined action starts"),Actor->Combat->GetActiveAction()==Next);
    TestEqual(TEXT("Only two execution costs charged"),Actor->Combat->GetStamina(),80.f);
    TestFalse(TEXT("Queue consumed"),Actor->AttackInput->HasBufferedAttack());
    Actor->Combat->CancelAction();
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatBufferedCancelTest,"Constellation.CombatCore.BufferedCancellationAndReplacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatBufferedCancelTest::RunTest(const FString&)
{
    for(int32 Mode=0;Mode<3;++Mode)
    {
        UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
        auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
        Actor->AttackInput->Initialize(Actor->Combat);
        auto* First=CombatTest::Action(Actor); auto* Next=CombatTest::Action(Actor); First->NextAction=Next;
        Actor->AttackInput->RequestAttack(First);
        Actor->GetMesh()->GetAnimInstance()->Montage_SetPosition(First->Montage,.55f);
        Actor->AttackInput->RequestAttack(First);
        if(Mode==0) Actor->Combat->CancelAction();
        if(Mode==1) Actor->Combat->ReceiveCombatDamage(100,Actor);
        UCombatActionDefinition* Replacement=nullptr;
        if(Mode==2)
        {
            for(int32 i=0;i<40;++i) { Actor->GetMesh()->TickAnimation(.05f,false); Actor->GetMesh()->RefreshBoneTransforms(); Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents(); }
            Replacement=CombatTest::Action(Actor); Actor->Combat->TryStartAction(Replacement);
        }
        World->GetTimerManager().Tick(.01f);
        TestFalse(TEXT("Stale queue cleared"),Actor->AttackInput->HasBufferedAttack());
        TestTrue(TEXT("No stale next action after cancellation, death or replacement"),
            Actor->Combat->GetActiveAction()==Replacement);
        Actor->Combat->CancelAction(); World->DestroyWorld(false);
    }
    return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatBufferedLimitsTest,"Constellation.CombatCore.BufferedResourceAndValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatBufferedLimitsTest::RunTest(const FString&)
{
    for(int32 Mode=0;Mode<3;++Mode)
    {
        UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
        auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
        Actor->AttackInput->Initialize(Actor->Combat);
        auto* First=CombatTest::Action(Actor); auto* Next=CombatTest::Action(Actor); First->NextAction=Next;
        FString Reason;
        First->InputWindowEnd=2.f;
        TestFalse(TEXT("Window outside montage rejected"),First->Validate(Reason));
        First->InputWindowEnd=.65f; First->InputWindowStart=.8f;
        TestFalse(TEXT("Reversed window rejected"),First->Validate(Reason));
        First->InputWindowStart=.5f;
        if(Mode==0) Next->StaminaCost=101.f;
        if(Mode==2)
        {
            Next->Cooldown=60.f;
            Actor->Combat->TryStartAction(Next); Actor->Combat->CancelAction();
        }
        Actor->AttackInput->RequestAttack(First);
        Actor->GetMesh()->GetAnimInstance()->Montage_SetPosition(First->Montage,.55f);
        TestTrue(TEXT("Input accepted before execution resource check"),Actor->AttackInput->RequestAttack(First));
        for(int32 i=0;i<40;++i) { Actor->GetMesh()->TickAnimation(.05f,false); Actor->GetMesh()->RefreshBoneTransforms(); Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents(); }
        if(Mode==1) Actor->AttackInput->Clear();
        World->GetTimerManager().Tick(.01f);
        TestFalse(TEXT("Unaffordable, cleared or cooling-down follow-up cannot start"),Actor->Combat->IsActing());
        TestFalse(TEXT("Failed follow-up leaves no stuck buffer"),Actor->AttackInput->HasBufferedAttack());
        TestEqual(TEXT("No follow-up cost on failure"),Actor->Combat->GetStamina(),Mode==2?80.f:90.f);
        World->DestroyWorld(false);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatStaminaRecoveryTest,"Constellation.CombatCore.StaminaRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatStaminaRecoveryTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->AttackInput->Initialize(Actor->Combat);
    auto* First=CombatTest::Action(Actor); First->StaminaCost=90;
    auto* Next=CombatTest::Action(Actor); First->NextAction=Next;
    auto Complete=[Actor]()
    {
        for(int32 i=0;i<40;++i) { Actor->GetMesh()->TickAnimation(.05f,false); Actor->GetMesh()->RefreshBoneTransforms(); Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents(); }
    };
    auto Tick=[Actor](float Delta) { Actor->Combat->TickComponent(Delta,LEVELTICK_All,nullptr); };
    TestTrue(TEXT("Initial attack starts"),Actor->AttackInput->RequestAttack(First));
    Actor->GetMesh()->GetAnimInstance()->Montage_SetPosition(First->Montage,.55f);
    TestTrue(TEXT("Follow-up queued"),Actor->AttackInput->RequestAttack(First));
    Complete(); World->GetTimerManager().Tick(.01f);
    TestEqual(TEXT("Buffered follow-up exhausts stamina"),Actor->Combat->GetStamina(),0.f);
    Tick(10.f);
    TestEqual(TEXT("No recovery during action"),Actor->Combat->GetStamina(),0.f);
    Complete();
    TestFalse(TEXT("Exhausted input rejected"),Actor->AttackInput->RequestAttack(Next));
    TestFalse(TEXT("No pending input lock"),Actor->AttackInput->HasBufferedAttack());
    Tick(.75f);
    TestEqual(TEXT("Recovery waits after completion"),Actor->Combat->GetStamina(),0.f);
    Tick(.5f);
    TestEqual(TEXT("Only time beyond delay recovers"),Actor->Combat->GetStamina(),5.f);
    Tick(.25f);
    TestTrue(TEXT("Attack works again after recovery"),Actor->AttackInput->RequestAttack(Next));
    Actor->Combat->CancelAction();
    Tick(1.f);
    TestEqual(TEXT("Cancellation also waits before recovery"),Actor->Combat->GetStamina(),0.f);
    Tick(.5f);
    TestEqual(TEXT("Cancelled action recovers"),Actor->Combat->GetStamina(),10.f);
    Tick(10.f);
    TestEqual(TEXT("Recovery clamps at maximum"),Actor->Combat->GetStamina(),100.f);
    Actor->AttackInput->RequestAttack(Next);
    Actor->Combat->ReceiveCombatDamage(100,Actor);
    const float DeadStamina=Actor->Combat->GetStamina();
    Tick(10.f);
    TestEqual(TEXT("Dead actors do not recover"),Actor->Combat->GetStamina(),DeadStamina);
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatHitReactionTest,"Constellation.CombatCore.HitReactionLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatHitReactionTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->AttackInput->Initialize(Actor->Combat);
    auto* First=CombatTest::Action(Actor); auto* Next=CombatTest::Action(Actor); First->NextAction=Next;
    TestTrue(TEXT("Attack starts"),Actor->AttackInput->RequestAttack(First));
    Actor->GetMesh()->GetAnimInstance()->Montage_SetPosition(First->Montage,.55f);
    Actor->AttackInput->RequestAttack(First);
    bool RestartedFromEnd=false;
    const auto Listener=Actor->Combat->OnActionEnded.AddLambda([&](uint64,ECombatActionResult)
    { RestartedFromEnd=Actor->Combat->TryStartAction(Next); });
    TestTrue(TEXT("Nonlethal hit accepted"),Actor->Combat->ReceiveCombatDamage(10,nullptr));
    Actor->Combat->OnActionEnded.Remove(Listener);
    TestFalse(TEXT("Hit interrupts active attack"),Actor->Combat->IsActing());
    TestFalse(TEXT("Hit clears buffered follow-up"),Actor->AttackInput->HasBufferedAttack());
    TestFalse(TEXT("End callback cannot bypass hit reaction"),RestartedFromEnd);
    TestFalse(TEXT("Attacks rejected during hit reaction"),Actor->AttackInput->RequestAttack(First));
    Actor->Combat->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Reaction still active before deadline"),Actor->AttackInput->RequestAttack(First));
    Actor->Combat->ReceiveCombatDamage(10,nullptr);
    Actor->Combat->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Another hit refreshes reaction"),Actor->AttackInput->RequestAttack(First));
    Actor->Combat->TickComponent(.16f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Attack resumes after reaction"),Actor->AttackInput->RequestAttack(First));
    Actor->Combat->CancelAction();
    Actor->Combat->ReceiveCombatDamage(100,nullptr);
    Actor->Combat->TickComponent(5.f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Reaction ending cannot revive dead actor"),Actor->AttackInput->RequestAttack(First));
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatHitHandoffTest,"Constellation.CombatCore.HitDuringHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatHitHandoffTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->AttackInput->Initialize(Actor->Combat);
    auto* First=CombatTest::Action(Actor); auto* Next=CombatTest::Action(Actor); First->NextAction=Next;
    Actor->AttackInput->RequestAttack(First);
    Actor->GetMesh()->GetAnimInstance()->Montage_SetPosition(First->Montage,.55f);
    Actor->AttackInput->RequestAttack(First);
    for(int32 i=0;i<40;++i) { Actor->GetMesh()->TickAnimation(.05f,false); Actor->GetMesh()->RefreshBoneTransforms(); Actor->GetMesh()->ConditionallyDispatchQueuedAnimEvents(); }
    TestTrue(TEXT("Follow-up is pending between actions"),Actor->AttackInput->HasBufferedAttack());
    Actor->Combat->ReceiveCombatDamage(10,nullptr);
    TestFalse(TEXT("Hit also clears idle handoff queue"),Actor->AttackInput->HasBufferedAttack());
    World->GetTimerManager().Tick(.01f);
    TestFalse(TEXT("No stale follow-up after hit"),Actor->Combat->IsActing());
    Actor->Combat->TickComponent(.35f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Stamina does not recover during hit reaction"),Actor->Combat->GetStamina(),90.f);
    Actor->Combat->TickComponent(.5f,LEVELTICK_All,nullptr);
    Actor->AttackInput->RequestAttack(Next); // May start now; cancel before checking recovery.
    Actor->Combat->CancelAction();
    Actor->Combat->TickComponent(1.5f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Recovery resumes after hit and action"),Actor->Combat->GetStamina(),90.f);
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeTest,"Constellation.CombatCore.DodgeLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(Actor);
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Ground dodge starts"),Actor->Combat->TryDodge(FVector::ForwardVector));
    TestEqual(TEXT("Dodge costs twenty"),Actor->Combat->GetStamina(),80.f);
    TestFalse(TEXT("Repeated dodge rejected"),Actor->Combat->TryDodge(FVector::ForwardVector));
    TestFalse(TEXT("Attack rejected during dodge"),Actor->Combat->TryStartAction(Action));
    TestFalse(TEXT("Startup is vulnerable"),Actor->Combat->IsInvulnerable());
    Actor->Combat->TickComponent(.15f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Middle of dodge is invulnerable"),Actor->Combat->IsInvulnerable());
    TestFalse(TEXT("Invulnerable damage rejected"),Actor->Combat->ReceiveCombatDamage(25,nullptr));
    TestEqual(TEXT("Invulnerability preserves health"),Actor->Combat->GetHealth(),100.f);
    TestTrue(TEXT("Avoided damage does not cancel dodge"),Actor->Combat->IsDodging());
    Actor->Combat->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Recovery phase is vulnerable"),Actor->Combat->IsInvulnerable());
    TestTrue(TEXT("Recovery hit accepted"),Actor->Combat->ReceiveCombatDamage(10,nullptr));
    TestFalse(TEXT("Hit cancels dodge"),Actor->Combat->IsDodging());
    Actor->Combat->TickComponent(.36f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Dodge possible after hit recovery"),Actor->Combat->TryDodge(FVector::RightVector));
    Actor->Combat->TickComponent(.61f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Dodge finishes"),Actor->Combat->IsDodging());
    TestTrue(TEXT("Attack resumes"),Actor->Combat->TryStartAction(Action));
    Actor->Combat->CancelAction();
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeRestrictionsTest,"Constellation.CombatCore.DodgeRestrictions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeRestrictionsTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),19.f);
    TestFalse(TEXT("Insufficient stamina blocks dodge"),Actor->Combat->TryDodge(FVector::ForwardVector));
    TestEqual(TEXT("Rejected dodge has no cost"),Actor->Combat->GetStamina(),19.f);
    Actor->Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),100.f);
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    TestFalse(TEXT("Cannot initiate airborne dodge"),Actor->Combat->TryDodge(FVector::ForwardVector));
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    Actor->Combat->DodgeDuration=0;
    TestFalse(TEXT("Invalid duration rejected"),Actor->Combat->TryDodge(FVector::ForwardVector));
    Actor->Combat->DodgeDuration=.6f;
    auto* Action=CombatTest::Action(Actor);
    Actor->Combat->TryStartAction(Action);
    TestFalse(TEXT("Cannot bypass active attack with dodge"),Actor->Combat->TryDodge(FVector::ForwardVector));
    Actor->Combat->CancelAction();
    TestTrue(TEXT("No direction falls back to facing"),Actor->Combat->TryDodge(FVector::ZeroVector));
    Actor->Combat->DodgeDuration=10; // Runtime editing cannot extend an active dodge.
    Actor->Combat->TickComponent(.61f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Active duration is snapshotted"),Actor->Combat->IsDodging());
    Actor->Combat->DodgeDuration=.6f;
    Actor->Combat->TryDodge(FVector::ForwardVector);
    Actor->Combat->TickComponent(.15f,LEVELTICK_All,nullptr);
    Actor->Combat->CancelAction();
    TestFalse(TEXT("Cancellation removes invulnerability"),Actor->Combat->IsInvulnerable());
    TestTrue(TEXT("Damage after cancel accepted"),Actor->Combat->ReceiveCombatDamage(10,nullptr));
    Actor->Combat->TickComponent(.36f,LEVELTICK_All,nullptr);
    Actor->Combat->TryDodge(FVector::ForwardVector);
    Actor->Combat->ReceiveCombatDamage(100,nullptr);
    TestFalse(TEXT("Lethal startup hit stops dodge"),Actor->Combat->IsDodging());
    TestFalse(TEXT("Dead actor cannot dodge"),Actor->Combat->TryDodge(FVector::ForwardVector));
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeReentrantTest,"Constellation.CombatCore.DodgeReentrantStart",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeReentrantTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    Actor->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    Actor->Combat->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),20.f);
    auto* Action=CombatTest::Action(Actor); Action->StaminaCost=0;
    bool NestedDodge=false,NestedAttack=false,Entered=false;
    const auto Handle=Actor->Combat->OnDodgeStarted.AddLambda([&]()
    {
        if(Entered) return;
        Entered=true;
        Actor->Combat->CancelDodge();
        NestedDodge=Actor->Combat->TryDodge(FVector::ForwardVector);
        NestedAttack=Actor->Combat->TryStartAction(Action);
        Actor->Combat->DodgeStaminaCost=1; // Must not alter the already accepted cost.
    });
    TestFalse(TEXT("Cancelled start does not report active dodge"),Actor->Combat->TryDodge(FVector::ForwardVector));
    TestFalse(TEXT("Start callback cannot reuse uncommitted stamina"),NestedDodge);
    TestFalse(TEXT("Start callback cannot replace transaction with attack"),NestedAttack);
    TestEqual(TEXT("Accepted cost snapshot paid exactly once"),Actor->Combat->GetStamina(),0.f);
    TestFalse(TEXT("No movement left after cancelled start"),Actor->Combat->IsDodging());
    Actor->Combat->OnDodgeStarted.Remove(Handle);
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatPatternTest,"Constellation.CombatCore.PatternSelection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatPatternTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Profile=NewObject<UCombatPatternProfile>();
    FCombatPatternEntry Light; Light.Id="Light"; Light.Action=CombatTest::Action(Actor); Light.Weight=3; Light.MaxConsecutive=2;
    FCombatPatternEntry Heavy; Heavy.Id="Heavy"; Heavy.Action=CombatTest::Action(Actor); Heavy.Weight=1; Heavy.MaxDistance=150;
    Profile->Patterns={Light,Heavy};
    FString Reason;
    TestEqual(TEXT("Low roll selects weighted light"),Profile->Select(Actor->Combat,100,0,true,NAME_None,0,0.f,Reason),0);
    TestEqual(TEXT("High roll selects weighted heavy"),Profile->Select(Actor->Combat,100,0,true,NAME_None,0,.99f,Reason),1);
    TestEqual(TEXT("Out of range has no candidate"),Profile->Select(Actor->Combat,300,0,true,NAME_None,0,0.f,Reason),INDEX_NONE);
    TestEqual(TEXT("Wall excludes sight-requiring patterns"),Profile->Select(Actor->Combat,100,0,false,NAME_None,0,0.f,Reason),INDEX_NONE);
    TestTrue(TEXT("Sight rejection explained"),Reason.Contains(TEXT("Sight")));
    TestEqual(TEXT("Outside facing cone excluded"),Profile->Select(Actor->Combat,100,120,true,NAME_None,0,0.f,Reason),INDEX_NONE);
    TestEqual(TEXT("Consecutive limit forces other candidate"),Profile->Select(Actor->Combat,100,0,true,"Light",2,0.f,Reason),1);
    Profile->Patterns[0].Action->Cooldown=5;
    Actor->Combat->TryStartAction(Profile->Patterns[0].Action); Actor->Combat->CancelAction();
    TestEqual(TEXT("Cooldown is checked through combat system"),Profile->Select(Actor->Combat,100,0,true,NAME_None,0,0.f,Reason),1);
    Profile->Patterns[1].Action->StaminaCost=101;
    TestEqual(TEXT("No affordable ready candidate"),Profile->Select(Actor->Combat,100,0,true,NAME_None,0,0.f,Reason),INDEX_NONE);
    Profile->Patterns[1].Id="Light";
    TestFalse(TEXT("Duplicate pattern IDs are invalid"),Profile->Validate(Reason));
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatPatternInterruptedTest,"Constellation.CombatCore.PatternCommittedInterruption",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatPatternInterruptedTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false); World->CreateAISystem();
    auto* Actor=CombatTest::Actor(World,FVector(0,0,100),0); Actor->DispatchBeginPlay();
    auto* Player=CombatTest::Actor(World,FVector(125,0,100),1);
    auto* PC=World->SpawnActor<APlayerController>(); PC->SetAsLocalPlayerController(); World->AddController(PC); PC->Possess(Player);
    Player->Combat->TeamId=1; Actor->Combat->TeamId=0;
    auto* AI=World->SpawnActor<AAIController>(); AI->Possess(Actor);
    TestTrue(TEXT("Fixture player registered"),UGameplayStatics::GetPlayerPawn(Actor,0)==Player);
    auto* Profile=NewObject<UCombatPatternProfile>();
    FCombatPatternEntry Entry; Entry.Id="Only"; Entry.Action=CombatTest::Action(Actor); Entry.MaxConsecutive=1;
    Profile->Patterns={Entry};
    auto* Tree=NewObject<UBehaviorTree>(AI); Tree->BlackboardAsset=NewObject<UBlackboardData>(Tree);
    auto* Root=NewObject<UBTComposite_Sequence>(Tree); auto* Task=NewObject<UBTTask_CombatAction>(Tree); Task->PatternProfile=Profile;
    FBTCompositeChild Child; Child.ChildTask=Task; Root->Children.Add(Child); Tree->RootNode=Root;
    const auto Handle=Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).AddLambda([Actor](const FOnAttributeChangeData& Change)
    { if(Change.NewValue<Change.OldValue) Actor->Combat->CancelAllAbilities(); });
    AI->RunBehaviorTree(Tree);
    auto* Brain=Cast<UBehaviorTreeComponent>(AI->BrainComponent);
    if(TestNotNull(TEXT("Pattern brain exists"),Brain))
    {
        for(int32 i=0;i<4;++i) Brain->TickComponent(.05f,LEVELTICK_All,nullptr);
        AddInfo(Actor->Combat->LastPatternDecision);
        TestEqual(TEXT("Committed interruption consumes repeat budget"),Actor->Combat->GetExecutionId(),uint64(1));
        TestEqual(TEXT("Only one committed cost"),Actor->Combat->GetStamina(),90.f);
        TestTrue(TEXT("Repeat rejection is visible"),Actor->Combat->LastPatternDecision.Contains(TEXT("Repeat limit")));
        Brain->StopTree(EBTStopMode::Safe);
    }
    Actor->Combat->GetGameplayAttributeValueChangeDelegate(UCombatAttributes::GetStaminaAttribute()).Remove(Handle);
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatEncounterTest,"Constellation.CombatCore.EncounterLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatEncounterTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false); World->CreateAISystem();
    auto* Enemy=CombatTest::Actor(World,FVector(0,0,100),1);
    auto* Player=CombatTest::Actor(World,FVector(125,0,100),0);
    auto* PC=World->SpawnActor<APlayerController>(); PC->SetAsLocalPlayerController(); World->AddController(PC); PC->Possess(Player);
    auto* AI=World->SpawnActor<AAIController>(); AI->Possess(Enemy);
    Enemy->Combat->TeamId=1; Player->Combat->TeamId=0;
    auto* Profile=NewObject<UCombatEncounterProfile>();
    auto* Agent=NewObject<UCombatEnemyAgent>(Enemy); Agent->RegisterComponent(); Agent->Initialize(Profile);
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Visible nearby target enables attack"),Agent->CanAttack());
    auto* Action=CombatTest::Action(Enemy); Enemy->Combat->TryStartAction(Action);
    Player->Combat->ReceiveCombatDamage(100,nullptr);
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Target death cancels current attack"),Enemy->Combat->IsActing());
    TestFalse(TEXT("Returning does not attack"),Agent->CanAttack());
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Return at home restores spent stamina"),Enemy->Combat->GetStamina(),100.f);
    TestEqual(TEXT("Completed return advances encounter epoch"),Agent->GetEncounterEpoch(),uint64(1));
    Enemy->Combat->ReceiveCombatDamage(100,nullptr);
    Agent->TickComponent(5.f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Dead enemy stays dead"),Enemy->Combat->GetHealth(),0.f);
    TestTrue(TEXT("Death has final priority"),Agent->State==ECombatEnemyState::Dead);
    World->DestroyWorld(false); return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatEncounterLossTest,"Constellation.CombatCore.EncounterSightAndNavigationFailure",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatEncounterLossTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false); World->CreateAISystem();
    auto* Enemy=CombatTest::Actor(World,FVector(0,0,100),1);
    auto* Player=CombatTest::Actor(World,FVector(125,0,100),0);
    auto* PC=World->SpawnActor<APlayerController>(); PC->SetAsLocalPlayerController(); World->AddController(PC); PC->Possess(Player);
    auto* AI=World->SpawnActor<AAIController>(); AI->Possess(Enemy); Enemy->Combat->TeamId=1; Player->Combat->TeamId=0;
    auto* Profile=NewObject<UCombatEncounterProfile>(); Profile->LostSightTime=.3f; Profile->MaxMoveFailures=2; Profile->RetryDelay=.1f;
    auto* Agent=NewObject<UCombatEnemyAgent>(Enemy); Agent->RegisterComponent(); Agent->Initialize(Profile);
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    auto* Wall=World->SpawnActor<AActor>(); auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(5,100,100)); Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly); Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent(); Wall->SetActorLocation(FVector(60,0,100));
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Lost sight searches last position"),Agent->State==ECombatEnemyState::Searching);
    TestFalse(TEXT("Cannot attack through lost sight"),Agent->CanAttack());
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Sight timeout returns home"),Agent->State==ECombatEnemyState::Returning);
    TestTrue(TEXT("Sight timeout reason recorded"),Agent->Decision.Contains(TEXT("Sight timeout")));
    Wall->Destroy(); Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    Player->SetActorLocation(FVector(300,0,100));
    Agent->TickComponent(4.f,LEVELTICK_All,nullptr);
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    AddInfo(FString::Printf(TEXT("Navigation fixture state=%d decision=%s"),int32(Agent->State),*Agent->Decision));
    TestTrue(TEXT("Missing navigation exhausts bounded chase retries"),Agent->State==ECombatEnemyState::Returning);
    TestTrue(TEXT("Navigation failure reason recorded"),Agent->Decision.Contains(TEXT("navigation failed")));
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    Agent->TickComponent(.2f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Cooldown prevents immediate reacquisition loop"),Agent->State==ECombatEnemyState::Idle);
    Profile->LoseRadius=1; FString Reason;
    TestFalse(TEXT("Invalid acquisition ranges rejected"),Profile->Validate(Reason));
    World->DestroyWorld(false); return true;
}
#endif



























#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatObservationTest,"Constellation.CombatCore.ActionObservation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatObservationTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(W,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(A);
    Action->NextAction=CombatTest::Action(A); Action->Cooldown=2.f;
    if(!TestTrue(TEXT("Start real montage"),A->Combat->TryStartAction(Action))) {W->DestroyWorld(false);return false;}
    auto* Instance=A->GetMesh()->GetAnimInstance()->GetActiveInstanceForMontage(Action->Montage);
    if(!Instance) {W->DestroyWorld(false);return false;}
    Instance->SetPosition(.2f);
    TestEqual(TEXT("Before first notify is preparation"),A->Combat->ObserveAction().Phase,FString(TEXT("공격 준비")));
    TestFalse(TEXT("Input window not yet open"),A->Combat->ObserveAction().bInputOpen);
    Instance->SetPosition(.4f);
    TestFalse(TEXT("Timeline alone cannot claim active hit"),A->Combat->ObserveAction().bHitOpen);
    A->Combat->OpenHitWindow(TEXT("Swing"),Instance->GetInstanceID());
    TestTrue(TEXT("Actual ledger opens observed hit"),A->Combat->ObserveAction().bHitOpen);
    TestEqual(TEXT("Hit phase"),A->Combat->ObserveAction().Phase,FString(TEXT("타격 판정 중")));
    A->Combat->CloseHitWindow(TEXT("Swing"),Instance->GetInstanceID());
    Instance->SetPosition(.6f);
    TestEqual(TEXT("After final hit is recovery"),A->Combat->ObserveAction().Phase,FString(TEXT("공격 회수")));
    TestTrue(TEXT("Followup interval shown accurately"),A->Combat->ObserveAction().bInputOpen);
    Instance->SetPosition(.8f);
    TestFalse(TEXT("Outside followup interval"),A->Combat->ObserveAction().bInputOpen);
    TestTrue(TEXT("Cooldown reports remaining time"),A->Combat->GetCooldownRemaining(Action)>1.9f);
    const float SP=A->Combat->GetStamina();
    for(int I=0;I<10;++I) A->Combat->ObserveAction();
    TestEqual(TEXT("Observing does not consume resource"),A->Combat->GetStamina(),SP);
    A->Combat->CancelAction();
    TestFalse(TEXT("Cancel clears live action observation"),A->Combat->ObserveAction().bActive);
    TestFalse(TEXT("Cancel clears hit observation"),A->Combat->ObserveAction().bHitOpen);
    W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamageHistoryTest,"Constellation.CombatCore.DamageObservation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDamageHistoryTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(W,FVector(0,0,100),0);auto* C=A->Combat.Get();
    for(int I=0;I<20;++I) C->ReceiveCombatDamage(1,nullptr);
    TestEqual(TEXT("History bounded"),C->GetDamageHistory().Num(),12);
    TestEqual(TEXT("Actual HP captured"),C->GetDamageHistory().Last().HealthAfter,80.f);
    TestEqual(TEXT("Actual damage captured"),C->GetDamageHistory().Last().Damage,1.f);
    C->ReceiveCombatDamage(-1,nullptr);
    TestEqual(TEXT("Invalid damage does not add record"),C->GetDamageHistory().Last().HealthAfter,80.f);
    C->TickComponent(1.f,LEVELTICK_All,nullptr);
    C->DodgeInvulnerableStart=0;
    A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Start invulnerable dodge"),C->TryDodge(FVector::ForwardVector));
    TestFalse(TEXT("Invulnerable damage rejected"),C->ReceiveCombatDamage(10,nullptr));
    TestTrue(TEXT("Avoidance recorded"),C->GetDamageHistory().Last().bAvoided);
    TestEqual(TEXT("Avoided damage is zero"),C->GetDamageHistory().Last().Damage,0.f);
    C->CancelDodge(); C->ReceiveCombatDamage(1000,nullptr);
    TestEqual(TEXT("Overkill record clamps to actual damage"),C->GetDamageHistory().Last().Damage,80.f);
    TestEqual(TEXT("Death observed"),C->ObserveAction().Phase,FString(TEXT("사망")));
    TestEqual(TEXT("Known input reason translated"),CombatObservation::ExplainReason(TEXT("Not enough stamina")),FString(TEXT("SP 부족")));
    TestEqual(TEXT("Unknown diagnostic preserved"),CombatObservation::ExplainReason(TEXT("custom detail")),FString(TEXT("custom detail")));
    W->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeCancelWindowTest,"Constellation.CombatCore.DodgeCancelWindow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeCancelWindowTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* A=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* C=A->Combat.Get();A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    auto* Action=CombatTest::Action(A);Action->NextAction=CombatTest::Action(A);
    A->AttackInput->Initialize(C);
    TestTrue(TEXT("Attack starts"),C->TryStartAction(Action));
    auto Position=[&](float T){A->GetMesh()->GetAnimInstance()->Montage_SetPosition(Action->Montage,T);};
    Position(.55f);
    TestFalse(TEXT("Disabled cancel preserves old rules"),C->TryDodge(FVector::ForwardVector));
    Action->bAllowDodgeCancel=true;
    Position(.49f);TestFalse(TEXT("Before cancel window rejected"),C->TryDodge(FVector::ForwardVector));
    Position(.7f);TestFalse(TEXT("End is exclusive"),C->TryDodge(FVector::ForwardVector));
    Position(.55f);
    C->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),19);
    TestFalse(TEXT("Low SP does not cancel attack"),C->TryDodge(FVector::ForwardVector));
    TestTrue(TEXT("Rejected dodge preserves attack"),C->IsActing());
    C->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),20);
    A->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    TestFalse(TEXT("Airborne does not cancel attack"),C->TryDodge(FVector::ForwardVector));
    TestTrue(TEXT("Ground rejection preserves attack"),C->IsActing());
    A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Follow-up queued before cancel"),A->AttackInput->RequestAttack(Action));
    const int32 Instance=CombatTest::Instance(A,Action);
    C->OpenHitWindow(TEXT("CancelTest"),Instance);
    int32 Cancelled=0;
    C->OnActionEnded.AddLambda([&](uint64,ECombatActionResult R){if(R==ECombatActionResult::Cancelled) ++Cancelled;});
    Position(.5f);
    TestTrue(TEXT("Window start permits transition"),C->TryDodge(FVector::ForwardVector));
    TestFalse(TEXT("Attack ends"),C->IsActing());
    TestTrue(TEXT("Dodge begins"),C->IsDodging());
    TestEqual(TEXT("Dodge costs exactly once"),C->GetStamina(),0.f);
    TestEqual(TEXT("Attack cancelled exactly once"),Cancelled,1);
    TestFalse(TEXT("Buffered combo cleared"),A->AttackInput->HasBufferedAttack());
    auto* Victim=CombatTest::Actor(World,FVector(100,0,100),1);
    TestFalse(TEXT("Old hit window cannot deal damage"),C->ApplyHit(TEXT("CancelTest"),Victim));
    C->OnActionEnded.Clear();
    World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDodgeCancelReentryTest,"Constellation.CombatCore.DodgeCancelReentry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDodgeCancelReentryTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    for(bool Kill:{false,true})
    {
        auto* A=CombatTest::Actor(World,FVector(0,0,100),0);auto* C=A->Combat.Get();
        A->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        auto* Action=CombatTest::Action(A);Action->bAllowDodgeCancel=true;Action->StaminaCost=0;
        TestTrue(TEXT("Attack starts"),C->TryStartAction(Action));
        A->GetMesh()->GetAnimInstance()->Montage_SetPosition(Action->Montage,.55f);
        C->SetNumericAttributeBase(UCombatAttributes::GetStaminaAttribute(),20);
        bool NestedAttack=false,NestedDodge=false,Entered=false;
        C->OnActionEnded.AddLambda([&](uint64,ECombatActionResult){
            Entered=true;NestedAttack=C->TryStartAction(Action);NestedDodge=C->TryDodge(FVector::ForwardVector);
            C->DodgeStaminaCost=1;
            if(Kill) C->ReceiveCombatDamage(1000,nullptr);
        });
        TestEqual(TEXT("Death during cancel aborts transition"),C->TryDodge(FVector::ForwardVector),!Kill);
        TestTrue(TEXT("Cancellation callback ran"),Entered);
        TestFalse(TEXT("Cannot replace attack during transition"),NestedAttack);
        TestFalse(TEXT("Cannot nest dodge during transition"),NestedDodge);
        TestEqual(TEXT("Accepted cost snapshot or no charge after death"),C->GetStamina(),Kill?20.f:0.f);
        TestEqual(TEXT("No dodge after death"),C->IsDodging(),!Kill);
        C->OnActionEnded.Clear();
    }
    World->DestroyWorld(false);return true;
}

// Removing the accepted-hit broadcast or allowing duplicate contacts breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatConfirmedContextTest,"Constellation.CombatVFX.ConfirmedHitContext",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatConfirmedContextTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Target=CombatTest::Actor(World,FVector(1000,0,100),1);
    auto* Action=CombatTest::Action(Source);
    Action->Damage=200.f;
    int32 Count=0;
    FCombatConfirmedHit Observed;
    Source->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit& Hit){++Count;Observed=Hit;});
    TestTrue(TEXT("Action starts"),Source->Combat->TryStartAction(Action));
    const uint64 Execution=Source->Combat->GetExecutionId();
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestEqual(TEXT("Miss emits no impact"),Count,0);
    // Lethal target callbacks are allowed to cancel the attack synchronously.
    Target->Combat->OnDied.AddLambda([&](){Source->Combat->CancelAction();});
    TestTrue(TEXT("Confirmed lethal damage accepted"),Source->Combat->ApplyHit("Swing",Target,FVector(958,3,90),FVector(-1,0,0)));
    TestEqual(TEXT("One presentation event after accepted damage"),Count,1);
    TestTrue(TEXT("Payload retains source through cancellation"),Observed.Source.Get()==Source);
    TestTrue(TEXT("Payload identifies damaged target"),Observed.Target.Get()==Target);
    TestEqual(TEXT("Payload retains original execution"),Observed.ExecutionId,Execution);
    TestEqual(TEXT("Payload retains original window"),Observed.Window,FName("Swing"));
    TestEqual(TEXT("Payload preserves contact point"),Observed.Position,FVector(958,3,90));
    TestEqual(TEXT("Payload preserves contact normal"),Observed.Normal,FVector(-1,0,0));
    TestEqual(TEXT("Overkill presentation reports applied damage"),Observed.AppliedDamage,100.f);
    TestFalse(TEXT("Late contact cannot hit after cancellation"),Source->Combat->ApplyHit("Swing",Target));
    TestEqual(TEXT("No repeated event after death"),Count,1);
    TestEqual(TEXT("No duplicate damage"),Target->Combat->GetHealth(),0.f);
    World->DestroyWorld(false);return true;
}

// Broadcasting on a rejected or repeated ledger contact breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatConfirmedRejectTest,"Constellation.CombatVFX.RejectedAndRepeatedHits",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatConfirmedRejectTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Target=CombatTest::Actor(World,FVector(1000,0,100),1);
    auto* Action=CombatTest::Action(Source);
    int32 Count=0;
    Source->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit&){++Count;});
    Target->Combat->DodgeInvulnerableStart=0.f;
    Target->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    TestTrue(TEXT("Target enters invulnerable dodge"),Target->Combat->TryDodge(FVector(1,0,0)));
    TestTrue(TEXT("Source starts attack"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestFalse(TEXT("Invulnerable contact rejects damage"),Source->Combat->ApplyHit("Swing",Target));
    TestEqual(TEXT("Invulnerability emits no impact"),Count,0);
    TestEqual(TEXT("Invulnerability preserves health"),Target->Combat->GetHealth(),100.f);
    Target->Combat->CancelDodge();
    TestFalse(TEXT("Avoided contact is still claimed once per window"),Source->Combat->ApplyHit("Swing",Target));
    Source->Combat->CancelAction();
    TestTrue(TEXT("Next attack starts"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestTrue(TEXT("New execution accepts first contact"),Source->Combat->ApplyHit("Swing",Target));
    TestFalse(TEXT("Same execution suppresses second contact"),Source->Combat->ApplyHit("Swing",Target));
    TestEqual(TEXT("Only accepted first contact emits impact"),Count,1);
    TestEqual(TEXT("Health charged once"),Target->Combat->GetHealth(),80.f);
    Source->Combat->CancelAction();
    World->DestroyWorld(false);return true;
}

// Missing cancellation cleanup or accepting stale montage windows breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatPresentationWindowTest,"Constellation.CombatVFX.WindowCancellation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatPresentationWindowTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Action=CombatTest::Action(Source);
    int32 Opens=0,Closes=0;
    Source->Combat->OnHitWindowOpened.AddLambda([&](uint64,FName){++Opens;});
    Source->Combat->OnHitWindowClosed.AddLambda([&](uint64,FName){++Closes;});
    TestTrue(TEXT("Action starts"),Source->Combat->TryStartAction(Action));
    const int32 Old=CombatTest::Instance(Source,Action);
    Source->Combat->OpenHitWindow("Swing",Old);
    Source->Combat->OpenHitWindow("Swing",Old);
    TestEqual(TEXT("Repeated begin owns one presentation"),Opens,1);
    Source->Combat->CancelAction();
    TestEqual(TEXT("Cancellation closes presentation immediately"),Closes,1);
    Source->Combat->CloseHitWindow("Swing",Old);
    TestEqual(TEXT("Late notify cannot close twice"),Closes,1);
    TestTrue(TEXT("Attack restarts"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",Old);
    TestEqual(TEXT("Stale montage cannot start presentation"),Opens,1);
    const int32 Current=CombatTest::Instance(Source,Action);
    Source->Combat->OpenHitWindow("Swing",Current);
    Source->Combat->CloseHitWindow("Swing",Current);
    TestEqual(TEXT("New attack owns a new presentation"),Opens,2);
    TestEqual(TEXT("Actual window end stops presentation"),Closes,2);
    Source->Combat->CancelAction();
    TestEqual(TEXT("Closed window is not closed again on cancel"),Closes,2);
    World->DestroyWorld(false);return true;
}

// Leaving an attack actor alive on cancellation/death/restart breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXCleanupTest,"Constellation.CombatVFX.EffectCleanup",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXCleanupTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    Source->CombatVFX->Style=ECombatVFXStyle::Slime;
    Source->CombatVFX->SetPresentationEnabled(true);
    Source->CombatVFX->Initialize(Source->Combat);
    auto* Action=CombatTest::Action(Source);
    TestTrue(TEXT("Attack starts"),Source->Combat->TryStartAction(Action));
    TestFalse(TEXT("Windup has no active attack effect"),Source->CombatVFX->HasAttackPresentation());
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestTrue(TEXT("Actual window begins slime attack effect"),Source->CombatVFX->HasAttackPresentation());
    Source->Combat->CancelAction();
    TestFalse(TEXT("Cancellation removes attack immediately"),Source->CombatVFX->HasAttackPresentation());
    TestTrue(TEXT("Attack can restart"),Source->Combat->TryStartAction(Action));
    const int32 Id=CombatTest::Instance(Source,Action);
    Source->Combat->OpenHitWindow("Swing",Id);
    TestTrue(TEXT("Restart creates new attack effect"),Source->CombatVFX->HasAttackPresentation());
    Source->Combat->CloseHitWindow("Swing",Id);
    TestFalse(TEXT("Natural hit window end removes attack"),Source->CombatVFX->HasAttackPresentation());
    Source->Combat->CancelAction();
    Source->Combat->TryStartAction(Action);
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    Source->Combat->ReceiveCombatDamage(100.f,Source);
    TestFalse(TEXT("Death cleans presentation"),Source->CombatVFX->HasAttackPresentation());
    int32 Left=0;
    for(TActorIterator<AConstellationFXActor> It(World);It;++It)
        if(It->GetOwner()==Source && !It->IsActorBeingDestroyed()) ++Left;
    TestEqual(TEXT("No owned effects remain after death"),Left,0);
    World->DestroyWorld(false);return true;
}

// Airborne, stationary, or water steps becoming dry dust breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXFeetTest,"Constellation.CombatVFX.GroundedSurfaceFootsteps",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXFeetTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    Source->CombatVFX->Style=ECombatVFXStyle::Sword;
    Source->CombatVFX->SetPresentationEnabled(true);Source->CombatVFX->Initialize(Source->Combat);
    Source->CombatVFX->FootstepDistance=100.f;
    AActor* Floor=World->SpawnActor<AActor>();
    auto* Box=NewObject<UBoxComponent>(Floor); Floor->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(500,500,10)); Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionResponseToAllChannels(ECR_Block); Box->RegisterComponent();
    Floor->SetActorLocation(FVector(0,0,-6));
    auto Count=[&](EConstellationFXKind Kind)
    { int32 N=0;for(TActorIterator<AConstellationFXActor> It(World);It;++It)if(It->EffectKind==Kind && !It->IsActorBeingDestroyed())++N;return N; };
    auto* Move=Source->GetCharacterMovement();
    Move->SetMovementMode(MOVE_Walking);Move->Velocity=FVector::ZeroVector;
    Source->CombatVFX->TickComponent(.25f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Stationary produces no dust"),Count(EConstellationFXKind::RunDust),0);
    Move->SetMovementMode(MOVE_Falling);Move->Velocity=FVector(500,0,0);
    Source->CombatVFX->TickComponent(.25f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Airborne produces no dust"),Count(EConstellationFXKind::RunDust),0);
    Move->SetMovementMode(MOVE_Walking);Move->Velocity=FVector(500,0,0);
    Source->CombatVFX->TickComponent(.25f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Grounded dry step produces one puff"),Count(EConstellationFXKind::RunDust),1);
    Source->CombatVFX->StopPresentation();Box->ComponentTags.Add(TEXT("FXWater"));
    Source->CombatVFX->TickComponent(.25f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Water suppresses dry dust"),Count(EConstellationFXKind::RunDust),0);
    TestEqual(TEXT("Water creates ripple"),Count(EConstellationFXKind::WaterRipple),1);
    Source->CombatVFX->StopPresentation();Box->ComponentTags.Reset();Box->ComponentTags.Add(TEXT("FXNoDust"));
    Source->CombatVFX->TickComponent(.25f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("No-dust surface suppresses puff"),Count(EConstellationFXKind::RunDust),0);
    World->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatTrailAuditTest,"Constellation.CombatVFX.AuthoredTrailAudit",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatTrailAuditTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/Constellation/VFX/NS_SwordTrail.NS_SwordTrail"));
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview"));
    if(!TestNotNull(TEXT("Authored sword trail"),System) || !TestNotNull(TEXT("Heroine mesh"),Mesh)) return false;
    TArray<FNiagaraVariable> Parameters;System->GetExposedParameters().GetUserParameters(Parameters);
    FString Report;
    for(const auto& Parameter:Parameters)
    { Report+=Parameter.GetName().ToString()+TEXT(":")+Parameter.GetType().GetName()+TEXT("\n"); }
    Report+=FString::Printf(TEXT("WeaponSocket=%s\n"),Mesh->FindSocket(TEXT("WeaponSocket"))?TEXT("true"):TEXT("false"));
    FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectSavedDir()/TEXT("VFXImplementation/trail-native-audit.txt")));
    AddInfo(Report);return true;
}

// Incorrect grip scale/origin or detaching the weapon from the moving hand breaks this test.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXSwordGripTest,"Constellation.CombatVFX.RefinedPreviewSwordGrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXSwordGripTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    Source->CombatVFX->SetPresentationEnabled(true);Source->CombatVFX->Initialize(Source->Combat);
    if (!TestNotNull(TEXT("Reference sword is equipped on refined preview"),Source->Sword->GetStaticMesh().Get()))
    {World->DestroyWorld(false);return false;}
    TestEqual(TEXT("Vetted preview sword uses half scale"),Source->Sword->GetComponentScale().X,.5);
    const FVector Grip=Source->Sword->GetComponentTransform().TransformPosition(FVector(0,0,65));
    const FVector Fingers=(Source->GetMesh()->GetBoneLocation(TEXT("middle_02_r"))+Source->GetMesh()->GetBoneLocation(TEXT("ring_02_r")))*.5f;
    TestTrue(TEXT("Sword handle rests within 2cm of gripping fingers"),FVector::Dist(Grip,Fingers)<2.f);
    const FVector Before=Source->Sword->GetComponentLocation();
    Source->SetActorLocation(Source->GetActorLocation()+FVector(100,0,0));
    TestTrue(TEXT("Attached sword follows character movement"),Source->Sword->GetComponentLocation().Equals(Before+FVector(100,0,0),.01f));
    // Exercise the bounded native accent when an authored Niagara system is unavailable.
    Source->CombatVFX->SwordTrail.Reset();
    auto* Action=CombatTest::Action(Source);
    TestTrue(TEXT("Ribbon attack starts"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    const FVector InitialTip=Source->Sword->GetComponentTransform().TransformPosition(FVector(0,0,-95));
    for(int32 Sample=0;Sample<80;++Sample)
    {
        Source->Sword->AddLocalRotation(FRotator(10,0,0));
        Source->CombatVFX->TickComponent(.01f,LEVELTICK_All,nullptr);
    }
    const FVector FinalTip=Source->Sword->GetComponentTransform().TransformPosition(FVector(0,0,-95));
    TestTrue(TEXT("Fixture actually swings the blade tip"),FVector::DistSquared(InitialTip,FinalTip)>1.f);
    TestTrue(TEXT("Weapon motion emits visible native ribbon segments"),Source->CombatVFX->GetWeaponRibbonSegments()>0);
    TestTrue(TEXT("Repeated motion remains bounded to 16 segments"),Source->CombatVFX->GetWeaponRibbonSegments()<=16);
    Source->Combat->CancelAction();
    TestEqual(TEXT("Cancellation removes native ribbon samples"),Source->CombatVFX->GetWeaponRibbonSegments(),0);
    TestFalse(TEXT("Cancellation removes presentation component"),Source->CombatVFX->HasAttackPresentation());
    World->DestroyWorld(false);return true;
}

// A confirmed lethal hit may arrive after target callbacks kill its source; presentation must stay cleaned.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXReentrantDeathTest,"Constellation.CombatVFX.ReentrantSourceDeathCleanup",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXReentrantDeathTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Target=CombatTest::Actor(World,FVector(1000,0,100),1);
    Source->CombatVFX->SetPresentationEnabled(true);Source->CombatVFX->Initialize(Source->Combat);
    auto* Action=CombatTest::Action(Source);Action->Damage=100.f;
    Target->Combat->OnDied.AddLambda([&](){Source->Combat->ReceiveCombatDamage(100.f,Target);});
    int32 Confirmed=0;
    Source->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit&){++Confirmed;});
    TestTrue(TEXT("Attack starts"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestTrue(TEXT("Lethal hit remains accepted during callback"),Source->Combat->ApplyHit("Swing",Target));
    TestEqual(TEXT("Accepted hit context still reported"),Confirmed,1);
    TestEqual(TEXT("Reentrant source damage is resolved"),Source->Combat->GetHealth(),0.f);
    int32 Left=0;for(TActorIterator<AConstellationFXActor> It(World);It;++It)
        if(It->GetOwner()==Source && !It->IsActorBeingDestroyed()) ++Left;
    TestEqual(TEXT("Late accepted event cannot respawn effects after source death"),Left,0);
    World->DestroyWorld(false);return true;
}

// Capsule contacts inside a large visible mesh must not hide impact presentation or change gameplay payload.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXContactProjectionTest,"Constellation.CombatVFX.ContactPresentationProjection",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCombatVFXContactProjectionTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Target=CombatTest::Actor(World,FVector(1000,0,100),1);
    Target->CombatVFX->SetPresentationEnabled(true);
    Target->GetMesh()->RefreshBoneTransforms();Target->GetMesh()->UpdateBounds();
    const FBox VisualBounds=Target->GetMesh()->Bounds.GetBox();
    const FVector ExactContact=VisualBounds.GetCenter();
    FCombatConfirmedHit Observed;
    Source->CombatVFX->SetPresentationEnabled(true);Source->CombatVFX->Initialize(Source->Combat);
    Source->CombatVFX->SwordTrail.Reset();
    Source->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit& Hit){Observed=Hit;});
    auto* Action=CombatTest::Action(Source);
    TestTrue(TEXT("Action starts"),Source->Combat->TryStartAction(Action));
    Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestTrue(TEXT("Contact damage accepted"),Source->Combat->ApplyHit("Swing",Target,ExactContact,FVector(-1,0,0)));
    TestEqual(TEXT("Gameplay contact position remains exact"),Observed.Position,ExactContact);
    TestEqual(TEXT("Gameplay contact normal remains exact"),Observed.Normal,FVector(-1,0,0));
    TestEqual(TEXT("Damage still applies exactly once"),Target->Combat->GetHealth(),80.f);
    AConstellationFXActor* Impact=nullptr;
    for(TActorIterator<AConstellationFXActor> It(World);It;++It)
        if(It->GetOwner()==Source && It->EffectKind==EConstellationFXKind::SwordHit && !It->IsActorBeingDestroyed()) Impact=*It;
    if(TestNotNull(TEXT("Confirmed sword impact spawned"),Impact))
    {
        TestTrue(TEXT("Presentation lies outside visible front surface"),Impact->GetActorLocation().X<VisualBounds.Min.X);
        TestTrue(TEXT("Projection follows contact normal only"),FMath::IsNearlyEqual(Impact->GetActorLocation().Y,ExactContact.Y) && FMath::IsNearlyEqual(Impact->GetActorLocation().Z,ExactContact.Z));
    }
    Source->Combat->CancelAction();World->DestroyWorld(false);return true;
}

#endif
