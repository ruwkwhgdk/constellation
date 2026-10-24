#include "ItemAcquisitionSceneAction.h"
#include "ItemAcquisitionDefinition.h"
#include "ItemAcquisitionSubsystem.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"

bool UItemAcquisitionSceneLease::Begin(const FItemAcquisitionPresentation& Presentation,FKey Key,FString& Error)
{
 Error.Reset();
 auto* Scene=Cast<ASceneDirectorPlayer>(GetOwner());
 auto* UI=GetWorld()?GetWorld()->GetSubsystem<UItemAcquisitionSubsystem>():nullptr;
 if(bPending){Error=TEXT("이 연출에는 이미 대기 중인 아이템 표시가 있습니다.");return false;}
 if(!Scene||!Scene->IsDirectorPlaying()||!UI){Error=TEXT("실행 중인 연출과 아이템 표시 서브시스템이 필요합니다.");return false;}
 bPreviousPaused=Scene->IsDirectorPaused();bPending=true;
 Scene->OnDirectorStopped.AddUniqueDynamic(this,&UItemAcquisitionSceneLease::DirectorStopped);
 Scene->SetDirectorPaused(true);
 TWeakObjectPtr<UItemAcquisitionSceneLease> Weak(this);
 const FGuid Id=UI->Enqueue(Presentation,Key,this,[Weak](bool Confirmed){if(auto* Lease=Weak.Get())Lease->Resolve(Confirmed);});
 // Rejection may synchronously call Resolve: do not resurrect the finished request.
 if(!bPending||!Id.IsValid())
 {
  if(bPending)Resolve(false);
  Error=TEXT("아이템 표시 요청을 시작할 수 없습니다.");return false;
 }
 RequestId=Id;return true;
}
void UItemAcquisitionSceneLease::Resolve(bool Confirmed)
{
 if(!bPending)return;
 bPending=false;RequestId.Invalidate();
 if(auto* Scene=Cast<ASceneDirectorPlayer>(GetOwner()))
 {
  Scene->OnDirectorStopped.RemoveDynamic(this,&UItemAcquisitionSceneLease::DirectorStopped);
  if(Scene->IsDirectorPlaying())
  {
   if(Confirmed)Scene->SetDirectorPaused(bPreviousPaused);
   else Scene->StopDirector(); // Cancellation must never run subsequent grant/event nodes.
  }
 }
}
void UItemAcquisitionSceneLease::CancelPending()
{
 if(!bPending)return;
 const FGuid Id=RequestId;
 bPending=false;RequestId.Invalidate(); // Cancel can synchronously invoke our callback.
 if(auto* Scene=Cast<ASceneDirectorPlayer>(GetOwner()))Scene->OnDirectorStopped.RemoveDynamic(this,&UItemAcquisitionSceneLease::DirectorStopped);
 if(Id.IsValid()&&GetWorld())if(auto* UI=GetWorld()->GetSubsystem<UItemAcquisitionSubsystem>())UI->Cancel(Id);
}
void UItemAcquisitionSceneLease::DirectorStopped(bool){CancelPending();}
void UItemAcquisitionSceneLease::EndPlay(const EEndPlayReason::Type Reason)
{
 const bool WasPending=bPending;CancelPending();
 if(WasPending)if(auto* Scene=Cast<ASceneDirectorPlayer>(GetOwner());Scene&&Scene->IsDirectorPlaying())Scene->StopDirector();
 Super::EndPlay(Reason);
}
bool UItemAcquisitionSceneAction::Execute_Implementation(ASceneDirectorPlayer* Player,AActor*,const FDirectorActionParameters& Parameters,FString& Error)
{
 Error.Reset();
 if(!IsValid(Player)||!IsValid(Definition)){Error=TEXT("아이템 표시 정의와 연출 플레이어가 필요합니다.");return false;}
 if(!Player->IsDirectorPlaying()){Error=TEXT("아이템 표시는 실행 중인 연출에서 호출해야 합니다.");return false;}
 if(Parameters.Amount<=0){Error=TEXT("아이템 표시 수량은 1 이상이어야 합니다.");return false;}
 auto* Lease=Player->FindComponentByClass<UItemAcquisitionSceneLease>();
 if(!Lease){Lease=NewObject<UItemAcquisitionSceneLease>(Player);Player->AddInstanceComponent(Lease);Lease->RegisterComponent();}
 FItemAcquisitionPresentation Presentation=Definition->Presentation;
 Presentation.Quantity=Parameters.Amount;
 return Lease->Begin(Presentation,ConfirmKey,Error);
}
