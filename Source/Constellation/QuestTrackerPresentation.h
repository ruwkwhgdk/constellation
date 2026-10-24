#pragma once
#include "QuestTypes.h"

namespace QuestTrackerPresentation
{
 inline FText QuantityText(const FQuestDisplayInfo& Info)
 {
  if(!Info.bVisible||Info.State!=EQuestState::Progressed||!Info.bShowObjectiveQuantity||Info.MaxInnerProgress<=0)
   return FText::GetEmpty();
  return FText::Format(NSLOCTEXT("QuestTracker","ObjectiveQuantity","{0}/{1}"),
   FText::AsNumber(FMath::Clamp(Info.InnerProgress,0,Info.MaxInnerProgress)),FText::AsNumber(Info.MaxInnerProgress));
 }
}
