#include "SDirectorQTE.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Misc/AutomationTest.h"

namespace
{
/** Deterministic platform state; the real widget event and geometry code remains under test. */
class STestDirectorQTE : public SDirectorQTE
{
public:
    SLATE_BEGIN_ARGS(STestDirectorQTE) : _InitiallyHeld(false) {}
        SLATE_ARGUMENT(FDirectorQTESettings, Settings)
        SLATE_ARGUMENT(bool, InitiallyHeld)
        SLATE_EVENT(FOnDirectorQTECompleted, OnCompleted)
    SLATE_END_ARGS()
    void Construct(const FArguments& Args)
    {
        bPhysicalHeld = Args._InitiallyHeld;
        SDirectorQTE::Construct(SDirectorQTE::FArguments().Settings(Args._Settings).OnCompleted(Args._OnCompleted));
    }
    bool bPhysicalHeld = false;
    bool bApplicationActive = true;
protected:
    virtual bool IsApplicationActive() const override { return bApplicationActive; }
    virtual bool IsLeftMouseDown() const override { return bPhysicalHeld; }
};

FPointerEvent Pointer(const FGeometry& G, FVector2D Local, bool bDown)
{
    const FVector2D Absolute = G.LocalToAbsolute(Local);
    TSet<FKey> Buttons;
    if (bDown) Buttons.Add(EKeys::LeftMouseButton);
    return FPointerEvent(0, Absolute, Absolute, Buttons, EKeys::LeftMouseButton, 0, FModifierKeysState());
}

TSharedRef<STestDirectorQTE> Prompt(const FDirectorQTESettings& Settings, int32& Callbacks,
    bool bInitiallyHeld = false)
{
    return SNew(STestDirectorQTE).Settings(Settings).InitiallyHeld(bInitiallyHeld)
        .OnCompleted(FOnDirectorQTECompleted::CreateLambda([&Callbacks](EDirectorQTEOutcome) { ++Callbacks; }));
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTESlateClickTest, "Constellation.SceneDirector.QTE.Slate.ClickEvents",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTESlateClickTest::RunTest(const FString&)
{
    if (!FSlateApplication::IsInitialized()) { AddError(TEXT("Slate must be initialized")); return false; }
    FDirectorQTESettings Settings;
    Settings.Type = EDirectorQTEType::RepeatClick;
    Settings.ClickTarget = 2;
    Settings.AppearanceDuration = 0;
    const FGeometry G = FGeometry::MakeRoot(FVector2D(1000, 800), FSlateLayoutTransform());
    int32 Callbacks = 0;
    auto Widget = Prompt(Settings, Callbacks, true);
    Widget->Tick(G, 0, 0);
    const FVector2D Origin = Widget->GetPromptOrigin();
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Initially held mouse cannot count"), Widget->GetState().GetClickCount(), 0);
    Widget->bPhysicalHeld = false;
    Widget->OnMouseButtonUp(G, Pointer(G, Origin, false));
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Repeated down without release counts once"), Widget->GetState().GetClickCount(), 1);
    Widget->OnMouseButtonUp(G, Pointer(G, Origin, false));
    Widget->OnMouseButtonDoubleClick(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Slate double-click event is the second independent press"), Callbacks, 1);
    TestTrue(TEXT("Two presses succeed"), Widget->GetState().GetOutcome() == EDirectorQTEOutcome::Success);
    Widget->Cancel();
    Widget->OnMouseButtonDoubleClick(G, Pointer(G, Origin, true));
    Widget->Tick(G, 1, 1);
    TestEqual(TEXT("Retirement and cancellation cannot repeat callback"), Callbacks, 1);
    TestTrue(TEXT("Retirement finishes"), Widget->IsRetired());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTESlatePauseTest, "Constellation.SceneDirector.QTE.Slate.PauseAndEscape",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTESlatePauseTest::RunTest(const FString&)
{
    if (!FSlateApplication::IsInitialized()) { AddError(TEXT("Slate must be initialized")); return false; }
    FDirectorQTESettings Settings;
    Settings.AppearanceDuration = 0;
    const FGeometry G = FGeometry::MakeRoot(FVector2D(1000, 800), FSlateLayoutTransform());
    int32 Callbacks = 0;
    auto Widget = Prompt(Settings, Callbacks);
    Widget->Tick(G, 0, 0);
    const FVector2D Origin = Widget->GetPromptOrigin();
    const FKeyEvent Escape(EKeys::Escape, FModifierKeysState(), 0, false, 0, 0);
    TestFalse(TEXT("Escape propagates to existing host stop policy"), Widget->OnKeyDown(G, Escape).IsEventHandled());
    TestEqual(TEXT("Escape is not a QTE failure"), Callbacks, 0);
    Widget->SetPaused(true);
    Widget->Tick(G, 10, 10);
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Paused input does not complete"), Callbacks, 0);
    TestEqual(TEXT("Pause freezes deadline"), Widget->GetState().GetRemainingFraction(), 1.f);
    Widget->bPhysicalHeld = true;
    Widget->SetPaused(false);
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Held button through resume is blocked"), Callbacks, 0);
    Widget->bPhysicalHeld = false;
    Widget->OnMouseButtonUp(G, Pointer(G, Origin, false));
    Widget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Fresh press after pause succeeds once"), Callbacks, 1);

    int32 FocusCallbacks = 0;
    auto FocusWidget = Prompt(Settings, FocusCallbacks);
    FocusWidget->Tick(G, 0, 0);
    FocusWidget->bApplicationActive = false;
    FocusWidget->Tick(G, 20, 20);
    TestTrue(TEXT("Application deactivation freezes state"), FocusWidget->GetState().IsPaused());
    FocusWidget->bApplicationActive = true;
    FocusWidget->Tick(G, 20, 0);
    FocusWidget->OnMouseButtonDown(G, Pointer(G, Origin, true));
    TestEqual(TEXT("Mouse already released while inactive needs no extra dummy click"), FocusCallbacks, 1);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTESlateGeometryTest, "Constellation.SceneDirector.QTE.Slate.ResizeAndDPI",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTESlateGeometryTest::RunTest(const FString&)
{
    if (!FSlateApplication::IsInitialized()) { AddError(TEXT("Slate must be initialized")); return false; }
    FDirectorQTESettings Settings;
    Settings.Type = EDirectorQTEType::DirectionDrag;
    Settings.AppearanceDuration = 0;
    Settings.DragDistance = 100;
    Settings.DragDirection = FVector2D(1, 0);
    const FGeometry Initial = FGeometry::MakeRoot(FVector2D(1000, 800), FSlateLayoutTransform());
    const FGeometry Resized = FGeometry::MakeRoot(FVector2D(1500, 900),
        FSlateLayoutTransform(2.f, FVector2D(37, 51)));
    int32 Callbacks = 0;
    auto Widget = Prompt(Settings, Callbacks);
    Widget->Tick(Initial, 0, 0);
    const FVector2D Origin = Widget->GetPromptOrigin();
    Widget->bPhysicalHeld = true;
    Widget->OnMouseButtonDown(Initial, Pointer(Initial, Origin, true));
    Widget->OnMouseMove(Initial, Pointer(Initial, Origin + FVector2D(40, 0), true));
    TestTrue(TEXT("Initial gesture has progress"), Widget->GetState().GetProgress() > 0);
    Widget->OnMouseMove(Resized, Pointer(Resized, Origin + FVector2D(110, 0), true));
    TestEqual(TEXT("Layout change cannot become phantom completion"), Callbacks, 0);
    TestTrue(TEXT("Local anchor remains fixed through resize and DPI"), Origin.Equals(Widget->GetPromptOrigin()));
    TestFalse(TEXT("Layout change invalidates active drag"), Widget->GetState().IsDragging());
    Widget->OnMouseButtonDown(Resized, Pointer(Resized, Origin, true));
    TestFalse(TEXT("Held button cannot restart invalidated gesture"), Widget->GetState().IsDragging());
    Widget->bPhysicalHeld = false;
    Widget->OnMouseButtonUp(Resized, Pointer(Resized, Origin, false));
    Widget->bPhysicalHeld = true;
    Widget->OnMouseButtonDown(Resized, Pointer(Resized, Origin, true));
    Widget->OnMouseMove(Resized, Pointer(Resized, Origin + FVector2D(101, 0), true));
    TestEqual(TEXT("New geometry converts physical input back to matching local art"), Callbacks, 1);
    Widget->Cancel();
    TestEqual(TEXT("Cancel after result cannot duplicate callback"), Callbacks, 1);
    return true;
}
#endif
