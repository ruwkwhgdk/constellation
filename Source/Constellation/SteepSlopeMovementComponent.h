// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SteepSlopeMovementComponent.generated.h"

UCLASS()
class CONSTELLATION_API USteepSlopeMovementComponent : public UCharacterMovementComponent
{
    GENERATED_BODY()

public:
    USteepSlopeMovementComponent();

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float NormalWalkableAngle = 45.f;

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float MaxClimbableAngle = 65.f;

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float ClimbGraceDuration = 1.2f;   // 이 시간 동안 발버둥(약→강)

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float ClimbingSlideRatio = 0.35f;  // 발버둥 시작 시 미끄러짐 강도 (0~1)

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float SlideStrengthMul = 2.0f;     // 전체 미끄러짐 세기 배율

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float SlideMaxSpeed = 900.f;

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float SlideAccelRate = 4.f;

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float SideFrictionOnSlide = 0.5f;  // 미끄러질 때 좌우 속도 감쇠 (1=유지, 0=즉시제거)

    UPROPERTY(EditAnywhere, Category = "SteepSlope")
    float SlideMinSpeed = 300.f;   // 미끄러짐 시작 시 최소 보장 속도


protected:
    float ClimbTimer = 0.f; // 경사에 머문 누적 시간 (0에서 증가)

    virtual void InitializeComponent() override;
    virtual void PhysWalking(float deltaTime, int32 Iterations) override;
    virtual void HandleImpact(const FHitResult& Impact, float TimeSlice = 0.f, const FVector& MoveDelta = FVector::ZeroVector) override;

#if WITH_EDITOR
    virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif
};