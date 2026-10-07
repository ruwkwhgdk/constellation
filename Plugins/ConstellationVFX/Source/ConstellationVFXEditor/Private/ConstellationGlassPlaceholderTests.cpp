#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationVFXEditorLibrary.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_CallFunction.h"

// Restoring the default explosion or linking its return value must fail the saved-asset regression.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGlassPlaceholderSavedTest,"Constellation.VFX.GlassPlaceholderSavedGraph",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FGlassPlaceholderSavedTest::RunTest(const FString&)
{
    auto* Blueprint=LoadObject<UBlueprint>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_Glass.BP_Glass"));
    if(!TestNotNull(TEXT("Authored glass blueprint"),Blueprint)) return false;
    TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
    UK2Node_CallFunction* Audited=nullptr;
    for(auto* Graph:Graphs)for(UEdGraphNode* Node:Graph->Nodes)
        if(Node && Node->NodeGuid==FGuid(0xA2BC80AC,0x441F6932,0x750B6E96,0xA6CA4A47)) Audited=Cast<UK2Node_CallFunction>(Node);
    if(!TestNotNull(TEXT("Original audited graph node remains"),Audited)) return false;
    auto* Template=Audited->FindPin(TEXT("SystemTemplate"));
    auto* Result=Audited->FindPin(TEXT("ReturnValue"));
    auto* In=Audited->FindPin(TEXT("execute"));auto* Out=Audited->FindPin(TEXT("then"));
    if(!Template||!Result||!In||!Out)return false;
    TestTrue(TEXT("Saved placeholder has null template"),Template->DefaultObject==nullptr);
    TestEqual(TEXT("Return value stays unused"),Result->LinkedTo.Num(),0);
    TestEqual(TEXT("Physics execution still enters node"),In->LinkedTo.Num(),1);
    TestEqual(TEXT("Sound execution still leaves node"),Out->LinkedTo.Num(),1);
    FString Report;
    TestTrue(TEXT("Repeated dry-run recognizes neutralized graph"),UConstellationVFXEditorLibrary::NeutralizeLegacyGlassPlaceholder(Blueprint,false,Report));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGlassPlaceholderScopeTest,"Constellation.VFX.GlassPlaceholderScopeGuard",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FGlassPlaceholderScopeTest::RunTest(const FString&)
{
    FString Report;
    auto* Other=NewObject<UBlueprint>();
    TestFalse(TEXT("Unrelated blueprint cannot be modified"),UConstellationVFXEditorLibrary::NeutralizeLegacyGlassPlaceholder(Other,true,Report));
    TestFalse(TEXT("Null blueprint rejected"),UConstellationVFXEditorLibrary::NeutralizeLegacyGlassPlaceholder(nullptr,true,Report));
    return true;
}
#endif
