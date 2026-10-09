#include "AbilityAcquisitionEditorLibrary.h"
#include "AbilityAcquisitionSubsystem.h"
#include "Engine/Blueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_VariableSet.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
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
