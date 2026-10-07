#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SlimeClimbComponent.h"
#include "SlimeClimbMath.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSlimeClimbWeightTest,
    "Constellation.Audit.SlimeClimb.PositiveCandidateWeights",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSlimeClimbWeightTest::RunTest(const FString&)
{
    // The previous reciprocal had a pole at -100 and reversed normals below it.
    const float Scores[] = { -250.f, -101.f, -100.f, -99.f, -1.f, 0.f, 100.f, 500.f };
    float PreviousWeight = TNumericLimits<float>::Max();
    for (float Score : Scores)
    {
        const float Weight = SlimeClimbCandidateWeight(Score);
        TestTrue(TEXT("Every usable candidate has a finite positive weight"),
            FMath::IsFinite(Weight) && Weight > 0.f);
        TestTrue(TEXT("Better scores always receive more weight"), Weight < PreviousWeight);
        PreviousWeight = Weight;
    }
    TestEqual(TEXT("Existing nonnegative weighting is preserved"), SlimeClimbCandidateWeight(100.f), 0.5f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSlimeClimbRecoveryTest,
    "Constellation.Audit.SlimeClimb.FirstDetectionFailureAndInvalidSteps",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSlimeClimbRecoveryTest::RunTest(const FString&)
{
    // A transient world avoids the user's map, actors and gameplay save slots.
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Transient test world"), World)) return false;
    const FVector SpawnLocation(1200.f, -700.f, 300.f);
    ACharacter* Character = World->SpawnActor<ACharacter>(SpawnLocation, FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Test character"), Character))
    {
        World->DestroyWorld(false);
        return false;
    }
    USlimeClimbComponent* Climb = NewObject<USlimeClimbComponent>(Character);
    Character->AddInstanceComponent(Climb);
    Climb->RegisterComponent();
    Character->DispatchBeginPlay();
    TestTrue(TEXT("Component BeginPlay ran"), Climb->HasBegunPlay());
    UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
    Movement->SetMovementMode(MOVE_Flying);
    Movement->Velocity = FVector(100.f, 0.f, 0.f);
    TestFalse(TEXT("No surface exists in an empty world"), Climb->DetectSurface());
    Climb->UpdateOrientation(Character->GetRootComponent(), Movement, FVector::ForwardVector, 0.016f);
    TestTrue(TEXT("First failed climb detection preserves the spawn position"),
        Character->GetActorLocation().Equals(SpawnLocation));
    TestTrue(TEXT("Failed detection stops flying drift"), Movement->Velocity.IsNearlyZero());

    AActor* Surface = World->SpawnActor<AActor>();
    if (!TestNotNull(TEXT("Test surface"), Surface))
    {
        World->DestroyWorld(false);
        return false;
    }
    UBoxComponent* Box = NewObject<UBoxComponent>(Surface);
    Surface->SetRootComponent(Box);
    // Offset the narrow ledge so the downward line fallback misses it, while
    // a valid sphere sample catches it. This makes invalid sample counts fail.
    Box->SetBoxExtent(FVector(10.f, 500.f, 10.f));
    Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->RegisterComponent();
    Surface->SetActorLocation(SpawnLocation + FVector(20.f, 0.f, -100.f));
    Climb->TargetSurfaceNormal = FVector::ForwardVector;
    Climb->HorizontalSteps = 4;
    Climb->VerticalSteps = 0;
    TestTrue(TEXT("Zero sampling counts still detect the nearby surface"), Climb->DetectSurface());
    TestTrue(TEXT("Zero sampling counts yield a finite upward normal"),
        !Climb->TargetSurfaceNormal.ContainsNaN() && Climb->TargetSurfaceNormal.Z > 0.5f);
    Climb->HorizontalSteps = 0;
    TestTrue(TEXT("Zero horizontal count still samples the nearby surface"), Climb->DetectSurface());
    Climb->HorizontalSteps = -3;
    Climb->VerticalSteps = -3;
    TestTrue(TEXT("Negative sampling counts still detect the nearby surface"), Climb->DetectSurface());

    // Recover to the most recently confirmed location, not permanently to spawn.
    const FVector ValidLocation = SpawnLocation + FVector(20.f, 0.f, 0.f);
    Character->SetActorLocation(ValidLocation);
    Movement->SetMovementMode(MOVE_Walking);
    Climb->UpdateOrientation(Character->GetRootComponent(), Movement, FVector::ForwardVector, 0.016f);
    Character->SetActorLocation(ValidLocation + FVector(20.f, 0.f, 0.f));
    Movement->SetMovementMode(MOVE_Flying);
    Climb->bFoundSurface = false;
    Climb->UpdateOrientation(Character->GetRootComponent(), Movement, FVector::ForwardVector, 0.016f);
    TestTrue(TEXT("Later failed detection restores the last confirmed position"),
        Character->GetActorLocation().Equals(ValidLocation));
    World->DestroyWorld(false);
    return true;
}
#endif
