#include "SwordAcquisitionStage.h"
#include "SwordAcquisitionAnimationSet.h"
#include "SceneDirectorPlayer.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"

bool ASwordAcquisitionStage::BeginAnimation()
{
 auto* Mesh=Character->GetMesh();auto* Anim=Mesh->GetAnimInstance();
 if(!Anim||Anim->IsAnyMontagePlaying())return false;
 SwordMesh=nullptr;
 for(auto* Component:Sword->GetComponents())
  if(auto* Static=Cast<UStaticMeshComponent>(Component);Static&&Static->GetStaticMesh()&&Static->GetStaticMesh()->GetName()==TEXT("SM_Weapon_Sword")){SwordMesh=Static;break;}
 if(!SwordMesh.IsValid())return false;
 RuntimeMontages.Empty();
 for(FName Name:{TEXT("Approach"),TEXT("BraceLoop"),TEXT("ExtractRecover"),TEXT("ReleaseLeft"),TEXT("Raise"),TEXT("RaisedHoldLoop"),TEXT("Lower")})
 {
  const auto* Clip=AnimationSet->Clips.Find(Name);
  if(!Clip||!Clip->Montage||Clip->SwordSamples.Num()<2)return false;
  auto* Copy=DuplicateObject<UAnimMontage>(Clip->Montage,this);Copy->SetFlags(RF_Transient);
  if(Copy->CompositeSections.Num()!=1)return false;
  Copy->bEnableAutoBlendOut=false;
  Copy->CompositeSections[0].NextSectionName=Clip->bLoop?Copy->CompositeSections[0].SectionName:NAME_None;
  RuntimeMontages.Add(Name,Copy);
 }
 BeforeSwordMesh=SwordMesh->GetComponentTransform();OldSwordMobility=uint8(SwordMesh->Mobility);
 SwordMesh->SetMobility(EComponentMobility::Movable);
 bOldPostDisabled=Mesh->GetDisablePostProcessBlueprint();Mesh->SetDisablePostProcessBlueprint(true);
 // Read montage position after skeletal update, so prop and rendered body share a clock.
 PrimaryActorTick.TickGroup=TG_PostPhysics;AddTickPrerequisiteComponent(Mesh);
 AnimationClip=NAME_None;AnimationQueue.Empty();LoopAfterQueue=NAME_None;bAnimationWaiting=false;bAnimationInstalled=true;
 return true;
}
bool ASwordAcquisitionStage::PlayAnimation(FName Clip)
{
 auto* Anim=Character->GetMesh()->GetAnimInstance();auto* Montage=RuntimeMontages.FindRef(Clip).Get();
 if(!Anim||!Montage)return false;
 // Adjacent delivered clips have matching authored boundary poses.
 if(Anim->Montage_PlayWithBlendIn(Montage,FAlphaBlendArgs(ActiveMontage?0.f:.2f),1.f)<=0)return false;
 ActiveMontage=Montage;AnimationClip=Clip;AnimationTime=0;
 UE_LOG(LogTemp,Display,TEXT("SwordAcquisition animation=%s"),*Clip.ToString());return true;
}
bool ASwordAcquisitionStage::QueueAnimation(FName Cue)
{
 if(bAnimationWaiting||!Director.IsValid())return false;
 if(Cue==TEXT("Grip")){AnimationQueue={TEXT("Approach")};LoopAfterQueue=TEXT("BraceLoop");}
 else if(Cue==TEXT("Pull")){AnimationQueue={TEXT("ExtractRecover"),TEXT("ReleaseLeft")};LoopAfterQueue=NAME_None;}
 else if(Cue==TEXT("RaiseHold")){AnimationQueue={TEXT("Raise")};LoopAfterQueue=TEXT("RaisedHoldLoop");}
 else if(Cue==TEXT("Lower")){AnimationQueue={TEXT("Lower")};LoopAfterQueue=NAME_None;}
 else return false;
 Director->SetDirectorPaused(true);bAnimationWaiting=true;
 const auto* Current=AnimationSet->Clips.Find(AnimationClip);
 if(ActiveMontage&&Current&&Current->bLoop)
 {
  // Finish the current breath cycle, then exit at its authored matching pose.
  Character->GetMesh()->GetAnimInstance()->Montage_SetNextSection(ActiveMontage->CompositeSections[0].SectionName,NAME_None,ActiveMontage);
  return true;
 }
 const FName Next=AnimationQueue[0];AnimationQueue.RemoveAt(0);return PlayAnimation(Next);
}
void ASwordAcquisitionStage::TickAnimation()
{
 if(!Character.IsValid()||!SwordMesh.IsValid()||!ActiveMontage)return;
 auto* Anim=Character->GetMesh()->GetAnimInstance();if(!Anim)return;
 AnimationTime=Anim->Montage_GetPosition(ActiveMontage);
 const auto* Clip=AnimationSet->Clips.Find(AnimationClip);if(!Clip)return;
 const float Frame=FMath::Clamp(AnimationTime*AnimationSet->SampleRate,0.f,float(Clip->SwordSamples.Num()-1));
 const int32 A=FMath::FloorToInt(Frame),B=FMath::Min(A+1,Clip->SwordSamples.Num()-1);
 FTransform Prop;Prop.Blend(Clip->SwordSamples[A],Clip->SwordSamples[B],Frame-A);
 SwordMesh->SetWorldTransform(AnimationSet->MeshToGuard*Prop*Character->GetMesh()->GetComponentTransform(),false,nullptr,ETeleportType::TeleportPhysics);
 if(bAnimationWaiting&&AnimationTime>=ActiveMontage->GetPlayLength()-KINDA_SMALL_NUMBER)
 {
  if(!AnimationQueue.IsEmpty())
  {
   const FName Next=AnimationQueue[0];AnimationQueue.RemoveAt(0);
   if(!PlayAnimation(Next))Director->StopDirector();
  }
  else
  {
   bAnimationWaiting=false;
   if(!LoopAfterQueue.IsNone()&&!PlayAnimation(LoopAfterQueue)){Director->StopDirector();return;}
   LoopAfterQueue=NAME_None;Director->SetDirectorPaused(false);
  }
 }
}
void ASwordAcquisitionStage::RestoreAnimation(bool Cancelled)
{
 if(!bAnimationInstalled)return;
 if(auto* C=Character.Get())
 {
  auto* Mesh=C->GetMesh();if(auto* Anim=Mesh->GetAnimInstance();Anim&&ActiveMontage)Anim->Montage_Stop(Cancelled?0.f:.35f,ActiveMontage);
  Mesh->SetDisablePostProcessBlueprint(bOldPostDisabled);RemoveTickPrerequisiteComponent(Mesh);
 }
 if(SwordMesh.IsValid())
 {
  SwordMesh->SetWorldTransform(BeforeSwordMesh,false,nullptr,ETeleportType::TeleportPhysics);
  SwordMesh->SetMobility(EComponentMobility::Type(OldSwordMobility));
 }
 ActiveMontage=nullptr;RuntimeMontages.Empty();AnimationQueue.Empty();AnimationClip=NAME_None;
 bAnimationWaiting=bAnimationInstalled=false;
}
