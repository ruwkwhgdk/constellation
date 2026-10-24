#include "AbilityAcquisitionEditorLibrary.h"
#include "AbilityAcquisitionSubsystem.h"
#include "Engine/Blueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_VariableSet.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "K2Node_Event.h"
#include "K2Node_IfThenElse.h"
#include "SceneDirectorInteractionComponent.h"
bool UAbilityAcquisitionEditorLibrary::EnsureSceneInteractionComponent(AActor* Source)
{
 if(!Source)return false;if(Source->FindComponentByClass<USceneDirectorInteractionComponent>())return true;
 Source->Modify();auto* C=NewObject<USceneDirectorInteractionComponent>(Source,TEXT("Ac_SceneDirectorInteraction"),RF_Transactional);Source->AddInstanceComponent(C);C->RegisterComponent();Source->MarkPackageDirty();return true;
}
bool UAbilityAcquisitionEditorLibrary::InstallJumpInteractionRoute(UBlueprint* BP,FString& Error)
{
 if(!BP){Error=TEXT("No blueprint");return false;}
 auto* G=FBlueprintEditorUtils::FindEventGraph(BP);if(!G){Error=TEXT("No event graph");return false;}
 for(UEdGraphNode* N:G->Nodes)if(N->NodeComment==TEXT("JumpAcquisition.Route"))return true;
 UK2Node_Event* Event=nullptr;for(UEdGraphNode* N:G->Nodes)if(auto* E=Cast<UK2Node_Event>(N);E&&E->EventReference.GetMemberName()==TEXT("Interact"))Event=E;
 auto* Then=Event?Event->FindPin(UEdGraphSchema_K2::PN_Then):nullptr;
 if(!Then||Then->LinkedTo.Num()!=1||!Event->FindPin(TEXT("Interactor"))){Error=TEXT("Unexpected Interact schema");return false;}
 auto* Original=Then->LinkedTo[0];BP->Modify();G->Modify();
 auto Add=[&](UEdGraphNode* N,int Y){G->AddNode(N,false,false);N->CreateNewGuid();N->PostPlacedNewNode();N->AllocateDefaultPins();N->NodePosX=Event->NodePosX+300;N->NodePosY=Event->NodePosY+Y;};
 auto* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(USceneDirectorInteractionComponent::StaticClass()->FindFunctionByName(TEXT("RouteInteraction")));Add(Call,-350);Call->NodeComment=TEXT("JumpAcquisition.Route");
 auto* Self=NewObject<UK2Node_Self>(G);Add(Self,-150);auto* Branch=NewObject<UK2Node_IfThenElse>(G);Add(Branch,-550);
 bool OK=true;auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!G->GetSchema()->TryCreateConnection(A,B))OK=false;};
 Then->BreakLinkTo(Original);Link(Then,Call->GetExecPin());Link(Self->FindPin(UEdGraphSchema_K2::PN_Self),Call->FindPin(TEXT("Owner")));Link(Event->FindPin(TEXT("Interactor")),Call->FindPin(TEXT("Interactor")));Link(Call->GetThenPin(),Branch->GetExecPin());Link(Call->GetReturnValuePin(),Branch->GetConditionPin());Link(Branch->GetElsePin(),Original);
 if(!OK){Error=TEXT("Route pins failed; do not save");return false;}FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("Compile failed");return false;}return true;
}
bool UAbilityAcquisitionEditorLibrary::InstallAcquisitionHooks(UBlueprint* BP,FString& Error)
{
 if(!BP){Error=TEXT("Missing blueprint");return false;}
 UEdGraph* G=nullptr;for(UEdGraph* Graph:BP->FunctionGraphs)if(Graph->GetName()==TEXT("Unlock Ability"))G=Graph;
 if(!G){Error=TEXT("Unlock Ability graph missing");return false;}
 int32 Existing=0;for(UEdGraphNode* N:G->Nodes)if(N->NodeComment.StartsWith(TEXT("AbilityAcquisition.BeforeUnlock.")))Existing++;
 if(Existing){if(Existing==3)return true;Error=TEXT("Partial hook installation; restore backup before retry");return false;}
 const FName Names[]={TEXT("IsJumpUnlocked"),TEXT("IsCombatUnlocked"),TEXT("IsTransformUnlocked")};
 TArray<UK2Node_VariableSet*> Targets;for(auto Name:Names){UK2Node_VariableSet* Match=nullptr;for(UEdGraphNode* N:G->Nodes)if(auto* Set=Cast<UK2Node_VariableSet>(N);Set&&Set->VariableReference.GetMemberName()==Name){if(Match){Error=TEXT("Duplicate setter");return false;}Match=Set;}if(!Match||!Match->FindPin(Name)||Match->FindPin(Name)->LinkedTo.Num()!=1||Match->GetExecPin()->LinkedTo.Num()!=1){Error=TEXT("Unexpected setter schema");return false;}Targets.Add(Match);}
 UFunction* Function=UAbilityAcquisitionLibrary::StaticClass()->FindFunctionByName(TEXT("BeforeUnlock"));if(!Function)return false;
 BP->Modify();G->Modify();bool OK=true;
 for(int32 I=0;I<3;I++)
 {
  auto* Target=Targets[I];auto* Incoming=Target->GetExecPin()->LinkedTo[0];auto* Unlock=Target->FindPin(Names[I])->LinkedTo[0];
  auto Add=[&](UEdGraphNode* N){G->AddNode(N,false,false);N->CreateNewGuid();N->PostPlacedNewNode();N->AllocateDefaultPins();N->NodePosX=Target->NodePosX-320;N->NodePosY=Target->NodePosY;};
  auto* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(Function);Add(Call);Call->NodeComment=FString::Printf(TEXT("AbilityAcquisition.BeforeUnlock.%d"),I);
  auto* Self=NewObject<UK2Node_Self>(G);Add(Self);Self->NodePosY+=160;
  auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!G->GetSchema()->TryCreateConnection(A,B))OK=false;};
  Call->FindPin(TEXT("Slot"))->DefaultValue=FString::FromInt(I);
  Link(Self->FindPin(UEdGraphSchema_K2::PN_Self),Call->FindPin(TEXT("AbilityComponent")));Link(Unlock,Call->FindPin(TEXT("Unlock")));
  Incoming->BreakLinkTo(Target->GetExecPin());Link(Incoming,Call->GetExecPin());Link(Call->GetThenPin(),Target->GetExecPin());
 }
 if(!OK){Error=TEXT("Pin connection failed; do not save");return false;}
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("Compile failed; do not save");return false;}return true;
}
