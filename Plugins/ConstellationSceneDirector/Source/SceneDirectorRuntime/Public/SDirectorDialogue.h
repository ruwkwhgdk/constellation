#pragma once
#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Styling/SlateStyle.h"
#include "SDirectorChoices.h"
#include "SceneDirectorAsset.h"
#include "DirectorDialogueReveal.h"
class UTexture2D;

// Shared by the game viewport and the sequence preview. Textures are owned by the player/CDO.
class SCENEDIRECTORRUNTIME_API SDirectorDialogue : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SDirectorDialogue) : _Position(EDirectorDialoguePosition::Bottom) {}
        SLATE_ATTRIBUTE(EDirectorDialoguePosition, Position)
        SLATE_ATTRIBUTE(FText, Speaker)
        SLATE_ATTRIBUTE(FText, Dialogue)
        SLATE_ATTRIBUTE(float, CharacterInterval)
        SLATE_ATTRIBUTE(float, RevealDuration)
        SLATE_ATTRIBUTE(bool, Waiting)
        SLATE_ARGUMENT(UTexture2D*, Background)
        SLATE_ARGUMENT(UTexture2D*, Continue)
        SLATE_ARGUMENT(UTexture2D*, SpeakerBackground)
        SLATE_ARGUMENT(FDirectorChoiceStyle, ChoiceStyle)
        SLATE_ATTRIBUTE(TArray<FDirectorChoice>, Choices)
        SLATE_ATTRIBUTE(FGuid, ChoicePrompt)
        SLATE_EVENT(FOnDirectorChoice, OnChoice)
        SLATE_EVENT(FSimpleDelegate, OnAdvance)
        SLATE_EVENT(FSimpleDelegate, OnTextTick)
    SLATE_END_ARGS()
    void Construct(const FArguments& Args);
    bool FinishReveal();
    void MoveChoice(int32 Direction){if(ChoiceList)ChoiceList->MoveFocus(Direction);}
    void ConfirmChoice(){if(ChoiceList)ChoiceList->Confirm();}
    virtual void Tick(const FGeometry&, double CurrentTime, float DeltaTime) override;
    virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override;
private:
    virtual bool CustomPrepass(float LayoutScaleMultiplier) override;
    TAttribute<EDirectorDialoguePosition> Position;
    TAttribute<FText> Dialogue;
    TAttribute<float> CharacterInterval,RevealDuration;
    TAttribute<FGuid> Prompt;
    FGuid LastPrompt;
    FText LastDialogue;
    FDirectorDialogueReveal Reveal;
    FSimpleDelegate TextTick;
    void RefreshDialogue();
    TAttribute<TArray<FDirectorChoice>> Choices;
    TSharedPtr<SDirectorChoices> ChoiceList;
    TAttribute<bool> Waiting;
    FSimpleDelegate Advance;
    FSlateBrush BackgroundBrush, ArrowBrush, SpeakerBrush;
    TSharedPtr<SWidget> Arrow;
    TSharedPtr<FSlateStyleSet> TextStyles;
    double ArrowTime=0;
};
