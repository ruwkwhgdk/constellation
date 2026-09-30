#include "SubwayTravelSubsystem.h"
#include "SubwayPortalTransform.h"
#include "SubwayStreamingGate.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/Level.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"

void USubwayTravelSubsystem::Initialize(FSubsystemCollectionBase &C)
{
    Super::Initialize(C);
    TickHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateUObject(this, &USubwayTravelSubsystem::TickTravel));
}
void USubwayTravelSubsystem::Deinitialize()
{
    FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
    Streams.Empty();
    Environments.Empty();
    Super::Deinitialize();
}
void USubwayTravelSubsystem::EnsureWorld(UWorld *W)
{
    if (SessionWorld.Get() == W)
        return;
    Streams.Empty();
    Environments.Empty();
    CooldownUntil = 0;
    SessionWorld = W;
    ActiveLevel = W ? W->PersistentLevel : nullptr;
    CaptureEnvironment(ActiveLevel.Get());
}
ULevel *USubwayTravelSubsystem::FindLevel(const FString &P) const
{
    UWorld *W = SessionWorld.Get();
    if (!W)
        return nullptr;
    if (UGameplayStatics::GetCurrentLevelName(W, true) == FPackageName::GetShortName(P))
        return W->PersistentLevel;
    const FStreamState *S = Streams.Find(P);
    return S && S->Stream.IsValid() ? S->Stream->GetLoadedLevel() : nullptr;
}
void USubwayTravelSubsystem::CaptureEnvironment(ULevel *L)
{
    if (!L)
        return;
    for (AActor *A : L->Actors)
    {
        if (!IsValid(A) || !A->ActorHasTag(TEXT("SE_GlobalEnvironment")))
            continue;
        if (Environments.ContainsByPredicate(
                [A](const FEnvironmentState &S) { return S.Actor.Get() == A; }))
            continue;
        FEnvironmentState S;
        S.Actor = A;
        S.Hidden = A->IsHidden();
        S.Tick = A->IsActorTickEnabled();
        if (auto *PP = Cast<APostProcessVolume>(A))
            S.PostProcessEnabled = PP->bEnabled;
        TInlineComponentArray<USceneComponent *> Components(A);
        for (USceneComponent *C : Components)
            S.Components.Emplace(C, C->IsVisible());
        Environments.Add(MoveTemp(S));
    }
}
void USubwayTravelSubsystem::ActivateEnvironment(ULevel *L)
{
    for (const FEnvironmentState &S : Environments)
    {
        AActor *A = S.Actor.Get();
        if (!A)
            continue;
        const bool Enable = A->GetLevel() == L;
        A->SetActorHiddenInGame(!Enable || S.Hidden);
        A->SetActorTickEnabled(Enable && S.Tick);
        if (auto *PP = Cast<APostProcessVolume>(A))
            PP->bEnabled = Enable && S.PostProcessEnabled;
        for (const auto &Pair : S.Components)
            if (USceneComponent *C = Pair.Key.Get())
                C->SetVisibility(Enable && Pair.Value, false);
    }
}
void USubwayTravelSubsystem::Preload(UWorld *W, const FString &P)
{
    EnsureWorld(W);
    if (!W || P.IsEmpty() || !FPackageName::DoesPackageExist(P))
        return;
    int32 RetryCount = 0;
    if (const FStreamState *Previous = Streams.Find(P))
    {
        const bool Unloaded = !Previous->Stream.IsValid() || !Previous->Stream->GetLoadedLevel();
        if (!SubwayCanRetryLoad(Previous->Failed, Unloaded,
                                FPlatformTime::Seconds() - Previous->Started, Previous->RetryCount))
            return;
        RetryCount = Previous->RetryCount + 1;
        if (Previous->Stream.IsValid())
            Previous->Stream->SetIsRequestingUnloadAndRemoval(true);
        Streams.Remove(P);
    }
    if (FindLevel(P))
        return;
    ULevelStreamingDynamic::FLoadLevelInstanceParams Params(W, P, FTransform::Identity);
    Params.bInitiallyVisible = false;
    bool Success = false;
    ULevelStreamingDynamic *Stream = ULevelStreamingDynamic::LoadLevelInstance(Params, Success);
    if (!Success || !Stream)
    {
        UE_LOG(LogTemp, Error, TEXT("Subway preload failed: %s"), *P);
        return;
    }
    Stream->bShouldBlockOnLoad = false;
    FStreamState S;
    S.Stream = Stream;
    S.Started = FPlatformTime::Seconds();
    S.RetryCount = RetryCount;
    Streams.Add(P, S);
}
bool USubwayTravelSubsystem::TickTravel(float)
{
    if (!SessionWorld.IsValid())
        return true;
    const double Now = FPlatformTime::Seconds();
    for (auto &Pair : Streams)
    {
        FStreamState &S = Pair.Value;
        ULevelStreamingDynamic *Stream = S.Stream.Get();
        if (!Stream || S.Failed)
            continue;
        if (Stream->GetLoadedLevel() && !S.Prepared)
        {
            CaptureEnvironment(Stream->GetLoadedLevel());
            ActivateEnvironment(ActiveLevel.Get());
            Stream->SetShouldBeVisible(true);
            S.Prepared = true;
        }
        if (Stream->IsLevelVisible())
        {
            // BeginPlay may change visibility, so apply isolation again after activation.
            if (S.ReadyAt == 0)
            {
                ActivateEnvironment(ActiveLevel.Get());
                S.ReadyAt = Now;
            }
        }
        else if (Now - S.Started > 60)
        {
            S.Failed = true;
            Stream->SetShouldBeVisible(false);
            Stream->SetShouldBeLoaded(false);
            UE_LOG(LogTemp, Error, TEXT("Subway preload timeout; safety barrier stays closed: %s"),
                   *Pair.Key);
        }
    }
    return true;
}
bool USubwayTravelSubsystem::IsReady(UWorld *W, const FString &P)
{
    EnsureWorld(W);
    ULevel *L = FindLevel(P);
    if (!L)
        return false;
    if (L == W->PersistentLevel)
        return true;
    const FStreamState *S = Streams.Find(P);
    return S && !S->Failed && S->ReadyAt > 0 && FPlatformTime::Seconds() - S->ReadyAt > 1 &&
           S->Stream.IsValid() && S->Stream->IsLevelVisible();
}
bool USubwayTravelSubsystem::IsActiveLevel(ULevel *L)
{
    if (L)
        EnsureWorld(L->GetWorld());
    return ActiveLevel.Get() == L;
}
bool USubwayTravelSubsystem::IsTravelBusy() const
{
    return FPlatformTime::Seconds() < CooldownUntil;
}
bool USubwayTravelSubsystem::StartTravel(APlayerController *PC, const FString &P,
                                         const FTransform &Source, const FTransform &Arrival)
{
    if (!PC || !PC->IsLocalController() || IsTravelBusy() || !IsReady(PC->GetWorld(), P))
        return false;
    ACharacter *C = Cast<ACharacter>(PC->GetPawn());
    if (!C)
        return false;
    auto *Movement = C->GetCharacterMovement();
    const FSubwayPortalPose Pose = SubwayPortalTransform(Source, Arrival, C->GetActorLocation(),
                                                         C->GetActorQuat(), Movement->Velocity);
    const FVector Location = Pose.Location;
    const FQuat Delta = Arrival.GetRotation() * Source.GetRotation().Inverse();
    const FRotator Rotation = Pose.Rotation.Rotator();
    const FRotator View = (Delta * PC->GetControlRotation().Quaternion()).Rotator();
    const FVector Velocity = Pose.Velocity;
    const float Half = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SubwayArrival), false, C);
    FHitResult Floor;
    if (!PC->GetWorld()->LineTraceSingleByChannel(
            Floor, Location, Location - FVector(0, 0, Half + 60), ECC_Visibility, Query) ||
        !Movement->IsWalkable(Floor) || !Floor.GetActor() ||
        Floor.GetActor()->GetLevel() != FindLevel(P))
        return false;
    if (PC->GetWorld()->OverlapBlockingTestByProfile(
            Location, Rotation.Quaternion(), C->GetCapsuleComponent()->GetCollisionProfileName(),
            FCollisionShape::MakeCapsule(C->GetCapsuleComponent()->GetScaledCapsuleRadius(),
                                         Half - 1),
            Query))
        return false;
    if (!C->TeleportTo(Location, Rotation, false, true))
        return false;
    Movement->Velocity = Velocity;
    PC->SetControlRotation(View);
    // Reset only this pawn's spring-arm history, not the user's camera settings.
    TInlineComponentArray<USpringArmComponent *> Arms(C);
    for (USpringArmComponent *Arm : Arms)
    {
        const bool Pos = Arm->bEnableCameraLag, Rot = Arm->bEnableCameraRotationLag;
        Arm->bEnableCameraLag = false;
        Arm->bEnableCameraRotationLag = false;
        Arm->TickComponent(0, LEVELTICK_All, nullptr);
        Arm->bEnableCameraLag = Pos;
        Arm->bEnableCameraRotationLag = Rot;
    }
    ActiveLevel = FindLevel(P);
    ActivateEnvironment(ActiveLevel.Get());
    CooldownUntil = FPlatformTime::Seconds() + .35;
    if (PC->PlayerCameraManager)
        PC->PlayerCameraManager->SetGameCameraCutThisFrame();
    UE_LOG(LogTemp, Log, TEXT("Subway streamed handoff: %s (pawn and velocity retained)"), *P);
    return true;
}
