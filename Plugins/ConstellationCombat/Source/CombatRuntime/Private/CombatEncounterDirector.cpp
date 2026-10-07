#include "CombatEncounterDirector.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "SceneEventSubsystem.h"
ACombatEncounterDirector::ACombatEncounterDirector(){PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=.1f;}
int32 ACombatEncounterDirector::ActiveAttackers() const
{
 int32 Count=0;
 for(const auto& Holder:Holders) if(Holder.IsValid() && IsValid(Holder->GetAvatarActor()) && Holder->GetHealth()>0) ++Count;
 return Count;
}
int32 ACombatEncounterDirector::LivingEnemies() const
{
 int32 Count=0;for(const auto& Enemy:Enemies) if(IsValid(Enemy) && Enemy->Combat->GetHealth()>0) ++Count;return Count;
}
bool ACombatEncounterDirector::CanAcquire(const UCombatAbilitySystem* System) const
{
 if(!System || Outcome!=ECombatEncounterOutcome::Active || System->GetHealth()<=0) return false;
 bool Member=false;for(const auto& Enemy:Enemies) if(IsValid(Enemy) && Enemy->Combat==System){Member=true;break;}
 if(!Member) return false;
 return Holders.Contains(const_cast<UCombatAbilitySystem*>(System)) || ActiveAttackers()<FMath::Clamp(MaxAttackers,1,16);
}
bool ACombatEncounterDirector::Acquire(UCombatAbilitySystem* System)
{
 if(!CanAcquire(System))return false;
 for(auto It=Holders.CreateIterator();It;++It)if(!It->IsValid() || !IsValid((*It)->GetAvatarActor()) || (*It)->GetHealth()<=0)It.RemoveCurrent();
 Holders.Add(System);return true;
}
void ACombatEncounterDirector::Release(UCombatAbilitySystem* System){Holders.Remove(System);}
void ACombatEncounterDirector::Tick(float Delta)
{
 Super::Tick(Delta);
 if(!HasAuthority() || Outcome!=ECombatEncounterOutcome::Active || Enemies.IsEmpty())return;
 if(!IsValid(Player) || Player->Combat->GetHealth()<=0) Outcome=ECombatEncounterOutcome::Failed;
 else if(LivingEnemies()==0) Outcome=ECombatEncounterOutcome::Completed;
 else return;
 // Freeze the result before callbacks; callbacks cannot acquire a new attack slot.
 for(const auto& Enemy:Enemies)if(IsValid(Enemy))Enemy->Combat->CancelAction();
 Holders.Reset();
 if(!BattleInstance.IsValid()) BattleInstance=FGuid::NewGuid();
 if(bNotifySceneEvents && !BattleZoneKey.IsNone())
  if(auto* Events=GetWorld()->GetSubsystem<USceneEventSubsystem>())
   Events->NotifyCombatFinished(BattleZoneKey,BattleInstance,Outcome==ECombatEncounterOutcome::Completed?ESceneCombatResult::Victory:ESceneCombatResult::Defeat);
 OnOutcomeChanged.Broadcast(Outcome);
}
