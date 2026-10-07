#include "ConstellationFXReview.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "ConstellationGlass.h"
#include "ConstellationCaveFX.h"
#include "ConstellationGlassRelay.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/PlatformMisc.h"
#include "Serialization/JsonSerializer.h"
AConstellationFXReview::AConstellationFXReview(){PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));}
void AConstellationFXReview::BeginPlay(){Super::BeginPlay();bBenchmark=FParse::Param(FCommandLine::Get(),TEXT("VFXBenchmark"));bGlassReview=FParse::Param(FCommandLine::Get(),TEXT("VFXGlassReview"));bAutomated=bGlassReview||bBenchmark||FParse::Param(FCommandLine::Get(),TEXT("VFXReview"))||FParse::Param(FCommandLine::Get(),TEXT("VFXCaveReview"));if(!bAutomated){SetActorTickEnabled(false);return;}
 Camera=GetWorld()->SpawnActor<ACameraActor>();Camera->GetCameraComponent()->SetFieldOfView(48);Camera->SetActorLocation(GetActorLocation()+FVector(420,-520,280));Camera->SetActorRotation((GetActorLocation()+FVector(0,0,100)-Camera->GetActorLocation()).Rotation());
 if(auto* PC=UGameplayStatics::GetPlayerController(this,0)){PC->SetViewTarget(Camera);PC->SetCinematicMode(true,true,true,true,true);}
 for(TActorIterator<AConstellationGlass> It(GetWorld());It;++It){Glass=*It;break;}
 if(bGlassReview){
 if(Glass){Glass->SetActorHiddenInGame(true);Glass->SetActorEnableCollision(false);}
 if(auto* C=LoadClass<AActor>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Glass.BP_Glass_C")))LegacyGlass=GetWorld()->SpawnActor<AActor>(C,FVector(0,0,110),FRotator(0,40,0));
 GlassRelay=GetWorld()->SpawnActor<AConstellationGlassRelay>();
}
 if(bBenchmark)for(TActorIterator<AConstellationCaveFX> It(GetWorld());It;++It)It->SetEffectsEnabled(false);
 IFileManager::Get().MakeDirectory(*(FPaths::ProjectSavedDir()/TEXT("VFXReview")),true);
}
void AConstellationFXReview::StartStage(){++Stage;StageClock=0;bCaptured=false;UConstellationFXLibrary::StopEffectsForOwner(this);if(Glass){Glass->ResetGlass();Glass->SetActorHiddenInGame(Stage!=5);}
 if(Stage>=(bEnvironmentOnly?1:9)){FinishReview();return;}
 if(bEnvironmentOnly)return;
 if(!bAutomated&&GEngine){static const TCHAR* Labels[]={TEXT("Sword hit"),TEXT("Sword block"),TEXT("Sword parry"),TEXT("Slime attack"),TEXT("Slime hit"),TEXT("Glass break"),TEXT("Running dust"),TEXT("Cave spores"),TEXT("Water ripple")};GEngine->AddOnScreenDebugMessage(780,1.8f,FColor::White,FString(Labels[Stage]));}
 FVector P=GetActorLocation()+FVector(0,0,110);EConstellationFXKind K=EConstellationFXKind::SwordHit;FLinearColor C(.65,.88,1,1);float S=2;
 switch(Stage){case 0:K=EConstellationFXKind::SwordHit;break;case 1:K=EConstellationFXKind::SwordBlock;C=FLinearColor(1,.6,.2,1);break;case 2:K=EConstellationFXKind::SwordParry;break;case 3:K=EConstellationFXKind::SlimeAttack;C=FLinearColor(.12,.8,.3,1);break;case 4:K=EConstellationFXKind::SlimeHit;C=FLinearColor(.12,.8,.3,1);break;case 5:if(Glass){bGalleryGlassPassed=Glass->BreakGlass(Glass->GetActorLocation(),FVector(1,-1,.3));}return;case 6:K=EConstellationFXKind::RunDust;P.Z=GetActorLocation().Z+4;C=FLinearColor(.4,.3,.18,.8);S=3;break;case 7:K=EConstellationFXKind::CaveSpore;C=FLinearColor(.2,.8,.7,.6);S=2;break;case 8:K=EConstellationFXKind::WaterRipple;P.Z=GetActorLocation().Z+3;C=FLinearColor(.3,.6,.7,.7);S=3;break;}
 if(auto* FX=UConstellationFXLibrary::SpawnEffect(this,K,P,FVector(1,-1,.35),C,S))FX->SetOwner(this);
}
void AConstellationFXReview::Tick(float Dt){Super::Tick(Dt);Clock+=Dt;if(Clock<4)return;
 if(bGlassReview){
  if(!bGlassInvoked){bGlassInvoked=true;if(LegacyGlass)if(auto* F=LegacyGlass->FindFunction(TEXT("OnBreakObject"))){
   FStructOnScope Args(F);auto* L=FindFProperty<FStructProperty>(F,TEXT("HitLocation"));auto* A=FindFProperty<FObjectPropertyBase>(F,TEXT("HitActor"));
   if(L&&A&&L->Struct==TBaseStructure<FVector>::Get()){*L->ContainerPtrToValuePtr<FVector>(Args.GetStructMemory())=LegacyGlass->GetActorLocation();A->SetObjectPropertyValue_InContainer(Args.GetStructMemory(),this);LegacyGlass->ProcessEvent(F,Args.GetStructMemory());}
  }}
  int N=0;for(TActorIterator<AConstellationFXActor> It(GetWorld());It;++It)if(It->GetOwner()==GlassRelay&&!It->IsActorBeingDestroyed())++N;PeakEffects=FMath::Max(PeakEffects,N);
  if(PeakEffects>0&&Clock>4.35f&&!bCaptured){bCaptured=true;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("VFXReview/glass-authored.png"),false,false);}
  if(Clock>7)FinishReview();return;
 }
 if(bBenchmark){
  if(Clock<8){BaselineMs.Add(double(Dt)*1000);return;}
  StressClock-=Dt;if(StressClock<=0){StressClock=.65f;for(int I=0;I<24;++I){EConstellationFXKind K=EConstellationFXKind(I%12);FVector P=GetActorLocation()+FVector((I%6-3)*65,(I/6-2)*75,45+(I%3)*45);if(auto* F=UConstellationFXLibrary::SpawnEffect(this,K,P,FVector::UpVector,FLinearColor(.3,.7,.6,.5),1))F->SetOwner(this);}}
  if(Clock>9)FrameMs.Add(double(Dt)*1000);int32 N=0,Particles=0;for(TActorIterator<AConstellationFXActor> It(GetWorld());It;++It)if(!It->IsActorBeingDestroyed()){++N;Particles+=It->ParticleCount;}PeakEffects=FMath::Max(PeakEffects,N);PeakParticles=FMath::Max(PeakParticles,Particles);
  if(Clock>15)FinishReview();return;
 }if(Stage<0){StartStage();return;}StageClock+=Dt;
 if(bAutomated&&StageClock>(bEnvironmentOnly?4.f:Stage>=7?.7f:.12f)&&!bCaptured){bCaptured=true;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/(bEnvironmentOnly?FString(TEXT("VFXReview/cave.png")):FString::Printf(TEXT("VFXReview/effect_%02d.png"),Stage)),false,false);}
 if(Clock>5)FrameMs.Add(double(Dt)*1000);
 if(StageClock>(bEnvironmentOnly?6.f:1.8f))StartStage();
}
void AConstellationFXReview::FinishReview(){SetActorTickEnabled(false);TSharedRef<FJsonObject> J=MakeShared<FJsonObject>();J->SetBoolField(TEXT("completed"),true);if(!bBenchmark&&!bGlassReview&&!bEnvironmentOnly){J->SetBoolField(TEXT("glass_present"),IsValid(Glass));J->SetBoolField(TEXT("glass_break_succeeded"),bGalleryGlassPassed);}
 if(bGlassReview){J->SetBoolField(TEXT("passed"),LegacyGlass&&GlassRelay&&GlassRelay->BoundCollections>0&&PeakEffects>0);J->SetNumberField(TEXT("bound_glass_collections"),GlassRelay?GlassRelay->BoundCollections:0);J->SetNumberField(TEXT("peak_relay_effects"),PeakEffects);}
 if(bBenchmark){double B=0;for(double V:BaselineMs)B+=V;J->SetNumberField(TEXT("baseline_mean_ms"),BaselineMs.Num()?B/BaselineMs.Num():0);J->SetNumberField(TEXT("baseline_samples"),BaselineMs.Num());J->SetNumberField(TEXT("peak_concurrent_effect_actors"),PeakEffects);J->SetNumberField(TEXT("peak_particle_instances"),PeakParticles);J->SetStringField(TEXT("load"),TEXT("24 effects every 0.65s, 12 types, 4s warmup +4s baseline +1s load warmup +6s samples; no screenshots"));}J->SetNumberField(TEXT("effect_stages"),bEnvironmentOnly?1:9);double Sum=0;for(double V:FrameMs)Sum+=V;FrameMs.Sort();J->SetNumberField(TEXT("samples"),FrameMs.Num());J->SetNumberField(TEXT("mean_frame_ms"),FrameMs.Num()?Sum/FrameMs.Num():0);J->SetNumberField(TEXT("p95_frame_ms"),FrameMs.Num()?FrameMs[FMath::Min(FrameMs.Num()-1,int32(FrameMs.Num()*.95))]:0);J->SetStringField(TEXT("measurement"),bBenchmark?TEXT("1280x720 offscreen whole-frame delta; same scene baseline, no screenshots, not isolated GPU timing"):TEXT("Unreal game delta including screenshot readback; diagnostic only, not isolated GPU cost"));FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(J,Writer);FFileHelper::SaveStringToFile(Text,*(FPaths::ProjectSavedDir()/(bGlassReview?TEXT("VFXReview/glass-runtime.json"):bBenchmark?TEXT("VFXReview/benchmark.json"):bEnvironmentOnly?TEXT("VFXReview/cave-review.json"):TEXT("VFXReview/review.json"))));if(bAutomated)FPlatformMisc::RequestExit(false);else if(!bEnvironmentOnly){Clock=0;Stage=-1;FrameMs.Reset();SetActorTickEnabled(true);}}
