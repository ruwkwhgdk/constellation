#pragma once
#include "TextManagementHistory.h"
namespace ConstellationText
{
TArray<FString> DialogueFields(UDataTable* Table);
bool CreateDialogueDraft(UDataTable* Table,const FString& Key,const FString& Field,const FString& Content,FTextDraft& Draft,FText& Message);
bool ShowCreateDialogue(UDataTable* Initial,FTextDraft& Draft,FText& Message);
}
