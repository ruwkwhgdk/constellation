#include "ConstellationFXGallery.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "ConstellationSwordRibbonComponent.h"
#include "Animation/SkeletalMeshActor.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "ConstellationGlass.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Engine/Canvas.h"
#if WITH_EDITOR
#include "ShaderCompiler.h"
#endif
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/DefaultPawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "InputCoreTypes.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformMisc.h"

AConstellationFXGalleryMode::AConstellationFXGalleryMode(){DefaultPawnClass=ADefaultPawn::StaticClass();HUDClass=AConstellationFXGalleryHUD::StaticClass();}
const TCHAR* AConstellationFXGallery::StationName(int32 I){static const TCHAR* N[]={TEXT("Sword swing / trail"),TEXT("Sword impact"),TEXT("Sword block"),TEXT("Sword parry"),TEXT("Slime attack"),TEXT("Slime hit"),TEXT("Player hit"),TEXT("Glass break"),TEXT("Running dust"),TEXT("Cave: mist / dust / spores / water")};return N[FMath::Clamp(I,0,9)];}
FVector AConstellationFXGallery::StationPosition(int32 I)const{return GetActorLocation()+FVector((I%5)*650,(I/5)*1000,0);}
AConstellationFXGallery::AConstellationFXGallery(){PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));Sword=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Sword"));Sword->SetupAttachment(RootComponent);Sword->SetCollisionEnabled(ECollisionEnabled::NoCollision);Ribbon=CreateDefaultSubobject<UConstellationSwordRibbonComponent>(TEXT("Ribbon"));Ribbon->SetupAttachment(RootComponent);Ribbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);Ribbon->SetCastShadow(false);Trail=CreateDefaultSubobject<UNiagaraComponent>(TEXT("Trail"));Trail->SetupAttachment(Sword);Trail->SetAutoActivate(false);}
void AConstellationFXGallery::BeginPlay(){Super::BeginPlay();
 bReactionCapture=FParse::Param(FCommandLine::Get(),TEXT("VFXReactionCapture"));
 bProbe=FParse::Param(FCommandLine::Get(),TEXT("VFXGalleryProbe"));bCapture=FParse::Param(FCommandLine::Get(),TEXT("VFXGalleryCapture"));
 // Explicit legacy diagnostics own their camera; interactive viewing never does.
 if(FParse::Param(FCommandLine::Get(),TEXT("VFXCaveReview"))||FParse::Param(FCommandLine::Get(),TEXT("VFXReview"))||FParse::Param(FCommandLine::Get(),TEXT("VFXBenchmark"))||FParse::Param(FCommandLine::Get(),TEXT("VFXGlassReview"))){SetActorTickEnabled(false);return;}
 const TCHAR* Paths[]={TEXT("/Engine/BasicShapes/Sphere.Sphere"),TEXT("/Engine/BasicShapes/Plane.Plane"),TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),TEXT("/Game/Constellation/VFX/Meshes/SM_GlassShard.SM_GlassShard"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Glow.M_FX_Glow"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Gel.M_FX_Gel"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Glass.M_FX_Glass"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Soft.M_FX_Soft"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Ring.M_FX_Ring"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Dust.M_FX_Dust")};
 for(auto P:Paths)if(auto* O=LoadObject<UObject>(nullptr,P))RetainedAssets.Add(O);
 for(const TCHAR* Name:{TEXT("M_FX_Impact"),TEXT("M_FX_GelImpact"),TEXT("M_FX_Cut"),TEXT("M_FX_ImpactStar"),TEXT("M_FX_Slash")})if(auto* O=LoadObject<UObject>(nullptr,*FString::Printf(TEXT("/Game/Constellation/VFX/Materials/%s.%s"),Name,Name)))RetainedAssets.Add(O);
 for(const TCHAR* Direction:{TEXT("Front"),TEXT("Back"),TEXT("Left"),TEXT("Right")})
  if(auto* Clip=LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Hit_%s.AS_player_heroine_new_Hit_%s"),Direction,Direction)))RetainedAssets.Add(Clip);
 Sword->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Constellation/Characters/Shared/Equipment/SM_Weapon_Sword.SM_Weapon_Sword")));Sword->SetWorldScale3D(FVector(.7));Sword->SetVisibility(false);
 Ribbon->Configure(UConstellationFXLibrary::CombatColor(EConstellationFXKind::SwordHit));
 for(int I=0;I<=int(EConstellationFXKind::PlayerHit);++I)if(auto* F=UConstellationFXLibrary::SpawnEffect(this,EConstellationFXKind(I),GetActorLocation()-FVector(0,0,100000),FVector::UpVector,FLinearColor::White,1)){F->SetOwner(this);F->SetLifeSpan(1.2f);}
 for(TActorIterator<AConstellationGlass> I(GetWorld());I;++I){Glass=*I;break;}
 if(!Glass)Glass=GetWorld()->SpawnActor<AConstellationGlass>(StationPosition(7)+FVector(0,0,115),FRotator(0,90,0));
 if(auto* PC=UGameplayStatics::GetPlayerController(this,0)){PC->SetCinematicMode(false,false,false,true,true);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();PC->SetInputMode(FInputModeGameOnly());PC->bShowMouseCursor=false;if(PC->PlayerCameraManager)PC->PlayerCameraManager->SetFOV(60);}
 bRepeat=!(bProbe||bCapture||bReactionCapture);FrameStation();
}
void AConstellationFXGallery::RestoreReaction()
{
 if(ReactionMesh) if(auto* Single=ReactionMesh->GetSingleNodeInstance())
 {Single->SetAnimationAsset(ReactionBase,false,1.f);Single->SetPosition(ReactionBaseTime,false);Single->SetPlaying(false);}
 ReactionMesh=nullptr;ReactionBase=nullptr;ReactionAge=1;
}
void AConstellationFXGallery::PreviewReaction()
{
 const TCHAR* Names[]={TEXT("Front"),TEXT("Back"),TEXT("Left"),TEXT("Right")};
 for(TActorIterator<ASkeletalMeshActor> It(GetWorld());It;++It) if(It->ActorHasTag(TEXT("VFXTarget6")))
 {
  auto* Mesh=It->GetSkeletalMeshComponent();auto* Single=Mesh->GetSingleNodeInstance();
  auto* Clip=LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Hit_%s.AS_player_heroine_new_Hit_%s"),Names[HitDirection],Names[HitDirection]));
  if(Single && Clip && Clip->GetSkeleton()->IsCompatibleMesh(Mesh->GetSkeletalMeshAsset()))
  {ReactionMesh=Mesh;ReactionBase=Single->GetCurrentAsset();ReactionBaseTime=Single->GetCurrentTime();ReactionAge=0;Single->SetAnimationAsset(Clip,false,Clip->GetPlayLength()/.35f);Single->SetPosition(0,false);Single->SetPlaying(true);}
  break;
 }
}
void AConstellationFXGallery::FrameStation(){if(auto* PC=UGameplayStatics::GetPlayerController(this,0))if(APawn* P=PC->GetPawn()){const FVector At=StationPosition(Selected)+FVector(0,0,100);const FVector Eye=At+FVector(220,-420,100);P->SetActorLocation(Eye,false);PC->SetControlRotation((At-Eye).Rotation());PC->SetViewTarget(P);if(PC->PlayerCameraManager)PC->PlayerCameraManager->UpdateCamera(0.f);}}
void AConstellationFXGallery::SelectStation(int32 I,bool Frame){Selected=(I%10+10)%10;if(Frame)FrameStation();Replay();}
void AConstellationFXGallery::Replay(){
 if(ReadyTime<2)return;
 RestoreReaction();
 UConstellationFXLibrary::StopEffectsForOwner(this);Ribbon->ResetTrail();Trail->DeactivateImmediate();Sword->SetVisibility(false);SlashAge=10;ReplayClock=0;++ReplayCount;
 if(Glass)Glass->ResetGlass();
 FVector P=StationPosition(Selected)+FVector(0,-25,110);
 for(TActorIterator<ASkeletalMeshActor> It(GetWorld());It;++It)if(It->ActorHasTag(FName(*FString::Printf(TEXT("VFXTarget%d"),Selected)))) {
  const FBox B=It->GetSkeletalMeshComponent()->Bounds.GetBox();P=B.GetCenter();P.Z=FMath::Clamp(110.+StationPosition(Selected).Z,B.Min.Z+15,B.Max.Z-15);
  if(auto* PC=UGameplayStatics::GetPlayerController(this,0))if(PC->GetPawn()){const FVector D=(PC->GetPawn()->GetActorLocation()-P).GetSafeNormal();double Exit=DBL_MAX;for(int Axis=0;Axis<3;++Axis)if(FMath::Abs(D[Axis])>UE_SMALL_NUMBER)Exit=FMath::Min(Exit,((D[Axis]>0?B.Max[Axis]:B.Min[Axis])-P[Axis])/D[Axis]);if(FMath::IsFinite(Exit))P+=D*(Exit+2);}
  break;
 }
 auto Spawn=[&](EConstellationFXKind K,FVector At,FLinearColor C,float S){if(auto* F=UConstellationFXLibrary::SpawnEffect(this,K,At,FVector(0,-1,.35),C,S))F->SetOwner(this);};
 const FLinearColor Blue=UConstellationFXLibrary::CombatColor(EConstellationFXKind::SwordHit);
 const FLinearColor Green=UConstellationFXLibrary::CombatColor(EConstellationFXKind::SlimeHit),Orange=UConstellationFXLibrary::CombatColor(EConstellationFXKind::PlayerHit);
 auto CombatSpawn=[&](EConstellationFXKind K){if(auto* F=UConstellationFXLibrary::SpawnEffect(this,K,P,FVector(1,-.15,.15),UConstellationFXLibrary::CombatColor(K),UConstellationFXLibrary::CombatScale(K)))F->SetOwner(this);};
 switch(Selected){
 case 0:SlashAge=0;Sword->SetVisibility(true);break;
 case 1:CombatSpawn(EConstellationFXKind::SwordHit);break;
 case 2:CombatSpawn(EConstellationFXKind::SwordBlock);break;
 case 3:CombatSpawn(EConstellationFXKind::SwordParry);break;
 case 4:CombatSpawn(EConstellationFXKind::SlimeAttack);break;
 case 5:CombatSpawn(EConstellationFXKind::SlimeHit);break;
 case 6:CombatSpawn(EConstellationFXKind::PlayerHit);PreviewReaction();break;
 case 7:if(Glass)Glass->BreakGlass(Glass->GetActorLocation(),FVector(0,-1,.3));break;
 case 8:for(int I=0;I<5;++I)Spawn(EConstellationFXKind::RunDust,StationPosition(8)+FVector(I*30-60,(I%2)*20-10,8),FLinearColor(.45,.33,.2,1),1.5);break;
 case 9:Spawn(EConstellationFXKind::CaveMist,StationPosition(9),FLinearColor(.2,.35,.45,.35),.7);Spawn(EConstellationFXKind::CaveDust,P,FLinearColor(.7,.7,.6,.8),1.5);Spawn(EConstellationFXKind::CaveSpore,P,FLinearColor(.2,1,.7,1),1.5);Spawn(EConstellationFXKind::WaterDrop,StationPosition(9)+FVector(60,-90,240),Blue,2);Spawn(EConstellationFXKind::WaterRipple,StationPosition(9)+FVector(60,-90,6),Blue,3);break;
 }
}
void AConstellationFXGallery::Tick(float Dt){Super::Tick(Dt);
#if WITH_EDITOR
 if(GShaderCompilingManager&&GShaderCompilingManager->IsCompiling()){ReadyTime=0;return;}
#endif
 if(ReactionMesh){ReactionAge+=Dt;if(ReactionAge>=.35f)RestoreReaction();}
 Clock+=Dt;ReadyTime+=Dt;if(ReadyTime<2)return;
 auto* PC=UGameplayStatics::GetPlayerController(this,0);
 if(ReadyTime-Dt<2){FrameStation();Replay();}
 if(PC){const FKey Keys[]={EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight,EKeys::Nine,EKeys::Zero};for(int I=0;I<10;++I)if(PC->WasInputKeyJustPressed(Keys[I]))SelectStation(I);
 if(PC->WasInputKeyJustPressed(EKeys::PageDown))SelectStation(Selected+1);if(PC->WasInputKeyJustPressed(EKeys::PageUp))SelectStation(Selected-1);if(PC->WasInputKeyJustPressed(EKeys::F))FrameStation();if(PC->WasInputKeyJustPressed(EKeys::Enter))Replay();if(PC->WasInputKeyJustPressed(EKeys::R))bRepeat=!bRepeat;if(Selected==6 && PC->WasInputKeyJustPressed(EKeys::H)){HitDirection=(HitDirection+1)%4;Replay();}}
 ReplayClock+=Dt;if(bRepeat&&ReplayClock>(Selected==9?6.5f:Selected==7?4.f:2.f))Replay();
 if(Selected==0&&SlashAge<.65f){
  SlashAge+=Dt;const float T=FMath::Clamp(SlashAge/.45f,0.f,1.f);const float Angle=FMath::Lerp(-1.4f,1.4f,T);
  const FVector Pivot=StationPosition(0)+FVector(0,0,115),Outward=FVector(FMath::Sin(Angle),-.08f,FMath::Cos(Angle)).GetSafeNormal();
  Sword->SetWorldLocation(Pivot);Sword->SetWorldRotation(FRotationMatrix::MakeFromZ(-Outward).Rotator());
  Ribbon->AddTip(Sword->GetComponentTransform().TransformPosition(FVector(0,0,-95)),Dt);
  if(SlashAge>=.65f){Sword->SetVisibility(false);Ribbon->ResetTrail();}
 }
 if(bReactionCapture)
 {
  const float T=ReadyTime-2.f;const int32 Stage=int32(T/1.5f);const float Phase=FMath::Fmod(T,1.5f);
  if(Stage>=4){FPlatformMisc::RequestExit(false);SetActorTickEnabled(false);return;}
  if(Stage!=ReactionCaptureStage){ReactionCaptureStage=Stage;ReactionCaptureFrame=0;HitDirection=Stage;SelectStation(6);}
  if((ReactionCaptureFrame==0 && Phase>=.12f)||(ReactionCaptureFrame==1 && Phase>=.65f))
  {FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/FString::Printf(TEXT("VFXReview/reaction_%d_%s.png"),Stage,ReactionCaptureFrame==0?TEXT("peak"):TEXT("recovered")),false,false);++ReactionCaptureFrame;}
 }
 if(bProbe||bCapture){ProbeClock+=Dt;
  const float Step=bCapture?3.5f:4.f;
  int32 Next=int32(ProbeClock/Step);
  if(Next!=ProbeStage){ProbeStage=Next;bProbeCaptured=false;if(Next<(bCapture?10:8))SelectStation(bCapture?Next:7);if(bProbe&&Next==0&&PC&&PC->GetPawn())ProbeStart=PC->GetPawn()->GetActorLocation();}
  if(bCapture&&ProbeStage<10&&!bProbeCaptured&&FMath::Fmod(ProbeClock,Step)>(Selected==9?1.f:Selected==0?.18f:.045f)){bProbeCaptured=true;if(Selected==0){UE_LOG(LogTemp,Display,TEXT("RIBBON_REVIEW age=%f active=%d"),SlashAge,Ribbon->GetSegmentCount());if(const auto* Mesh=Ribbon->GetProcMeshSection(0)){UE_LOG(LogTemp,Display,TEXT("RIBBON_MESH vertices=%d triangles=%d"),Mesh->ProcVertexBuffer.Num(),Mesh->ProcIndexBuffer.Num()/3);}}FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/FString::Printf(TEXT("VFXReview/gallery_%02d.png"),Selected),false,false);}
  if(bProbe&&PC&&PC->GetPawn()){if(ProbeClock>.3f&&ProbeClock<.7f)PC->GetPawn()->AddMovementInput(FVector::RightVector,1);if(ProbeClock>.8f&&ProbeClock<1)bMovementVerified=FVector::Dist(ProbeStart,PC->GetPawn()->GetActorLocation())>10;}
  if(bProbe&&ProbeClock>4)GlassFrames.Add(Dt*1000.);
  if(ProbeStage>=(bCapture?10:8)){GlassFrames.Sort();double Sum=0;for(double V:GlassFrames)Sum+=V;const bool Free=PC&&PC->GetPawn()&&PC->GetViewTarget()==PC->GetPawn()&&!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored();FString Json=FString::Printf(TEXT("{\"pawn_moved\":%s,\"free_movement\":%s,\"replays\":%d,\"samples\":%d,\"mean_ms\":%.3f,\"p95_ms\":%.3f,\"max_ms\":%.3f,\"capture\":%s}"),bMovementVerified?TEXT("true"):TEXT("false"),Free?TEXT("true"):TEXT("false"),ReplayCount,GlassFrames.Num(),GlassFrames.Num()?Sum/GlassFrames.Num():0,GlassFrames.Num()?GlassFrames[FMath::Min(GlassFrames.Num()-1,int32(GlassFrames.Num()*.95))]:0,GlassFrames.Num()?GlassFrames.Last():0,bCapture?TEXT("true"):TEXT("false"));FFileHelper::SaveStringToFile(Json,*(FPaths::ProjectSavedDir()/(bCapture?TEXT("VFXReview/gallery-capture.json"):TEXT("VFXReview/gallery-probe.json"))));FPlatformMisc::RequestExit(false);SetActorTickEnabled(false);}
 }
}
void AConstellationFXGalleryHUD::DrawHUD()
{
 Super::DrawHUD();if(!Canvas)return;
 for(TActorIterator<AConstellationFXGallery> I(GetWorld());I;++I)
 {
  const TCHAR* Directions[]={TEXT("Front"),TEXT("Back"),TEXT("Left"),TEXT("Right")};
  const FString Direction=I->Selected==6?FString::Printf(TEXT(" | Hit from %s"),Directions[I->HitDirection]):FString();
  DrawRect(FLinearColor(0,0,0,.7f),16,16,890,112);
  DrawText(FString::Printf(TEXT("VFX GALLERY | %d  %s | %s%s"),(I->Selected+1)%10,AConstellationFXGallery::StationName(I->Selected),I->ReadyTime<2?TEXT("PREPARING"):I->bRepeat?TEXT("LOOP ON"):TEXT("MANUAL"),*Direction),FLinearColor::White,30,26,nullptr,1.25);
  DrawText(TEXT("WASD + mouse: fly | E/Q: up/down | 1..9,0: station | PgUp/PgDn: previous/next"),FLinearColor::White,30,61);
  DrawText(TEXT("Enter: replay | R: loop | F: frame | H: hit direction (station 7) | Shift+F1: mouse"),FLinearColor::White,30,87);break;
 }
}
