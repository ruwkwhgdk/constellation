#include "SceneSchoolAction.h"
#include "SceneDirectorPlayer.h"
#include "QuestSubsystem.h"
#include "Components/CapsuleComponent.h"
#include "UObject/StructOnScope.h"
bool USceneSchoolAction::Execute_Implementation(ASceneDirectorPlayer* P,AActor* T,const FDirectorActionParameters& V,FString& E)
{
 const FName Op=V.Identifier;
 if(Op==TEXT("AdvanceQuest")){UQuestSubsystem::AdvanceQuestProgressFor(P,TEXT("MQ1_ExitSchool"));return true;}
 if(!IsValid(T)){E=TEXT("학교 연출 대상이 없습니다: ")+Op.ToString();return false;}
 if(Op==TEXT("CapturePlayerPose"))return P->CaptureGameplayPose(T);
 if(Op==TEXT("DeactivateActor")){P->SetActorDeactivated(T,true);T->SetActorEnableCollision(false);return true;}
 if(Op==TEXT("HideActor")){P->SetActorDeactivated(T,true);return true;}
 if(Op==TEXT("ResizeCapsule")){if(auto* C=T->FindComponentByClass<UCapsuleComponent>()){C->SetCapsuleSize(V.Amount,V.Value);return true;}E=TEXT("CapsuleComponent 없음");return false;}
 FName Function=NAME_None;
 if(Op==TEXT("ActivateNPC"))Function=TEXT("Activate NPC");
 if(Op==TEXT("DeactivateNPC"))Function=TEXT("Deactivate NPC");
 if(Op==TEXT("TriggerCache"))Function=TEXT("TriggerAll");
 auto* F=Function.IsNone()?nullptr:T->FindFunction(Function);
 if(Op==TEXT("ActivateNPC")&&F)
 {
  auto* Collision=FindFProperty<FBoolProperty>(F,TEXT("ActivateCollision"));auto* Movement=FindFProperty<FBoolProperty>(F,TEXT("ActivateMovement"));
  if(F->NumParms!=2||!Collision||!Movement){E=TEXT("NPC 활성화 함수의 인수가 변경되었습니다.");return false;}FStructOnScope Args(F);Collision->SetPropertyValue_InContainer(Args.GetStructMemory(),false);Movement->SetPropertyValue_InContainer(Args.GetStructMemory(),false);T->ProcessEvent(F,Args.GetStructMemory());
  P->SetActorDeactivated(T,false);return true;
 }
 if(!F||F->NumParms){E=TEXT("검증된 무인자 게임 함수가 없습니다: ")+Function.ToString();return false;}
 T->ProcessEvent(F,nullptr);if(Op==TEXT("DeactivateNPC"))P->SetActorDeactivated(T,true);return true;
}
