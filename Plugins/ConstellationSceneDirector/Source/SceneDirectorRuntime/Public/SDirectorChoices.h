#pragma once
#include "CoreMinimal.h"
#include "SceneDirectorChoice.h"
#include "Widgets/SCompoundWidget.h"
DECLARE_DELEGATE_OneParam(FOnDirectorChoice,FName);
class SVerticalBox;
class SCENEDIRECTORRUNTIME_API SDirectorChoices : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SDirectorChoices) {}
        SLATE_ARGUMENT(FDirectorChoiceStyle, Style)
        SLATE_ATTRIBUTE(TArray<FDirectorChoice>, Options)
        SLATE_ATTRIBUTE(FGuid, PromptId)
        SLATE_ATTRIBUTE(bool, CanChoose)
        SLATE_EVENT(FOnDirectorChoice, OnChosen)
    SLATE_END_ARGS()
    void Construct(const FArguments& Args);
    virtual void Tick(const FGeometry&,double,float) override;
    void Refresh();
    void MoveFocus(int32 Direction);
    bool Confirm();
    bool Choose(int32 Index);
    int32 GetFocusedIndex()const{return FocusedIndex;}
    bool IsCommitted()const{return bCommitted;}
    virtual bool SupportsKeyboardFocus()const override{return true;}
    virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent&)override;
private:
    TAttribute<TArray<FDirectorChoice>> Options;
    TAttribute<FGuid> PromptId;
    TAttribute<bool> CanChoose;
    TArray<FDirectorChoice> Current;
    FGuid CurrentPrompt;
    FOnDirectorChoice Chosen;
    TSharedPtr<SVerticalBox> Rows;
    FSlateBrush FocusBG,FocusStroke,IdleBG,IdleStroke,Cursor;
    FButtonStyle ButtonStyle;
    int32 FocusedIndex=0;
    bool bCommitted=false,bInitialized=false;
    void Rebuild();
};
