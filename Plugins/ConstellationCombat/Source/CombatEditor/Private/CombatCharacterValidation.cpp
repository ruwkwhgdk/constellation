#include "CombatLabEditorLibrary.h"
#include "CombatLabCharacter.h"
#include "CombatActionDefinition.h"
#include "CombatAbilitySystem.h"
#include "CombatPatternProfile.h"
#include "CombatEncounterProfile.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

bool UCombatLabEditorLibrary::ValidateCombatCharacter(ACombatLabCharacter* Character,TArray<FString>& Errors,TArray<FString>& Warnings)
{
    Errors.Reset(); Warnings.Reset();
    if(!Character || !Character->bTrainingEnemy)
    { Errors.Add(TEXT("CombatLabCharacter 몬스터(Training Enemy)를 하나 선택하세요.")); return false; }
    auto* Mesh=Character->GetMesh()->GetSkeletalMeshAsset();
    if(!Mesh || !Mesh->GetSkeleton()) Errors.Add(TEXT("Mesh: 스켈레톤이 있는 메시가 필요합니다."));
    const auto CheckAnimation=[&](UAnimSequence* Animation,const TCHAR* Field)
    {
        if(!Animation) Errors.Add(FString(Field)+TEXT(": 애니메이션이 없습니다."));
        else if(Mesh && Animation->GetSkeleton()!=Mesh->GetSkeleton())
            Errors.Add(FString(Field)+TEXT(": 메시와 스켈레톤이 다릅니다."));
    };
    CheckAnimation(Character->IdleAnimation,TEXT("IdleAnimation"));
    CheckAnimation(Character->MoveAnimation,TEXT("MoveAnimation"));
    if(!FMath::IsFinite(Character->AnimationMoveSpeed) || Character->AnimationMoveSpeed<=0)
        Errors.Add(TEXT("AnimationMoveSpeed: 양의 유한한 기준 속도가 필요합니다."));

    auto* Encounter=Character->EncounterProfile.Get();
    FString Reason;
    const bool EncounterValid=Encounter && Encounter->Validate(Reason);
    if(!EncounterValid) Errors.Add(TEXT("EncounterProfile: ")+(Encounter?Reason:TEXT("교전 프로필이 없습니다.")));
    auto* Profile=Character->PatternProfile.Get();
    if(!Profile) { Errors.Add(TEXT("PatternProfile: 공격 패턴 프로필이 없습니다.")); return Errors.IsEmpty(); }
    TSet<FName> PatternIds;
    int32 Enabled=0,CoversStop=0;
    const FCombatPatternEntry* OnlyEnabled=nullptr;
    for(const auto& Pattern:Profile->Patterns)
    {
        const FString Prefix=FString::Printf(TEXT("Patterns.%s: "),*Pattern.Id.ToString());
        if(Pattern.Id.IsNone() || PatternIds.Contains(Pattern.Id))
            Errors.Add(Prefix+TEXT("Id: 비어 있거나 중복된 패턴 이름입니다."));
        PatternIds.Add(Pattern.Id);
        if(!FMath::IsFinite(Pattern.MinDistance) || !FMath::IsFinite(Pattern.MaxDistance) ||
            Pattern.MinDistance<0 || Pattern.MaxDistance<Pattern.MinDistance ||
            !FMath::IsFinite(Pattern.MaxAngle) || Pattern.MaxAngle<0 || Pattern.MaxAngle>180 ||
            !FMath::IsFinite(Pattern.Weight) || Pattern.Weight<0 || Pattern.MaxConsecutive<0)
            Errors.Add(Prefix+TEXT("거리·각도·가중치·연속 제한의 범위를 확인하세요."));
        auto* Action=Pattern.Action.Get();
        if(!Action) Errors.Add(Prefix+TEXT("Action: 공격 액션이 없습니다."));
        if(Action)
        {
            FString ActionError;
            if(!Action->Validate(ActionError)) Errors.Add(Prefix+ActionError);
            if(!Character->Combat || !FMath::IsFinite(Character->Combat->MaxStamina) || Character->Combat->MaxStamina<=0 || Action->StaminaCost>Character->Combat->MaxStamina) Errors.Add(Prefix+TEXT("StaminaCost가 설정된 최대 SP를 초과하거나 최대 SP가 잘못되었습니다."));
            if(Action->NextAction) Errors.Add(Prefix+TEXT("NextAction: 몬스터 제작 도구는 플레이어 콤보 연결을 지원하지 않습니다."));
            if(Mesh && Action->Montage && Action->Montage->GetSkeleton()!=Mesh->GetSkeleton())
                Errors.Add(Prefix+TEXT("Montage: 메시와 스켈레톤이 다릅니다."));
        }
        if(Pattern.Weight<=0 || !FMath::IsFinite(Pattern.Weight)) continue;
        ++Enabled; OnlyEnabled=&Pattern;
        if(EncounterValid && Pattern.MinDistance<=FMath::Max(0.f,Encounter->AttackDistance-20.f) &&
            Pattern.MaxDistance>=Encounter->AttackDistance) ++CoversStop;
    }
    if(Enabled==0) Errors.Add(TEXT("Patterns: Weight가 양수인 활성 패턴이 없습니다."));
    else if(EncounterValid && CoversStop==0)
        Errors.Add(TEXT("AttackDistance: 접근 정지 구간 [AttackDistance-20, AttackDistance]을 커버하는 활성 패턴이 없습니다."));
    if(Enabled==1 && OnlyEnabled->MaxConsecutive>0)
        Warnings.Add(TEXT("MaxConsecutive: 유일한 활성 패턴의 연속 제한을 소진하면 계속 대기할 수 있습니다."));
    if(EncounterValid && Encounter->LeashRadius<Encounter->DetectRadius)
        Warnings.Add(TEXT("LeashRadius가 DetectRadius보다 작아 시작점 기준 교전 범위가 먼저 적용됩니다."));
    Warnings.Add(TEXT("데이터 연결 검사입니다. 경로 이동·공격 타격·모션 품질은 플레이로 확인하세요."));
    return Errors.IsEmpty();
}
