#include "PlayerHUDStyleEditorLibrary.h"
#include "StarlightPlayerHUDWidget.h"
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/ProgressBar.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "Components/ActorComponent.h"
#include "EdGraphSchema_K2.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
bool UPlayerHUDStyleEditorLibrary::ApplyStarlightHUD(UBlueprint* Widget,UBlueprint* Heroine,UBlueprint* Stats,FString& Error)
{
 auto* BP=Cast<UWidgetBlueprint>(Widget);
 if(!Stats||Stats->GetName()!=TEXT("Ac_Stats")){Error=TEXT("Expected common stats component");return false;}
 if(!BP||!Heroine||BP->GetName()!=TEXT("WBP_PlayerHUD")||Heroine->GetName()!=TEXT("BP_Player_Heroine")){Error=TEXT("Unexpected assets");return false;}
 for(FName Name:{FName("HPProgressBar"),FName("StaminaProgressBar")})if(!Cast<UProgressBar>(BP->WidgetTree->FindWidget(Name))){Error=TEXT("Original resource bars missing");return false;}
 struct FHook{const TCHAR* Node;const TCHAR* Pin;const TCHAR* Function;const TCHAR* Tag;};
 const FHook Hooks[]={{TEXT("K2Node_IfThenElse_10"),TEXT("else"),TEXT("NotifyLegacySprintRejected"),TEXT("StarlightHUD.SprintRejected")},{TEXT("K2Node_IfThenElse_0"),TEXT("then"),TEXT("NotifyDamage"),TEXT("StarlightHUD.Damage")}};
 // Validate all target nodes before changing either asset.
 for(const auto& Hook:Hooks)
 {
  UK2Node_IfThenElse* Branch=nullptr;
  for(UEdGraph* Graph:Heroine->UbergraphPages)for(UEdGraphNode* Node:Graph->Nodes)if(Node->GetName()==Hook.Node)Branch=Cast<UK2Node_IfThenElse>(Node);
  if(!Branch||!Branch->FindPin(Hook.Pin)){Error=TEXT("Audited heroine branch missing");return false;}
 }
 BP->Modify();BP->ParentClass=UStarlightPlayerHUDWidget::StaticClass();FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error){Error=TEXT("HUD compilation failed");return false;}
 Heroine->Modify();
 for(const auto& Hook:Hooks)
 {
  UK2Node_IfThenElse* Branch=nullptr;bool Exists=false;
  for(UEdGraph* Graph:Heroine->UbergraphPages)for(UEdGraphNode* Node:Graph->Nodes){if(Node->NodeComment==Hook.Tag)Exists=true;if(Node->GetName()==Hook.Node)Branch=Cast<UK2Node_IfThenElse>(Node);}
  if(Exists)continue;
  UEdGraph* Graph=Branch->GetGraph();auto* Schema=Graph->GetSchema();auto* Output=Branch->FindPinChecked(Hook.Pin);const auto Destinations=Output->LinkedTo;
  auto* Call=NewObject<UK2Node_CallFunction>(Graph);Call->SetFromFunction(UStarlightPlayerHUDWidget::StaticClass()->FindFunctionByName(Hook.Function));Graph->AddNode(Call);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodeComment=Hook.Tag;Call->NodePosX=Branch->NodePosX+240;Call->NodePosY=Branch->NodePosY+180;
  auto* Self=NewObject<UK2Node_Self>(Graph);Graph->AddNode(Self);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX;Self->NodePosY=Call->NodePosY+140;
  Output->BreakAllPinLinks();
  bool Linked=Schema->TryCreateConnection(Output,Call->GetExecPin())&&Schema->TryCreateConnection(Self->FindPinChecked(UEdGraphSchema_K2::PN_Self),Call->FindPinChecked(TEXT("Source")));
  for(auto* Dest:Destinations)Linked&=Schema->TryCreateConnection(Call->GetThenPin(),Dest);
  if(!Linked){Error=TEXT("Cosmetic hook connection failed");return false;}
 }
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Heroine);FKismetEditorUtilities::CompileBlueprint(Heroine);
 if(Heroine->Status==BS_Error){Error=TEXT("Heroine compilation failed");return false;}
 UEdGraphNode* DamageDelegate=nullptr;bool HasHook=false;
 for(UEdGraph* Graph:Stats->FunctionGraphs)if(Graph->GetName()==TEXT("Calculate Damage"))for(UEdGraphNode* Node:Graph->Nodes)
 {
  if(Node->NodeComment==TEXT("StarlightHUD.StatsDamage"))HasHook=true;
  if(Node->GetName()==TEXT("K2Node_CallDelegate_2"))DamageDelegate=Node;
 }
 if(!DamageDelegate){Error=TEXT("Common damage delegate missing");return false;}
 if(!HasHook)
 {
  Stats->Modify();auto* Graph=DamageDelegate->GetGraph();auto* Schema=Graph->GetSchema();auto* Output=DamageDelegate->FindPinChecked(UEdGraphSchema_K2::PN_Then);const auto Destinations=Output->LinkedTo;
  auto MakeCall=[Graph](UFunction* Function){auto* Node=NewObject<UK2Node_CallFunction>(Graph);Node->SetFromFunction(Function);Graph->AddNode(Node);Node->CreateNewGuid();Node->PostPlacedNewNode();Node->AllocateDefaultPins();return Node;};
  auto* Call=MakeCall(UStarlightPlayerHUDWidget::StaticClass()->FindFunctionByName(TEXT("NotifyDamage")));Call->NodeComment=TEXT("StarlightHUD.StatsDamage");
  auto* Owner=MakeCall(UActorComponent::StaticClass()->FindFunctionByName(TEXT("GetOwner")));
  Output->BreakAllPinLinks();bool Linked=Schema->TryCreateConnection(Output,Call->GetExecPin())&&Schema->TryCreateConnection(Owner->GetReturnValuePin(),Call->FindPinChecked(TEXT("Source")));
  for(auto* Dest:Destinations)Linked&=Schema->TryCreateConnection(Call->GetThenPin(),Dest);
  if(!Linked){Error=TEXT("Common damage hook connection failed");return false;}
 }
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Stats);FKismetEditorUtilities::CompileBlueprint(Stats);
 if(Stats->Status==BS_Error){Error=TEXT("Stats compilation failed");return false;}
 Error.Reset();return true;
}

#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
bool UPlayerHUDStyleEditorLibrary::InjectSprintReview(APlayerController* Player)
{
 auto* Subsystem=Player&&Player->GetLocalPlayer()?ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(Player->GetLocalPlayer()):nullptr;
 auto* Action=LoadObject<UInputAction>(nullptr,TEXT("/Game/Constellation/Input/IA_Dash.IA_Dash"));
 if(!Subsystem||!Action)return false;
 Subsystem->InjectInputForAction(Action,FInputActionValue(true),{},{});return true;
}

