#include "FallAnimationEditorLibrary.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/Skeleton.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_Slot.h"
#include "EdGraph/EdGraph.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"

FString UFallAnimationEditorLibrary::InstallFallSlot(UAnimBlueprint* BP)
{
 if(!BP||!BP->TargetSkeleton)return TEXT("ERROR missing animation blueprint/skeleton");
 TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);
 for(auto* G:Graphs)if(G->GetFName()==TEXT("AnimGraph"))
 {
  if(FindObject<UEdGraphNode>(G,TEXT("FallFullBodySlot")))return TEXT("changes=0 errors=0");
  UAnimGraphNode_Root* Root=nullptr;
  for(const auto& N:G->Nodes)if(auto* R=Cast<UAnimGraphNode_Root>(N.Get()))Root=R;
  if(!Root||Root->FindPinChecked(TEXT("Result"))->LinkedTo.Num()!=1)return TEXT("ERROR unexpected root pose layout");
  auto* Input=Root->FindPinChecked(TEXT("Result"));auto* Source=Input->LinkedTo[0];const auto* Schema=G->GetSchema();BP->Modify();G->Modify();Root->Modify();
  auto* Slot=NewObject<UAnimGraphNode_Slot>(G,TEXT("FallFullBodySlot"));G->AddNode(Slot,false,false);Slot->CreateNewGuid();Slot->PostPlacedNewNode();Slot->NodePosX=Root->NodePosX-220;Slot->NodePosY=Root->NodePosY;Slot->Node.SlotName=TEXT("FallFullBody");Slot->Node.bAlwaysUpdateSourcePose=true;Slot->AllocateDefaultPins();
  Input->BreakAllPinLinks();
  if(!Schema->TryCreateConnection(Source,Slot->FindPinChecked(TEXT("Source")))||!Schema->TryCreateConnection(Slot->FindPinChecked(TEXT("Pose")),Input))
  {G->RemoveNode(Slot);Schema->TryCreateConnection(Source,Input);return TEXT("ERROR could not connect fall slot");}
  BP->TargetSkeleton->Modify();BP->TargetSkeleton->RegisterSlotNode(TEXT("FallFullBody"));BP->TargetSkeleton->SetSlotGroupName(TEXT("FallFullBody"),TEXT("FallGroup"));
  FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FCompilerResultsLog Log;FKismetEditorUtilities::CompileBlueprint(BP,EBlueprintCompileOptions::None,&Log);
  return FString::Printf(TEXT("changes=1 errors=%d warnings=%d"),Log.NumErrors,Log.NumWarnings);
 }
 return TEXT("ERROR no root animation graph");
}
