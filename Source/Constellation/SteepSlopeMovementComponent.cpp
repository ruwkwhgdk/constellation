// Fill out your copyright notice in the Description page of Project Settings.

#include "SteepSlopeMovementComponent.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"

USteepSlopeMovementComponent::USteepSlopeMovementComponent()
{
    // 엔진 본래의 WalkableFloorAngle을 우리가 원하는 최대 각도로 맞춰준다
    SetWalkableFloorAngle(MaxClimbableAngle);
}

void USteepSlopeMovementComponent::InitializeComponent()
{
    Super::InitializeComponent();
    SetWalkableFloorAngle(MaxClimbableAngle);
}

void USteepSlopeMovementComponent::PhysWalking(float deltaTime, int32 Iterations)
{
    if (deltaTime >= MIN_TICK_TIME && UpdatedComponent && MovementMode == MOVE_Walking)
    {
        const FVector Start = UpdatedComponent->GetComponentLocation();
        const FVector End = Start - FVector(0, 0, 200.f);
        FHitResult FloorHit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(UpdatedComponent->GetOwner());

        if (GetWorld()->LineTraceSingleByChannel(FloorHit, Start, End, ECC_WorldStatic, Params))
        {
            const float SlopeAngle = FMath::RadiansToDegrees(
                FMath::Acos(FVector::DotProduct(FloorHit.ImpactNormal, FVector::UpVector)));

            if (SlopeAngle > NormalWalkableAngle && SlopeAngle <= MaxClimbableAngle)
            {
                ClimbTimer += deltaTime;

                const FVector SlopeNormal = FloorHit.ImpactNormal;
                const FVector GravityDir = FVector(0.f, 0.f, -1.f);
                const FVector SlideDir = (GravityDir - SlopeNormal * FVector::DotProduct(GravityDir, SlopeNormal))
                    .GetSafeNormal();

                const float SlideRamp = FMath::Clamp(ClimbTimer / ClimbGraceDuration, 0.f, 1.f);

                if (SlideRamp < 1.f)
                {
                    // 발버둥 구간: 걷기 유지, 미끄러뜨리는 힘만 추가 (올라갈 수 있음)
                    const float Strength = FMath::Lerp(ClimbingSlideRatio, 1.f, SlideRamp);
                    const float GravityAccel = FMath::Abs(GetGravityZ());
                    const float SlopeSin = FMath::Sin(FMath::DegreesToRadians(SlopeAngle));
                    const float SlideForce = GravityAccel * SlopeSin * SlideStrengthMul * Strength;
                    Velocity += SlideDir * SlideForce * deltaTime;
                }
                else
                {
                    // 미끄러짐 구간: 경사 아래로 속도를 직접 설정 (걷기 유지, 마찰 우회)
                    const float NormalV = FVector::DotProduct(Velocity, SlopeNormal);
                    const FVector TangentVel = Velocity - SlopeNormal * NormalV;

                    float AlongSlide = FVector::DotProduct(TangentVel, SlideDir);
                    const FVector SideVel = TangentVel - SlideDir * AlongSlide;

                    // 목표 속도로 가속 (0으로 리셋 안 되게 현재 값에서 누적)
                    AlongSlide = FMath::FInterpTo(AlongSlide, SlideMaxSpeed, deltaTime, SlideAccelRate);
                    AlongSlide = FMath::Max(AlongSlide, SlideMinSpeed);  // 최소 미끄러짐 속도 보장

                    // 좌우는 감쇠, 위로 가는 성분 제거
                    Velocity = SideVel * SideFrictionOnSlide + SlideDir * AlongSlide + SlopeNormal * NormalV;

                    // Walking 유지 (Falling 깜빡임 방지). Super가 이 속도로 바닥 따라 이동시킴
                    if (GEngine)
                        GEngine->AddOnScreenDebugMessage(-1, 0.f, FColor::Yellow,
                            FString::Printf(TEXT("SLIDING Angle=%.1f AlongSlide=%.0f"), SlopeAngle, AlongSlide));
                    // return 안 함 → Super::PhysWalking이 이 Velocity로 경사를 따라 이동
                }

                if (GEngine)
                    GEngine->AddOnScreenDebugMessage(-1, 0.f, FColor::Yellow,
                        FString::Printf(TEXT("STRUGGLE Angle=%.1f Ramp=%.2f Vel=%.0f"),
                            SlopeAngle, SlideRamp, Velocity.Size()));
            }
            else
            {
                ClimbTimer = 0.f;
            }
        }
    }

    Super::PhysWalking(deltaTime, Iterations);
}

void USteepSlopeMovementComponent::HandleImpact(const FHitResult& Impact, float TimeSlice, const FVector& MoveDelta)
{
    // 미끄러짐은 PhysWalking이 전담하므로 여기서는 기본 동작만
    Super::HandleImpact(Impact, TimeSlice, MoveDelta);
}

#if WITH_EDITOR
void USteepSlopeMovementComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);

    if (PropertyChangedEvent.Property &&
        PropertyChangedEvent.Property->GetFName() == GET_MEMBER_NAME_CHECKED(USteepSlopeMovementComponent, MaxClimbableAngle))
    {
        // 에디터에서 MaxClimbableAngle 값을 바꿀 때마다 실제 WalkableFloorAngle도 같이 갱신
        SetWalkableFloorAngle(MaxClimbableAngle);
    }
}
#endif