#include "ConstellationVFXEditorLibrary.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "NiagaraFunctionLibrary.h"

namespace
{
    constexpr TCHAR BlueprintPath[]=TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Glass.BP_Glass");
    constexpr TCHAR ExplosionPath[]=TEXT("/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion.SimpleExplosion");
    const FGuid AuditedGuid(0xA2BC80AC,0x441F6932,0x750B6E96,0xA6CA4A47);
    UK2Node_CallFunction* FindAuditedNode(UBlueprint* Blueprint)
    {
        TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
        for(auto* Graph:Graphs)for(UEdGraphNode* Node:Graph->Nodes)
            if(Node && Node->NodeGuid==AuditedGuid) return Cast<UK2Node_CallFunction>(Node);
        return nullptr;
    }
    FString Links(UK2Node_CallFunction* Node)
    {
        TArray<FString> Rows;
        for(auto* Pin:Node->Pins)
        {
            TArray<FString> Connections;
            for(auto* Other:Pin->LinkedTo)
                Connections.Add(Other->GetOwningNode()->NodeGuid.ToString()+TEXT(":")+Other->PinName.ToString());
            Connections.Sort();
            Rows.Add(Pin->PinName.ToString()+TEXT(":")+FString::FromInt(int32(Pin->Direction))+TEXT("=")+FString::Join(Connections,TEXT(",")));
        }
        Rows.Sort();return FString::Join(Rows,TEXT(";"));
    }
}
bool UConstellationVFXEditorLibrary::NeutralizeLegacyGlassPlaceholder(UBlueprint* Blueprint,bool bApply,FString& Report)
{
    if(!Blueprint || Blueprint->GetPathName()!=BlueprintPath) {Report=TEXT("Rejected: only audited BP_Glass is permitted");return false;}
    auto* Node=FindAuditedNode(Blueprint);
    const UFunction* Function=Node?Node->GetTargetFunction():nullptr;
    if(!Function || Function->GetFName()!=TEXT("SpawnSystemAtLocation") || Function->GetOuterUClass()!=UNiagaraFunctionLibrary::StaticClass())
        {Report=TEXT("Rejected: audited Niagara call not found");return false;}
    auto* Template=Node->FindPin(TEXT("SystemTemplate"));auto* Result=Node->FindPin(TEXT("ReturnValue"));
    auto* In=Node->FindPin(TEXT("execute"));auto* Out=Node->FindPin(TEXT("then"));
    if(!Template||!Result||!In||!Out || !Template->LinkedTo.IsEmpty() || !Result->LinkedTo.IsEmpty() || In->LinkedTo.Num()!=1 || Out->LinkedTo.Num()!=1)
        {Report=TEXT("Rejected: template/return/execution wiring differs from audited unused placeholder");return false;}
    if(!Template->DefaultObject && Template->DefaultValue.IsEmpty()) {Report=TEXT("Already neutralized; execution, physics and sound remain connected");return true;}
    if(!Template->DefaultObject || Template->DefaultObject->GetPathName()!=ExplosionPath || !Template->DefaultValue.IsEmpty())
        {Report=TEXT("Rejected: authored system differs from exact SimpleExplosion placeholder");return false;}
    if(!bApply) {Report=TEXT("Ready: exact SimpleExplosion placeholder; unused return; exec input/output connected");return true;}
    const FString BeforeLinks=Links(Node);
    UObject* Previous=Template->DefaultObject;
    Blueprint->Modify();Node->Modify();
    Template->DefaultObject=nullptr;
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
    auto* After=FindAuditedNode(Blueprint);
    if(Blueprint->Status==BS_Error || !After || Links(After)!=BeforeLinks || !After->FindPin(TEXT("SystemTemplate")) || After->FindPin(TEXT("SystemTemplate"))->DefaultObject)
    {
        if(After && After->FindPin(TEXT("SystemTemplate"))) After->FindPin(TEXT("SystemTemplate"))->DefaultObject=Previous;
        FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);FKismetEditorUtilities::CompileBlueprint(Blueprint);
        Report=TEXT("Rejected and restored: compilation or graph-link verification failed");return false;
    }
    Report=TEXT("Neutralized exact SimpleExplosion template; compiled; all original pin links preserved; save explicitly");return true;
}
