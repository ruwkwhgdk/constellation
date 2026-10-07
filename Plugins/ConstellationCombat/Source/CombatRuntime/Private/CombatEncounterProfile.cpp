#include "CombatEncounterProfile.h"
#include "Misc/DataValidation.h"
bool UCombatEncounterProfile::Validate(FString& Reason) const
{
    for(float Value:{DetectRadius,LoseRadius,LeashRadius,AttackDistance,MoveSpeed,ThinkInterval,HomeTolerance,RetryDelay,RetryCooldown,StuckTimeout})
        if(!FMath::IsFinite(Value) || Value<=0) { Reason=TEXT("Encounter values must be finite and positive"); return false; }
    if(LoseRadius<DetectRadius || AttackDistance>=DetectRadius || HomeTolerance>=LeashRadius ||
        !FMath::IsFinite(LostSightTime) || LostSightTime<0 || MaxMoveFailures<1)
        { Reason=TEXT("Invalid detection, leash or retry ranges"); return false; }
    Reason.Reset(); return true;
}
#if WITH_EDITOR
EDataValidationResult UCombatEncounterProfile::IsDataValid(FDataValidationContext& Context) const
{
    FString Reason;
    if(!Validate(Reason)) { Context.AddError(FText::FromString(Reason)); return EDataValidationResult::Invalid; }
    return EDataValidationResult::Valid;
}
#endif
