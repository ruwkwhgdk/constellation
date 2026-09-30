#include "SubwayTravelVolume.h"
#include "SubwayTravelSubsystem.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
ASubwayTravelVolume::ASubwayTravelVolume()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    Zone = CreateDefaultSubobject<UBoxComponent>(TEXT("TravelZone"));
    SetRootComponent(Zone);
    Zone->SetBoxExtent(FVector(140, 190, 280));
    Zone->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Zone->SetHiddenInGame(true);
    SafetyBarrier = CreateDefaultSubobject<UBoxComponent>(TEXT("LoadingSafetyBarrier"));
    SafetyBarrier->SetupAttachment(Zone);
    SafetyBarrier->SetRelativeLocation(FVector(80, 0, 140));
    SafetyBarrier->SetBoxExtent(FVector(12, 210, 160));
    SafetyBarrier->SetCollisionProfileName(TEXT("BlockAll"));
    SafetyBarrier->SetHiddenInGame(true);
}
void ASubwayTravelVolume::Tick(float DT)
{
    Super::Tick(DT);
    if (!GetGameInstance())
        return;
    auto *Travel = GetGameInstance()->GetSubsystem<USubwayTravelSubsystem>();
    if (!Travel || !Travel->IsActiveLevel(GetLevel()))
    {
        SafetyBarrier->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        return;
    }
    APlayerController *PC = UGameplayStatics::GetPlayerController(this, 0);
    ACharacter *Pawn = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
    if (!Pawn || !PC->IsLocalController())
        return;
    const FString P = DestinationMap.ToSoftObjectPath().GetLongPackageName();
    const FVector Local = GetActorTransform().InverseTransformPosition(Pawn->GetActorLocation());
    if (Local.SizeSquared() < FMath::Square(PreloadDistance))
        Travel->Preload(GetWorld(), P);
    const bool Ready = Travel->IsReady(GetWorld(), P);
    // The pawn crosses the portal before reaching this backstop. Keep it solid even
    // after loading, in case the destination floor/capsule validation rejects travel.
    SafetyBarrier->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    const FVector Extent = Zone->GetUnscaledBoxExtent();
    const float Feet =
        Pawn->GetActorLocation().Z - Pawn->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    const bool Inside = FMath::Abs(Local.X) <= Extent.X && FMath::Abs(Local.Y) <= Extent.Y &&
                        Local.Z >= 0 && Local.Z <= Extent.Z && Feet <= MaximumFootHeight;
    if (Gate.Update(Local.X, Inside, Ready, Travel->IsTravelBusy()) &&
        Travel->StartTravel(PC, P, GetActorTransform(), ArrivalTransform))
        Gate.Commit();
}
