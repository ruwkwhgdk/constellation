#include "SDirectorQTE.h"

#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"

namespace
{
const FLinearColor Gold(1.f, .69f, .27f);
const FLinearColor Ivory(1.f, .95f, .80f);
const FLinearColor Broken(1.f, .31f, .08f);

/** Only small local shapes are emitted: never a viewport background or texture. */
struct FQTEPainter
{
    const FGeometry& Geometry;
    FSlateWindowElementList& Out;
    int32 Layer;
    FVector2D Origin;
    float Opacity;

    void Line(const TArray<FVector2D>& Points, FLinearColor Color, float Width = 1.5f) const
    {
        if (Points.Num() < 2 || Opacity <= 0) return;
        TArray<FVector2D> Local;
        Local.Reserve(Points.Num());
        for (const FVector2D& Point : Points) Local.Add(Origin + Point);
        FLinearColor Shadow(.015f, .012f, .02f, .65f * Color.A * Opacity);
        FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), Local,
            ESlateDrawEffect::None, Shadow, true, Width + 2.f);
        Color.A *= Opacity;
        FSlateDrawElement::MakeLines(Out, Layer + 1, Geometry.ToPaintGeometry(), Local,
            ESlateDrawEffect::None, Color, true, Width);
    }

    void Fill(const TArray<FVector2D>& Points, FLinearColor Color) const
    {
        if (Points.Num() < 3 || Opacity <= 0) return;
        TArray<FSlateVertex> Vertices;
        TArray<SlateIndex> Indices;
        Color.A *= Opacity;
        const FColor Packed = Color.ToFColor(true);
        const auto Transform = Geometry.GetAccumulatedRenderTransform();
        for (const FVector2D& P : Points)
            Vertices.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(
                Transform, FVector2f(Origin + P), FVector2f(.5f, .5f), Packed));
        for (int32 I = 1; I + 1 < Points.Num(); ++I)
            Indices.Append({0, SlateIndex(I), SlateIndex(I + 1)});
        const auto* Brush = FCoreStyle::Get().GetBrush("WhiteBrush");
        FSlateDrawElement::MakeCustomVerts(Out, Layer + 1,
            FSlateApplication::Get().GetRenderer()->GetResourceHandle(*Brush),
            Vertices, Indices, nullptr, 0, 0);
    }

    void Arc(FVector2D Center, float Radius, float Fraction, FLinearColor Color,
        float Width = 2, float Start = -HALF_PI) const
    {
        if (Fraction <= 0) return;
        const int32 Steps = FMath::Max(2, FMath::CeilToInt(96 * Fraction));
        TArray<FVector2D> Points;
        for (int32 I = 0; I <= Steps; ++I)
        {
            const float Angle = Start + 2 * PI * Fraction * I / Steps;
            Points.Add(Center + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
        }
        Line(Points, Color, Width);
    }

    void Star(FVector2D Center, float Radius, FLinearColor Color) const
    {
        // Each quadrant is a convex kite so the concave four-point star triangulates correctly.
        for (int32 I = 0; I < 4; ++I)
        {
            const float A = HALF_PI * I;
            const FVector2D Tip(FMath::Cos(A) * Radius, FMath::Sin(A) * Radius);
            const FVector2D Before(FMath::Cos(A - PI / 4) * Radius * .26,
                FMath::Sin(A - PI / 4) * Radius * .26);
            const FVector2D After(FMath::Cos(A + PI / 4) * Radius * .26,
                FMath::Sin(A + PI / 4) * Radius * .26);
            Fill({Center, Center + Before, Center + Tip, Center + After}, Color);
        }
    }

    void Mouse(FVector2D Center, float Scale = 1) const
    {
        // Rounded capsule with a distinctly filled left button.
        TArray<FVector2D> Outline;
        for (int32 I = 0; I <= 20; ++I)
        {
            const float A = PI + PI * I / 20;
            Outline.Add(Center + FVector2D(18 * FMath::Cos(A), -9 + 18 * FMath::Sin(A)) * Scale);
        }
        for (int32 I = 0; I <= 20; ++I)
        {
            const float A = PI * I / 20;
            Outline.Add(Center + FVector2D(18 * FMath::Cos(A), 12 + 18 * FMath::Sin(A)) * Scale);
        }
        const FVector2D FirstPoint = Outline[0];
        Outline.Add(FirstPoint);
        TArray<FVector2D> Button = {Center + FVector2D(-2, -24) * Scale,
            Center + FVector2D(-2, -1) * Scale, Center + FVector2D(-15, -1) * Scale};
        for (int32 I = 0; I <= 10; ++I)
        {
            const float A = PI + HALF_PI * I / 10;
            Button.Add(Center + FVector2D(15 * FMath::Cos(A), -9 + 15 * FMath::Sin(A)) * Scale);
        }
        Fill(Button, Gold);
        Line(Outline, Ivory, 1.8f);
        Line({Center + FVector2D(0, -26) * Scale, Center + FVector2D(0, -2) * Scale}, Ivory, 1.4f);
        Line({Center + FVector2D(1, -15) * Scale, Center + FVector2D(1, -7) * Scale}, Ivory, 2.6f);
    }

    void Hand(FVector2D Tip, float Alpha) const
    {
        FLinearColor Color = Ivory;
        Color.A = Alpha;
        // A small outline hand, offset beneath its fingertip; it never owns a hit target.
        const TArray<FVector2D> Shape = {{0,0},{-3,-2},{-5,1},{-2,15},{-5,13},
            {-8,14},{-8,18},{0,29},{10,34},{20,29},{22,21},{17,9},{14,8},
            {12,10},{10,6},{7,6},{5,9},{3,4},{0,4},{0,0}};
        TArray<FVector2D> Points;
        for (const FVector2D& P : Shape) Points.Add(Tip + P);
        Line(Points, Color, 1.5f);
        Arc(Tip, 6, 1, Color, 1);
    }
};

float PathLength(const TArray<FVector2D>& Points)
{
    float Length = 0;
    for (int32 I = 1; I < Points.Num(); ++I) Length += FVector2D::Distance(Points[I - 1], Points[I]);
    return Length;
}

FVector2D PointAlong(const TArray<FVector2D>& Points, float Distance)
{
    for (int32 I = 1; I < Points.Num(); ++I)
    {
        const float Length = FVector2D::Distance(Points[I - 1], Points[I]);
        if (Distance <= Length && Length > UE_SMALL_NUMBER)
            return FMath::Lerp(Points[I - 1], Points[I], Distance / Length);
        Distance -= Length;
    }
    return Points.IsEmpty() ? FVector2D::ZeroVector : Points.Last();
}
}

void SDirectorQTE::Construct(const FArguments& Args)
{
    OnCompleted = Args._OnCompleted;
    OnDirectorKey = Args._OnDirectorKey;
    ScreenPosition = Args._Settings.ScreenPosition;
    State = MakeUnique<FDirectorQTEState>(Args._Settings, IsLeftMouseDown());
    SetVisibility(EVisibility::Visible);
    ForceVolatile(true);
}

bool SDirectorQTE::IsApplicationActive() const { return FSlateApplication::Get().IsActive(); }
bool SDirectorQTE::IsLeftMouseDown() const
{
    return FSlateApplication::Get().GetPressedMouseButtons().Contains(EKeys::LeftMouseButton);
}

void SDirectorQTE::UpdatePause()
{
    const bool bWasPaused = State->IsPaused();
    State->SetPaused(bExplicitlyPaused || bFocusLost || !IsApplicationActive());
    if (bWasPaused && !State->IsPaused() && !IsLeftMouseDown())
        State->Release(FVector2D::ZeroVector);
}

void SDirectorQTE::UpdateGeometry(const FGeometry& Geometry)
{
    const FVector2D Size = Geometry.GetLocalSize();
    if (Size.X <= 0 || Size.Y <= 0) return;
    const float Scale = Geometry.GetAccumulatedLayoutTransform().GetScale();
    const FVector2D AbsoluteOrigin = Geometry.LocalToAbsolute(FVector2D::ZeroVector);
    if (!bGeometryInitialized)
    {
        PromptOrigin = Size * ScreenPosition;
        bGeometryInitialized = true;
    }
    else if (!PreviousSize.Equals(Size) || !FMath::IsNearlyEqual(PreviousScale, Scale) ||
        !PreviousAbsoluteOrigin.Equals(AbsoluteOrigin))
    {
        // Keep the original local anchor. A viewport resize or DPI/window transform is not
        // pointer travel: invalidate the gesture and require a physical release before retry.
        State->SetPaused(true);
        UpdatePause();
    }
    PreviousSize = Size;
    PreviousScale = Scale;
    PreviousAbsoluteOrigin = AbsoluteOrigin;
}

void SDirectorQTE::SetPaused(bool bPaused)
{
    bExplicitlyPaused = bPaused;
    UpdatePause();
}

void SDirectorQTE::Cancel()
{
    State->Cancel();
    ReportOutcome();
}

void SDirectorQTE::ReportOutcome()
{
    const EDirectorQTEOutcome Outcome = State->GetOutcome();
    if (bReported || Outcome == EDirectorQTEOutcome::Pending) return;
    bReported = true;
    RetirementDuration = Outcome == EDirectorQTEOutcome::Success ? .25f :
        Outcome == EDirectorQTEOutcome::Failure ? .3f : 0.f;
    SetVisibility(EVisibility::HitTestInvisible);
    if (HasMouseCapture()) FSlateApplication::Get().ReleaseMouseCapture();
    OnCompleted.ExecuteIfBound(Outcome);
}

void SDirectorQTE::Tick(const FGeometry& Geometry, double CurrentTime, float DeltaTime)
{
    SLeafWidget::Tick(Geometry, CurrentTime, DeltaTime);
    UpdateGeometry(Geometry);
    UpdatePause();
    if (bReported)
    {
        // Gameplay focus is restored immediately on completion; retirement must not depend on it.
        RetirementElapsed += DeltaTime;
    }
    else if (!State->IsPaused())
    {
        VisualElapsed += DeltaTime;
        State->Tick(DeltaTime);
    }
    ReportOutcome();
}

FVector2D SDirectorQTE::PointerPosition(const FGeometry& Geometry, const FPointerEvent& Event) const
{
    return Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition()) - PromptOrigin;
}

FReply SDirectorQTE::OnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bReported) return FReply::Unhandled();
    UpdateGeometry(Geometry);
    UpdatePause();
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        State->Press(PointerPosition(Geometry, Event));
        ReportOutcome();
        if (!bReported) return FReply::Handled().CaptureMouse(SharedThis(this));
        return FReply::Handled().ReleaseMouseCapture();
    }
    return FReply::Handled();
}

FReply SDirectorQTE::OnMouseButtonDoubleClick(const FGeometry& Geometry, const FPointerEvent& Event)
{
    // Slate routes the second independent press of a double click through this event.
    return OnMouseButtonDown(Geometry, Event);
}

FReply SDirectorQTE::OnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bReported) return FReply::Unhandled();
    UpdateGeometry(Geometry);
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        State->Release(PointerPosition(Geometry, Event));
        ReportOutcome();
        return FReply::Handled().ReleaseMouseCapture();
    }
    return FReply::Handled();
}

FReply SDirectorQTE::OnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bReported) return FReply::Unhandled();
    UpdateGeometry(Geometry);
    UpdatePause();
    State->Move(PointerPosition(Geometry, Event));
    ReportOutcome();
    return FReply::Handled();
}

FReply SDirectorQTE::OnMouseWheel(const FGeometry&, const FPointerEvent&)
{
    return bReported ? FReply::Unhandled() : FReply::Handled();
}
FReply SDirectorQTE::OnKeyDown(const FGeometry&, const FKeyEvent& Event)
{
    if (bReported) return FReply::Unhandled();
    if (OnDirectorKey.IsBound() && OnDirectorKey.Execute(Event, true).IsEventHandled())
        return FReply::Handled();
    // Preserve the host editor's Escape-to-stop policy when no director handler claims it.
    return Event.GetKey() == EKeys::Escape ? FReply::Unhandled() : FReply::Handled();
}
FReply SDirectorQTE::OnKeyUp(const FGeometry&, const FKeyEvent& Event)
{
    if (bReported) return FReply::Unhandled();
    if (OnDirectorKey.IsBound() && OnDirectorKey.Execute(Event, false).IsEventHandled())
        return FReply::Handled();
    return Event.GetKey() == EKeys::Escape ? FReply::Unhandled() : FReply::Handled();
}
FReply SDirectorQTE::OnKeyChar(const FGeometry&, const FCharacterEvent&) { return FReply::Handled(); }

FReply SDirectorQTE::OnFocusReceived(const FGeometry&, const FFocusEvent&)
{
    bFocusLost = false;
    UpdatePause();
    return FReply::Handled();
}

void SDirectorQTE::OnFocusLost(const FFocusEvent& Event)
{
    SLeafWidget::OnFocusLost(Event);
    bFocusLost = true;
    UpdatePause();
}

void SDirectorQTE::OnMouseCaptureLost(const FCaptureLostEvent& Event)
{
    SLeafWidget::OnMouseCaptureLost(Event);
    if (!bReported && State->IsDragging())
    {
        // Capture can be stolen by another UI without a matching release.
        State->SetPaused(true);
        UpdatePause();
    }
}

int32 SDirectorQTE::OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&,
    FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool) const
{
    if (!State || IsRetired()) return Layer;
    const auto& Settings = State->GetSettings();
    const float Exit = bReported ? FMath::Clamp(RetirementElapsed / RetirementDuration, 0.f, 1.f) : 0;
    const float Alpha = State->GetAppearanceFraction() * (1 - Exit) * Style.GetColorAndOpacityTint().A;
    const bool bFailure = State->GetOutcome() == EDirectorQTEOutcome::Failure;
    const FLinearColor Accent = bFailure ? Broken : Gold;
    FQTEPainter P{Geometry, Out, Layer,
        bGeometryInitialized ? PromptOrigin : Geometry.GetLocalSize() * ScreenPosition, Alpha};
    const bool bPath = Settings.Type == EDirectorQTEType::DirectionDrag || Settings.Type == EDirectorQTEType::TracePath;
    if (!bPath)
    {
        const float Radius = FMath::Max(52.f, Settings.HitRadius);
        P.Arc(FVector2D::ZeroVector, Radius, bFailure ? .68f : 1.f, Accent, 1);
        const float StarAngle = -.65f + VisualElapsed * .16f;
        P.Star(FVector2D(FMath::Cos(StarAngle), FMath::Sin(StarAngle)) * Radius, 6, Accent);
        P.Mouse(FVector2D::ZeroVector);
        if (Settings.Type == EDirectorQTEType::RepeatClick)
            P.Arc(FVector2D::ZeroVector, Radius - 6, State->GetProgress(), Accent, 3);
        if (Settings.bTimed)
            P.Arc(FVector2D::ZeroVector, Radius + 12, State->GetRemainingFraction(), Ivory, 3);
        if (bReported && !bFailure)
        {
            P.Arc(FVector2D::ZeroVector, Radius + Exit * 24, 1, Accent, 2);
            P.Star(FVector2D::ZeroVector, 6 + Exit * 15, Accent);
        }
    }
    else
    {
        TArray<FVector2D> Points = Settings.Type == EDirectorQTEType::TracePath ? Settings.Path :
            TArray<FVector2D>{FVector2D::ZeroVector, Settings.DragDirection.GetSafeNormal() * Settings.DragDistance};
        if (Points.Num() < 2) return Layer;
        const float Length = PathLength(Points);
        const float Completed = Length * State->GetProgress();
        // Exact configured polyline for both feedback and judgment. Dots do not create input widgets.
        for (float D = Completed; D <= Length; D += 9.f)
        {
            if (bFailure && FMath::Fmod(D, 36.f) < 15.f) continue;
            const FVector2D Pos = PointAlong(Points, D);
            P.Line({Pos, Pos + FVector2D(.1, 0)}, bFailure ? Broken : Ivory, 2.2f);
        }
        if (Completed > 0)
        {
            TArray<FVector2D> Progress = {Points[0]};
            float Traveled = 0;
            for (int32 I = 1; I < Points.Num(); ++I)
            {
                const float Segment = FVector2D::Distance(Points[I - 1], Points[I]);
                if (Traveled + Segment >= Completed)
                {
                    Progress.Add(PointAlong(Points, Completed));
                    break;
                }
                Progress.Add(Points[I]);
                Traveled += Segment;
            }
            P.Line(Progress, Accent, 3);
        }
        P.Star(Points[0], 9, Accent);
        P.Star(Points.Last(), 11 + (bReported && !bFailure ? Exit * 9 : 0), Accent);
        P.Mouse(Points[0] + FVector2D(27, 33), .65f);
        if (Settings.Type == EDirectorQTEType::DirectionDrag)
        {
            const FVector2D Direction = Settings.DragDirection.GetSafeNormal();
            const FVector2D Perpendicular(-Direction.Y, Direction.X);
            const FVector2D Tip = Points.Last() + Direction * 20;
            P.Line({Tip - Direction * 7 + Perpendicular * 5, Tip,
                Tip - Direction * 7 - Perpendicular * 5}, Accent, 2);
        }
        if (!bReported)
        {
            const float Demo = State->IsDragging() ? State->GetProgress() :
                FMath::Clamp(FMath::Fmod(VisualElapsed * .5f, 1.35f), 0.f, 1.f);
            P.Hand(PointAlong(Points, Demo * Length), State->IsDragging() ? .18f : .8f);
        }
        if (Settings.bTimed)
        {
            float MaxX = Points[0].X;
            float MinY = Points[0].Y;
            for (const FVector2D& Point : Points) { MaxX = FMath::Max(MaxX, float(Point.X)); MinY = FMath::Min(MinY, float(Point.Y)); }
            P.Arc(FVector2D(MaxX + 24, MinY - 35), 14, State->GetRemainingFraction(), Ivory, 2.5f);
        }
        if (bReported && !bFailure) P.Arc(Points.Last(), 12 + Exit * 23, 1, Accent, 1.5f);
    }
    return Layer + 2;
}
