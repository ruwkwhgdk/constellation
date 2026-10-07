#include "CombatLabCharacter.h"
#include "SCombatWorkbench.h"
#include "GameFramework/PlayerController.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Framework/Application/SlateApplication.h"

void ACombatLabCharacter::EnsureWorkbench()
{
    if(Workbench.IsValid() || bTrainingEnemy || !FSlateApplication::IsInitialized()) return;
    auto* PC=Cast<APlayerController>(GetController());
    auto* GI=GetGameInstance();
    if(!PC || !PC->IsLocalController() || !GI || !GI->GetGameViewportClient()) return;
    Workbench=SNew(SCombatWorkbench,this);
    GI->GetGameViewportClient()->AddViewportWidgetContent(Workbench.ToSharedRef(),50);
}
void ACombatLabCharacter::ToggleWorkbench()
{
    EnsureWorkbench();
    if(Workbench) Workbench->SetOpen(!bWorkbenchOpen);
}
void ACombatLabCharacter::ClearWorkbench()
{
    if(!Workbench) return;
    if(bWorkbenchOpen) Workbench->SetOpen(false);
    Workbench->RestoreObservation();
    if(auto* GI=GetGameInstance())
        if(auto* Viewport=GI->GetGameViewportClient()) Viewport->RemoveViewportWidgetContent(Workbench.ToSharedRef());
    Workbench.Reset(); bWorkbenchOpen=false;
}
