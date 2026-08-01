#include "SlimeClimbComponent.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet/KismetMathLibrary.h"
#include "Engine/EngineTypes.h"
#include "GameFramework/CharacterMovementComponent.h"

USlimeClimbComponent::USlimeClimbComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void USlimeClimbComponent::BeginPlay()
{
    Super::BeginPlay();
}

bool USlimeClimbComponent::DetectSurface()
{
    AActor* Owner = GetOwner();
    if (!Owner) return false;

    const FVector Origin = Owner->GetActorLocation();
    TArray<AActor*> IgnoreActors; IgnoreActors.Add(Owner);
    const EDrawDebugTrace::Type DebugType =
        bDrawDebug ? EDrawDebugTrace::ForOneFrame : EDrawDebugTrace::None;

    const FVector DownDir = (-CurrentSurfaceNormal).GetSafeNormal();
    const FVector MoveDir = LastMoveDirection.GetSafeNormal();

    // 가중 평균용 (작은 요철 무시, 곡면 반응)
    FVector WeightedNormalSum = FVector::ZeroVector;
    float WeightSum = 0.f;

    float BestScore = TNumericLimits<float>::Max();  // 폴백용 최고 후보
    FVector BestNormal = FVector::ZeroVector;
    bool bFound = false;

    // penetrating 폴백용
    FVector PenetNormalSum = FVector::ZeroVector;
    int32 PenetCount = 0;

    for (int32 v = 0; v <= VerticalSteps; ++v)
    {
        const float PolarRad = FMath::DegreesToRadians(-90.f + (180.f / VerticalSteps) * v);
        for (int32 h = 0; h < HorizontalSteps; ++h)
        {
            const float AzimuthRad = (2.f * PI / HorizontalSteps) * h;
            const FVector Dir = FVector(
                FMath::Cos(PolarRad) * FMath::Cos(AzimuthRad),
                FMath::Cos(PolarRad) * FMath::Sin(AzimuthRad),
                FMath::Sin(PolarRad)).GetSafeNormal();

            FHitResult Hit;
            const bool bHit = UKismetSystemLibrary::SphereTraceSingle(
                this, Origin, Origin + Dir * TraceLength, TraceRadius,
                UEngineTypes::ConvertToTraceType(ECC_Visibility),
                false, IgnoreActors, DebugType, Hit, true);

            if (!bHit || !Hit.bBlockingHit) continue;

            const float DownAlign = FVector::DotProduct(Dir, DownDir);
            const float MoveAlign = MoveDir.IsNearlyZero() ? 0.f
                : FVector::DotProduct(Dir, MoveDir);

            FVector CandidateNormal = FVector::ZeroVector;
            bool bUsable = false;

            if (!Hit.bStartPenetrating && Hit.Distance > 1.f)
            {
                // 정상 히트
                CandidateNormal = Hit.ImpactNormal;
                bUsable = true;
            }
            else if (Hit.bStartPenetrating)
            {
                // 파묻힘: '미는 방향'이면 곡면 벽 신호로 바로 채택
                if (MoveAlign > 0.5f)
                {
                    CandidateNormal = Hit.Normal.GetSafeNormal();
                    if (!CandidateNormal.IsNearlyZero())
                        bUsable = true;
                }

                // 미는 방향이 아니어도 탈출 방향 평균용으로 누적 (폴백 1)
                const FVector PenetNormal = Hit.Normal.GetSafeNormal();
                if (!PenetNormal.IsNearlyZero())
                {
                    PenetNormalSum += PenetNormal;
                    ++PenetCount;
                }
            }

            if (bUsable)
            {
                const float Score =
                    Hit.Distance
                    + (1.f - DownAlign) * StickWeight
                    - FMath::Max(0.f, MoveAlign) * ClimbBias;

                // 스코어가 좋을수록(작을수록) 가중치 큼 → 여러 후보를 평균
                const float Weight = 1.f / (1.f + Score * 0.01f);
                WeightedNormalSum += CandidateNormal * Weight;
                WeightSum += Weight;

                if (Score < BestScore)   // 최고 후보 기록 (폴백)
                {
                    BestScore = Score;
                    BestNormal = CandidateNormal;
                    bFound = true;
                }
            }
        }
    }

    // 가중 평균을 최종 노멀로 사용 (작은 요철 희석, 곡면 유지) — 단, 바닥이
    // 벽과 만나는 접합부처럼 서로 다른 두 면이 동시에 스캔에 걸리는 경우에는
    // 평균을 내면 실제로 존재하지 않는 대각선 노멀이 나온다. 이 대각선 노멀은
    // 재부착 트레이스가 허공을 가리키게 만들어 벽 오르기가 끊기고 멈추는
    // 현상의 원인이 되므로, 후보들의 정렬도(Coherence)를 먼저 확인한다.
    // 정규화 전 가중 평균의 길이는 후보들이 서로 얼마나 일치하는지를 그대로
    // 나타낸다 (전부 같은 방향이면 1에 가깝고, 서로 다른 면이면 뚝 떨어진다).
    if (bFound && WeightSum > 0.f)
    {
        const FVector RawAvg = WeightedNormalSum / WeightSum;
        const float Coherence = RawAvg.Size();
        if (Coherence > NormalCoherenceThreshold)
        {
            const FVector AvgNormal = RawAvg.GetSafeNormal();
            if (!AvgNormal.IsNearlyZero())
                BestNormal = AvgNormal;
        }
        // Coherence가 낮으면 두 면이 섞였다는 뜻이므로 평균을 버리고
        // 위에서 이미 기록해 둔 단일 최고 후보(BestNormal)를 그대로 쓴다.
    }

    // 볼록 모서리 예측: 이동 중이고 벽/곡면일 때 (조건 완화 + 다중 시도)
    const bool bOnWall = (CurrentSurfaceNormal.Z < FloorNormalZThreshold);
    if (bOnWall && !MoveDir.IsNearlyZero())
    {
        // 여러 전방 거리에서 시도 (정점을 놓치지 않도록)
        const float AheadDistances[] = { 1.5f, 2.5f, 3.5f };
        for (float AheadMul : AheadDistances)
        {
            const FVector AheadOrigin = Origin
                + MoveDir * TraceRadius * AheadMul
                + CurrentSurfaceNormal * TraceRadius * 1.5f;

            const FVector AheadDir = (-CurrentSurfaceNormal - MoveDir * 0.5f).GetSafeNormal();

            FHitResult AheadHit;
            if (UKismetSystemLibrary::SphereTraceSingle(
                this, AheadOrigin, AheadOrigin + AheadDir * (TraceLength * 1.5f), TraceRadius,
                UEngineTypes::ConvertToTraceType(ECC_WorldStatic),
                false, IgnoreActors, DebugType, AheadHit, true))
            {
                if (!AheadHit.bStartPenetrating && AheadHit.Distance > 1.f)
                {
                    const float Diff = FVector::DotProduct(AheadHit.ImpactNormal, CurrentSurfaceNormal);
                    if (Diff < 0.8f)   // 새로운 면 발견
                    {
                        TargetSurfaceNormal = AheadHit.ImpactNormal;
                        bFoundSurface = true;
                        return true;
                    }
                }
            }
        }
    }

    // 폴백 1: 유효 히트가 없지만 penetrating은 있었다 → 탈출 방향 평균
    if (!bFound && PenetCount > 0)
    {
        const FVector Avg = (PenetNormalSum / PenetCount).GetSafeNormal();
        if (!Avg.IsNearlyZero())
        {
            BestNormal = Avg;
            bFound = true;
        }
    }

    // 폴백 2: 그래도 없으면 발밑으로 라인 트레이스 한 방
    if (!bFound)
    {
        FHitResult DownHit;
        const FVector DownEnd = Origin + DownDir * (TraceLength * 1.5f);
        if (UKismetSystemLibrary::LineTraceSingle(
            this, Origin, DownEnd,
            UEngineTypes::ConvertToTraceType(ECC_Visibility),
            false, IgnoreActors, DebugType, DownHit, true))
        {
            if (!DownHit.bStartPenetrating)
            {
                BestNormal = DownHit.ImpactNormal;
                bFound = true;
            }
        }
    }

    // 최종 노멀 갱신 (데드존: 변화가 충분히 클 때만 반영 → 작은 요철 무시)
    bFoundSurface = bFound;
    if (bFound)
    {
        const float Change = FVector::DotProduct(BestNormal, TargetSurfaceNormal);
        if (Change < NormalDeadzone)   // 많이 다를 때만 갱신
            TargetSurfaceNormal = BestNormal;
        // Change >= NormalDeadzone이면 기존 유지 (요철 무시)
    }
    return bFound;
}

bool USlimeClimbComponent::IsOnWalkableFloor() const
{
    return TargetSurfaceNormal.Z >= FloorNormalZThreshold;
}

void USlimeClimbComponent::UpdateOrientation(USceneComponent* MeshPivotComp, UCharacterMovementComponent* MoveComp, FVector CurrentLookVector, float DeltaTime)
{
    if (!MeshPivotComp) return;

    AActor* Owner = GetOwner();
    if (!Owner) return;

    // ★ 최후 안전장치: 감지 실패 시 슬라임을 마지막 유효 위치에 고정 (날아감 방지)
    // bTreatAsFloor(히스테리시스 플래그)가 아니라 실제 MovementMode(Flying)로 판단한다.
    // 두 값이 같은 프레임에 갱신되지 않아 어긋나는 경우에도 안전망이 확실히 걸리도록 함.
    const bool bClimbingNow = MoveComp && MoveComp->MovementMode == MOVE_Flying;
    if (!bFoundSurface)
    {
        if (bClimbingNow)   // 벽/곡면에서만 (바닥은 물리에 맡김)
        {
            Owner->SetActorLocation(LastValidLocation, false);
            MoveComp->Velocity = FVector::ZeroVector;
        }
        return;   // 감지 실패 프레임엔 아무것도 안 함 (다음 프레임 재감지 대기)
    }

    // 1. 노멀 보간
    const FVector OldNormal = CurrentSurfaceNormal;
    CurrentSurfaceNormal = FMath::VInterpTo(
        CurrentSurfaceNormal, TargetSurfaceNormal, DeltaTime, NormalInterpSpeed).GetSafeNormal();

    // 2. 바닥/벽 판정 히스테리시스 (먼저 갱신 — 이동 방식 결정에 필요)
    const float Z = TargetSurfaceNormal.Z;
    if (bTreatAsFloor && Z < FloorNormalZThreshold - 0.15f)  bTreatAsFloor = false;
    else if (!bTreatAsFloor && Z > FloorNormalZThreshold + 0.05f) bTreatAsFloor = true;

    // 3. 표면 재부착 (벽/곡면일 때, 부양 방지 — 이동은 물리에 맡김)
    if (!bTreatAsFloor)
    {
        const FVector Origin = Owner->GetActorLocation();
        TArray<AActor*> IgnoreActors; IgnoreActors.Add(Owner);

        FHitResult SnapHit;
        bool bSnapped = UKismetSystemLibrary::SphereTraceSingle(
            this, Origin, Origin - CurrentSurfaceNormal * TraceLength, TraceRadius,
            UEngineTypes::ConvertToTraceType(ECC_WorldStatic),
            false, IgnoreActors, EDrawDebugTrace::None, SnapHit, true)
            && !SnapHit.bStartPenetrating;

        // 보조 시도: 주 트레이스가 실패하면, 후진 방향으로 한 발 물러난 지점에서
        // 이전 노멀과 현재 노멀의 중간 방향으로 다시 시도한다.
        // (모서리를 돌며 뒤로 이동할 때 노멀이 보간되는 도중 실제 표면과 어긋나
        //  주 트레이스가 허공을 가리키게 되는 경우를 보완 — 후진 부양 버그의 원인)
        if (!bSnapped)
        {
            const FVector BlendedDir = (-OldNormal - CurrentSurfaceNormal).GetSafeNormal();
            const FVector RetreatOrigin = Origin - LastMoveDirection.GetSafeNormal() * TraceRadius;
            if (!BlendedDir.IsNearlyZero())
            {
                FHitResult BlendedHit;
                if (UKismetSystemLibrary::SphereTraceSingle(
                    this, RetreatOrigin, RetreatOrigin + BlendedDir * TraceLength, TraceRadius,
                    UEngineTypes::ConvertToTraceType(ECC_WorldStatic),
                    false, IgnoreActors, EDrawDebugTrace::None, BlendedHit, true)
                    && !BlendedHit.bStartPenetrating)
                {
                    SnapHit = BlendedHit;
                    bSnapped = true;
                }
            }
        }

        if (bSnapped)
        {
            const FVector SurfacePoint = SnapHit.ImpactPoint + SnapHit.ImpactNormal * SurfaceOffset;
            // 표면으로부터의 수직 거리
            const FVector ToSlime = Origin - SurfacePoint;
            const float NormalDist = FVector::DotProduct(ToSlime, SnapHit.ImpactNormal);

            // 너무 멀리 떴을 때만 수직으로 부드럽게 끌어당김 (평행 이동은 안 건드림)
            if (FMath::Abs(NormalDist) > SurfaceOffset * 0.5f)
            {
                const FVector Correction = SnapHit.ImpactNormal * NormalDist;
                const FVector TargetLoc = Origin - Correction;
                Owner->SetActorLocation(
                    FMath::VInterpTo(Origin, TargetLoc, DeltaTime, ReattachSpeed), true);
            }
        }
        else
        {
            // ★ 재부착 트레이스 실패 = 표면을 놓치고 허공에 뜬 상태
            // (뒤로 이동하며 모서리를 돌 때 CurrentSurfaceNormal 방향이 더 이상
            //  실제 표면을 가리키지 않아 발생 — 마지막 유효 위치로 즉시 복귀시켜
            //  중력 없는 Fly 상태로 계속 떠내려가는 것을 방지)
            Owner->SetActorLocation(LastValidLocation, false);
            if (MoveComp)
                MoveComp->Velocity = FVector::ZeroVector;
            return;   // 이번 프레임 메시 정렬은 건너뛰고 다음 프레임에 재시도
        }
    }

    // 표면에 붙어있음이 확인된 위치만 '마지막 유효 위치'로 기록
    LastValidLocation = Owner->GetActorLocation();

    // 4. MeshPivot 정렬
    const FVector Up = CurrentSurfaceNormal;

    const FQuat DeltaQ = FQuat::FindBetweenNormals(OldNormal, Up);
    SurfaceForward = DeltaQ.RotateVector(SurfaceForward);

    FVector DesiredSource;
    if (bTreatAsFloor)
        DesiredSource = CurrentLookVector;
    else
    {
        DesiredSource = LastMoveDirection;
        if (DesiredSource.IsNearlyZero())
            DesiredSource = CurrentLookVector;
    }

    FVector DesiredForward = FVector::VectorPlaneProject(DesiredSource, Up).GetSafeNormal();
    if (!DesiredForward.IsNearlyZero() &&
        FMath::Abs(FVector::DotProduct(DesiredForward, Up)) < 0.9f)
    {
        SurfaceForward = FMath::VInterpTo(SurfaceForward, DesiredForward, DeltaTime, NormalInterpSpeed).GetSafeNormal();
    }
    SurfaceForward = FVector::VectorPlaneProject(SurfaceForward, Up).GetSafeNormal();

    const FVector Forward = SurfaceForward;
    if (!Forward.IsNearlyZero() &&
        FMath::Abs(FVector::DotProduct(Forward, Up)) < 0.99f)
    {
        const FQuat TargetQ = FRotationMatrix::MakeFromZX(Up, Forward).ToQuat();
        const FQuat NewQ = FQuat::Slerp(
            MeshPivotComp->GetComponentQuat(), TargetQ,
            FMath::Clamp(DeltaTime * MeshRotateSpeed, 0.f, 1.f));
        MeshPivotComp->SetWorldRotation(NewQ);
    }
}

void USlimeClimbComponent::MoveOnSurface(USceneComponent* MeshPivotComp, float InputX, float InputY)
{
    APawn* PawnOwner = Cast<APawn>(GetOwner());
    if (!PawnOwner || !MeshPivotComp) return;

    const FVector Up = CurrentSurfaceNormal;
    const FVector Right = FVector::VectorPlaneProject(MeshPivotComp->GetRightVector(), Up).GetSafeNormal();
    const FVector Forward = FVector::VectorPlaneProject(MeshPivotComp->GetForwardVector(), Up).GetSafeNormal();
    const FVector MoveDir = (Forward * InputY + Right * InputX);

    if (!MoveDir.IsNearlyZero())
    {
        LastMoveDirection = MoveDir.GetSafeNormal();
        PawnOwner->AddMovementInput(LastMoveDirection, 1.f);
    }
}