#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Containers/Ticker.h"
#include "SubwayTravelSubsystem.generated.h"
class APlayerController;
class ULevelStreamingDynamic;
class USceneComponent;
/** Two map assets, one live pawn. No OpenLevel, input lock or screen fade. */
UCLASS()
class CONSTELLATION_API USubwayTravelSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
  public:
    virtual void Initialize(FSubsystemCollectionBase &Collection) override;
    virtual void Deinitialize() override;
    void Preload(UWorld *World, const FString &Package);
    bool IsReady(UWorld *World, const FString &Package);
    bool IsActiveLevel(ULevel *Level);
    bool IsTravelBusy() const;
    bool StartTravel(APlayerController *Player, const FString &Package, const FTransform &Source,
                     const FTransform &Arrival);

  private:
    struct FEnvironmentState
    {
        TWeakObjectPtr<AActor> Actor;
        bool Hidden = false, Tick = false, PostProcessEnabled = false;
        TArray<TPair<TWeakObjectPtr<USceneComponent>, bool>> Components;
    };
    struct FStreamState
    {
        TWeakObjectPtr<ULevelStreamingDynamic> Stream;
        double Started = 0, ReadyAt = 0;
        bool Prepared = false, Failed = false;
        int32 RetryCount = 0;
    };
    void EnsureWorld(UWorld *World);
    ULevel *FindLevel(const FString &Package) const;
    void CaptureEnvironment(ULevel *Level);
    void ActivateEnvironment(ULevel *Level);
    bool TickTravel(float DeltaSeconds);
    FTSTicker::FDelegateHandle TickHandle;
    TWeakObjectPtr<UWorld> SessionWorld;
    TWeakObjectPtr<ULevel> ActiveLevel;
    TMap<FString, FStreamState> Streams;
    TArray<FEnvironmentState> Environments;
    double CooldownUntil = 0;
};
