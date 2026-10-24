#include "CarryEditorLibrary.h"
#include "InteractionAvailabilityComponent.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Message.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "Kismet2/BlueprintEditorUtils.h"

FString UCarryEditorLibrary::InstallInteractionAvailabilityGate(UBlueprint* Blueprint)
{
    if(!Blueprint || Blueprint->GetPathName()!=TEXT("/Game/Constellation/Gameplay/Interaction/Components/Ac_Interact.Ac_Interact"))
        return TEXT("ERROR: unexpected blueprint");
    TArray<UEdGraph*> Graphs; Blueprint->GetAllGraphs(Graphs);
    int32 Count=0;
    for(UEdGraph* Graph:Graphs)
    {
        const auto Nodes=Graph->Nodes;
        for(UEdGraphNode* Node:Nodes)
        {
            auto* Message=Cast<UK2Node_Message>(Node);
            if(!Message || Message->FunctionReference.GetMemberName()!=TEXT("Interact")) continue;
            ++Count;
            auto* Exec=Message->GetExecPin(); auto* Target=Message->FindPin(UEdGraphSchema_K2::PN_Self);
            if(!Exec || Exec->LinkedTo.Num()!=1 || !Target || Target->LinkedTo.Num()!=1)
                return TEXT("ERROR: unexpected interaction wiring");
            if(Exec->LinkedTo[0]->GetOwningNode()->NodeComment==TEXT("Interaction availability guard")) continue;
            FGraphNodeCreator<UK2Node_CallFunction> CallCreator(*Graph);
            auto* Check=CallCreator.CreateNode();
            Check->SetFromFunction(UInteractionAvailabilityComponent::StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UInteractionAvailabilityComponent,CanActorInteract)));
            Check->NodePosX=Message->NodePosX-500; Check->NodePosY=Message->NodePosY+180; CallCreator.Finalize();
            FGraphNodeCreator<UK2Node_IfThenElse> GateCreator(*Graph);
            auto* Gate=GateCreator.CreateNode();
            Gate->NodePosX=Message->NodePosX-260; Gate->NodePosY=Message->NodePosY;
            Gate->NodeComment=TEXT("Interaction availability guard"); GateCreator.Finalize();
            auto* Schema=Graph->GetSchema();
            if(!Schema->TryCreateConnection(Target->LinkedTo[0],Check->FindPinChecked(TEXT("Target")))
                || !Schema->TryCreateConnection(Check->GetReturnValuePin(),Gate->GetConditionPin()))
                return TEXT("ERROR: availability data wiring");
            auto* Previous=Exec->LinkedTo[0];
            Exec->BreakLinkTo(Previous);
            Previous->MakeLinkTo(Gate->GetExecPin());
            Gate->GetThenPin()->MakeLinkTo(Exec);
            FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
        }
    }
    return Count==1 ? TEXT("OK: shared input guarded") : TEXT("ERROR: unexpected interaction call count");
}
