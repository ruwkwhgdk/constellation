#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CarryComponent.h"
#include "TimerManager.h"
#include "CarryInputLibrary.h"
#include "HoldableComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Animation/AnimMontage.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarryLifecycleTest, "Constellation.Carry.WeightOwnershipAndRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCarryLifecycleTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    ACharacter* Character = World->SpawnActor<ACharacter>(FVector(0,0,100), FRotator::ZeroRotator);
    UCarryComponent* Carry = NewObject<UCarryComponent>(Character);
    Character->AddInstanceComponent(Carry); Carry->RegisterComponent();
    UStaticMeshComponent* Sword=NewObject<UStaticMeshComponent>(Character,TEXT("Sword"));
    Character->AddInstanceComponent(Sword); Sword->RegisterComponent(); Sword->SetVisibility(true);
    AActor* Item = World->SpawnActor<AActor>();
    UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Item);
    Item->SetRootComponent(Mesh);
    Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    Mesh->SetWorldScale3D(FVector(.4));
    Mesh->SetMobility(EComponentMobility::Movable);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->RegisterComponent();
    Item->SetActorLocation(FVector(80,0,100));
    UHoldableComponent* Holdable = NewObject<UHoldableComponent>(Item);
    Item->AddInstanceComponent(Holdable); Holdable->RegisterComponent();
    TestTrue(TEXT("Idle allows walking"), Carry->AllowsWalking());
    Mesh->SetMassOverrideInKg(NAME_None,10.01f,true);
    TestFalse(TEXT("Too heavy rejected"), Carry->TryPickUp(Holdable));
    Mesh->SetMassOverrideInKg(NAME_None,10.f,true);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TestFalse(TEXT("Query-only item cannot provide physical release collisions"),Carry->TryPickUp(Holdable));
    Carry->AbortCarry(); Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    TestTrue(TEXT("Exact weight accepted"), Carry->TryPickUp(Holdable));
    TestTrue(TEXT("Actions blocked immediately"), Carry->BlocksOtherActions());
    TestFalse(TEXT("Weapon visual hidden during carry"),Sword->IsVisible());
    TestFalse(TEXT("Pickup animation blocks walking"), Carry->AllowsWalking());
    TestFalse(TEXT("Repeated pickup rejected"), Carry->TryPickUp(Holdable));
    Carry->OnPickupContact(); Carry->OnPickupContact(); Carry->FinishAction();
    TestEqual(TEXT("Single item held"), Carry->GetHeldActor(), Item);
    TestTrue(TEXT("Carrying allows walking"), Carry->AllowsWalking());
    TestTrue(TEXT("Carried item consumes attack"), UCarryInputLibrary::RouteCarryInput(Character,"IA_Attack","Started"));
    TestTrue(TEXT("Carried item consumes jump"), UCarryInputLibrary::RouteCarryInput(Character,"IA_Jump","Triggered"));
    TestTrue(TEXT("Carried item consumes transform"), UCarryInputLibrary::RouteCarryInput(Character,"IA_Transform","Started"));
    UCarryInputLibrary::RouteCarryInput(Character,"IA_Attack","Canceled");
    TestEqual(TEXT("Canceled aim keeps carried state"), Carry->State,ECarryState::Carrying);
    TestFalse(TEXT("No floor means placing fails"), Carry->TryPlace());
    TestEqual(TEXT("Failed place keeps item"), Carry->GetHeldActor(), Item);
    Carry->AbortCarry(); Carry->AbortCarry();
    TestNull(TEXT("Abort clears item"), Carry->GetHeldActor());
    TestFalse(TEXT("Abort releases ownership"), Holdable->Carrier.IsValid());
    TestFalse(TEXT("Abort restores action permission"), Carry->BlocksOtherActions());
    TestNull(TEXT("Abort detaches item"), Item->GetAttachParentActor());
    TestTrue(TEXT("Weapon visual restored on recovery"),Sword->IsVisible());
    TestTrue(TEXT("Damage drop clears the carrier capsule"),FVector::Dist2D(Item->GetActorLocation(),Character->GetActorLocation())>Character->GetCapsuleComponent()->GetScaledCapsuleRadius()+Mesh->Bounds.BoxExtent.Size2D());
    AActor* OriginalParent=World->SpawnActor<AActor>();
    USceneComponent* ParentRoot=NewObject<USceneComponent>(OriginalParent); OriginalParent->SetRootComponent(ParentRoot); ParentRoot->RegisterComponent();
    Item->SetActorLocation(FVector(80,0,100)); Item->AttachToActor(OriginalParent,FAttachmentTransformRules::KeepWorldTransform);
    TestTrue(TEXT("Attached item can begin pickup"),Carry->TryPickUp(Holdable));
    Carry->AbortCarry();
    TestEqual(TEXT("Precontact abort preserves original attachment"),Item->GetAttachParentActor(),OriginalParent);
    World->DestroyWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarryPlacementTest,"Constellation.Carry.PlacementRecheckAndThrowGeometry",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCarryPlacementTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto Box=[World](FVector Location,FVector Extent)
    {
        AActor* Actor=World->SpawnActor<AActor>(); UBoxComponent* Shape=NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Shape); Shape->SetBoxExtent(Extent); Shape->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Shape->SetCollisionResponseToAllChannels(ECR_Block); Shape->RegisterComponent(); Actor->SetActorLocation(Location); return Actor;
    };
    Box(FVector(0,0,-10),FVector(1000,1000,10));
    ACharacter* Character=World->SpawnActor<ACharacter>(FVector(0,0,100),FRotator::ZeroRotator);
    const float OriginalSpeed=Character->GetCharacterMovement()->MaxWalkSpeed;
    UCarryComponent* Carry=NewObject<UCarryComponent>(Character); Character->AddInstanceComponent(Carry); Carry->RegisterComponent();
    // Both missing-animation and authored-montage paths use real action seconds.
    for(ECarryState Action : {ECarryState::PickingUp,ECarryState::Placing,ECarryState::Throwing})
    {
        Carry->State=Action; Carry->StartAction(nullptr,1.f,3.f);
        TestTrue(TEXT("Each long fallback action has a subsecond deadline"),FMath::IsNearlyEqual(World->GetTimerManager().GetTimerRemaining(Carry->FinishTimer),.75f));
        Carry->AbortCarry();
    }
    // Fitted furniture aligns itself; the player stays at the interaction pose.
    {
        AActor* Prop=World->SpawnActor<AActor>(); UStaticMeshComponent* PM=NewObject<UStaticMeshComponent>(Prop);
        Prop->SetRootComponent(PM); PM->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
        PM->SetWorldScale3D(FVector(.2f)); PM->SetMobility(EComponentMobility::Movable);
        PM->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); PM->RegisterComponent(); PM->SetMassOverrideInKg(NAME_None,5,true);
        Prop->SetActorLocation(FVector(80,-35,25));
        UHoldableComponent* HC=NewObject<UHoldableComponent>(Prop); Prop->AddInstanceComponent(HC); HC->RegisterComponent();
        UDataTable* Table=NewObject<UDataTable>(); Table->RowStruct=FHoldableItemRow::StaticStruct();
        FHoldableItemRow Row; Row.FittedHoldMontage=NewObject<UAnimMontage>(); Row.FittedThrowMontage=NewObject<UAnimMontage>(); Row.FittedPickupMontage=NewObject<UAnimMontage>();
        const FTransform Target(FRotator(0,90,0),FVector(95,0,25),FVector(.2f));
        Row.FittedPickupMeshSpace=Target.GetRelativeTransform(Character->GetMesh()->GetComponentTransform());
        Table->AddRow(TEXT("Pickup"),Row); HC->ItemRow.DataTable=Table; HC->ItemRow.RowName=TEXT("Pickup");
        const FTransform PlayerStart=Character->GetActorTransform();
        TestTrue(TEXT("Fitted pickup begins"),Carry->TryPickUp(HC));
        TestTrue(TEXT("Pickup animation clock starts during furniture alignment"),World->GetTimerManager().IsTimerActive(Carry->ContactTimer));
        TestTrue(TEXT("Pickup completes within one second"),World->GetTimerManager().GetTimerRemaining(Carry->FinishTimer)<=1.f);
        TestEqual(TEXT("Alignment immediately disables collision"),PM->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
        for(int I=0;I<60;++I) Carry->TickComponent(.016f,LEVELTICK_All,&Carry->PrimaryComponentTick);
        TestTrue(TEXT("Furniture aligns to authored ground pose"),Prop->GetActorTransform().Equals(Target,.1f));
        TestTrue(TEXT("Alignment never moves player"),Character->GetActorTransform().Equals(PlayerStart));
        Carry->AbortCarry();
        Prop->SetActorLocationAndRotation(FVector(80,-35,25),FRotator::ZeroRotator);
        AActor* AlignmentWall=Box(FVector(95,0,25),FVector(12,8,24));
        TestTrue(TEXT("Non-colliding alignment accepts occupied target pose"),Carry->TryPickUp(HC));
        Carry->OnPickupContact();
        Carry->TickComponent(.3f,LEVELTICK_All,&Carry->PrimaryComponentTick);
        TestTrue(TEXT("Occupied alignment completes contact without a second sight rejection"),Carry->bContactOccurred);
        Carry->FinishAction();
        TestEqual(TEXT("Occupied alignment reaches Carrying"),Carry->State,ECarryState::Carrying);
        Carry->AbortCarry();
        Prop->SetActorLocationAndRotation(FVector(80,-35,25),FRotator::ZeroRotator);
        AlignmentWall->Destroy();
        PM->SetSimulatePhysics(true);
        TestTrue(TEXT("Physical furniture alignment begins"),Carry->TryPickUp(HC));
        TestFalse(TEXT("Alignment pauses rigid simulation"),PM->IsSimulatingPhysics());
        Carry->TickComponent(.1f,LEVELTICK_All,&Carry->PrimaryComponentTick);
        Carry->AbortCarry();
        TestTrue(TEXT("Cancel alignment restores rigid simulation"),PM->IsSimulatingPhysics());
        TestTrue(TEXT("Cancel alignment preserves player position"),Character->GetActorTransform().Equals(PlayerStart));
        Prop->SetActorLocationAndRotation(FVector(80,-35,25),FRotator::ZeroRotator);
        TestTrue(TEXT("Alignment starts before moving blocker arrives"),Carry->TryPickUp(HC));
        Carry->TickComponent(.1f,LEVELTICK_All,&Carry->PrimaryComponentTick);
        AActor* MovingBlocker=Box(Prop->GetActorLocation(),FVector(12,12,12));
        Carry->AbortCarry();
        TestFalse(TEXT("Blocked cancel defers rigid simulation"),PM->IsSimulatingPhysics());
        MovingBlocker->Destroy(); static_cast<UActorComponent*>(HC)->TickComponent(0,LEVELTICK_All,&HC->PrimaryComponentTick);
        TestTrue(TEXT("Cleared cancel restores rigid simulation"),PM->IsSimulatingPhysics());
        Prop->SetActorLocationAndRotation(FVector(80,-35,25),FRotator::ZeroRotator);
        TestTrue(TEXT("Hitch recovery pickup begins"),Carry->TryPickUp(HC));
        Carry->OnPickupContact();
        TestTrue(TEXT("Early notify is queued during alignment"),Carry->bPickupContactPending);
        Carry->TickComponent(.8f,LEVELTICK_All,&Carry->PrimaryComponentTick);
        TestTrue(TEXT("Queued contact is consumed after alignment"),Carry->bContactOccurred&&!Carry->bPickupContactPending&&!Carry->bAligningPickup);
        Carry->AbortCarry();
        Prop->Destroy();
    }
    // Furniture pivots sit at floor level and can settle slightly below it.
    AActor* Chair=World->SpawnActor<AActor>();
    UStaticMeshComponent* ChairMesh=NewObject<UStaticMeshComponent>(Chair);
    Chair->SetRootComponent(ChairMesh);
    ChairMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Constellation/Environments/School/Meshes/SM_SchoolChair_Holdable.SM_SchoolChair_Holdable")));
    ChairMesh->SetMobility(EComponentMobility::Movable);
    ChairMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    ChairMesh->RegisterComponent(); ChairMesh->SetMassOverrideInKg(NAME_None,8,true); Chair->SetActorLocation(FVector(100,0,-.01));
    UHoldableComponent* ChairHold=NewObject<UHoldableComponent>(Chair);
    Chair->AddInstanceComponent(ChairHold); ChairHold->RegisterComponent();
    TestTrue(TEXT("Settled floor-pivot furniture remains selectable"),Carry->TryPickUp(ChairHold));
    Carry->AbortCarry();
    UDataTable* GroundTable=NewObject<UDataTable>(); GroundTable->RowStruct=FHoldableItemRow::StaticStruct();
    FHoldableItemRow GroundRow; GroundRow.FittedHoldMontage=NewObject<UAnimMontage>(); GroundRow.FittedThrowMontage=NewObject<UAnimMontage>(); GroundRow.FittedPickupMontage=NewObject<UAnimMontage>();
    GroundRow.FittedPickupMeshSpace=FTransform(FRotator(0,90,0),FVector(110,0,.35)).GetRelativeTransform(Character->GetMesh()->GetComponentTransform());
    GroundTable->AddRow(TEXT("Ground"),GroundRow); ChairHold->ItemRow.DataTable=GroundTable; ChairHold->ItemRow.RowName=TEXT("Ground");
    Chair->SetActorLocation(FVector(100,0,-.1));
    TestTrue(TEXT("Shallow settled furniture can align off floor support"),Carry->TryPickUp(ChairHold));
    Carry->AbortCarry(); ChairHold->ItemRow=FDataTableRowHandle(); Chair->SetActorLocationAndRotation(FVector(100,0,-.01),FRotator::ZeroRotator);
    AActor* Occluder=Box(FVector(50,0,70),FVector(5,60,70));
    TestFalse(TEXT("Furniture behind a wall stays unselectable"),Carry->TryPickUp(ChairHold));
    Carry->AbortCarry(); Occluder->Destroy();
    ChairHold->CarryOffset=FTransform(FRotator::ZeroRotator,FVector(60,0,-35));
    Chair->SetActorLocationAndRotation(FVector(160,0,28.2),FRotator(90,0,0));
    TestTrue(TEXT("Overturned furniture is reached by its visible body, not its distant pivot"),Carry->TryPickUp(ChairHold));
    Carry->AbortCarry();
    Chair->SetActorLocationAndRotation(FVector(100,0,28.2),FRotator(-90,0,0));
    // This is above the toppled chair and behind the sight ray, but overlaps
    // its upright carry pose. A non-colliding held object must still lift.
    AActor* CarryPoseObstacle=Box(FVector(60,0,160),FVector(10,10,10));
    TestTrue(TEXT("Toppled furniture can start pickup beside an obstacle"),Carry->TryPickUp(ChairHold));
    Carry->OnPickupContact(); Carry->FinishAction();
    TestEqual(TEXT("Collision-free pickup allows the upright carry pose to overlap"),Carry->GetHeldActor(),Chair);
    Carry->AbortCarry(); CarryPoseObstacle->Destroy(); Chair->Destroy();
    AActor* Item=World->SpawnActor<AActor>(); UStaticMeshComponent* Mesh=NewObject<UStaticMeshComponent>(Item);
    Item->SetRootComponent(Mesh); Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Mesh->SetWorldScale3D(FVector(.4)); Mesh->SetMobility(EComponentMobility::Movable); Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->SetCollisionResponseToAllChannels(ECR_Block); Mesh->RegisterComponent(); Mesh->SetMassOverrideInKg(NAME_None,5,true); Item->SetActorLocation(FVector(80,0,19.95));
    UHoldableComponent* Holdable=NewObject<UHoldableComponent>(Item); Item->AddInstanceComponent(Holdable); Holdable->RegisterComponent();
    Carry->bCarryFeetPlanted=true;
    TestTrue(TEXT("Ground item can be selected by interaction sweep"),Carry->HandleInteract());
    TestFalse(TEXT("New pickup clears previous throw foot anchors"),Carry->bCarryFeetPlanted);
    TestEqual(TEXT("Pickup contact follows target duration"),World->GetTimerManager().GetTimerRemaining(Carry->ContactTimer),.375f);
    TestEqual(TEXT("Pickup finish follows target duration"),World->GetTimerManager().GetTimerRemaining(Carry->FinishTimer),.75f);
    Carry->OnPickupContact(); Carry->FinishAction();
    TestEqual(TEXT("Ground item is held"),Carry->GetHeldActor(),Item);
    UDataTable* FittedTable=NewObject<UDataTable>(); FittedTable->RowStruct=FHoldableItemRow::StaticStruct();
    FHoldableItemRow Fitted; Fitted.FittedThrowMontage=NewObject<UAnimMontage>(); Fitted.FittedHoldMontage=NewObject<UAnimMontage>();
    FittedTable->AddRow(TEXT("Fitted"),Fitted); Holdable->ItemRow.DataTable=FittedTable; Holdable->ItemRow.RowName=TEXT("Fitted");
    Carry->State=ECarryState::Throwing;
    TestTrue(TEXT("Fitted throw releases at visible prop transform without teleport"),Carry->GetReleaseTransform().Equals(Mesh->GetComponentTransform()));
    Holdable->ItemRow=FDataTableRowHandle(); Carry->State=ECarryState::Carrying;
    TestEqual(TEXT("Carrying retains the character's normal walking speed"),Character->GetCharacterMovement()->MaxWalkSpeed,OriginalSpeed);
    FHitResult SupportHit;
    TestTrue(TEXT("Lifting away from exact floor contact is allowed"),
        Carry->IsPathFree(FVector(80,0,20),FVector(80,0,130),FQuat::Identity,SupportHit));
    TestFalse(TEXT("Deep floor penetration is not ignored"),
        Carry->IsPathFree(FVector(80,0,15),FVector(80,0,130),FQuat::Identity,SupportHit));
    AActor* LiftCeiling=Box(FVector(80,0,75),FVector(30,30,5));
    TestFalse(TEXT("Clearing initial floor contact still checks the ceiling"),
        Carry->IsPathFree(FVector(80,0,20),FVector(80,0,130),FQuat::Identity,SupportHit));
    LiftCeiling->Destroy();
    AActor* LiftWall=Box(FVector(130,0,80),FVector(5,100,80));
    TestFalse(TEXT("Clearing initial floor contact still checks walls along the lift"),
        Carry->IsPathFree(FVector(80,0,20),FVector(180,0,130),FQuat::Identity,SupportHit));
    LiftWall->Destroy();
    TestTrue(TEXT("Clear floor allows placing"),Carry->TryPlace());
    TestEqual(TEXT("Place contact follows target duration"),World->GetTimerManager().GetTimerRemaining(Carry->ContactTimer),.4125f);
    TestEqual(TEXT("Place finish follows target duration"),World->GetTimerManager().GetTimerRemaining(Carry->FinishTimer),.75f);
    AActor* Obstacle=Box(FVector(82,0,23),FVector(22,22,22));
    Carry->OnPlaceRelease(); Carry->FinishAction();
    TestEqual(TEXT("New obstacle must retain held item instead of stacking on it"),Carry->GetHeldActor(),Item);
    TestEqual(TEXT("Blocked release returns to carrying"),Carry->State,ECarryState::Carrying);
    Obstacle->Destroy();
    TestTrue(TEXT("Aim can start"),Carry->BeginAim());
    TestTrue(TEXT("Clear ballistic path valid"),Carry->bAimValid);
    Carry->CancelAim();
    AActor* Wall=Box(FVector(75,0,130),FVector(15,100,100));
    CastChecked<UBoxComponent>(Wall->GetRootComponent())->SetCollisionResponseToChannel(ECC_Visibility,ECR_Ignore);
    Carry->BeginAim();
    TestFalse(TEXT("Blocked release space invalidates preview"),Carry->bAimValid);
    TestFalse(TEXT("Invalid preview cannot throw"),Carry->CommitThrow());
    TestEqual(TEXT("Invalid throw retains item"),Carry->GetHeldActor(),Item);
    Wall->Destroy();
    // Held objects have no collision and must not rewind character movement.
    AActor* SideWall=Box(FVector(0,50,115),FVector(100,5,70));
    Character->SetActorRotation(FRotator(0,90,0));
    Carry->TickComponent(.016f,LEVELTICK_All,&Carry->PrimaryComponentTick);
    TestTrue(TEXT("Held object does not block rotation"),FMath::IsNearlyEqual(Character->GetActorRotation().Yaw,90.f));
    TestEqual(TEXT("Held mesh has no collision"),Mesh->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
    SideWall->Destroy();
    AActor* ThinWall=Box(FVector(150,0,115),FVector(2,100,70));
    Character->SetActorLocation(FVector(250,0,100));
    Carry->TickComponent(.016f,LEVELTICK_All,&Carry->PrimaryComponentTick);
    TestTrue(TEXT("Held object does not rewind movement past a thin wall"),Character->GetActorLocation().Equals(FVector(250,0,100)));
    ThinWall->Destroy();
    Character->SetActorLocationAndRotation(FVector(0,0,100),FRotator::ZeroRotator);
    Mesh->SetLinearDamping(5); Mesh->SetAngularDamping(5);
    Carry->BeginAim(); TestTrue(TEXT("Valid throw committed"),Carry->CommitThrow());
    Carry->OnThrowRelease(); const FVector Velocity=Mesh->GetPhysicsLinearVelocity(); Carry->OnThrowRelease();
    TestNull(TEXT("Throw clears held item exactly once"),Carry->GetHeldActor());
    TestTrue(TEXT("Throw enables physics"),Mesh->IsSimulatingPhysics());
    TestEqual(TEXT("Ballistic flight matches preview linear damping"),Mesh->GetLinearDamping(),0.f);
    TestEqual(TEXT("Ballistic spin matches preview angular damping"),Mesh->GetAngularDamping(),0.f);
    TestTrue(TEXT("Throw has forward and upward velocity"),Velocity.X>0&&Velocity.Z>0);
    TestTrue(TEXT("Duplicate release preserves velocity"),Velocity.Equals(Mesh->GetPhysicsLinearVelocity()));
    Carry->FinishAction(); TestFalse(TEXT("Recovered throw allows normal actions"),Carry->BlocksOtherActions());
    TestEqual(TEXT("Recovered throw restores original speed"),Character->GetCharacterMovement()->MaxWalkSpeed,OriginalSpeed);
    TestTrue(TEXT("A released nearby item can be reclaimed"),Carry->TryPickUp(Holdable));
    TestEqual(TEXT("Reclaim restores original linear damping"),Mesh->GetLinearDamping(),5.f);
    TestEqual(TEXT("Reclaim restores original angular damping"),Mesh->GetAngularDamping(),5.f);
    Carry->AbortCarry();
    World->DestroyWorld(false); return true;
}
#endif
