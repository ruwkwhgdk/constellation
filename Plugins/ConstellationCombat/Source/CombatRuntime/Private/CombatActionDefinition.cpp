#include "CombatActionDefinition.h"
#include "CombatHitWindow.h"
#include "Animation/AnimMontage.h"
#include "Misc/DataValidation.h"
bool UCombatActionDefinition::Validate(FString& Reason) const
{
    if (!Montage || !Montage->GetSkeleton() || Montage->GetPlayLength() <= 0.f)
        { Reason = TEXT("A valid montage and skeleton are required."); return false; }
    if (!FMath::IsFinite(Damage) || Damage < 0 || !FMath::IsFinite(StaminaCost) || StaminaCost < 0 ||
        !FMath::IsFinite(Cooldown) || Cooldown < 0 || !FMath::IsFinite(PlayRate) || PlayRate <= 0 ||
        !FMath::IsFinite(Reach) || Reach <= 0 || !FMath::IsFinite(Radius) || Radius <= 0)
        { Reason = TEXT("Action numbers must be finite and within their permitted ranges."); return false; }
    if(!FMath::IsFinite(UltimateCost) || UltimateCost<0 || UltimateCost>100 ||
        !FMath::IsFinite(UltimateGain) || UltimateGain<0 || UltimateGain>100)
        {Reason=TEXT("궁극기 비용·적중 충전량은 0~100이어야 합니다.");return false;}
    if(!FMath::IsFinite(DashDistance) || DashDistance<0 || !FMath::IsFinite(DashDuration) || DashDuration<=0 ||
        (DashDistance>0 && DashDuration>Montage->GetPlayLength()/PlayRate))
        {Reason=TEXT("돌진 거리·시간은 유효한 양수이며 행동 시간 이내여야 합니다.");return false;}
    if(NextAction && (!FMath::IsFinite(InputWindowStart) || !FMath::IsFinite(InputWindowEnd) ||
        InputWindowStart<0 || InputWindowEnd<=InputWindowStart || InputWindowEnd>Montage->GetPlayLength()))
        { Reason=TEXT("Follow-up input window must be a finite ordered range inside the montage."); return false; }
    if(bAllowDodgeCancel && (!FMath::IsFinite(DodgeCancelStart) || !FMath::IsFinite(DodgeCancelEnd) ||
        DodgeCancelStart<0 || DodgeCancelEnd<=DodgeCancelStart || DodgeCancelEnd>Montage->GetPlayLength()))
        {Reason=TEXT("회피 전환: 0 ≤ 시작 < 종료 ≤ 몽타주 길이여야 합니다.");return false;}
    TSet<FName> Names;
    for (const FAnimNotifyEvent& Event : Montage->Notifies)
    {
        if (const UCombatHitWindow* Window = Cast<UCombatHitWindow>(Event.NotifyStateClass))
        {
            if (Window->WindowId.IsNone() || Names.Contains(Window->WindowId) ||
                Event.GetTriggerTime() < 0.f || Event.GetDuration() <= 0.f ||
                Event.GetEndTriggerTime() > Montage->GetPlayLength() + KINDA_SMALL_NUMBER)
                { Reason = TEXT("Hit windows need unique IDs and valid montage time ranges."); return false; }
            Names.Add(Window->WindowId);
        }
    }
    if (Names.IsEmpty()) { Reason = TEXT("Add at least one Combat Hit Window to the montage."); return false; }
    Reason.Reset(); return true;
}
#if WITH_EDITOR
EDataValidationResult UCombatActionDefinition::IsDataValid(FDataValidationContext& Context) const
{
    FString Reason;
    if (!Validate(Reason)) { Context.AddError(FText::FromString(Reason)); return EDataValidationResult::Invalid; }
    return EDataValidationResult::Valid;
}
#endif
