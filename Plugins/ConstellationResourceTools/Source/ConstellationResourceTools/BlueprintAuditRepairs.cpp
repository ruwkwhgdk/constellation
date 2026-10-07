#include "ResourceRecoveryLibrary.h"
#include "BehaviorTree/Tasks/BTTask_BlueprintBase.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CallArrayFunction.h"
#include "K2Node_GetArrayItem.h"
#include "Kismet/KismetArrayLibrary.h"
#include "K2Node_DynamicCast.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Literal.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"

FString UResourceRecoveryLibrary::RepairObsoleteShowcaseCall(UWorld* World)
{
    if (!World || World->GetPackage()->GetName() != TEXT("/Game/LuosCaves/Maps/LCaves_Will_Chambers_Contribution_Showcase"))
        return TEXT("ERROR map outside reviewed scope");
    UBlueprint* Blueprint = World->PersistentLevel->GetLevelScriptBlueprint(true);
    if (!Blueprint) return TEXT("ERROR missing level blueprint");
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    int32 Changes = 0;
    for (UEdGraph* Graph : Graphs)
    {
        const auto Nodes = Graph->Nodes;
        for (UEdGraphNode* Node : Nodes)
        {
            UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node);
            if (!Call || Call->FunctionReference.GetMemberName() != TEXT("Play")) continue;
            UClass* Owner = Call->FunctionReference.GetMemberParentClass();
            if (!Owner || Owner->GetPathName() != TEXT("/Script/LevelSequenceEditor.LevelSequenceEditorBlueprintLibrary")) continue;
            UEdGraphPin* Target = Call->FindPin(UEdGraphSchema_K2::PN_Self);
            UEdGraphPin* Then = Call->FindPin(UEdGraphSchema_K2::PN_Then);
            if (!Target || Target->LinkedTo.Num() != 1 || !Then || !Then->LinkedTo.IsEmpty())
                return TEXT("ERROR unexpected showcase call wiring");
            UK2Node_Literal* Literal = Cast<UK2Node_Literal>(Target->LinkedTo[0]->GetOwningNode());
            if (!Literal || Literal->GetObjectRef() != nullptr || Target->LinkedTo[0]->LinkedTo.Num() != 1)
                return TEXT("ERROR showcase actor reference no longer missing");
            FBlueprintEditorUtils::RemoveNode(Blueprint, Call, true);
            FBlueprintEditorUtils::RemoveNode(Blueprint, Literal, true);
            Changes += 2;
        }
    }
    if (Changes) FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
    FCompilerResultsLog Log;
    FKismetEditorUtilities::CompileBlueprint(Blueprint, EBlueprintCompileOptions::None, &Log);
    return FString::Printf(TEXT("APPLY changes=%d errors=%d warnings=%d"), Changes, Log.NumErrors, Log.NumWarnings);
}

FString UResourceRecoveryLibrary::RepairKnownBlueprintLogic(UBlueprint* Source, bool bApply)
{
    if (!Source) return TEXT("ERROR null blueprint");
    const bool bQuestTrigger = Source->GetName() == TEXT("BP_QuestProgressTrigger");
    const bool bTask = Source->GetName() == TEXT("BTT_Attack") || Source->GetName() == TEXT("BTT_GetNextPatrolPoint");
    const bool bPatrol = Source->GetName() == TEXT("BTT_GetNextPatrolPoint");
    const bool bDistanceService = Source->GetName() == TEXT("BTS_CheckDistance");
    if (!bQuestTrigger && !bTask && !bDistanceService) return TEXT("ERROR asset not in reviewed repair scope");
    UBlueprint* Blueprint = bApply ? Source : DuplicateObject<UBlueprint>(Source, GetTransientPackage(),
        MakeUniqueObjectName(GetTransientPackage(), Source->GetClass(), TEXT("AuditPreview")));
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    int32 Changes = 0;
    for (UEdGraph* Graph : Graphs)
    {
        if (!Graph || Graph->GetFName() != TEXT("EventGraph")) continue;
        const UEdGraphSchema* Schema = Graph->GetSchema();
        const auto Nodes = Graph->Nodes; // Adding nodes must not invalidate iteration.
        for (UEdGraphNode* Node : Nodes)
        {
            if (bQuestTrigger)
            {
                UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node);
                if (!Call || (Call->FunctionReference.GetMemberName() != TEXT("AddQuestProgressFor") &&
                              Call->FunctionReference.GetMemberName() != TEXT("AddQuestInnerProgressFor"))) continue;
                UEdGraphPin* Then = Call->FindPin(UEdGraphSchema_K2::PN_Then);
                UEdGraphPin* Result = Call->FindPin(UEdGraphSchema_K2::PN_ReturnValue);
                if (!Then || !Result || Then->LinkedTo.Num() != 1) return TEXT("ERROR unexpected quest call wiring");
                if (Then->LinkedTo[0]->GetOwningNode()->NodeComment == TEXT("Audit: consume trigger only after progress changed")) continue;
                if (Result->LinkedTo.Num() != 0) return TEXT("ERROR quest return value already has consumers");
                UEdGraphPin* Next = Then->LinkedTo[0];
                FGraphNodeCreator<UK2Node_IfThenElse> Creator(*Graph);
                UK2Node_IfThenElse* Gate = Creator.CreateNode();
                Gate->NodePosX = Call->NodePosX + 300;
                Gate->NodePosY = Call->NodePosY;
                Gate->NodeComment = TEXT("Audit: consume trigger only after progress changed");
                Creator.Finalize();
                Then->BreakLinkTo(Next);
                Then->MakeLinkTo(Gate->GetExecPin());
                Result->MakeLinkTo(Gate->GetConditionPin());
                Gate->GetThenPin()->MakeLinkTo(Next);
                ++Changes;
            }
            else if (bTask && Cast<UK2Node_DynamicCast>(Node))
            {
                UK2Node_DynamicCast* CastNode = CastChecked<UK2Node_DynamicCast>(Node);
                UEdGraphPin* Failed = CastNode->FindPin(TEXT("CastFailed"));
                if (!Failed || !Failed->LinkedTo.IsEmpty()) continue;
                if (!Blueprint->ParentClass || !Blueprint->ParentClass->IsChildOf(UBTTask_BlueprintBase::StaticClass()))
                    return TEXT("ERROR task parent mismatch");
                FGraphNodeCreator<UK2Node_CallFunction> Creator(*Graph);
                UK2Node_CallFunction* Finish = Creator.CreateNode();
                Finish->SetFromFunction(UBTTask_BlueprintBase::StaticClass()->FindFunctionByName(TEXT("FinishExecute")));
                Finish->NodePosX = CastNode->NodePosX + 300;
                Finish->NodePosY = CastNode->NodePosY + 200;
                Finish->NodeComment = TEXT("Audit: invalid pawn/controller fails task instead of hanging");
                Creator.Finalize();
                Finish->FindPinChecked(TEXT("bSuccess"))->DefaultValue = TEXT("false");
                Failed->MakeLinkTo(Finish->FindPinChecked(UEdGraphSchema_K2::PN_Execute));
                ++Changes;
            }
            else if (bDistanceService && Cast<UK2Node_DynamicCast>(Node))
            {
                UK2Node_DynamicCast* CastNode = CastChecked<UK2Node_DynamicCast>(Node);
                UEdGraphPin* Failed = CastNode->FindPin(TEXT("CastFailed"));
                if (!Failed || !Failed->LinkedTo.IsEmpty()) continue;
                UEdGraphPin* Success = CastNode->FindPin(UEdGraphSchema_K2::PN_Then);
                if (!Success || Success->LinkedTo.Num() != 1) return TEXT("ERROR unexpected distance service wiring");
                UK2Node_CallFunction* Setter = Cast<UK2Node_CallFunction>(Success->LinkedTo[0]->GetOwningNode());
                if (!Setter || Setter->FunctionReference.GetMemberName() != TEXT("SetBlackboardValueAsBool"))
                    return TEXT("ERROR unexpected distance service setter");
                UEdGraphPin* Key = Setter->FindPin(TEXT("Key"));
                if (!Key || Key->LinkedTo.Num() != 1) return TEXT("ERROR missing attack range key");
                FGraphNodeCreator<UK2Node_CallFunction> Creator(*Graph);
                UK2Node_CallFunction* Clear = Creator.CreateNode();
                Clear->SetFromFunction(Setter->GetTargetFunction());
                Clear->NodePosX = CastNode->NodePosX + 300;
                Clear->NodePosY = CastNode->NodePosY + 250;
                Clear->NodeComment = TEXT("Audit: clear attack range when target is absent");
                Creator.Finalize();
                Clear->FindPinChecked(TEXT("Value"))->DefaultValue = TEXT("false");
                Failed->MakeLinkTo(Clear->FindPinChecked(UEdGraphSchema_K2::PN_Execute));
                Key->LinkedTo[0]->MakeLinkTo(Clear->FindPinChecked(TEXT("Key")));
                ++Changes;
            }
            if (bPatrol)
            {
                UK2Node_CallFunction* Setter = Cast<UK2Node_CallFunction>(Node);
                if (!Setter || Setter->FunctionReference.GetMemberName() != TEXT("SetBlackboardValueAsVector")) continue;
                UEdGraphPin* Execute = Setter->FindPin(UEdGraphSchema_K2::PN_Execute);
                UEdGraphPin* Value = Setter->FindPin(TEXT("Value"));
                if (!Execute || Execute->LinkedTo.Num() != 1 || !Value || Value->LinkedTo.Num() != 1)
                    return TEXT("ERROR unexpected patrol setter wiring");
                if (Execute->LinkedTo[0]->GetOwningNode()->NodeComment == TEXT("Audit: validate patrol array before reading")) continue;
                UK2Node_GetArrayItem* Get = Cast<UK2Node_GetArrayItem>(Value->LinkedTo[0]->GetOwningNode());
                if (!Get) return TEXT("ERROR patrol value is not an array item");
                UEdGraphPin* Array = Get->GetTargetArrayPin();
                UEdGraphPin* Index = Get->GetIndexPin();
                if (Array->LinkedTo.Num() != 1 || Index->LinkedTo.Num() != 1)
                    return TEXT("ERROR unexpected patrol array/index wiring");
                FGraphNodeCreator<UK2Node_CallArrayFunction> CheckCreator(*Graph);
                UK2Node_CallArrayFunction* Check = CheckCreator.CreateNode();
                Check->SetFromFunction(UKismetArrayLibrary::StaticClass()->FindFunctionByName(TEXT("Array_IsValidIndex")));
                Check->NodePosX = Setter->NodePosX - 300;
                Check->NodePosY = Setter->NodePosY + 300;
                CheckCreator.Finalize();
                if (!Schema->TryCreateConnection(Array->LinkedTo[0], Check->FindPinChecked(TEXT("TargetArray"))) ||
                    !Schema->TryCreateConnection(Index->LinkedTo[0], Check->FindPinChecked(TEXT("IndexToTest"))))
                    return TEXT("ERROR patrol validation connection failed");
                FGraphNodeCreator<UK2Node_IfThenElse> GateCreator(*Graph);
                UK2Node_IfThenElse* Gate = GateCreator.CreateNode();
                Gate->NodePosX = Setter->NodePosX - 300;
                Gate->NodePosY = Setter->NodePosY;
                Gate->NodeComment = TEXT("Audit: validate patrol array before reading");
                GateCreator.Finalize();
                UEdGraphPin* Before = Execute->LinkedTo[0];
                Before->BreakLinkTo(Execute);
                Before->MakeLinkTo(Gate->GetExecPin());
                Check->FindPinChecked(UEdGraphSchema_K2::PN_ReturnValue)->MakeLinkTo(Gate->GetConditionPin());
                Gate->GetThenPin()->MakeLinkTo(Execute);
                FGraphNodeCreator<UK2Node_CallFunction> FinishCreator(*Graph);
                UK2Node_CallFunction* Finish = FinishCreator.CreateNode();
                Finish->SetFromFunction(UBTTask_BlueprintBase::StaticClass()->FindFunctionByName(TEXT("FinishExecute")));
                Finish->NodePosX = Setter->NodePosX;
                Finish->NodePosY = Setter->NodePosY + 500;
                FinishCreator.Finalize();
                Finish->FindPinChecked(TEXT("bSuccess"))->DefaultValue = TEXT("false");
                Gate->GetElsePin()->MakeLinkTo(Finish->FindPinChecked(UEdGraphSchema_K2::PN_Execute));
                ++Changes;
            }
        }
    }
    if (bPatrol)
    {
        // A stale index must recover on the next attempt even when the route shrinks.
        for (UEdGraph* Graph : Graphs)
        {
            if (!Graph) continue;
            const auto Nodes = Graph->Nodes;
            for (UEdGraphNode* Node : Nodes)
            {
                UK2Node_IfThenElse* Gate = Cast<UK2Node_IfThenElse>(Node);
                if (!Gate || Gate->NodeComment != TEXT("Audit: validate patrol array before reading")) continue;
                UEdGraphPin* Failed = Gate->GetElsePin();
                if (Failed->LinkedTo.Num() != 1) return TEXT("ERROR unexpected patrol failure wiring");
                UEdGraphPin* Next = Failed->LinkedTo[0];
                if (Next->GetOwningNode()->NodeComment == TEXT("Audit: reset stale patrol index for next attempt")) continue;
                UK2Node_CallFunction* ExistingReset = nullptr;
                for (UEdGraphNode* Candidate : Nodes)
                {
                    UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Candidate);
                    if (Call && Call->FunctionReference.GetMemberName() == TEXT("SetBlackboardValueAsInt") &&
                        Call->FindPinChecked(TEXT("Value"))->LinkedTo.IsEmpty() &&
                        Call->FindPinChecked(TEXT("Value"))->DefaultValue == TEXT("0"))
                    {
                        ExistingReset = Call;
                        break;
                    }
                }
                if (!ExistingReset || ExistingReset->FindPinChecked(TEXT("Key"))->LinkedTo.Num() != 1)
                    return TEXT("ERROR missing original patrol index reset");
                FGraphNodeCreator<UK2Node_CallFunction> Creator(*Graph);
                UK2Node_CallFunction* Reset = Creator.CreateNode();
                Reset->SetFromFunction(ExistingReset->GetTargetFunction());
                Reset->NodePosX = Gate->NodePosX;
                Reset->NodePosY = Gate->NodePosY + 500;
                Reset->NodeComment = TEXT("Audit: reset stale patrol index for next attempt");
                Creator.Finalize();
                Reset->FindPinChecked(TEXT("Value"))->DefaultValue = TEXT("0");
                ExistingReset->FindPinChecked(TEXT("Key"))->LinkedTo[0]->MakeLinkTo(Reset->FindPinChecked(TEXT("Key")));
                Failed->BreakLinkTo(Next);
                Failed->MakeLinkTo(Reset->FindPinChecked(UEdGraphSchema_K2::PN_Execute));
                Reset->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(Next);
                ++Changes;
            }
        }
    }
    if (Changes) FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
    FCompilerResultsLog Log;
    FKismetEditorUtilities::CompileBlueprint(Blueprint, EBlueprintCompileOptions::None, &Log);
    return FString::Printf(TEXT("%s changes=%d errors=%d warnings=%d"), bApply ? TEXT("APPLY") : TEXT("PREVIEW"), Changes, Log.NumErrors, Log.NumWarnings);
}
