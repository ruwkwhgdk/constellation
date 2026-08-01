#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SlimeClimbComponent.generated.h"

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class CONSTELLATION_API USlimeClimbComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    USlimeClimbComponent();

    // --- 감지 결과 ---
    UPROPERTY(BlueprintReadOnly, Category = "SlimeClimb")
    FVector TargetSurfaceNormal = FVector::UpVector;

    UPROPERTY(BlueprintReadWrite, Category = "SlimeClimb")
    FVector CurrentSurfaceNormal = FVector::UpVector;

    UPROPERTY(BlueprintReadOnly, Category = "SlimeClimb")
    bool bFoundSurface = false;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb")
    bool bTreatAsFloor = true;

    // --- 감지 파라미터 ---
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float TraceRadius = 34.f;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float TraceLength = 150.f;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    int32 HorizontalSteps = 8;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    int32 VerticalSteps = 6;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float NormalDeadzone = 0.99f;   // 이보다 노멀이 많이 바뀔 때만 반영 (1에 가까울수록 둔감)

    // --- 정렬/이동 파라미터 ---
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float NormalInterpSpeed = 8.f;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float MoveSpeed = 400.f;

    // 표면에서 이 거리를 유지하도록 스냅 (캡슐 반경 정도)
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float SurfaceOffset = 34.f;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float MeshRotateSpeed = 4.f;   // 슬라임 몸이 방향을 따라 도는 속도 (낮을수록 부드러움)

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "SlimeClimb|Debug")
    bool bDrawDebug = false;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float StickWeight = 200.f;   // 현재 면에 붙어있으려는 힘

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float ClimbBias = 250.f;   // 미는 방향 벽으로 넘어가려는 힘

    // How aligned the accumulated candidate normals must be (0-1) before we
    // trust their weighted average. Below this, the candidates disagree
    // enough that they likely come from two different surfaces (e.g. floor
    // meeting a wall), and blending them would produce a normal that points
    // at nothing real, so we fall back to the single best candidate instead.
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Detection")
    float NormalCoherenceThreshold = 0.75f;

    // 감지 실행 (매 틱 호출)
    UFUNCTION(BlueprintCallable, Category = "SlimeClimb")
    bool DetectSurface();

    // UpdateOrientation에 CurrentLookVector 추가
    UFUNCTION(BlueprintCallable, Category = "SlimeClimb")
    void UpdateOrientation(USceneComponent* MeshPivotComp, class UCharacterMovementComponent* MoveComp, FVector CurrentLookVector, float DeltaTime);

    // 걷기 가능 바닥인지 (BP에서 판정에 사용)
    UFUNCTION(BlueprintCallable, Category = "SlimeClimb")
    bool IsOnWalkableFloor() const;

    // FloorNormalZ 기준값
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float FloorNormalZThreshold = 0.7f;

    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float ReattachSpeed = 8.f;   // 부양 시 표면으로 끌어당기는 속도

    // 입력을 표면 평면에 투영해 이동. MeshPivot 기준 방향 사용.
    UFUNCTION(BlueprintCallable, Category = "SlimeClimb")
    void MoveOnSurface(USceneComponent* MeshPivotComp, float InputX, float InputY);

protected:
    virtual void BeginPlay() override;

    FVector LastMoveDirection = FVector::ForwardVector;
    FVector SurfaceForward = FVector::ForwardVector;
    FVector LastValidLocation = FVector::ZeroVector;
};
