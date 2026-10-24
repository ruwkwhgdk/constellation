#include "SchoolGateEditorLibrary.h"
#include "SchoolGateOpeningComponent.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Event.h"
#include "K2Node_CallParentFunction.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
FString USchoolGateEditorLibrary::Install(UBlueprint* BP)
{
 if(!BP||BP->GetName()!=TEXT("BP_School_Gate"))return TEXT("ERROR: wrong blueprint");
 TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);
 for(auto* Graph:Graphs)
 {
  UK2Node_Event* Event=nullptr;UK2Node_CallParentFunction* Parent=nullptr;
  for(UEdGraphNode* N:Graph->Nodes)
  {
   if(N->NodeComment==TEXT("Synchronized 6.5s gate opening"))return TEXT("OK: installed");
   if(auto* E=Cast<UK2Node_Event>(N))if(E->EventReference.GetMemberName()==TEXT("Interact"))Event=E;
   if(auto* P=Cast<UK2Node_CallParentFunction>(N))if(P->FunctionReference.GetMemberName()==TEXT("Interact"))Parent=P;
  }
  if(!Event||!Parent)continue;
  auto* ActorPin=Event->FindPin(TEXT("Interactor"));if(!ActorPin)return TEXT("ERROR: interactor pin missing");
  FGraphNodeCreator<UK2Node_CallFunction> CC(*Graph);auto* Call=CC.CreateNode();Call->SetFromFunction(USchoolGateOpeningComponent::StaticClass()->FindFunctionByName(TEXT("BeginOpening")));Call->NodeComment=TEXT("Synchronized 6.5s gate opening");Call->NodePosX=500;Call->NodePosY=-500;CC.Finalize();
  FGraphNodeCreator<UK2Node_IfThenElse> BC(*Graph);auto* Branch=BC.CreateNode();Branch->NodePosX=850;Branch->NodePosY=-500;BC.Finalize();
  FGraphNodeCreator<UK2Node_Self> SC(*Graph);auto* Self=SC.CreateNode();Self->NodePosX=200;Self->NodePosY=-650;SC.Finalize();
  auto* Schema=Graph->GetSchema();
  if(!Schema->TryCreateConnection(ActorPin,Call->FindPinChecked(TEXT("Interactor")))||!Schema->TryCreateConnection(Self->FindPinChecked(UEdGraphSchema_K2::PN_Self),Call->FindPinChecked(TEXT("Gate")))||!Schema->TryCreateConnection(Call->GetReturnValuePin(),Branch->GetConditionPin()))return TEXT("ERROR: data wiring");
  auto* Then=Event->FindPinChecked(UEdGraphSchema_K2::PN_Then);Then->BreakAllPinLinks();Parent->GetExecPin()->BreakAllPinLinks();Parent->GetThenPin()->BreakAllPinLinks();
  Then->MakeLinkTo(Call->GetExecPin());Call->GetThenPin()->MakeLinkTo(Branch->GetExecPin());Branch->GetThenPin()->MakeLinkTo(Parent->GetExecPin());
  FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);return TEXT("OK: animation controls leaves; parent bookkeeping preserved");
 }
 return TEXT("ERROR: Interact event not found");
}


#include "Settings/LevelEditorPlaySettings.h"
#include "Misc/App.h"
void USchoolGateEditorLibrary::PrepareReviewAudio()
{
 auto* S=GetMutableDefault<ULevelEditorPlaySettings>();S->EnableGameSound=true;S->SoloAudioInFirstPIEClient=true;FApp::SetUnfocusedVolumeMultiplier(1.f);FApp::SetVolumeMultiplier(1.f);
}

