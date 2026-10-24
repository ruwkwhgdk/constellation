#pragma once
#include "TextManagementIndex.h"
namespace ConstellationText
{
struct FTextItem
{
    TSharedPtr<FEntry> Entry;
    FString Key;
    TArray<FLocation> Locations;
    TArray<FUsage> Usages;
    TArray<FString> Groups;
};
FString UsageGroup(const FLocation& Location);
FString DisplayKey(const FLocation& Location);
TArray<TSharedPtr<FTextItem>> BuildTextItems(const FIndex& Index,bool bIncludeExamples=false,bool bIncludeHidden=false);
}
