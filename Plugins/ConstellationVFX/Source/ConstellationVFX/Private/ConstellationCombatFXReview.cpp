#include "ConstellationCombatFXReview.h"
#include "ConstellationCombatFX.h"
#include "ConstellationSwordRibbonComponent.h"
#include "ConstellationFXActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/GameViewportClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

AConstellationCombatFXReview::AConstellationCombatFXReview()
{
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}
void AConstellationCombatFXReview::BeginPlay()
{
    Super::BeginPlay();
    bCapture=FParse::Param(FCommandLine::Get(),TEXT("VFXCandidatesCapture"));
    // Temporary review isolation only; no map saves or normal gallery changes.
    for(TActorIterator<AActor> It(GetWorld());It;++It)
        if(*It!=this && !It->IsHidden()){HiddenActors.Add(*It);It->SetActorHiddenInGame(true);}
    for(int32 I=0;I<7;++I)
    {
        auto* Ribbon=NewObject<UConstellationSwordRibbonComponent>(this);Ribbon->SetupAttachment(RootComponent);Ribbon->RegisterComponent();
        UConstellationCombatFX::ConfigureTrail(Ribbon,EConstellationAttackTrail(I));Ribbons.Add(Ribbon);
    }
    Camera=GetWorld()->SpawnActor<ACameraActor>();
    if(Camera)
    {
        const FVector View=GetActorLocation()+FVector(0,0,1000);
        Camera->SetActorLocation(View);Camera->SetActorRotation(FRotator(-90,-90,0));
        Camera->GetCameraComponent()->SetProjectionMode(ECameraProjectionMode::Orthographic);
        Camera->GetCameraComponent()->SetOrthoWidth(1200.f);
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_MotionBlurAmount=true;
        Camera->GetCameraComponent()->PostProcessSettings.MotionBlurAmount=0.f;
        if(auto* PC=GetWorld()->GetFirstPlayerController()){PC->SetViewTarget(Camera);if(PC->GetHUD())PC->GetHUD()->bShowHUD=false;}
    }
    IFileManager::Get().MakeDirectory(*(FPaths::ProjectSavedDir()/TEXT("VFXCandidates")),true);
    UE_LOG(LogTemp,Display,TEXT("VFX_CANDIDATES synthetic arcs: row1 Light1 Light2 Light3 Heavy1; row2 Heavy2 LightParry HeavyParry. Not motion validation."));
}
void AConstellationCombatFXReview::Contacts()
{
    UConstellationFXLibrary::StopEffectsForOwner(this);
    const EConstellationFXKind Kinds[]={EConstellationFXKind::SwordHit,EConstellationFXKind::SlimeHit,EConstellationFXKind::PlayerHit,EConstellationFXKind::SwordBlock,EConstellationFXKind::SwordParry,EConstellationFXKind::GroggyEnter,EConstellationFXKind::GroggyHold,EConstellationFXKind::GroggyExit};
    for(int32 I=0;I<8;++I)
    {
        const FVector P=GetActorLocation()+FVector((I%4-1.5f)*260.f,(I/4-.5f)*300.f,0);
        if(auto* FX=UConstellationFXLibrary::SpawnEffect(this,Kinds[I],P,FVector::RightVector,UConstellationFXLibrary::CombatColor(Kinds[I]),UConstellationFXLibrary::CombatScale(Kinds[I])))FX->SetOwner(this);
    }
}
void AConstellationCombatFXReview::Tick(float Delta)
{
    Super::Tick(Delta);Clock+=Delta;
    // The gallery HUD may be created after this actor's BeginPlay.
    // Use an empty engine HUD in this separate diagnostic process, not a new UI.
    if(!bHUDSwapped)
        if(auto* PC=GetWorld()->GetFirstPlayerController();PC && PC->GetHUD())
        {PreviousHUD=PC->GetHUD()->GetClass();PC->ClientSetHUD(AHUD::StaticClass());bHUDSwapped=true;}
    const bool ContactStage=Clock>=12.f;
    const float Phase=FMath::Fmod(Clock,2.f);
    if(ContactStage)
    {
        for(auto Ribbon:Ribbons)Ribbon->ResetTrail();
        if(Phase<PreviousPhase)Contacts();
        if(bCapture && !bContactsCaptured && Clock>16.f && Phase>.045f && Phase<.2f)
        {
            bContactsCaptured=true;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("VFXCandidates/contacts.png"),false,false);
            UE_LOG(LogTemp,Display,TEXT("VFX_CANDIDATES contact sheet requested: row1 SwordHit SlimeHit PlayerHit Guard; row2 Perfect GroggyEnter Hold Exit"));
        }
    }
    else
    {
        for(int32 I=0;I<Ribbons.Num();++I)
        {
            const FVector Center=GetActorLocation()+FVector((I%4-1.5f)*260.f,(I/4-.5f)*300.f,0);
            if(Phase<.3f || Phase>.85f){Ribbons[I]->ResetTrail();continue;}
            const float Angle=(Phase-.3f)/.55f*PI*1.35f;
            Ribbons[I]->AddTip(Center+FVector(FMath::Cos(Angle)*90,FMath::Sin(Angle)*90,0),Delta);
        }
        if(bCapture && !bTrailsCaptured && Clock>10.6f && Phase<.82f)
        {
            bTrailsCaptured=true;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("VFXCandidates/trails.png"),false,false);
        }
    }
    PreviousPhase=Phase;
    if(bCapture && Clock>19.f)FPlatformMisc::RequestExit(false);
    else if(!bCapture && Clock>20.f){UConstellationFXLibrary::StopEffectsForOwner(this);Clock=0.f;PreviousPhase=2.f;}
}
void AConstellationCombatFXReview::EndPlay(const EEndPlayReason::Type Reason)
{
    UConstellationFXLibrary::StopEffectsForOwner(this);if(Camera)Camera->Destroy();
    for(auto Actor:HiddenActors)if(Actor.IsValid())Actor->SetActorHiddenInGame(false);
    if(Reason==EEndPlayReason::Destroyed && bHUDSwapped && PreviousHUD)
        if(auto* PC=GetWorld()->GetFirstPlayerController())PC->ClientSetHUD(PreviousHUD);
    Super::EndPlay(Reason);
}
