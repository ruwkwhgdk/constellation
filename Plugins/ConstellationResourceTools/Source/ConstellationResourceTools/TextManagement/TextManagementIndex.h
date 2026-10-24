#pragma once
#include "CoreMinimal.h"
#include "AssetRegistry/AssetData.h"
#include "Engine/DataTable.h"
class UBlueprint;
class USceneDirectorAsset;

namespace ConstellationText
{
enum class ELocationKind : uint8 { Asset, DataTable, StringTable, Director, BlueprintNode };
enum class EReferenceKind : uint8 { Exact, Dynamic, Candidate, Broken };
struct FLocation
{
    ELocationKind Kind = ELocationKind::Asset;
    FSoftObjectPath Asset;
    FSoftObjectPath Event;
    FName Row;
    FString Key;
    FString Field;
    FGuid Node;
    FName Choice;
    FString Id() const;
    FString Label() const;
};
struct FEntry
{
    FLocation Location;
    FLocation Origin;
    FString Source;
    FString Display;
    FString Context;
    bool bShadowed = false;
};
struct FUsage
{
    FLocation Source;
    FLocation Consumer;
    EReferenceKind Kind = EReferenceKind::Exact;
    FString Reason;
};
struct FCoverage
{
    FString Asset;
    FString State;
    FString Reason;
};
class FIndex
{
public:
    TArray<TSharedPtr<FEntry>> Entries;
    TArray<FUsage> Usages;
    TArray<FCoverage> Coverage;
    void Collect(UObject* Object);
    void Start();
    bool Tick();
    void Cancel();
    bool IsScanning() const { return Cursor < Queue.Num(); }
    int32 Pending() const { return Queue.Num()-Cursor; }
    TArray<FUsage> FindUsages(const FEntry& Entry) const;
    static bool Matches(const FEntry& Entry, const FString& Query);
    void AddText(const FText& Text, const FLocation& Location, const FString& Context, bool bShadowed=false);
    void AddRow(const FDataTableRowHandle& Handle, const FLocation& Consumer, const FText& Direct, bool bSpeaker=false);
    void CollectProperties(const UStruct* Type, const void* Data, const FLocation& Base, int32 Depth=0);
    void CollectBlueprint(UBlueprint* Blueprint);
    void CollectDirector(USceneDirectorAsset* Director, const FSoftObjectPath& Root);
    void CollectGameRules(UObject* Object, const FLocation& Base);
private:
    TArray<FAssetData> Queue;
    int32 Cursor=0;
    TSet<FString> Visited;
};
FString ReferenceLabel(EReferenceKind Kind);
bool Navigate(const FLocation& Location, FText& Message);
void RegisterTextManagement();
void UnregisterTextManagement();
}
