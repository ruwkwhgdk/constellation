#include "SceneDirectorLibrary.h"
#include "Engine/GameViewportClient.h"
#include "UnrealClient.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
bool USceneDirectorLibrary::ResolveQTEForReview(ASceneDirectorPlayer* Player,bool bSuccess)
{
 if(!IsValid(Player)||!Player->GetWorld()||Player->GetWorld()->WorldType!=EWorldType::PIE||!Player->IsWaitingForQTE())return false;
 Player->ResolveQTE(Player->QTEPrompt,bSuccess?EDirectorQTEOutcome::Success:EDirectorQTEOutcome::Failure);
 // Review injection bypasses widget input and its retirement animation.
 Player->CleanupQTE(true);
 return true;
}
bool USceneDirectorLibrary::CaptureGameViewportFrame(UWorld* World,const FString& Filename)
{
 // Global Shot requests can be consumed by an editor viewport during a redraw.
 // Read only this PIE world's game viewport; never substitute the editor view.
 auto* Client=World&&World->IsGameWorld()?World->GetGameViewport():nullptr;
 FViewport* View=Client?Client->Viewport:nullptr;if(!View)return false;
 const FIntPoint Size=View->GetSizeXY();TArray<FColor> Pixels;
 if(Size.X<=0||Size.Y<=0||!View->ReadPixels(Pixels)||Pixels.Num()!=Size.X*Size.Y)return false;
 for(FColor& Pixel:Pixels)Pixel.A=255;
 TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);
 return !PNG.IsEmpty()&&FFileHelper::SaveArrayToFile(PNG,*Filename);
}
FDirectorStep USceneDirectorLibrary::MakeDirectorStep(EDirectorNodeType Type)
{FDirectorStep Step;Step.Type=Type;return Step;}

#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
int32 USceneDirectorLibrary::RemoveSchoolOpeningLegacyPresentation(UWorld* World,bool bApply)
{
 auto* BP=World&&World->PersistentLevel?World->PersistentLevel->GetLevelScriptBlueprint():nullptr;
 if(!BP||!BP->GetPathName().Contains(TEXT("AbandonedSchool")))return -1;
 auto* G=FBlueprintEditorUtils::FindEventGraph(BP);if(!G)return -1;
 TArray<UK2Node_CallFunction*> Targets;
 for(UEdGraphNode* Node:G->Nodes)if(auto* C=Cast<UK2Node_CallFunction>(Node))
 {
  const FName Name=C->GetFName(),Function=C->FunctionReference.GetMemberName();
  const bool Match=((Name==TEXT("K2Node_CallFunction_6")||Name==TEXT("K2Node_CallFunction_5"))&&Function==TEXT("Sequence Play Fade"))||(Name==TEXT("K2Node_CallFunction_24")&&Function==TEXT("Show Region Title"));
  if(Match&&C->GetExecPin()&&!C->GetExecPin()->LinkedTo.IsEmpty())Targets.Add(C);
 }
 if(!bApply||Targets.IsEmpty())return Targets.Num();
 BP->Modify();G->Modify();
 for(auto* C:Targets)
 {
  auto Inputs=C->GetExecPin()->LinkedTo;auto Outputs=C->GetThenPin()->LinkedTo;
  C->Modify();C->GetExecPin()->BreakAllPinLinks();C->GetThenPin()->BreakAllPinLinks();
  for(auto* In:Inputs)for(auto* Out:Outputs)if(!G->GetSchema()->TryCreateConnection(In,Out))return -1;
  C->NodeComment=TEXT("S0: continuous gameplay handoff; title owned by SchoolOpeningSceneActor");
 }
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error)return -1;BP->MarkPackageDirty();return Targets.Num();
}
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
