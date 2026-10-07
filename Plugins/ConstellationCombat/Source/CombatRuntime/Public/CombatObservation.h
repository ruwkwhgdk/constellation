#pragma once
#include "CoreMinimal.h"

// Read-only observation of the executing montage. Times are montage seconds, not wall-clock seconds.
struct FCombatActionObservation
{
    bool bActive=false, bHitOpen=false, bInputOpen=false, bHasFollowup=false;
    float Position=0, Duration=0, InputStart=0, InputEnd=0;
    FString Phase=TEXT("대기"), Name;
};
struct FCombatDamageRecord
{
    float GameTime=0, Damage=0, HealthAfter=0;
    bool bAvoided=false;
    FString Source;
};
namespace CombatObservation
{
    COMBATRUNTIME_API FString ExplainReason(const FString& Reason);
}
