#include "PickupTutorialTrigger.h"
#include "TutorialPromptWidget.h"
#include "InteractionPromptComponent.h"
#include "SchoolOpeningSceneActor.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"

APickupTutorialTrigger::APickupTutorialTrigger()
{
 PrimaryActorTick.bCanEverTick=true;
 PrimaryActorTick.TickInterval=.1f;
 Area=CreateDefaultSubobject<UBoxComponent>(TEXT("Area"));
 SetRootComponent(Area);
 Area->SetBoxExtent(AreaExtent);
 Area->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 Area->SetGenerateOverlapEvents(false);
}

void APickupTutorialTrigger::OnConstruction(const FTransform& Transform)
{
 Super::OnConstruction(Transform);
 Area->SetBoxExtent(AreaExtent.GetAbs());
}

void APickupTutorialTrigger::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 if(bHasShown)return;
 UWorld* World=GetWorld();
 APlayerController* PC=World?World->GetFirstPlayerController():nullptr;
 APawn* Pawn=PC?PC->GetPawn():nullptr;
 if(!Pawn||!PC->IsLocalController()||PC->IsMoveInputIgnored()||World->IsPaused())return;
 const FVector Local=Area->GetComponentTransform().InverseTransformPosition(Pawn->GetActorLocation());
 if(!FBox(-Area->GetUnscaledBoxExtent(),Area->GetUnscaledBoxExtent()).IsInsideOrOn(Local))return;
 for(TActorIterator<ASchoolOpeningSceneActor> It(World);It;++It)if(It->bPending)return;
 const auto* Interaction=Pawn->FindComponentByClass<UInteractionPromptComponent>();
 if(!Interaction||Interaction->GetInteractionKeyText().IsEmpty())return;
 Prompt=CreateWidget<UTutorialPromptWidget>(PC);
 if(!Prompt)return;
 Prompt->Action=ETutorialPromptAction::PickUp;
 Prompt->TargetKeys={EKeys::F};
 Prompt->HoldSeconds=8.f;
 if(!Prompt->AddToPlayerScreen(201)){Prompt=nullptr;return;}
 bHasShown=true;
 SetActorTickEnabled(false);
}

void APickupTutorialTrigger::EndPlay(const EEndPlayReason::Type Reason)
{
 if(Prompt)Prompt->RemoveFromParent();
 Prompt=nullptr;
 Super::EndPlay(Reason);
}
