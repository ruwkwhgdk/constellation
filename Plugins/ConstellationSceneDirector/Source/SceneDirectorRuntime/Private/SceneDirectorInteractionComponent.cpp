#include "SceneDirectorInteractionComponent.h"
#include "SceneEventSubsystem.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorAsset.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"
bool USceneDirectorInteractionComponent::RouteInteraction(AActor* Owner,AActor* Interactor)
{
 if(!IsValid(Owner))return false;
 if(auto* S=Owner->GetWorld()->GetSubsystem<USceneEventSubsystem>();S&&S->RouteInteraction(Owner,Interactor))return true;
 auto* C=Owner->FindComponentByClass<USceneDirectorInteractionComponent>();return C&&C->HandleInteraction(Interactor);
}
bool USceneDirectorInteractionComponent::HandleInteraction(AActor* Interactor)
{
 if(IsValid(ActivePlayer)&&ActivePlayer->IsDirectorPlaying())return true;
 if(!GetWorld())return false;LastError.Reset();auto* PC=GetWorld()->GetFirstPlayerController();
 if(!PC||PC->GetPawn()!=Interactor){LastError=TEXT("플레이어 상호작용이 필요합니다.");return true;}
 auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>();if(!S){LastError=TEXT("게임 월드가 필요합니다.");return true;}
 if(S->PendingCount()>0){LastError=TEXT("다른 연출이 대기 중입니다.");return true;}
 ActivePlayer=S->Start(Director,GetPathName(),GetOwner()->GetActorTransform(),Director&&Director->bUseInteractionOrigin,{},LastError);
 if(ActivePlayer)ActivePlayer->OnDirectorStopped.AddDynamic(this,&USceneDirectorInteractionComponent::Finished);
 return true;
}
void USceneDirectorInteractionComponent::Finished(bool)
{
 if(auto* R=ActivePlayer.Get()){LastError=R->LastError;R->OnDirectorStopped.RemoveDynamic(this,&USceneDirectorInteractionComponent::Finished);}ActivePlayer=nullptr;
}
void USceneDirectorInteractionComponent::Cancel(){if(IsValid(ActivePlayer))ActivePlayer->StopDirector();}
void USceneDirectorInteractionComponent::EndPlay(const EEndPlayReason::Type Reason){Cancel();Super::EndPlay(Reason);}
