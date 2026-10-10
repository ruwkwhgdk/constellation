#pragma once
#include "Widgets/SCompoundWidget.h"
#include "SceneDirectorVision.h"
class SCENEDIRECTORRUNTIME_API SDirectorVision : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SDirectorVision){} SLATE_ATTRIBUTE(FDirectorVisionState,State) SLATE_END_ARGS()
 void Construct(const FArguments& Args);
private:
 TAttribute<FDirectorVisionState> State;
};
