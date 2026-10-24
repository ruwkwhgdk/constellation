#include "SwordAcquisitionReviewLibrary.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UnrealType.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "EnhancedPlayerInput.h"
#include "InputAction.h"
#include "Camera/PlayerCameraManager.h"
float USwordAcquisitionReviewLibrary::CameraBlendRemaining(APawn* Pawn)
{
 auto* PC=Pawn?Cast<APlayerController>(Pawn->GetController()):nullptr;
 return PC&&PC->PlayerCameraManager?PC->PlayerCameraManager->BlendTimeToGo:-1.f;
}
bool USwordAcquisitionReviewLibrary::PrepareBackgroundTick(UObject* Context)
{
 if(!Context||!Context->GetWorld()||Context->GetWorld()->WorldType!=EWorldType::PIE||!FParse::Param(FCommandLine::Get(),TEXT("SwordReview"))||!FSlateApplication::IsInitialized())return false;
 // Test-owned process only: advance Slate's app-active clock without moving/focusing any OS window.
 FSlateApplication::Get().ProcessApplicationActivationEvent(true);return true;
}
bool USwordAcquisitionReviewLibrary::PawnInputEnabled(APawn* Pawn){return Pawn&&Pawn->InputEnabled();}
FString USwordAcquisitionReviewLibrary::ReviewInputState(APawn* Pawn)
{
 auto* PC=Pawn?Cast<APlayerController>(Pawn->GetController()):nullptr;if(!PC)return TEXT("no controller");
 auto* Input=Cast<UEnhancedPlayerInput>(PC->PlayerInput);auto* Action=LoadObject<UInputAction>(nullptr,TEXT("/Game/Constellation/Input/IA_Attack.IA_Attack"));
 const auto* Instance=Input?Input->FindActionInstanceData(Action):nullptr;
 auto* LP=PC->GetLocalPlayer();UGameViewportClient* View=LP?LP->ViewportClient.Get():nullptr;
 return FString::Printf(TEXT("pawn=%d controller=%d move=%d look=%d viewportIgnore=%d trigger=%d value=%s"),Pawn->InputEnabled(),PC->InputEnabled(),PC->IsMoveInputIgnored(),PC->IsLookInputIgnored(),View?View->IgnoreInput():-1,Instance?int32(Instance->GetTriggerEvent()):-1,Instance?*Instance->GetValue().ToString():TEXT("none"));
}
bool USwordAcquisitionReviewLibrary::ConfigureSwordReview(APawn* Pawn)
{
 if(!Pawn||!PrepareBackgroundTick(Pawn))return false;
 for(auto* Component:Pawn->GetComponents())
 {
  auto* Jump=FindFProperty<FBoolProperty>(Component->GetClass(),TEXT("IsJumpUnlocked"));auto* Combat=FindFProperty<FBoolProperty>(Component->GetClass(),TEXT("IsCombatUnlocked"));
  auto* Attack=FindFProperty<FBoolProperty>(Component->GetClass(),TEXT("IsAttackUnlocked"));
  if(Jump&&Combat&&Attack){Jump->SetPropertyValue_InContainer(Component,true);Combat->SetPropertyValue_InContainer(Component,false);Attack->SetPropertyValue_InContainer(Component,false);return true;}
 }
 return false;
}
