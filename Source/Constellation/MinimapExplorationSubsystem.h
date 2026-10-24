#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MinimapTypes.h"
#include "MinimapExplorationSubsystem.generated.h"

class UConstellationSaveGame;

struct FMinimapExplorationKey
{
    FName Region, Floor;
    int32 CellSize=0;
    bool operator==(const FMinimapExplorationKey& Other) const
    { return Region==Other.Region && Floor==Other.Floor && CellSize==Other.CellSize; }
    friend uint32 GetTypeHash(const FMinimapExplorationKey& Key)
    { return HashCombine(HashCombine(GetTypeHash(Key.Region),GetTypeHash(Key.Floor)),GetTypeHash(Key.CellSize)); }
};

/** Session-owned, monotonic discovery; pawn death and world reload do not restore old checkpoints. */
UCLASS()
class CONSTELLATION_API UMinimapExplorationSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable,Category="Minimap")
    void RevealCells(FName Region,FName Floor,int32 CellSize,const TArray<FIntPoint>& Cells);
    UFUNCTION(BlueprintPure,Category="Minimap")
    bool IsRevealed(FName Region,FName Floor,int32 CellSize,FIntPoint Cell) const;
    UFUNCTION(BlueprintPure,Category="Minimap")
    bool IsRegionUnlocked(FName Region) const;
    UFUNCTION(BlueprintCallable,Category="Minimap")
    void UnlockRegion(FName Region);
    UFUNCTION(BlueprintCallable,Category="Minimap")
    bool Flush();

    /** Does not write disk or alter other owners' fields. Call after loading the latest save. */
    void MergeIntoSave(UConstellationSaveGame* Save) const;
    bool UsesSaveSlot(const FString& Slot) const { return Slot==SaveSlotName; }
    void TickFlush(float DeltaSeconds);
#if WITH_DEV_AUTOMATION_TESTS
    /** Must be called on a fresh test object, before Initialize; never touches the gameplay slot. */
    void SetSaveSlotForTesting(const FString& Slot) { check(!bInitialized); check(!Slot.IsEmpty()); SaveSlotName=Slot; }
#endif
private:
    void RebuildCache();
    UPROPERTY() FMinimapSaveData Discovery;
    TMap<FMinimapExplorationKey,TSet<FIntPoint>> CellCache;
    TSet<FName> UnlockedCache;
    FString SaveSlotName=TEXT("ConstellationSaveGame");
    float DirtySeconds=0;
    bool bDirty=false;
    bool bInitialized=false;
};
