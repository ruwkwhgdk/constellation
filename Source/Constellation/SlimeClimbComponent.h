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

    // bTreatAsFloor를 실제로 뒤집기 전에, 반대 판정이 이 시간(초) 동안 계속
    // 유지되어야 한다. 90도 바닥/벽 모서리에서는 한 프레임만 보면 감지된 노멀이
    // 바닥과 벽 사이를 오갈 수 있는데(캐릭터가 이음매에 딱 붙어 있어 아주 작은
    // 위치 변화만으로도 트레이스의 최적 후보가 뒤바뀜), 그 값을 그대로 반영하면
    // BP_Player_Slime의 Tick이 매번 SetMovementMode(Walking/Flying)를 다시
    // 호출해 슬라임이 다음 표면에 올라타려다 계속 실패하는 것처럼 보인다.
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float FloorWallSwitchDelay = 0.15f;

    // 재부착 트레이스가 실패해도 이 시간(초) 동안은 위치/속도를 건드리지 않고
    // 넘어간다. 바닥/벽 전환 중에는 CurrentSurfaceNormal이 아직 목표를 향해
    // 보간되는 도중이라 재부착 트레이스가 한두 프레임 허공을 가리킬 수 있는데,
    // 실패할 때마다 즉시 LastValidLocation으로 되돌리고 속도를 0으로 만들면
    // 보간이 끝나기도 전에 매번 원점으로 리셋되어 절대 표면에 올라타지 못하고
    // 같은 자리에서 계속 실패하는 무한 루프가 된다.
    UPROPERTY(EditAnywhere, Category = "SlimeClimb|Movement")
    float ReattachFailGrace = 0.2f;

    // 입력을 표면 평면에 투영해 이동. MeshPivot 기준 방향 사용.
    UFUNCTION(BlueprintCallable, Category = "SlimeClimb")
    void MoveOnSurface(USceneComponent* MeshPivotComp, float InputX, float InputY);

protected:
    virtual void BeginPlay() override;

    FVector LastMoveDirection = FVector::ForwardVector;
    FVector SurfaceForward = FVector::ForwardVector;
    FVector LastValidLocation = FVector::ZeroVector;
    float FloorWallSwitchTimer = 0.f;
    float ReattachFailTimer = 0.f;
};
