#include "DirectorQTE.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEClickTest, "Constellation.SceneDirector.QTE.ClickFreshness",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTEClickTest::RunTest(const FString& Parameters)
{
    FDirectorQTESettings S;
    S.AppearanceDuration = .25f;
    FDirectorQTEState State(S, true);
    State.Tick(.25);
    State.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Held input from previous prompt is ignored"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    State.Release(FVector2D::ZeroVector);
    State.Press(FVector2D::ZeroVector);
    State.Cancel();
    State.Tick(20);
    TestTrue(TEXT("Success remains latched through cancel and timeout"), State.GetOutcome() == EDirectorQTEOutcome::Success);

    FDirectorQTEState Early(S);
    Early.Press(FVector2D::ZeroVector);
    Early.Tick(.25);
    Early.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Press during appearance cannot become a ready press"), Early.GetOutcome() == EDirectorQTEOutcome::Pending);
    Early.Release(FVector2D::ZeroVector);
    Early.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Fresh ready press succeeds"), Early.GetOutcome() == EDirectorQTEOutcome::Success);

    S.AppearanceDuration = 0;
    S.Type = EDirectorQTEType::RepeatClick;
    S.ClickTarget = 3;
    FDirectorQTEState Repeat(S);
    Repeat.Press(FVector2D::ZeroVector);
    Repeat.Press(FVector2D::ZeroVector);
    Repeat.Move(FVector2D(1,1));
    TestEqual(TEXT("Held repeats only count once"), Repeat.GetClickCount(), 1);
    Repeat.Release(FVector2D::ZeroVector);
    Repeat.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Below target is pending"), Repeat.GetOutcome() == EDirectorQTEOutcome::Pending);
    Repeat.Release(FVector2D::ZeroVector);
    Repeat.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Third independent press succeeds"), Repeat.GetOutcome() == EDirectorQTEOutcome::Success);
    S.bAnywhere = true;
    S.Type = EDirectorQTEType::SingleClick;
    FDirectorQTEState Anywhere(S);
    Anywhere.Press(FVector2D(10000,10000));
    TestTrue(TEXT("Anywhere option works for clicks"), Anywhere.GetOutcome() == EDirectorQTEOutcome::Success);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEClockTest, "Constellation.SceneDirector.QTE.ClockAndCancellation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTEClockTest::RunTest(const FString& Parameters)
{
    FDirectorQTESettings S;
    S.AppearanceDuration = .25f;
    S.TimeLimit = 1;
    FDirectorQTEState State(S);
    State.Tick(.25);
    TestEqual(TEXT("Appearance consumes no active time"), State.GetRemainingFraction(), 1.f);
    State.Tick(.5);
    State.SetPaused(true);
    State.Tick(200);
    State.Press(FVector2D::ZeroVector);
    TestEqual(TEXT("Pause freezes timer"), State.GetRemainingFraction(), .5f);
    TestTrue(TEXT("Pause freezes input"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    State.SetPaused(false);
    State.Release(FVector2D::ZeroVector);
    State.Tick(.5);
    State.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Expiry wins at exact boundary"), State.GetOutcome() == EDirectorQTEOutcome::Failure);
    State.Cancel();
    TestTrue(TEXT("Cancel cannot override failure"), State.GetOutcome() == EDirectorQTEOutcome::Failure);

    FDirectorQTEState Cancelled(S);
    Cancelled.Cancel();
    Cancelled.Tick(100);
    Cancelled.Press(FVector2D::ZeroVector);
    TestTrue(TEXT("Cancellation is distinct and terminal"), Cancelled.GetOutcome() == EDirectorQTEOutcome::Cancelled);

    FDirectorQTEState Overshoot(S);
    Overshoot.Tick(.75);
    TestEqual(TEXT("A tick crossing appearance only consumes leftover time"), Overshoot.GetRemainingFraction(), .5f);
    Overshoot.Tick(-1);
    Overshoot.Tick(std::numeric_limits<double>::quiet_NaN());
    TestEqual(TEXT("Invalid deltas do not corrupt time"), Overshoot.GetRemainingFraction(), .5f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEDragTest, "Constellation.SceneDirector.QTE.DragRetries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTEDragTest::RunTest(const FString& Parameters)
{
    FDirectorQTESettings S;
    S.AppearanceDuration = 0;
    S.Type = EDirectorQTEType::DirectionDrag;
    S.bTimed = false;
    S.bFailOnMistake = true;
    S.DragDistance = 100;
    FDirectorQTEState State(S);
    State.Press(FVector2D::ZeroVector);
    State.Move(FVector2D(110,0));
    TestTrue(TEXT("Unlimited mode overrides fail-on-mistake"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    TestFalse(TEXT("Wrong direction resets attempt"), State.IsDragging());
    State.Release(FVector2D(110,0));
    State.Press(FVector2D::ZeroVector);
    State.Move(FVector2D(-30,0));
    State.Release(FVector2D(-30,0));
    TestTrue(TEXT("Early release retries"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    TestEqual(TEXT("Retry resets progress"), State.GetProgress(), 0.f);
    State.Tick(100000);
    State.Press(FVector2D::ZeroVector);
    State.Move(FVector2D(-100,20));
    TestTrue(TEXT("Directional tolerance permits non-exact-line success"), State.GetOutcome() == EDirectorQTEOutcome::Success);
    S.bTimed = true;
    FDirectorQTEState Strict(S);
    Strict.Press(FVector2D::ZeroVector);
    Strict.Release(FVector2D::ZeroVector);
    TestTrue(TEXT("Timed explicit mistake policy fails"), Strict.GetOutcome() == EDirectorQTEOutcome::Failure);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTETraceTest, "Constellation.SceneDirector.QTE.TraceOrder",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTETraceTest::RunTest(const FString& Parameters)
{
    FDirectorQTESettings S;
    S.AppearanceDuration = 0;
    S.Type = EDirectorQTEType::TracePath;
    S.bTimed = false;
    S.Path = { FVector2D(0,0), FVector2D(100,0), FVector2D(100,100) };
    S.PathTolerance = 20;
    FDirectorQTEState State(S);
    State.Press(S.Path[0]);
    State.Move(S.Path.Last());
    TestTrue(TEXT("Endpoint teleport cannot succeed"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    TestFalse(TEXT("Teleport resets attempt"), State.IsDragging());
    State.Release(S.Path.Last());
    State.Press(S.Path[0]);
    State.Move(FVector2D(0,30));
    TestFalse(TEXT("Large corridor departure resets attempt"), State.IsDragging());
    State.Release(FVector2D(0,30));
    State.Press(S.Path[0]);
    for (int32 X = 10; X <= 100; X += 10) State.Move(FVector2D(X,0));
    TestTrue(TEXT("Corner is not completion"), State.GetOutcome() == EDirectorQTEOutcome::Pending);
    for (int32 Y = 10; Y <= 100; Y += 10) State.Move(FVector2D(100,Y));
    TestTrue(TEXT("Ordered traversal succeeds"), State.GetOutcome() == EDirectorQTEOutcome::Success);

    S.Path = { FVector2D(0,0), FVector2D(25,0) };
    FDirectorQTEState Short(S);
    Short.Press(S.Path[0]);
    Short.Move(S.Path.Last());
    TestFalse(TEXT("Short-path endpoint jump also resets"), Short.IsDragging());
    TestTrue(TEXT("Short-path teleport remains pending"), Short.GetOutcome() == EDirectorQTEOutcome::Pending);
    S.Path = { FVector2D(0,0), FVector2D(200,0) };
    FDirectorQTEState Offset(S);
    Offset.Press(FVector2D(0,10));
    for (int32 X = 10; X <= 200; X += 10) Offset.Move(FVector2D(X,10));
    TestTrue(TEXT("Parallel trace at half tolerance succeeds including offset endpoint"), Offset.GetOutcome() == EDirectorQTEOutcome::Success);

    S.Path = { FVector2D(0,0), FVector2D(100,0), FVector2D(100,100), FVector2D(0,100), FVector2D(0,10) };
    FDirectorQTEState Loop(S);
    Loop.Press(S.Path[0]);
    Loop.Move(S.Path.Last());
    TestTrue(TEXT("Nearby later endpoint cannot bypass unvisited loop"), Loop.GetOutcome() == EDirectorQTEOutcome::Pending);
    TestTrue(TEXT("Nearby endpoint does not advance later arc"), Loop.GetProgress() < .1f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorQTEValidationTest, "Constellation.SceneDirector.QTE.Validation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorQTEValidationTest::RunTest(const FString& Parameters)
{
    FString Error;
    FDirectorQTESettings S;
    TestTrue(TEXT("Defaults valid"), S.Validate(Error));
    S.Type = EDirectorQTEType::TracePath;
    TestTrue(TEXT("Default smooth trace valid"), S.Validate(Error));
    S.Path = { FVector2D(0,0), FVector2D(0,0) };
    TestFalse(TEXT("Degenerate trace rejected"), S.Validate(Error));
    FDirectorQTEState Invalid(S);
    TestTrue(TEXT("Invalid settings cancel safely"), Invalid.GetOutcome() == EDirectorQTEOutcome::Cancelled);
    S = FDirectorQTESettings();
    S.ScreenPosition.X = std::numeric_limits<double>::infinity();
    TestFalse(TEXT("Infinite coordinates rejected"), S.Validate(Error));
    S = FDirectorQTESettings();
    S.Type = EDirectorQTEType::DirectionDrag;
    S.DragDirection = FVector2D::ZeroVector;
    TestFalse(TEXT("Zero drag direction rejected"), S.Validate(Error));
    return true;
}
#endif
