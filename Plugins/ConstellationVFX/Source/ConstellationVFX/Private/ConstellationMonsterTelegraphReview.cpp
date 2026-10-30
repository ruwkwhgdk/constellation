#include "ConstellationMonsterTelegraphReview.h"
#include "ConstellationMonsterTelegraphComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

namespace
{
    const TCHAR* ShotNames[]={TEXT("bright-near-preparation"),TEXT("bright-near-execution"),TEXT("dark-far-preparation"),TEXT("dark-far-execution"),TEXT("bright-multiple"),TEXT("dark-multiple")};
}
AConstellationMonsterTelegraphReview::AConstellationMonsterTelegraphReview()
{
    PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}
void AConstellationMonsterTelegraphReview::BeginPlay()
{
    Super::BeginPlay();
    bCapture=FParse::Param(FCommandLine::Get(),TEXT("MonsterTelegraphCapture"));
    FString Run=FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S"));
    OutputDirectory=FPaths::ProjectSavedDir()/TEXT("MonsterTelegraph")/Run;
    IFileManager::Get().MakeDirectory(*OutputDirectory,true);
    for(TActorIterator<AActor> I(GetWorld());I;++I)if(*I!=this && !I->IsHidden()){HiddenActors.Add(*I);I->SetActorHiddenInGame(true);}
    auto* Asset=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Liquid/SKM_Slime_Liquid.SKM_Slime_Liquid"));
    auto* Animation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Attack.AS_Slime_Attack"));
    for(int32 I=0;I<3;++I)
    {
        auto* Monster=GetWorld()->SpawnActor<AActor>();Props.Add(Monster);
        auto* Mesh=NewObject<USkeletalMeshComponent>(Monster);Monster->SetRootComponent(Mesh);Mesh->RegisterComponent();
        Mesh->SetSkeletalMeshAsset(Asset);Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);Mesh->PlayAnimation(Animation,true);
        Monster->SetActorLocation(GetActorLocation()+FVector(0,I==0?0.f:I==1?-140.f:140.f,0));Monsters.Add(Mesh);
        auto* FX=NewObject<UConstellationMonsterTelegraphComponent>(Monster);Monster->AddInstanceComponent(FX);FX->RegisterComponent();
        FX->SetAnchor(Mesh,NAME_None,FVector(0,0,45));Telegraphs.Add(FX);
    }
    auto* Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Constellation/VFX/Telegraph/M_MonsterTelegraph.M_MonsterTelegraph"));
    Backdrop=UMaterialInstanceDynamic::Create(Material,this);Backdrop->SetScalarParameterValue(TEXT("Brightness"),1.f);
    auto* Panel=GetWorld()->SpawnActor<AStaticMeshActor>();Props.Add(Panel);
    Panel->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
    Panel->GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Panel->GetStaticMeshComponent()->SetMaterial(0,Backdrop);Panel->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Panel->SetActorLocation(GetActorLocation()+FVector(-200,0,100));Panel->SetActorScale3D(FVector(.1,40,25));
    auto* Light=GetWorld()->SpawnActor<ADirectionalLight>();Props.Add(Light);Light->GetLightComponent()->SetMobility(EComponentMobility::Movable);Light->SetActorRotation(FRotator(-35,180,0));Light->GetLightComponent()->SetIntensity(5.f);
    Camera=GetWorld()->SpawnActor<ACameraActor>();Camera->GetCameraComponent()->SetFieldOfView(50.f);
    auto& Post=Camera->GetCameraComponent()->PostProcessSettings;
    Post.bOverride_MotionBlurAmount=true;Post.MotionBlurAmount=0;
    Post.bOverride_AutoExposureMethod=true;Post.AutoExposureMethod=AEM_Manual;
    Post.bOverride_AutoExposureApplyPhysicalCameraExposure=true;Post.AutoExposureApplyPhysicalCameraExposure=false;
    Post.bOverride_BloomIntensity=true;Post.BloomIntensity=.25f;
    UE_LOG(LogTemp,Display,TEXT("MONSTER_TELEGRAPH_REVIEW output=%s existing_animation=%s mesh=%s; scripted visual fixture only"),*OutputDirectory,*GetNameSafe(Animation),*GetNameSafe(Asset));
}
void AConstellationMonsterTelegraphReview::StartStage(int32 Index)
{
    Stage=Index;StageAge=0;bCaptured=false;
    const int64 Id=++PreviewId;
    const bool Multiple=Stage>=4,Bright=Stage<2 || Stage==4;
    Backdrop->SetVectorParameterValue(TEXT("PhaseColor"),Bright?FLinearColor(.8f,.8f,.8f,1):FLinearColor(.008f,.008f,.008f,1));
    const float Distance=Multiple?850.f:Stage<2?450.f:1400.f;
    Camera->SetActorLocation(GetActorLocation()+FVector(Distance,0,150));
    Camera->SetActorRotation((GetActorLocation()+FVector(0,0,45)-Camera->GetActorLocation()).Rotation());
    if(auto* PC=GetWorld()->GetFirstPlayerController())PC->SetViewTarget(Camera);
    for(int32 I=0;I<Telegraphs.Num();++I)
    {
        Telegraphs[I]->StopAllTelegraphs();Monsters[I]->SetVisibility(Multiple || I==0);
        if(Multiple || I==0)
        {
            Telegraphs[I]->BeginTelegraph(Id);
            if(Multiple?I==1:Stage==1 || Stage==3)Telegraphs[I]->SetPhase(Id,EMonsterTelegraphPhase::Execution);
        }
    }
    UE_LOG(LogTemp,Display,TEXT("MONSTER_TELEGRAPH_STAGE %s distance_cm=%.0f bright=%d enemies=%d"),ShotNames[Stage],Distance,Bright,Multiple?3:1);
}
void AConstellationMonsterTelegraphReview::Tick(float Delta)
{
    Super::Tick(Delta);Clock+=Delta;
    if(!bHUDHidden)if(auto* PC=GetWorld()->GetFirstPlayerController();PC && PC->GetHUD()){PC->ClientSetHUD(AHUD::StaticClass());bHUDHidden=true;}
    if(Clock<5.f)return;
    if(Stage<0){StartStage(0);return;}
    StageAge+=Delta;
    if(!bCaptured && StageAge>1.2f)
    {
        bCaptured=true;
        if(bCapture)FScreenshotRequest::RequestScreenshot(OutputDirectory/(FString(ShotNames[Stage])+TEXT(".png")),false,false);
        UE_LOG(LogTemp,Display,TEXT("MONSTER_TELEGRAPH_CAPTURE %s animation_position=%.3f"),ShotNames[Stage],Monsters[0]->GetPosition());
    }
    if(StageAge>3.f)
    {
        if(Stage<5)StartStage(Stage+1);
        else if(bCapture){for(auto FX:Telegraphs)FX->StopAllTelegraphs();FPlatformMisc::RequestExit(false);}
        else {for(auto FX:Telegraphs)FX->StopAllTelegraphs();Stage=-1;Clock=0;}
    }
}
void AConstellationMonsterTelegraphReview::EndPlay(const EEndPlayReason::Type Reason)
{
    for(auto FX:Telegraphs)if(IsValid(FX))FX->StopAllTelegraphs();
    for(auto Actor:Props)if(IsValid(Actor))Actor->Destroy();if(Camera)Camera->Destroy();
    for(auto Actor:HiddenActors)if(Actor.IsValid())Actor->SetActorHiddenInGame(false);
    Super::EndPlay(Reason);
}
