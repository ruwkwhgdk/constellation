#include "CombatHitReactionComponent.h"
#include "CombatAbilitySystem.h"
#include "CombatLabCharacter.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Character.h"

UCombatHitReactionComponent::UCombatHitReactionComponent()
{
 PrimaryComponentTick.bCanEverTick=true;
 PrimaryComponentTick.bStartWithTickEnabled=false;
 const FString Base=TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Hit_");
 FrontAnimation=TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(Base+TEXT("Front.AS_player_heroine_new_Hit_Front")));
 BackAnimation=TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(Base+TEXT("Back.AS_player_heroine_new_Hit_Back")));
 LeftAnimation=TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(Base+TEXT("Left.AS_player_heroine_new_Hit_Left")));
 RightAnimation=TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(Base+TEXT("Right.AS_player_heroine_new_Hit_Right")));
}
void UCombatHitReactionComponent::Initialize(UCombatAbilitySystem* InCombat)
{
 StopReaction();
 if(Combat.IsValid())
 {
  Combat->OnDamageAccepted.RemoveAll(this); Combat->OnPresentationReset.RemoveAll(this); Combat->OnDied.RemoveAll(this);
 }
 Combat=InCombat; LoadedClips.Reset();
 auto* Character=Cast<ACharacter>(GetOwner()); Mesh=Character?Character->GetMesh():nullptr;
 if(!Combat.IsValid()) return;
 if(Mesh.IsValid() && Mesh->GetSkeletalMeshAsset() && Mesh->GetSkeletalMeshAsset()->GetName()==TEXT("SK_player_heroine_new_RunPreview"))
 {
  for(const TSoftObjectPtr<UAnimSequence>& Asset : {FrontAnimation,BackAnimation,LeftAnimation,RightAnimation})
  {
   UAnimSequence* Clip=Asset.LoadSynchronous();
   if(!Clip || !Clip->GetSkeleton() || !Clip->GetSkeleton()->IsCompatibleMesh(Mesh->GetSkeletalMeshAsset()))
   {
    UE_LOG(LogTemp,Warning,TEXT("Combat reaction unavailable: %s (loaded=%s, clip skeleton=%s, mesh skeleton=%s)"),*Asset.ToString(),Clip?TEXT("yes"):TEXT("no"),*GetNameSafe(Clip?Clip->GetSkeleton():nullptr),*GetNameSafe(Mesh->GetSkeletalMeshAsset()->GetSkeleton()));
    Clip=nullptr;
   }
   LoadedClips.Add(Clip);
  }
 }
 Combat->OnDamageAccepted.AddUObject(this,&UCombatHitReactionComponent::ReceiveHit);
 Combat->OnPresentationReset.AddUObject(this,&UCombatHitReactionComponent::StopReaction);
 Combat->OnDied.AddUObject(this,&UCombatHitReactionComponent::StopReaction);
}
void UCombatHitReactionComponent::ReceiveHit(const FCombatAcceptedDamage& Hit)
{
 StopReaction();
 if(!Combat.IsValid() || Combat->GetHealth()<=0 || !Mesh.IsValid() || !Mesh->GetSkeletalMeshAsset()) return;
 Duration=Combat->GetHitReactionRemaining();
 if(Duration<=0) return;
 // This pass intentionally leaves slime model/animation behavior untouched.
 if(Mesh->GetSkeletalMeshAsset()->GetName()!=TEXT("SK_player_heroine_new_RunPreview")) return;
 Elapsed=0;
 auto* Single=Mesh->GetSingleNodeInstance();
 if(!Single) return;
 const FVector D=Hit.LocalSourceDirection;
 const int32 Index=FMath::Abs(D.X)>=FMath::Abs(D.Y)?(D.X>=0?0:1):(D.Y>=0?3:2);
 UAnimSequence* Clip=LoadedClips.IsValidIndex(Index)?LoadedClips[Index].Get():nullptr;
 if(!Clip) return;
 SavedAnimation=Single->GetCurrentAsset(); SavedPosition=Single->GetCurrentTime(); SavedRate=Single->GetPlayRate();
 bSavedPlaying=Single->IsPlaying(); bSavedLooping=Single->IsLooping();
 // Damage has already cancelled the action, but SingleNode retains its montage asset.
 // Never resurrect that execution when presentation ends; resume the lab idle instead.
 if(Cast<UAnimMontage>(SavedAnimation))
 {
  const auto* Lab=Cast<ACombatLabCharacter>(GetOwner());
  SavedAnimation=Lab?Lab->IdleAnimation.Get():nullptr;
  SavedPosition=0.f; SavedRate=1.f; bSavedLooping=true; bSavedPlaying=SavedAnimation!=nullptr;
 }
 Single->SetAnimationAsset(Clip,false,Clip->GetPlayLength()/Duration); Single->SetPosition(0,false); Single->SetPlaying(true);
 bOwnsAnimation=true;
 bPresenting=true; SetComponentTickEnabled(true);
}
void UCombatHitReactionComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
 Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
 if(!bPresenting) return;
 if(!Combat.IsValid() || !Mesh.IsValid() || Combat->GetHealth()<=0 || !Combat->IsHitReacting()) {StopReaction();return;}
 if(!FMath::IsFinite(DeltaTime) || DeltaTime<=0) return;
 Elapsed+=DeltaTime;
 if(Elapsed>=Duration) {StopReaction();return;}

}
void UCombatHitReactionComponent::StopReaction()
{
 if(bPresenting && Mesh.IsValid())
 {
  if(bOwnsAnimation) if(auto* Single=Mesh->GetSingleNodeInstance())
  {
   Single->SetAnimationAsset(SavedAnimation,bSavedLooping,SavedRate); Single->SetPosition(SavedPosition,false); Single->SetPlaying(bSavedPlaying);
  }
 }
 bPresenting=false; bOwnsAnimation=false; SavedAnimation=nullptr; SetComponentTickEnabled(false);
}
void UCombatHitReactionComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 StopReaction();
 if(Combat.IsValid()) {Combat->OnDamageAccepted.RemoveAll(this);Combat->OnPresentationReset.RemoveAll(this);Combat->OnDied.RemoveAll(this);}
 Super::EndPlay(Reason);
}
