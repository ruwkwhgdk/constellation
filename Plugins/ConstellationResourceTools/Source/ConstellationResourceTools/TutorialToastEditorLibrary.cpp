#include "TutorialToastEditorLibrary.h"
#include "TutorialPromptWidget.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "K2Node_CallFunction.h"
#include "EdGraphSchema_K2.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
bool UTutorialToastEditorLibrary::PrepareToastCaller(UBlueprint* Blueprint,FString& Error)
{
 if(!Blueprint){Error=TEXT("Missing Blueprint");return false;}
 const FString Path=Blueprint->GetOutermost()->GetName();
 FString NodeName,Function;
 if(Path==TEXT("/Game/Constellation/UI/Blueprints/BP_HUD")){NodeName=TEXT("K2Node_CallFunction_13");Function=TEXT("RemoveFromParent");}
 else if(Path==TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object")){NodeName=TEXT("K2Node_CallFunction_49");Function=TEXT("Do Jump");}
 else if(Path==TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Sword_Pickup")){NodeName=TEXT("K2Node_CallFunction_52");Function=TEXT("Do Attack");}
 else if(Path==TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Transform")){NodeName=TEXT("K2Node_CallFunction_1");Function=TEXT("Execute Transform");}
 else{Error=TEXT("Unsupported caller");return false;}
 UK2Node_CallFunction* Target=nullptr;
 for(UEdGraph* Graph:Blueprint->UbergraphPages)for(UEdGraphNode* Node:Graph->Nodes)
  if(Node->GetName()==NodeName)Target=Cast<UK2Node_CallFunction>(Node);
 if(!Target||Target->FunctionReference.GetMemberName().ToString()!=Function){Error=TEXT("Caller graph differs from audited version");return false;}
 UEdGraphPin* In=Target->FindPin(UEdGraphSchema_K2::PN_Execute);
 UEdGraphPin* Out=Target->FindPin(UEdGraphSchema_K2::PN_Then);
 if(!In){Error=TEXT("Missing execution pin");return false;}
 if(In->LinkedTo.Num())
 {
  const auto Before=In->LinkedTo;const auto After=Out?Out->LinkedTo:TArray<UEdGraphPin*>();
  Blueprint->Modify();Target->Modify();In->BreakAllPinLinks();if(Out)Out->BreakAllPinLinks();
  for(UEdGraphPin* Source:Before)for(UEdGraphPin* Dest:After)
   if(!Target->GetGraph()->GetSchema()->TryCreateConnection(Source,Dest)){Error=TEXT("Execution bypass failed");return false;}
  Target->NodeComment=TEXT("Nonblocking toast: no synthetic action or shared-widget removal on completion.");
  FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
 }
 FKismetEditorUtilities::CompileBlueprint(Blueprint);
 if(Blueprint->Status==BS_Error){Error=TEXT("Blueprint compilation failed");return false;}return true;
}
UTutorialPromptWidget* UTutorialToastEditorLibrary::CreateToastReview(UWorld* World,int32 ActionIndex,float Duration)
{
 if(!World)return nullptr;
 auto* Class=LoadClass<UTutorialPromptWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_Tutorial.WBP_Tutorial_C"));
 if(!Class)return nullptr;
 auto* Widget=CreateWidget<UTutorialPromptWidget>(World->GetFirstPlayerController(),Class);
 if(!Widget)return nullptr;
 Widget->TargetKeys=ActionIndex==0?TArray<FKey>{EKeys::W,EKeys::A,EKeys::S,EKeys::D}:TArray<FKey>{ActionIndex==1?EKeys::SpaceBar:ActionIndex==2?EKeys::LeftMouseButton:EKeys::Z};
 Widget->HoldSeconds=Duration;Widget->AddToViewport(201);return Widget;
}
