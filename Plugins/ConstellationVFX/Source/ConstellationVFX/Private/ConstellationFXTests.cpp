#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "ConstellationGlass.h"
#include "Engine/World.h"
#include "ConstellationSceneFXAction.h"
#include "SceneDirectorPlayer.h"
#include "ConstellationCaveFX.h"
#include "EngineUtils.h"
#include "ConstellationFXReview.h"
#include "ConstellationFXGallery.h"
#include "Camera/CameraActor.h"
#include "Engine/GameViewportClient.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFXLifecycleTest,"Constellation.VFX.Lifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FFXLifecycleTest::RunTest(const FString&) {
 TestNull(TEXT("No world rejects playback"),UConstellationFXLibrary::SpawnEffect(nullptr,EConstellationFXKind::SwordHit,FVector::ZeroVector,FVector::ZeroVector,FLinearColor::White,1));
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false); W->InitializeActorsForPlay(FURL()); W->BeginPlay();
 AActor* Owner=W->SpawnActor<AActor>();
 auto* FX=UConstellationFXLibrary::SpawnEffect(W,EConstellationFXKind::SlimeHit,FVector::ZeroVector,FVector::ZeroVector,FLinearColor::Green,1);
 TestNotNull(TEXT("Effect spawns"),FX);
 if(FX){FX->Tick(1.f);TestFalse(TEXT("Spawn-frame hitch cannot expire a just-created effect"),FX->IsActorBeingDestroyed());FX->SetOwner(Owner);TestTrue(TEXT("Lifetime bounded"),FX->GetDuration()>0 && FX->GetDuration()<=12);FX->AdvanceEffect(20);TestTrue(TEXT("Effect expires"),FX->IsActorBeingDestroyed());}
 auto* Other=UConstellationFXLibrary::SpawnEffect(W,EConstellationFXKind::SwordParry,FVector::ZeroVector,FVector::ForwardVector,FLinearColor::White,1);Other->SetOwner(Owner);
 UConstellationFXLibrary::StopEffectsForOwner(Owner);TestTrue(TEXT("Owned effect stops"),Other->IsActorBeingDestroyed());
 auto* Glass=W->SpawnActor<AConstellationGlass>();
 TestFalse(TEXT("Glass starts intact"),Glass->bBroken);TestTrue(TEXT("First break"),Glass->BreakGlass(FVector::ZeroVector,FVector::ForwardVector));TestFalse(TEXT("Duplicate break ignored"),Glass->BreakGlass(FVector::ZeroVector,FVector::ForwardVector));TestFalse(TEXT("Broken glass collision off"),Glass->GetActorEnableCollision());Glass->ResetGlass();TestFalse(TEXT("Reset intact"),Glass->bBroken);TestTrue(TEXT("Reset collision"),Glass->GetActorEnableCollision());

 auto* Director=W->SpawnActor<ASceneDirectorPlayer>();auto* Action=NewObject<UConstellationSceneFXAction>();FDirectorActionParameters P;P.Identifier=TEXT("SwordParry");FString Error;
 TestTrue(TEXT("Scene effect starts"),Action->Execute_Implementation(Director,Owner,P,Error));
 Director->OnDirectorStopped.Broadcast(false);
 for(TActorIterator<AConstellationFXActor> It(W);It;++It)if(It->GetOwner()==Director)TestTrue(TEXT("Scene stop destroys its effects"),It->IsActorBeingDestroyed());
 auto* Cave=W->SpawnActor<AConstellationCaveFX>();Cave->SetEffectsEnabled(false);P.Identifier=TEXT("CaveEnable");P.Flag=true;TestTrue(TEXT("Scene enables cave"),Action->Execute_Implementation(Director,Cave,P,Error));TestTrue(TEXT("Cave enabled"),Cave->bEnabled);Director->OnDirectorStopped.Broadcast(false);TestFalse(TEXT("Scene abort restores cave"),Cave->bEnabled);
 P.Identifier=TEXT("GlassBreak");TestTrue(TEXT("Scene glass breaks"),Action->Execute_Implementation(Director,Glass,P,Error));Director->OnDirectorStopped.Broadcast(false);TestFalse(TEXT("Scene cancellation restores glass"),Glass->bBroken);
 P.Identifier=TEXT("GlassBreak");Action->Execute_Implementation(Director,Glass,P,Error);Director->OnDirectorStopped.Broadcast(true);TestTrue(TEXT("Completed glass stays broken"),Glass->bBroken);Director->OnDirectorStopped.Broadcast(false);TestTrue(TEXT("Later unrelated abort preserves broken glass"),Glass->bBroken);Action->Execute_Implementation(Director,Glass,P,Error);Director->OnDirectorStopped.Broadcast(false);TestTrue(TEXT("Already broken glass unaffected by scene abort"),Glass->bBroken);
 P.Identifier=TEXT("GlassReset");TestTrue(TEXT("Scene reset initially broken pane"),Action->Execute_Implementation(Director,Glass,P,Error));TestFalse(TEXT("Scene reset is intact"),Glass->bBroken);auto* Rival=W->SpawnActor<ASceneDirectorPlayer>();TestFalse(TEXT("Competing scene cannot reset glass"),Action->Execute_Implementation(Rival,Glass,P,Error));Director->OnDirectorStopped.Broadcast(false);TestTrue(TEXT("Reset abort restores initially broken pane"),Glass->bBroken);
 P.Identifier=TEXT("Unknown");TestFalse(TEXT("Unknown effect rejected"),Action->Execute_Implementation(Director,Owner,P,Error));
 W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFXInteractiveGalleryTest,"Constellation.VFX.InteractiveGallery",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FFXInteractiveGalleryTest::RunTest(const FString&) {
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);W->InitializeActorsForPlay(FURL());W->BeginPlay();
 auto* Review=W->SpawnActorDeferred<AConstellationFXReview>(AConstellationFXReview::StaticClass(),FTransform::Identity);Review->bAutoReview=true;Review->FinishSpawning(FTransform::Identity);if(!Review->HasActorBegunPlay())Review->DispatchBeginPlay();
 TestFalse(TEXT("Legacy saved auto-review cannot take over ordinary play"),Review->IsActorTickEnabled());
 int Cameras=0;for(TActorIterator<ACameraActor> I(W);I;++I)++Cameras;TestEqual(TEXT("No fixed camera in ordinary play"),Cameras,0);
 auto* Gallery=W->SpawnActor<AConstellationFXGallery>();if(!Gallery->HasActorBegunPlay())Gallery->DispatchBeginPlay();Gallery->ReadyTime=3;
 Gallery->SelectStation(6,false);bool PlayerHit=false;for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(!I->IsActorBeingDestroyed()&&I->GetOwner()==Gallery&&I->EffectKind==EConstellationFXKind::PlayerHit)PlayerHit=true;
 TestTrue(TEXT("Player hit has a distinct visible effect"),PlayerHit);
 Gallery->SelectStation(7,false);for(int N=0;N<20;++N)Gallery->Replay();int GlassEffects=0;for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(!I->IsActorBeingDestroyed()&&I->EffectKind==EConstellationFXKind::GlassBreak)++GlassEffects;
 TestEqual(TEXT("Repeated glass reuses one bounded burst"),GlassEffects,1);
 TestFalse(TEXT("Interactive replay does not request screenshots"),FScreenshotRequest::IsScreenshotRequested());
 Gallery->SelectStation(-1,false);TestEqual(TEXT("Previous station wraps to cave"),Gallery->Selected,9);
 W->DestroyWorld(false);return true;
}
#endif
