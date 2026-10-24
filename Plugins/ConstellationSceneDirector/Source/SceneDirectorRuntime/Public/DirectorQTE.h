#pragma once

#include "CoreMinimal.h"
#include "DirectorQTE.generated.h"

class USoundBase;

UENUM(BlueprintType)
enum class EDirectorQTEType : uint8 { SingleClick, RepeatClick, DirectionDrag, TracePath };
UENUM(BlueprintType)
enum class EDirectorQTEScenePolicy : uint8 { Hold, Continue };
UENUM(BlueprintType)
enum class EDirectorQTEOutcome : uint8 { Pending, Success, Failure, Cancelled };

/** Positions and distances use Slate local units relative to the prompt origin. */
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorQTESettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") EDirectorQTEType Type = EDirectorQTEType::SingleClick;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") bool bTimed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="0.01")) float TimeLimit = 5.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") FVector2D ScreenPosition = FVector2D(.5, .65);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") bool bAnywhere = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="1")) int32 ClickTarget = 5;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="1")) float HitRadius = 96.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") FVector2D DragDirection = FVector2D(-1, 0);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="1")) float DragDistance = 180.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="0", ClampMax="90")) float AngleToleranceDegrees = 30.f;
    /** Ordered polyline samples; UI draws this same polyline. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") TArray<FVector2D> Path = {
        FVector2D(-160,55), FVector2D(-140,61), FVector2D(-120,62), FVector2D(-100,59),
        FVector2D(-80,52), FVector2D(-60,42), FVector2D(-40,29), FVector2D(-20,15),
        FVector2D(0,0), FVector2D(20,-15), FVector2D(40,-29), FVector2D(60,-42),
        FVector2D(80,-52), FVector2D(100,-59), FVector2D(120,-62), FVector2D(140,-61), FVector2D(160,-55) };
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="1")) float PathTolerance = 24.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") bool bFailOnMistake = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE", meta=(ClampMin="0")) float AppearanceDuration = .2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") EDirectorQTEScenePolicy ScenePolicy = EDirectorQTEScenePolicy::Hold;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") TObjectPtr<USoundBase> SuccessSound = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="QTE") TObjectPtr<USoundBase> FailureSound = nullptr;

    bool Validate(FString& OutError) const;
};

/** Clock advances only through Tick. Tick before pointer events: expiry wins at its boundary.
 * SetPaused freezes time and invalidates any in-progress gesture until a fresh release/press.
 * No callbacks: consumer observes the immutable outcome and dispatches it exactly once.
 */
class SCENEDIRECTORRUNTIME_API FDirectorQTEState
{
public:
    explicit FDirectorQTEState(const FDirectorQTESettings& InSettings = FDirectorQTESettings(), bool bInitiallyHeld = false);
    void Tick(double DeltaSeconds);
    void Press(const FVector2D& Position);
    void Move(const FVector2D& Position);
    void Release(const FVector2D& Position);
    void SetPaused(bool bInPaused);
    void Cancel();
    EDirectorQTEOutcome GetOutcome() const { return Outcome; }
    const FDirectorQTESettings& GetSettings() const { return Settings; }
    bool IsReady() const { return Outcome == EDirectorQTEOutcome::Pending && !bPaused && AppearanceElapsed >= Settings.AppearanceDuration; }
    bool IsDragging() const { return bAttempt; }
    bool IsPaused() const { return bPaused; }
    float GetProgress() const;
    float GetRemainingFraction() const;
    int32 GetClickCount() const { return ClickCount; }
    float GetAppearanceFraction() const;
private:
    void Mistake();
    void ResetAttempt();
    FDirectorQTESettings Settings;
    EDirectorQTEOutcome Outcome = EDirectorQTEOutcome::Pending;
    double AppearanceElapsed = 0;
    double Elapsed = 0;
    bool bPaused = false;
    bool bHeld = false;
    bool bAttempt = false;
    int32 ClickCount = 0;
    FVector2D Start = FVector2D::ZeroVector;
    FVector2D Last = FVector2D::ZeroVector;
    float DragProgress = 0;
    TArray<FVector2D> Checkpoints;
    TArray<double> CheckpointDistances;
    double MaxTraceStep = 0;
    double TraceDistance = 0;
    int32 NextCheckpoint = 1;
};
