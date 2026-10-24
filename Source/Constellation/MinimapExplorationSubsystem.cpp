#include "MinimapExplorationSubsystem.h"
#include "ConstellationSaveGame.h"
#include "Kismet/GameplayStatics.h"

void FMinimapSaveData::Merge(const FMinimapSaveData& Other)
{
    if(Version!=1 || Other.Version!=1 || this==&Other)return;
    for(const FName Region:Other.UnlockedRegions)if(!Region.IsNone())UnlockedRegions.AddUnique(Region);
    for(const FMinimapExploredFloor& Incoming:Other.Floors)
    {
        if(Incoming.RegionId.IsNone() || Incoming.FloorId.IsNone() || Incoming.CellSize<=0)continue;
        FMinimapExploredFloor* Target=Floors.FindByPredicate([&](const FMinimapExploredFloor& Row)
        {return Row.RegionId==Incoming.RegionId && Row.FloorId==Incoming.FloorId && Row.CellSize==Incoming.CellSize;});
        if(!Target)
        {
            Target=&Floors.AddDefaulted_GetRef(); Target->RegionId=Incoming.RegionId;
            Target->FloorId=Incoming.FloorId; Target->CellSize=Incoming.CellSize;
        }
        TSet<FIntPoint> Known;
        Known.Reserve(Target->Cells.Num()+Incoming.Cells.Num());
        for(const FIntPoint Cell:Target->Cells)Known.Add(Cell);
        for(const FIntPoint Cell:Incoming.Cells)if(!Known.Contains(Cell)){Known.Add(Cell);Target->Cells.Add(Cell);}
    }
}

void UMinimapExplorationSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    bInitialized=true;
    // This is the only automatic restore. World transitions and possession never clear Discovery.
    if(UGameplayStatics::DoesSaveGameExist(SaveSlotName,0))
    {
        const auto* Save=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName,0));
        if(Save && Save->Minimap.Version==1)Discovery.Merge(Save->Minimap);
        else UE_LOG(LogTemp,Warning,TEXT("Minimap could not restore supported exploration from %s; existing file will be preserved."),*SaveSlotName);
    }
    RebuildCache();
}

void UMinimapExplorationSubsystem::RebuildCache()
{
    CellCache.Reset(); UnlockedCache.Reset();
    for(const FName Region:Discovery.UnlockedRegions)UnlockedCache.Add(Region);
    for(const FMinimapExploredFloor& Floor:Discovery.Floors)
    {
        auto& Cells=CellCache.FindOrAdd({Floor.RegionId,Floor.FloorId,Floor.CellSize});
        for(const FIntPoint Cell:Floor.Cells)Cells.Add(Cell);
    }
}

void UMinimapExplorationSubsystem::RevealCells(FName Region,FName Floor,int32 CellSize,const TArray<FIntPoint>& Cells)
{
    if(Region.IsNone() || Floor.IsNone() || CellSize<=0 || Cells.IsEmpty() || IsRegionUnlocked(Region))return;
    auto& Known=CellCache.FindOrAdd({Region,Floor,CellSize});
    FMinimapExploredFloor* Record=nullptr;
    for(const FIntPoint Cell:Cells)
    {
        if(Known.Contains(Cell))continue;
        if(!Record)
        {
            Record=Discovery.Floors.FindByPredicate([&](const FMinimapExploredFloor& Row)
            {return Row.RegionId==Region && Row.FloorId==Floor && Row.CellSize==CellSize;});
            if(!Record){Record=&Discovery.Floors.AddDefaulted_GetRef();Record->RegionId=Region;Record->FloorId=Floor;Record->CellSize=CellSize;}
        }
        Known.Add(Cell); Record->Cells.Add(Cell); bDirty=true;
    }
}

bool UMinimapExplorationSubsystem::IsRevealed(FName Region,FName Floor,int32 CellSize,FIntPoint Cell) const
{
    if(Region.IsNone() || Floor.IsNone() || CellSize<=0)return false;
    if(IsRegionUnlocked(Region))return true;
    const auto* Known=CellCache.Find({Region,Floor,CellSize});
    return Known && Known->Contains(Cell);
}

bool UMinimapExplorationSubsystem::IsRegionUnlocked(FName Region) const
{
    return !Region.IsNone() && UnlockedCache.Contains(Region);
}

void UMinimapExplorationSubsystem::UnlockRegion(FName Region)
{
    if(Region.IsNone() || IsRegionUnlocked(Region))return;
    UnlockedCache.Add(Region); Discovery.UnlockedRegions.Add(Region); bDirty=true;
}

void UMinimapExplorationSubsystem::MergeIntoSave(UConstellationSaveGame* Save) const
{
    if(Save)Save->Minimap.Merge(Discovery);
}

bool UMinimapExplorationSubsystem::Flush()
{
    if(!bDirty)return true;
    UConstellationSaveGame* Save=nullptr;
    if(UGameplayStatics::DoesSaveGameExist(SaveSlotName,0))
    {
        Save=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName,0));
        if(!Save || Save->Minimap.Version!=1)
        {
            UE_LOG(LogTemp,Error,TEXT("Minimap save aborted: existing slot %s is unreadable or has unsupported exploration version."),*SaveSlotName);
            return false;
        }
    }
    else Save=NewObject<UConstellationSaveGame>();
    MergeIntoSave(Save);
    if(!UGameplayStatics::SaveGameToSlot(Save,SaveSlotName,0))
    {
        UE_LOG(LogTemp,Error,TEXT("Minimap save failed: %s"),*SaveSlotName);return false;
    }
    Discovery.Merge(Save->Minimap); RebuildCache(); bDirty=false; DirtySeconds=0;
    return true;
}

void UMinimapExplorationSubsystem::TickFlush(float DeltaSeconds)
{
    if(!bDirty || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds<=0)return;
    DirtySeconds+=DeltaSeconds;
    if(DirtySeconds>=15.f){DirtySeconds=0;Flush();}
}

void UMinimapExplorationSubsystem::Deinitialize()
{
    Flush(); Super::Deinitialize();
}
