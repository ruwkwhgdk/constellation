#pragma once
#include "TextManagementEditing.h"
namespace ConstellationText
{
struct FTextRevision
{
    FString Id,TargetId,Time,Before,After,State,RestoredFrom;
};
struct FTextDraft
{
    FEditSnapshot Base;
    FString Text;
    FString PendingId;
    FString RestoredFrom;
    bool IsDirty()const{return Text!=Base.Source||!PendingId.IsEmpty();}
};
TArray<FTextRevision> ReadTextHistory(const FString& Directory,const FString& TargetId);
// Saver is an explicit I/O boundary: production passes SaveEdit; tests can simulate cancellation.
bool CommitTextDraft(FTextDraft& Draft,const FString& Directory,FText& Message,TFunctionRef<bool(const FLocation&,FText&)> Saver);
bool StageTextRestore(FTextDraft& Draft,const FTextRevision& Revision,FText& Message,bool bBefore=true);
}
