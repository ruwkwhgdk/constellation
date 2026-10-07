#include "CombatAbilitySystem.h"
#include "CombatLabCharacter.h"
#include "CombatVFXComponent.h"
#include "CombatAttackInput.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Camera/PlayerCameraManager.h"

void ACombatLabCharacter::ApplyProjectLook(const FInputActionValue& Value)
{
    if (bWorkbenchOpen || LockedTarget.IsValid()) return;
    const FVector2D Axis=Value.Get<FVector2D>();
    if(!FMath::IsFinite(Axis.X) || !FMath::IsFinite(Axis.Y)) return;
    // Same path as BP_Player_Heroine: IA_Look modifiers, then controller yaw/pitch input.
    AddControllerYawInput(Axis.X);
    AddControllerPitchInput(Axis.Y);
}
void ACombatLabCharacter::ClearProjectControls()
{
    if(ControlsSubsystem.IsValid() && ActiveLookContext)
        ControlsSubsystem->RemoveMappingContext(ActiveLookContext);
    ControlsSubsystem.Reset(); ActiveLookContext=nullptr;
}
void ACombatLabCharacter::SetupProjectControls(UInputComponent* Input)
{
    ClearProjectControls();
    auto* PC=Cast<APlayerController>(GetController());
    if(!PC) return;
    PRAGMA_DISABLE_DEPRECATION_WARNINGS
    PC->SetDeprecatedInputYawScale(ProjectYawScale);
    PC->SetDeprecatedInputPitchScale(ProjectPitchScale);
    PRAGMA_ENABLE_DEPRECATION_WARNINGS
    if(PC->PlayerCameraManager)
    {
        PC->PlayerCameraManager->ViewPitchMin=ProjectPitchMin;
        PC->PlayerCameraManager->ViewPitchMax=ProjectPitchMax;
    }
    auto* Enhanced=Cast<UEnhancedInputComponent>(Input);
    auto* Local=PC->GetLocalPlayer();
    if(!Enhanced || !ProjectLookAction || !ProjectInputContext || !Local) return;
    auto* Subsystem=Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();
    if(!Subsystem) return;
    // Reuse the project's actual Look mapping and modifiers without activating unrelated gameplay inputs.
    ActiveLookContext=NewObject<UInputMappingContext>(this);
    for(const FEnhancedActionKeyMapping& Mapping:ProjectInputContext->GetMappings())
        if(Mapping.Action==ProjectLookAction)
            ActiveLookContext->MapKey(ProjectLookAction,Mapping.Key)=Mapping;
    ControlsSubsystem=Subsystem;
    Subsystem->AddMappingContext(ActiveLookContext,0);
    Enhanced->BindAction(ProjectLookAction,ETriggerEvent::Triggered,this,&ACombatLabCharacter::ApplyProjectLook);
}
void ACombatLabCharacter::UnPossessed()
{
    CombatVFX->StopPresentation(); ClearWorkbench(); Combat->CancelAction(); AttackInput->Clear(); ClearProjectControls(); Super::UnPossessed();
}
void ACombatLabCharacter::EndPlay(const EEndPlayReason::Type Reason)
{
    CombatVFX->StopPresentation(); ClearWorkbench(); ClearProjectControls(); Super::EndPlay(Reason);
}
