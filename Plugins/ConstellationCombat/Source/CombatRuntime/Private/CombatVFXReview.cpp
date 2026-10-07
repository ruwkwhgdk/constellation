#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatVFXComponent.h"
#include "CombatHitReactionComponent.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "CombatEnemyAgent.h"
#include "ConstellationFXActor.h"
#include "AIController.h"
#include "BrainComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "Materials/Material.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"
#include "InputKeyEventArgs.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "UnrealClient.h"
#include "Kismet/KismetSystemLibrary.h"

namespace
{
    void LogOwnedEffects(ACombatLabCharacter* Character,const TCHAR* Stage)
    {
        UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_CAPTURE stage=%s swordcolor=%s slimecolor=%s camera=%s"),Stage,
            *Character->CombatVFX->SwordColor.ToString(),*Character->CombatVFX->SlimeColor.ToString(),*Character->Camera->GetComponentLocation().ToString());
        if (const auto* View=UGameplayStatics::GetPlayerCameraManager(Character,0))
            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_VIEW stage=%s actualcamera=%s"),Stage,*View->GetCameraLocation().ToString());
        for(TActorIterator<AConstellationFXActor> It(Character->GetWorld());It;++It)
        {
            if(It->GetOwner()!=Character || It->IsActorBeingDestroyed() || It->ActorHasTag(TEXT("CombatVFXWarmup"))) continue;
            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_EFFECT stage=%s kind=%d owner=%s origin=%s particles=%d"),Stage,int32(It->EffectKind),*GetNameSafe(It->GetOwner()),*It->GetActorLocation().ToString(),It->ParticleCount);
            TInlineComponentArray<UInstancedStaticMeshComponent*> Components(*It);
            for(auto* Component:Components)
            {
                FLinearColor Tint=FLinearColor::Transparent;float Brightness=-1.f;
                auto* Material=Component->GetMaterial(0);
                if(Material){Material->GetVectorParameterValue(FMaterialParameterInfo(TEXT("Tint")),Tint);Material->GetScalarParameterValue(FMaterialParameterInfo(TEXT("Brightness")),Brightness);}
                FTransform Instance=FTransform::Identity;if(Component->GetInstanceCount()>0) Component->GetInstanceTransform(0,Instance,true);
                UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_RENDER component=%s extent=%s proxy=%d psopending=%d registered=%d visible=%d renderinstances=%d alpha=%.4f"),
                    *GetNameSafe(Component),*Component->Bounds.BoxExtent.ToString(),Component->GetSceneProxy()!=nullptr,Component->IsPSOPrecaching(),
                    Component->IsRegistered(),Component->IsVisible(),Component->GetNumRenderInstances(),
                    Component->PerInstanceSMCustomData.IsEmpty()?-1.f:Component->PerInstanceSMCustomData[0]);
                UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_MATERIAL component=%s mesh=%s material=%s base=%s tint=%s brightness=%.3f instances=%d firstworld=%s firstscale=%s bounds=%s"),
                    *GetNameSafe(Component),*GetPathNameSafe(Component->GetStaticMesh()),*GetPathNameSafe(Material),Material?*GetPathNameSafe(Material->GetMaterial()):TEXT("null"),
                    *Tint.ToString(),Brightness,Component->GetInstanceCount(),*Instance.GetLocation().ToString(),*Instance.GetScale3D().ToString(),*Component->Bounds.Origin.ToString());
            }
        }
    }
    void CaptureReview(ACombatLabCharacter* Character,FString Directory,FString Name,FString Stage=FString())
    {
        // UE keeps one global screenshot request. Long frames can coalesce separate event timers.
        // Preserve an earlier request and retry this one after its frame has been consumed.
        if(FScreenshotRequest::IsScreenshotRequested())
        {
            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_CAPTURE_QUEUED %s"),*Name);
            FTimerHandle Retry;Character->GetWorldTimerManager().SetTimer(Retry,
                FTimerDelegate::CreateWeakLambda(Character,[Character,Directory,Name,Stage](){CaptureReview(Character,Directory,Name,Stage);}),.02f,false);
            return;
        }
        if(!Stage.IsEmpty()) LogOwnedEffects(Character,*Stage);
        if(auto* Single=Character->GetMesh()->GetSingleNodeInstance())
            UE_LOG(LogTemp,Display,TEXT("COMBAT_REACTION_CAPTURE image=%s presenting=%d clip=%s time=%.4f"),*Name,Character->HitReaction->IsPresenting(),*GetNameSafe(Single->GetCurrentAsset()),Single->GetCurrentTime());
        FScreenshotRequest::RequestScreenshot(Directory/Name,false,false);
    }
}
static void ReviewAuthoredVFX(ACombatLabCharacter* Player)
{
 if(Player->bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatVFXSlotReview")))return;
 struct FState {bool Passed=true;TWeakObjectPtr<ACombatLabCharacter> Enemy;TWeakObjectPtr<UNiagaraComponent> Burst;};auto S=MakeShared<FState>();
 auto Check=[S](bool OK,const TCHAR* Name){S->Passed&=OK;UE_LOG(LogTemp,Display,TEXT("CombatVFXSlot%s: %s"),Name,OK?TEXT("PASS"):TEXT("FAIL"));};
 auto At=[Player](float T,TFunction<void()> Fn){FTimerHandle H;Player->GetWorldTimerManager().SetTimer(H,FTimerDelegate::CreateWeakLambda(Player,MoveTemp(Fn)),T,false);};
 At(1,[Player,S,Check]{
  bool Enabled=true;for(TActorIterator<ACombatLabCharacter> It(Player->GetWorld());It;++It){Enabled&=It->CombatVFX->bPresentationEnabled;if(It->bTrainingEnemy){if(!S->Enemy.IsValid())S->Enemy=*It;It->EnemyAgent->SetComponentTickEnabled(false);if(auto* AI=Cast<AAIController>(It->GetController())){AI->StopMovement();if(AI->BrainComponent)AI->BrainComponent->StopLogic(TEXT("Authored VFX review"));}It->Combat->CancelAction();}}
  Check(Enabled && S->Enemy.IsValid(),TEXT("SavedActivation"));
  if(!S->Enemy.IsValid())return;
  Player->Combat->CancelAction();Player->CombatVFX->StopPresentation();
  auto& Cue=S->Enemy->CombatVFX->HitCue;Cue.Mode=ECombatVFXCueMode::Niagara;Cue.Duration=.5f;Cue.System=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/Constellation/VFX/NS_SwordTrail.NS_SwordTrail"));Check(Cue.System!=nullptr,TEXT("NiagaraAsset"));
  FCombatConfirmedHit Hit;Hit.Source=Player;Hit.Target=S->Enemy;Hit.Position=Player->GetActorLocation();Hit.Normal=FVector::UpVector;Player->Combat->OnHitConfirmed.Broadcast(Hit);
  for(TObjectIterator<UNiagaraComponent> It;It;++It)if(It->GetWorld()==Player->GetWorld() && It->GetAsset()==Cue.System && It->IsActive())S->Burst=*It;
  Check(S->Burst.IsValid(),TEXT("NiagaraSpawn"));
 });
 At(1.8f,[S,Check]{Check(!S->Burst.IsValid() || !S->Burst->IsRegistered(),TEXT("NiagaraExpiry"));});
 At(2,[Player,S,Check]{
  if(!S->Enemy.IsValid())return;
  auto& Cue=Player->CombatVFX->AttackCue;Cue.Mode=ECombatVFXCueMode::Niagara;Cue.System=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/Constellation/VFX/NS_SwordTrail.NS_SwordTrail"));Cue.Duration=3;
  Player->Combat->OnHitWindowOpened.Broadcast(999,TEXT("Review"));Check(Player->CombatVFX->HasAttackPresentation(),TEXT("NiagaraAttack"));
  Player->Combat->OnHitWindowClosed.Broadcast(999,TEXT("Review"));Check(!Player->CombatVFX->HasAttackPresentation(),TEXT("NiagaraCancellation"));
  UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_SLOT_REVIEW %s"),S->Passed?TEXT("PASS"):TEXT("FAIL"));UKismetSystemLibrary::QuitGame(Player,nullptr,EQuitPreference::Quit,false);
 });
}

void ACombatLabCharacter::ConfigureVFXReview()
{
    ReviewAuthoredVFX(this);
    if (bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatVFXReview"))) return;
    struct FReview
    {
        int32 SwordHits=0,SlimeHits=0,PlayerHitEffects=0,Dust=0,SwordFrames=0,SlimeFrames=0,PeakRibbonSegments=0;
        bool Cancelled=false,HadAttackAtCancel=false,StartedSword=false,StartedSlime=false,SwordWindowCapture=false,DustCaptureScheduled=false;
        TSet<TWeakObjectPtr<AConstellationFXActor>> Seen;
        TWeakObjectPtr<ACombatLabCharacter> Enemy;
        FTimerHandle Observe;
    };
    const bool FirstUseProbe=FParse::Param(FCommandLine::Get(),TEXT("CombatVFXFirstUseProbe"));
    auto State=MakeShared<FReview>();
    auto Schedule=[this](float Delay,FTimerDelegate Callback)
    { FTimerHandle Handle;GetWorldTimerManager().SetTimer(Handle,Callback,Delay,false); };
    CombatVFX->SetPresentationEnabled(true);
    CombatVFX->Initialize(Combat);
    Combat->bDrawHitDebug=false;
    const FString Directory=FPaths::ProjectSavedDir()/TEXT("VFXImplementation");
    IFileManager::Get().MakeDirectory(*Directory,true);
    Combat->OnHitConfirmed.AddWeakLambda(this,[this,State,Directory,FirstUseProbe](const FCombatConfirmedHit& Hit)
    {
        UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_CONTACT position=%s normal=%s"),*Hit.Position.ToString(),*Hit.Normal.ToString());
        for (TActorIterator<AConstellationFXActor> It(GetWorld());It;++It)
            if (!It->ActorHasTag(TEXT("CombatVFXWarmup")) && It->GetOwner()==this && (It->EffectKind==EConstellationFXKind::SwordHit || It->EffectKind==EConstellationFXKind::SlimeHit))
                UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_IMPACT kind=%d origin=%s"),int32(It->EffectKind),*It->GetActorLocation().ToString());
        ++State->SwordHits;FTimerHandle Capture;
        const FString Name=FirstUseProbe && State->SwordHits==1 ? TEXT("combat-sword-first.png") : TEXT("combat-sword.png");
        GetWorldTimerManager().SetTimer(Capture,FTimerDelegate::CreateWeakLambda(this,[this,Directory,Name]()
        { CaptureReview(this,Directory,Name,TEXT("swordhit")); }),.035f,false);
    });
    Combat->OnHitWindowOpened.AddWeakLambda(this,[this,State,Directory](uint64,FName)
    {
        if (State->SwordWindowCapture) return;
        State->SwordWindowCapture=true;
        FTimerHandle Capture;GetWorldTimerManager().SetTimer(Capture,FTimerDelegate::CreateWeakLambda(this,[this,Directory]()
        { CaptureReview(this,Directory,TEXT("combat-sword-trail.png")); }),.08f,false);
    });
    Schedule(.15f,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory]()
    {
        // Keep the authored multi-enemy map, but isolate this deterministic rendering probe.
        bool FirstEnemy=true;
        for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)if(It->bTrainingEnemy)
        {
            It->EnemyAgent->SetComponentTickEnabled(false);It->Combat->CancelAction();
            if(auto* AI=Cast<AAIController>(It->GetController())){AI->StopMovement();if(AI->BrainComponent)AI->BrainComponent->StopLogic(TEXT("VFX render probe"));}
            if(!FirstEnemy)It->SetActorLocation(It->GetActorLocation()+FVector(10000,10000,0));FirstEnemy=false;
        }
        for (TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)
            if (It->bTrainingEnemy && It->Combat->GetHealth()>0)
            {
                State->Enemy=*It;
                if (auto* AI=Cast<AAIController>(It->GetController()))
                { AI->StopMovement();if (AI->BrainComponent) AI->BrainComponent->StopLogic(TEXT("VFX review")); }
                It->GetCharacterMovement()->StopMovementImmediately();
                It->EnemyAgent->SetComponentTickEnabled(false);
                It->Combat->CancelAction();It->Combat->bDrawHitDebug=false;
                It->CombatVFX->SetPresentationEnabled(true);It->CombatVFX->Initialize(It->Combat);
                It->Combat->OnHitConfirmed.AddWeakLambda(this,[this,State,Directory](const FCombatConfirmedHit& Hit)
                {
                    ++State->SlimeHits;FTimerHandle Capture;
                    const double HitTime=GetWorld()->GetTimeSeconds();
                    UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_SLIME_CONTACT time=%.6f source=%s target=%s position=%s normal=%s targetbounds=%s targetextent=%s"),
                        HitTime,*GetNameSafe(Hit.Source.Get()),*GetNameSafe(Hit.Target.Get()),*Hit.Position.ToString(),*Hit.Normal.ToString(),
                        *GetMesh()->Bounds.Origin.ToString(),*GetMesh()->Bounds.BoxExtent.ToString());
                    // Multicast delegate order is not guaranteed; inspect after all confirmed-hit listeners.
                    GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this,[this,State,Source=Hit.Source]()
                    {
                    for(TActorIterator<AConstellationFXActor> FX(GetWorld());FX;++FX)
                        if(FX->GetOwner()==Source.Get() && FX->EffectKind==EConstellationFXKind::PlayerHit && !FX->IsActorBeingDestroyed() && !FX->ActorHasTag(TEXT("CombatVFXWarmup")))
                        {
                            ++State->PlayerHitEffects;
                            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_PLAYER_HIT origin=%s particles=%d duration=%.3f hidden=%d"),
                                *FX->GetActorLocation().ToString(),FX->ParticleCount,FX->GetDuration(),FX->IsHidden());
                        }
                    if(State->Enemy.IsValid()) LogOwnedEffects(State->Enemy.Get(),TEXT("slime-post-contact"));
                    }));
                    GetWorldTimerManager().SetTimer(Capture,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory,HitTime]()
                    {
                        UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_SLIME_CAPTURE elapsed=%.6f playerhitactors=%d"),GetWorld()->GetTimeSeconds()-HitTime,State->PlayerHitEffects);
                        if(State->Enemy.IsValid()) LogOwnedEffects(State->Enemy.Get(),TEXT("slime-capture"));
                        if(FParse::Param(FCommandLine::Get(),TEXT("CombatVFXFreezeImpactProbe")))
                        {
                            // Keep the exact live capture-time particle pose, only allowing render publication to settle.
                            for(TActorIterator<AConstellationFXActor> FX(GetWorld());FX;++FX)
                                if(FX->GetOwner()==State->Enemy.Get() && FX->EffectKind==EConstellationFXKind::PlayerHit && !FX->IsActorBeingDestroyed())
                                {
                                    FX->SetActorTickEnabled(false);FX->SetLifeSpan(0.f);
                                    UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_FREEZE_PROBE actor=%s"),*FX->GetName());
                                }
                            FTimerHandle Settled;
                            GetWorldTimerManager().SetTimer(Settled,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory]()
                            {
                                if(State->Enemy.IsValid()) LogOwnedEffects(State->Enemy.Get(),TEXT("slime-frozen-probe"));
                                CaptureReview(this,Directory,TEXT("combat-slime-frozen-probe.png"));
                                for(TActorIterator<AConstellationFXActor> FX(GetWorld());FX;++FX)
                                    if(FX->GetOwner()==State->Enemy.Get() && FX->EffectKind==EConstellationFXKind::PlayerHit && !FX->IsActorBeingDestroyed()) FX->SetLifeSpan(.5f);
                            }),.25f,false);
                        }
                        else CaptureReview(this,Directory,TEXT("combat-slime.png"));
                    }),.085f,false);
                });
                It->Combat->OnHitWindowOpened.AddWeakLambda(this,[this,State,Directory](uint64,FName)
                {
                    FTimerHandle Capture;GetWorldTimerManager().SetTimer(Capture,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory]()
                    {
                        // A contact on the same window already captures the attack and impact together.
                        // A second screenshot stalls the next frame beyond the short impact flash lifetime.
                        if(State->SlimeHits==0) CaptureReview(this,Directory,TEXT("combat-slime-attack.png"));
                    }),.025f,false);
                });
                It->SetActorLocation(GetActorLocation()+FVector(120,0,0));
                It->SetActorRotation(FRotator(0,180,0));SetActorRotation(FRotator::ZeroRotator);
                Arm->TargetArmLength=300.f;Arm->TargetOffset=FVector(60,0,-10);Arm->SocketOffset=FVector::ZeroVector;
                Arm->bEnableCameraLag=false;Camera->SetFieldOfView(65.f);
                Camera->PostProcessSettings.bOverride_MotionBlurAmount=true;Camera->PostProcessSettings.MotionBlurAmount=0.f;Camera->PostProcessBlendWeight=1.f;
                if (auto* PC=Cast<APlayerController>(Controller)) PC->SetControlRotation(FRotator(-12,-90,0));
                break;
            }
        GetWorldTimerManager().SetTimer(State->Observe,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory]()
        {
            if (CombatVFX->HasAttackPresentation()) ++State->SwordFrames;
            State->PeakRibbonSegments=FMath::Max(State->PeakRibbonSegments,CombatVFX->GetWeaponRibbonSegments());
            if (State->Enemy.IsValid() && State->Enemy->CombatVFX->HasAttackPresentation()) ++State->SlimeFrames;
            for (TActorIterator<AConstellationFXActor> It(GetWorld());It;++It)
                if (!It->ActorHasTag(TEXT("CombatVFXWarmup")) && !State->Seen.Contains(*It))
                { State->Seen.Add(*It);
                    if (It->EffectKind==EConstellationFXKind::RunDust && It->GetOwner()==this)
                    {
                        ++State->Dust;
                        if(State->Dust>=3 && !State->DustCaptureScheduled)
                        {
                            State->DustCaptureScheduled=true;
                            if(auto* PC=Cast<APlayerController>(Controller)) PC->SetControlRotation(FRotator(-12,-90,0));
                            FTimerHandle Capture;GetWorldTimerManager().SetTimer(Capture,FTimerDelegate::CreateWeakLambda(this,[this,Directory]()
                            { CaptureReview(this,Directory,TEXT("combat-dust.png"),TEXT("rundust")); }),.12f,false);
                        }
                    } }
        }),.015f,true);
    }));
    if(FirstUseProbe) Schedule(.55f,FTimerDelegate::CreateWeakLambda(this,[this](){Combat->TryStartAction(Action);}));
    // Shared mesh/material resources get four seconds to finish first-use preparation before real combat.
    Schedule(4.0f,FTimerDelegate::CreateWeakLambda(this,[this,State](){State->StartedSword=Combat->TryStartAction(Action);}));
    Schedule(5.45f,FTimerDelegate::CreateWeakLambda(this,[State]()
    { if (State->Enemy.IsValid()) State->StartedSlime=State->Enemy->Combat->TryStartAction(State->Enemy->Action); }));
    Schedule(6.75f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        if (State->Enemy.IsValid()) State->Enemy->SetActorLocation(GetActorLocation()+FVector(450,0,0));
        Combat->TryStartAction(Action);
    }));
    Schedule(7.17f,FTimerDelegate::CreateWeakLambda(this,[this,State]()
    {
        State->HadAttackAtCancel=CombatVFX->HasAttackPresentation();
        Combat->CancelAction();State->Cancelled=!CombatVFX->HasAttackPresentation() && !Combat->IsActing();
    }));
    Schedule(7.65f,FTimerDelegate::CreateWeakLambda(this,[this]()
    { if (auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::D,IE_Pressed,1.f)); }));
    Schedule(9.65f,FTimerDelegate::CreateWeakLambda(this,[this]()
    { if (auto* PC=Cast<APlayerController>(Controller)) PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::D,IE_Released,0.f)); }));
    Schedule(10.45f,FTimerDelegate::CreateWeakLambda(this,[this,State,Directory,FirstUseProbe]()
    {
        GetWorldTimerManager().ClearTimer(State->Observe);
        const bool Passed=State->StartedSword && State->StartedSlime && State->SwordHits==(FirstUseProbe?2:1) && State->SlimeHits==1 && State->PlayerHitEffects==1 &&
            State->SwordFrames>0 && State->SlimeFrames>0 && State->HadAttackAtCancel && State->Cancelled && State->Dust>0;
        const FString Report=FString::Printf(TEXT("{\"passed\":%s,\"sword_hits\":%d,\"slime_hits\":%d,\"player_hit_effects\":%d,\"sword_frames\":%d,\"slime_frames\":%d,\"dust_puffs\":%d,\"cancel_had_effect\":%s,\"cancel_cleanup\":%s,\"sword_equipped\":%s,\"sword_socket\":\"%s\",\"sword_world_scale\":%.3f,\"player_health\":%.1f,\"peak_ribbon_segments\":%d,\"authored_trail_ready\":%s}"),
            Passed?TEXT("true"):TEXT("false"),State->SwordHits,State->SlimeHits,State->PlayerHitEffects,State->SwordFrames,State->SlimeFrames,State->Dust,
            State->HadAttackAtCancel?TEXT("true"):TEXT("false"),State->Cancelled?TEXT("true"):TEXT("false"),
            Sword->GetStaticMesh()?TEXT("true"):TEXT("false"),*Sword->GetAttachSocketName().ToString(),Sword->GetComponentScale().X,Combat->GetHealth(),State->PeakRibbonSegments,CombatVFX->IsAuthoredTrailReady()?TEXT("true"):TEXT("false"));
        FFileHelper::SaveStringToFile(Report,*(Directory/TEXT("combat-runtime-review.json")));
        UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_REVIEW %s"),*Report);
        CombatVFX->StopPresentation();if(State->Enemy.IsValid()) State->Enemy->CombatVFX->StopPresentation();
        UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
    }));
}
#endif
