#pragma once
#include "TextManagementIndex.h"
namespace ConstellationText
{
FString SuggestedCategory(const FEntry& Entry);
FString Category(const FEntry& Entry,const FString& Filename);
bool SetCategory(const FEntry& Entry,const FString& Value,const FString& Filename,FText& Message);
struct FEditSnapshot
{
    FLocation Target;
    FText Original;
    FString Source;
};
bool ReadEdit(const FEntry& Entry,FEditSnapshot& Snapshot,FText& Message);
bool ApplyEdit(const FEditSnapshot& Snapshot,const FString& NewSource,FText& Message);
bool SaveEdit(const FLocation& Target,FText& Message);
}
