#include "SceneDirectorLibrary.h"
FDirectorStep USceneDirectorLibrary::MakeDirectorStep(EDirectorNodeType Type)
{FDirectorStep Step;Step.Type=Type;return Step;}

#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
int32 USceneDirectorLibrary::ConfigureSchoolTutorialFocus(UWorld* World,bool bApply)
{
 auto* BP=World&&World->PersistentLevel?World->PersistentLevel->GetLevelScriptBlueprint():nullptr;
 if(!BP||!BP->GetPathName().Contains(TEXT("AbandonedSchool")))return -1;
 auto* G=FBlueprintEditorUtils::FindEventGraph(BP);if(!G)return -1;
 TArray<UK2Node_CallFunction*> Targets;
 for(UEdGraphNode* Node:G->Nodes)if(auto* C=Cast<UK2Node_CallFunction>(Node))
 {
  const bool Match=(C->GetFName()==TEXT("K2Node_CallFunction_7")&&C->FunctionReference.GetMemberName()==TEXT("SetInputMode_UIOnlyEx"))||(C->GetFName()==TEXT("K2Node_CallFunction_12")&&C->FunctionReference.GetMemberName()==TEXT("SetKeyboardFocus"));
  if(Match&&C->GetExecPin()&&!C->GetExecPin()->LinkedTo.IsEmpty())Targets.Add(C);
 }
 if(!bApply)return Targets.Num();
 BP->Modify();G->Modify();
 for(auto* C:Targets)
 {
  auto Inputs=C->GetExecPin()->LinkedTo;auto Outputs=C->GetThenPin()->LinkedTo;
  C->Modify();C->GetExecPin()->BreakAllPinLinks();C->GetThenPin()->BreakAllPinLinks();
  for(auto* In:Inputs)for(auto* Out:Outputs)if(!G->GetSchema()->TryCreateConnection(In,Out))return -1;
  C->NodeComment=TEXT("S0: focus owned by TutorialPromptWidget; deferred until opening ends");
 }
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error)return -1;BP->MarkPackageDirty();return Targets.Num();
}
