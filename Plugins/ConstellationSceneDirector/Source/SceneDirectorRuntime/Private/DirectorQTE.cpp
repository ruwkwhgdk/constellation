#include "DirectorQTE.h"

namespace
{
bool Finite(const FVector2D& V) { return FMath::IsFinite(V.X) && FMath::IsFinite(V.Y); }
}

bool FDirectorQTESettings::Validate(FString& OutError) const
{
    OutError.Reset();
    if (static_cast<uint8>(Type) > static_cast<uint8>(EDirectorQTEType::TracePath) ||
        static_cast<uint8>(ScenePolicy) > static_cast<uint8>(EDirectorQTEScenePolicy::Continue))
        OutError = TEXT("Unknown QTE type or scene policy.");
    else if (!Finite(ScreenPosition) || ScreenPosition.X < 0 || ScreenPosition.X > 1 || ScreenPosition.Y < 0 || ScreenPosition.Y > 1)
        OutError = TEXT("Screen position must be finite normalized coordinates.");
    else if (!FMath::IsFinite(AppearanceDuration) || AppearanceDuration < 0 ||
        !FMath::IsFinite(TimeLimit) || (bTimed && TimeLimit <= 0) ||
        !FMath::IsFinite(HitRadius) || HitRadius <= 0)
        OutError = TEXT("Appearance, timer and hit radius must be finite and valid.");
    else if (Type == EDirectorQTEType::RepeatClick && ClickTarget < 1)
        OutError = TEXT("Repeat click target must be positive.");
    else if (Type == EDirectorQTEType::DirectionDrag &&
        (!Finite(DragDirection) || !FMath::IsFinite(DragDirection.SizeSquared()) || DragDirection.SizeSquared() < UE_DOUBLE_SMALL_NUMBER ||
        !FMath::IsFinite(DragDistance) || DragDistance <= 0 ||
        !FMath::IsFinite(AngleToleranceDegrees) || AngleToleranceDegrees < 0 || AngleToleranceDegrees > 90))
        OutError = TEXT("Drag direction, distance or angle is invalid.");
    else if (Type == EDirectorQTEType::TracePath)
    {
        if (!FMath::IsFinite(PathTolerance) || PathTolerance < 1 || Path.Num() < 2 || Path.Num() > 4096)
            OutError = TEXT("Trace needs at least two samples and a finite tolerance of at least one unit.");
        else
        {
            double Length = 0;
            for (int32 I = 0; I < Path.Num(); ++I)
            {
                if (!Finite(Path[I])) { OutError = TEXT("Trace coordinates must be finite."); break; }
                if (I > 0)
                {
                    const double Segment = FVector2D::Distance(Path[I - 1], Path[I]);
                    if (!FMath::IsFinite(Segment) || Segment < UE_DOUBLE_SMALL_NUMBER)
                    { OutError = TEXT("Trace contains a degenerate segment."); break; }
                    Length += Segment;
                }
            }
            if (OutError.IsEmpty() && (Length <= PathTolerance || Length / (PathTolerance * .5) > 16384))
                OutError = TEXT("Trace is too short or exceeds the checkpoint budget.");
        }
    }
    return OutError.IsEmpty();
}

FDirectorQTEState::FDirectorQTEState(const FDirectorQTESettings& InSettings, bool bInitiallyHeld)
    : Settings(InSettings), bHeld(bInitiallyHeld)
{
    FString Error;
    if (!Settings.Validate(Error)) { Outcome = EDirectorQTEOutcome::Cancelled; return; }
    if (Settings.Type == EDirectorQTEType::TracePath)
    {
        Checkpoints.Add(Settings.Path[0]);
        CheckpointDistances.Add(0);
        double TotalLength = 0;
        for (int32 I = 1; I < Settings.Path.Num(); ++I)
        {
            const FVector2D A = Settings.Path[I - 1], B = Settings.Path[I];
            const double Length = FVector2D::Distance(A, B);
            TotalLength += Length;
            const int32 Count = FMath::CeilToInt(Length / (Settings.PathTolerance * .5));
            for (int32 J = 1; J <= Count; ++J)
            {
                Checkpoints.Add(FMath::Lerp(A, B, double(J) / Count));
                CheckpointDistances.Add(TotalLength - Length + Length * double(J) / Count);
            }
        }
        MaxTraceStep = FMath::Min(Settings.PathTolerance * 2., TotalLength * .2);
    }
}

void FDirectorQTEState::Tick(double DeltaSeconds)
{
    if (Outcome != EDirectorQTEOutcome::Pending || bPaused || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0) return;
    const double AppearanceRemaining = FMath::Max(0., double(Settings.AppearanceDuration) - AppearanceElapsed);
    const double AppearanceStep = FMath::Min(DeltaSeconds, AppearanceRemaining);
    AppearanceElapsed += AppearanceStep;
    Elapsed += DeltaSeconds - AppearanceStep;
    if (Settings.bTimed && Elapsed >= Settings.TimeLimit) Outcome = EDirectorQTEOutcome::Failure;
}

void FDirectorQTEState::Press(const FVector2D& Position)
{
    const bool bWasHeld = bHeld;
    bHeld = true;
    if (!IsReady() || bWasHeld) return;
    if (!Finite(Position)) { Mistake(); return; }
    const bool bClick = Settings.Type == EDirectorQTEType::SingleClick || Settings.Type == EDirectorQTEType::RepeatClick;
    const FVector2D Target = Settings.Type == EDirectorQTEType::TracePath ? Settings.Path[0] : FVector2D::ZeroVector;
    const double Radius = Settings.Type == EDirectorQTEType::TracePath ? FMath::Min(Settings.HitRadius, Settings.PathTolerance) : Settings.HitRadius;
    if (!(bClick && Settings.bAnywhere) && FVector2D::Distance(Position, Target) > Radius) { Mistake(); return; }
    if (bClick)
    {
        ++ClickCount;
        if (ClickCount >= (Settings.Type == EDirectorQTEType::SingleClick ? 1 : Settings.ClickTarget))
            Outcome = EDirectorQTEOutcome::Success;
        return;
    }
    bAttempt = true;
    Start = Last = Position;
    NextCheckpoint = 1;
    TraceDistance = 0;
    DragProgress = 0;
}

void FDirectorQTEState::Move(const FVector2D& Position)
{
    if (!IsReady() || !bHeld || !bAttempt) return;
    if (!Finite(Position)) { Mistake(); return; }
    if (Settings.Type == EDirectorQTEType::DirectionDrag)
    {
        const FVector2D Travel = Position - Start;
        const double Distance = Travel.Size();
        const double Alignment = Distance > UE_DOUBLE_SMALL_NUMBER ? FVector2D::DotProduct(Travel / Distance, Settings.DragDirection.GetSafeNormal()) : 0.;
        const bool bAligned = Alignment + UE_DOUBLE_SMALL_NUMBER >= FMath::Cos(FMath::DegreesToRadians(Settings.AngleToleranceDegrees));
        DragProgress = bAligned ? FMath::Clamp(float(Distance / Settings.DragDistance), 0.f, 1.f) : 0.f;
        if (Distance >= Settings.DragDistance)
        {
            if (bAligned) Outcome = EDirectorQTEOutcome::Success;
            else Mistake();
        }
    }
    else if (Settings.Type == EDirectorQTEType::TracePath)
    {
        // Bound per-event movement; never interpolate a teleport across unseen checkpoints.
        const double Travel = FVector2D::Distance(Last, Position);
        if (Travel > MaxTraceStep)
        { Mistake(); return; }
        // Search only a bounded, contiguous arc neighborhood. Lateral tolerance does
        // not advance progress; projection onto the ordered arc does. A crossing
        // later in the path cannot jump the unvisited arc between the two branches.
        const double MaxArc = FMath::Min(CheckpointDistances.Last(), TraceDistance + Travel * 1.5);
        double BestDistance = TNumericLimits<double>::Max();
        double BestArc = TraceDistance;
        for (int32 I = FMath::Max(1, NextCheckpoint - 6); I < Checkpoints.Num(); ++I)
        {
            const double SegmentStart = CheckpointDistances[I - 1];
            if (SegmentStart > MaxArc) break;
            const FVector2D A = Checkpoints[I - 1], AB = Checkpoints[I] - A;
            const double SegmentLength = CheckpointDistances[I] - SegmentStart;
            const double MaxT = FMath::Clamp((MaxArc - SegmentStart) / SegmentLength, 0., 1.);
            const double T = FMath::Clamp(FVector2D::DotProduct(Position - A, AB) / AB.SizeSquared(), 0., MaxT);
            const double Distance = FVector2D::Distance(Position, A + T * AB);
            const double Arc = SegmentStart + T * SegmentLength;
            if (Distance < BestDistance - UE_DOUBLE_SMALL_NUMBER ||
                (FMath::IsNearlyEqual(Distance, BestDistance) && Arc < BestArc))
            {
                BestDistance = Distance;
                BestArc = Arc;
            }
        }
        if (BestDistance > Settings.PathTolerance)
        { Mistake(); return; }
        TraceDistance = FMath::Max(TraceDistance, BestArc);
        while (NextCheckpoint < Checkpoints.Num() - 1 && CheckpointDistances[NextCheckpoint] <= TraceDistance)
            ++NextCheckpoint;
        if (TraceDistance >= CheckpointDistances.Last() - UE_DOUBLE_SMALL_NUMBER &&
            FVector2D::Distance(Position, Checkpoints.Last()) <= Settings.PathTolerance)
            Outcome = EDirectorQTEOutcome::Success;
    }
    Last = Position;
}

void FDirectorQTEState::Release(const FVector2D& Position)
{
    // A release is never a completing gesture: completion is immediate on movement.
    bHeld = false;
    if (IsReady() && bAttempt) Mistake();
    else ResetAttempt();
}

void FDirectorQTEState::ResetAttempt()
{
    bAttempt = false;
    NextCheckpoint = 1;
    TraceDistance = 0;
    DragProgress = 0;
}

void FDirectorQTEState::Mistake()
{
    ResetAttempt();
    if (Outcome == EDirectorQTEOutcome::Pending && Settings.bTimed && Settings.bFailOnMistake)
        Outcome = EDirectorQTEOutcome::Failure;
}

void FDirectorQTEState::SetPaused(bool bInPaused)
{
    if (bPaused == bInPaused) return;
    bPaused = bInPaused;
    ResetAttempt();
    // Conservatively require a release after resume; never count a hidden press.
    bHeld = true;
}

void FDirectorQTEState::Cancel()
{
    if (Outcome == EDirectorQTEOutcome::Pending) Outcome = EDirectorQTEOutcome::Cancelled;
    ResetAttempt();
}

float FDirectorQTEState::GetProgress() const
{
    if (Outcome == EDirectorQTEOutcome::Success) return 1.f;
    if (Settings.Type == EDirectorQTEType::SingleClick) return 0.f;
    if (Settings.Type == EDirectorQTEType::RepeatClick) return FMath::Clamp(float(ClickCount) / FMath::Max(1, Settings.ClickTarget), 0.f, 1.f);
    if (Settings.Type == EDirectorQTEType::DirectionDrag) return DragProgress;
    return CheckpointDistances.Num() > 1 ? float(TraceDistance / CheckpointDistances.Last()) : 0.f;
}

float FDirectorQTEState::GetRemainingFraction() const
{
    return Settings.bTimed && Settings.TimeLimit > 0 ? FMath::Clamp(float(1. - Elapsed / Settings.TimeLimit), 0.f, 1.f) : 1.f;
}

float FDirectorQTEState::GetAppearanceFraction() const
{
    return Settings.AppearanceDuration > 0 ? FMath::Clamp(float(AppearanceElapsed / Settings.AppearanceDuration), 0.f, 1.f) : 1.f;
}
