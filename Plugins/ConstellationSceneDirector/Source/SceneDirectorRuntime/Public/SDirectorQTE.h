#pragma once

#include "DirectorQTE.h"
#include "Widgets/SLeafWidget.h"

DECLARE_DELEGATE_OneParam(FOnDirectorQTECompleted, EDirectorQTEOutcome);
DECLARE_DELEGATE_RetVal_TwoParams(FReply, FOnDirectorQTEKey, const FKeyEvent&, bool);

/** Transparent, viewport-sized input surface. All art and hit tests share Slate local units. */
class SCENEDIRECTORRUNTIME_API SDirectorQTE : public SLeafWidget
{
public:
    SLATE_BEGIN_ARGS(SDirectorQTE) {}
        SLATE_ARGUMENT(FDirectorQTESettings, Settings)
        SLATE_EVENT(FOnDirectorQTECompleted, OnCompleted)
        SLATE_EVENT(FOnDirectorQTEKey, OnDirectorKey)
    SLATE_END_ARGS()

    void Construct(const FArguments& Args);
    void SetPaused(bool bPaused);
    void Cancel();
    const FDirectorQTEState& GetState() const { return *State; }
    FVector2D GetPromptOrigin() const { return PromptOrigin; }
    bool IsRetired() const { return bReported && RetirementElapsed >= RetirementDuration; }
    virtual bool SupportsKeyboardFocus() const override { return true; }
    virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D::ZeroVector; }
    virtual void Tick(const FGeometry& Geometry, double CurrentTime, float DeltaTime) override;
    virtual int32 OnPaint(const FPaintArgs&, const FGeometry&, const FSlateRect&,
        FSlateWindowElementList&, int32 Layer, const FWidgetStyle&, bool) const override;
    virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override;
    virtual FReply OnMouseButtonDoubleClick(const FGeometry&, const FPointerEvent&) override;
    virtual FReply OnMouseButtonUp(const FGeometry&, const FPointerEvent&) override;
    virtual FReply OnMouseMove(const FGeometry&, const FPointerEvent&) override;
    virtual FReply OnMouseWheel(const FGeometry&, const FPointerEvent&) override;
    virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent&) override;
    virtual FReply OnKeyUp(const FGeometry&, const FKeyEvent&) override;
    virtual FReply OnKeyChar(const FGeometry&, const FCharacterEvent&) override;
    virtual FReply OnFocusReceived(const FGeometry&, const FFocusEvent&) override;
    virtual void OnFocusLost(const FFocusEvent&) override;
    virtual void OnMouseCaptureLost(const FCaptureLostEvent&) override;

protected:
    virtual bool IsApplicationActive() const;
    virtual bool IsLeftMouseDown() const;

private:
    void UpdatePause();
    void UpdateGeometry(const FGeometry&);
    void ReportOutcome();
    FVector2D PointerPosition(const FGeometry&, const FPointerEvent&) const;
    TUniquePtr<FDirectorQTEState> State;
    FOnDirectorQTECompleted OnCompleted;
    FOnDirectorQTEKey OnDirectorKey;
    // ScreenPosition is copied at construction; editing a node cannot move an active prompt.
    FVector2D ScreenPosition = FVector2D(.5, .65);
    FVector2D PromptOrigin = FVector2D::ZeroVector;
    FVector2D PreviousSize = FVector2D::ZeroVector;
    FVector2D PreviousAbsoluteOrigin = FVector2D::ZeroVector;
    float PreviousScale = 1;
    bool bGeometryInitialized = false;
    bool bExplicitlyPaused = false;
    bool bFocusLost = false;
    bool bReported = false;
    float VisualElapsed = 0;
    float RetirementElapsed = 0;
    float RetirementDuration = 0;
};
