#include "CombatAbilitySystem.h"
#include "CombatActionGate.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"
#include "UObject/UnrealType.h"
bool UCombatAbilitySystem::AllowsExternalAction(FString& Reason) const
{
 if(bCheckingExternalGate){Reason=TEXT("Interaction query in progress");return false;}
 TGuardValue<bool> Querying(bCheckingExternalGate,true);
 auto* Avatar=GetAvatarActor();if(!IsValid(Avatar)){Reason=TEXT("No combat actor");return false;}
 if(auto* Pawn=Cast<APawn>(Avatar);Pawn && Pawn->GetController() && Pawn->GetController()->IsMoveInputIgnored())
 {Reason=TEXT("Gameplay input blocked");return false;}
 for(FName Name:{FName(TEXT("IsPushing")),FName(TEXT("IsClimbing")),FName(TEXT("bIsJumping")),FName(TEXT("IsTransforming")),FName(TEXT("bIsTransforming"))})
  if(auto* Property=FindFProperty<FBoolProperty>(Avatar->GetClass(),Name);Property && Property->GetPropertyValue_InContainer(Avatar))
  {Reason=TEXT("Traversal or transformation active");return false;}
 TArray<UObject*> Gates;Gates.Add(Avatar);
 for(auto* Component:Avatar->GetComponents())Gates.Add(Component);
 for(auto* Gate:Gates)
  if(IsValid(Gate) && Gate->GetClass()->ImplementsInterface(UCombatActionGate::StaticClass()) &&
     !ICombatActionGate::Execute_AllowsCombatAction(Gate,Reason))
  {if(Reason.IsEmpty())Reason=TEXT("Interaction blocks combat");return false;}
 if(!IsValid(Avatar) || GetHealth()<=0){Reason=TEXT("Dead");return false;}
 Reason.Reset();return true;
}
