#include "CombatPatternProfile.h"
#include "CombatActionDefinition.h"
#include "CombatAbilitySystem.h"
#include "Misc/DataValidation.h"
bool UCombatPatternProfile::Validate(FString& Reason) const
{
    if(Patterns.IsEmpty()) { Reason=TEXT("At least one pattern is required"); return false; }
    TSet<FName> Ids;
    for(const auto& P:Patterns)
    {
        if(P.Id.IsNone() || Ids.Contains(P.Id)) { Reason=TEXT("Pattern IDs must be nonempty and unique"); return false; }
        Ids.Add(P.Id);
        if(!P.Action || !P.Action->Validate(Reason)) { Reason=P.Id.ToString()+TEXT(": invalid action ")+Reason; return false; }
        if(!FMath::IsFinite(P.MinDistance) || !FMath::IsFinite(P.MaxDistance) || P.MinDistance<0 || P.MaxDistance<P.MinDistance ||
            !FMath::IsFinite(P.MaxAngle) || P.MaxAngle<0 || P.MaxAngle>180 || !FMath::IsFinite(P.Weight) || P.Weight<0 || P.MaxConsecutive<0)
            { Reason=P.Id.ToString()+TEXT(": invalid range, angle, weight or repeat limit"); return false; }
    }
    Reason.Reset(); return true;
}
int32 UCombatPatternProfile::Select(const UCombatAbilitySystem* System,float Distance,float Angle,bool HasSight,FName LastId,int32 Consecutive,float Roll,FString& Reason) const
{
    Reason.Reset();
    if(!Validate(Reason)) return INDEX_NONE;
    if(!System || !FMath::IsFinite(Distance) || Distance<0 || !FMath::IsFinite(Angle) || Angle<0 || Angle>180 || !FMath::IsFinite(Roll))
        { Reason=TEXT("Invalid selection context"); return INDEX_NONE; }
    TArray<int32> Candidates; double Total=0;
    for(int32 Index=0;Index<Patterns.Num();++Index)
    {
        const auto& P=Patterns[Index]; FString Excluded;
        if(P.Weight<=0) Excluded=TEXT("Disabled");
        else if(Distance<P.MinDistance || Distance>P.MaxDistance) Excluded=TEXT("Distance");
        else if(Angle>P.MaxAngle) Excluded=TEXT("Angle");
        else if(P.bRequireSight && !HasSight) Excluded=TEXT("Sight");
        else if(P.MaxConsecutive>0 && P.Id==LastId && Consecutive>=P.MaxConsecutive) Excluded=TEXT("Repeat limit");
        else System->CanStart(P.Action,Excluded);
        if(!Excluded.IsEmpty()) Reason+=P.Id.ToString()+TEXT(": ")+Excluded+TEXT("; ");
        else { Candidates.Add(Index); Total+=P.Weight; }
    }
    if(Candidates.IsEmpty()) { Reason+=TEXT("No eligible pattern"); return INDEX_NONE; }
    const double Ticket=FMath::Clamp(static_cast<double>(Roll),0.,1.)*Total;
    double Accumulated=0;
    for(int32 Index:Candidates)
    {
        Accumulated+=Patterns[Index].Weight;
        if(Ticket<Accumulated || Index==Candidates.Last())
        { Reason+=TEXT("Selected ")+Patterns[Index].Id.ToString(); return Index; }
    }
    return INDEX_NONE;
}
#if WITH_EDITOR
EDataValidationResult UCombatPatternProfile::IsDataValid(FDataValidationContext& Context) const
{
    FString Reason;
    if(!Validate(Reason)) { Context.AddError(FText::FromString(Reason)); return EDataValidationResult::Invalid; }
    return EDataValidationResult::Valid;
}
#endif
