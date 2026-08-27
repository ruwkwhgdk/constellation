// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestDefinition.h"

FText UQuestDefinition::FindEndingText(FName EndingID) const
{
	for (const FQuestEndingDef& Ending : PossibleEndings)
	{
		if (Ending.EndingID == EndingID)
		{
			return Ending.EndingDescription;
		}
	}
	return FText::GetEmpty();
}
