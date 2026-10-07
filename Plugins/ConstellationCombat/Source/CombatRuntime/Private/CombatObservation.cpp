#include "CombatObservation.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatHitWindow.h"
#include "CombatLabCharacter.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"

FCombatActionObservation UCombatAbilitySystem::ObserveAction() const
{
    FCombatActionObservation O;
    if(GetHealth()<=0) {O.Phase=TEXT("사망");return O;}
    if(IsDodging()) {O.Phase=IsInvulnerable()?TEXT("회피 · 무적"):TEXT("회피");return O;}
    if(IsHitReacting()) {O.Phase=TEXT("피격 경직");return O;}
    if(!ActiveAction) return O;
    O.Phase=TEXT("공격 시작 중");
    const auto* C=Cast<ACharacter>(GetAvatarActor());
    auto* Anim=C?C->GetMesh()->GetAnimInstance():nullptr;
    auto* Instance=Anim?Anim->GetActiveInstanceForMontage(ActiveAction->Montage):nullptr;
    if(!Instance || !MatchesMontageInstance(Instance->GetInstanceID())) return O;
    O.bActive=true; O.bHitOpen=Ledger.HasOpenWindow();
    O.Position=Instance->GetPosition(); O.Duration=ActiveAction->Montage->GetPlayLength();
    O.Name=ActiveAction->DisplayName.ToString();
    O.bHasFollowup=ActiveAction->NextAction!=nullptr;
    O.InputStart=ActiveAction->InputWindowStart; O.InputEnd=ActiveAction->InputWindowEnd;
    O.bInputOpen=O.bHasFollowup && O.Position>=O.InputStart && O.Position<=O.InputEnd;
    bool Future=false,Past=false;
    for(const FAnimNotifyEvent& Event:ActiveAction->Montage->Notifies)
        if(Cast<UCombatHitWindow>(Event.NotifyStateClass))
        {
            Future|=Event.GetTriggerTime()>O.Position;
            Past|=Event.GetEndTriggerTime()<=O.Position;
        }
    // Only the hit ledger can say that a hit window is actually open.
    O.Phase=O.bHitOpen?TEXT("타격 판정 중"):Future?(Past?TEXT("다음 타격 준비"):TEXT("공격 준비")):Past?TEXT("공격 회수"):TEXT("타격 구간 · 판정 닫힘");
    return O;
}
float UCombatAbilitySystem::GetCooldownRemaining(const UCombatActionDefinition* Action) const
{
    if(const double* End=Cooldowns.Find(Action))
        return GetWorld()?FMath::Max(0.f,float(*End-GetWorld()->GetTimeSeconds())):0.f;
    return 0;
}
void UCombatAbilitySystem::RecordDamage(float Damage,AActor* Source,bool Avoided)
{
    FCombatDamageRecord R;
    R.GameTime=GetWorld()?GetWorld()->GetTimeSeconds():0;
    R.Damage=Damage; R.HealthAfter=GetHealth(); R.bAvoided=Avoided;
    if(auto* C=Cast<ACombatLabCharacter>(Source)) R.Source=C->bTrainingEnemy?TEXT("몬스터"):TEXT("플레이어");
    else R.Source=Source?Source->GetName():TEXT("환경 / 테스트");
    if(DamageHistory.Num()>=12) DamageHistory.RemoveAt(0);
    DamageHistory.Add(MoveTemp(R));
}
FString CombatObservation::ExplainReason(const FString& Reason)
{
    if(Reason.IsEmpty()) return TEXT("없음");
    static const TMap<FString,FString> Labels={
        {TEXT("No buffered attack"),TEXT("예약 없음")},
        {TEXT("Not enough stamina"),TEXT("SP 부족")},
        {TEXT("Not enough ultimate charge"),TEXT("궁극기 게이지 부족")},
        {TEXT("Resource commit in progress"),TEXT("행동 비용 처리 중")},
        {TEXT("Skill slot empty"),TEXT("스킬 미지정")},
        {TEXT("Ultimate slot empty"),TEXT("궁극기 미지정")},
        {TEXT("Carry interaction active"),TEXT("물건 들기·던지기 중")},
        {TEXT("Gameplay input blocked"),TEXT("연출 또는 입력 잠금 중")},
        {TEXT("Traversal or transformation active"),TEXT("등반·밀기·변신 동작 중")},
        {TEXT("Interaction blocks combat"),TEXT("상호작용 중")},
        {TEXT("Interaction query in progress"),TEXT("상호작용 상태 확인 중")},
        {TEXT("Waiting for encounter attack slot"),TEXT("교전 공격 차례 대기")},
        {TEXT("Dash requires ground"),TEXT("돌진은 지상에서만 가능")},
        {TEXT("Skill started"),TEXT("스킬 실행")},
        {TEXT("Ultimate started"),TEXT("궁극기 실행")},
        {TEXT("Cooldown"),TEXT("쿨다운 대기")},
        {TEXT("Dead"),TEXT("사망")},
        {TEXT("Hit reaction"),TEXT("피격 경직 중")},
        {TEXT("Dodging"),TEXT("회피 중")},
        {TEXT("Dodge started"),TEXT("회피 시작")},
        {TEXT("Dodge requires ground"),TEXT("회피는 지상에서만 가능")},
        {TEXT("Cannot dodge during another action"),TEXT("현재 상태에서 회피 불가")},
        {TEXT("Dodge cancel window closed"),TEXT("회피 전환 구간이 아님")},
        {TEXT("Dodge transition interrupted"),TEXT("회피 전환 중단")},
        {TEXT("Another action is active"),TEXT("현재 공격 진행 중")},
        {TEXT("No follow-up"),TEXT("마지막 타격 · 후속 공격 없음")},
        {TEXT("Outside follow-up input window"),TEXT("선입력 가능 구간이 아님")},
        {TEXT("Follow-up queued"),TEXT("후속 공격 예약됨")},
        {TEXT("Follow-up started"),TEXT("예약 공격 시작")},
        {TEXT("Queue cancelled"),TEXT("후속 공격 예약 취소")},
        {TEXT("Started"),TEXT("공격 시작")},
        {TEXT("Action started"),TEXT("공격 시작")},
        {TEXT("Completed"),TEXT("공격 완료")},
        {TEXT("Cancelled"),TEXT("공격 취소")},
        {TEXT("Failed"),TEXT("공격 실행 실패")},
        {TEXT("Encounter reset"),TEXT("복귀 후 자원 회복")}
    };
    if(const FString* Label=Labels.Find(Reason)) return *Label;
    return Reason;
}
