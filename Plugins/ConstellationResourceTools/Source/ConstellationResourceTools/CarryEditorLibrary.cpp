#include "CarryEditorLibrary.h"
#include "CarryComponent.h"
#include "CarryInputLibrary.h"
#include "HoldableComponent.h"
#include "Animation/AnimMontage.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/Skeleton.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_Event.h"
#include "K2Node_EnhancedInputAction.h"
#include "InputAction.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_Slot.h"
#include "AnimGraphNode_LayeredBoneBlend.h"
#include "AnimGraphNode_SaveCachedPose.h"
#include "AnimGraphNode_UseCachedPose.h"
#include "AnimGraphNode_TwoBoneIK.h"
#include "AnimBlueprintExtension.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"

namespace
{
template<class T> T* Node(UEdGraph* Graph,FName Name,int32 X,int32 Y)
{
    T* N=NewObject<T>(Graph,Name); Graph->AddNode(N,false,false); N->CreateNewGuid(); N->NodePosX=X; N->NodePosY=Y;
    N->PostPlacedNewNode();
    return N;
}
FString Compile(UBlueprint* BP,int32 Count)
{
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); FCompilerResultsLog Log;
    FKismetEditorUtilities::CompileBlueprint(BP,EBlueprintCompileOptions::None,&Log);
    return FString::Printf(TEXT("changes=%d errors=%d warnings=%d"),Count,Log.NumErrors,Log.NumWarnings);
}
}
FString UCarryEditorLibrary::InspectCarrySkeleton(USkeleton* Skeleton)
{
    if(!Skeleton) return TEXT("NO_SKELETON"); FString Text;
    const FReferenceSkeleton& Ref=Skeleton->GetReferenceSkeleton();
    for(int32 I=0;I<Ref.GetNum();++I) Text+=FString::Printf(TEXT("%s parent=%d position=%s\n"),*Ref.GetBoneName(I).ToString(),Ref.GetParentIndex(I),*Ref.GetRefBonePose()[I].GetLocation().ToString());
    return Text;
}
FString UCarryEditorLibrary::InstallCarryInput(UBlueprint* BP)
{
    if(!BP||!BP->SimpleConstructionScript) return TEXT("ERROR missing character Blueprint");
    BP->Modify(); int32 Count=0; bool bHasCarry=false;
    for(USCS_Node* N:BP->SimpleConstructionScript->GetAllNodes()) if(N->ComponentClass->IsChildOf(UCarryComponent::StaticClass())) bHasCarry=true;
    if(!bHasCarry) { BP->SimpleConstructionScript->AddNode(BP->SimpleConstructionScript->CreateNode(UCarryComponent::StaticClass(),TEXT("CarryComponent"))); ++Count; }
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for(UEdGraph* G:Graphs)
    {
        const UEdGraphSchema_K2* Schema=Cast<UEdGraphSchema_K2>(G->GetSchema()); if(!Schema) continue;
        auto Original=G->Nodes;
        for(UEdGraphNode* OriginalNode:Original)
        {
            UK2Node_EnhancedInputAction* Input=Cast<UK2Node_EnhancedInputAction>(OriginalNode);
            UK2Node_CustomEvent* Event=Cast<UK2Node_CustomEvent>(OriginalNode);
            UK2Node_Event* EngineEvent=Cast<UK2Node_Event>(OriginalNode);
            UK2Node_FunctionEntry* Entry=Cast<UK2Node_FunctionEntry>(OriginalNode);
            FString Action;
            if(Input&&Input->InputAction) Action=Input->InputAction->GetName();
            else if(Event)
            {
                const FString EventName=Event->CustomFunctionName.ToString();
                if(EventName==TEXT("Do Attack")||EventName==TEXT("Do Dodge")||EventName==TEXT("Do Jump")||EventName==TEXT("Do Push")) Action=TEXT("BlockAction");
            }
            if((EngineEvent&&EngineEvent->EventReference.GetMemberName()==TEXT("TakeDamage"))
                ||(Entry&&(Entry->FunctionReference.GetMemberName()==TEXT("Emit Damaged Effect")||Entry->FunctionReference.GetMemberName()==TEXT("Reset All States")))) Action=TEXT("AbortCarry");
            if(Action.IsEmpty()||Action==TEXT("IA_Look")||Action==TEXT("IA_Debug")) continue;
            for(UEdGraphPin* Out:OriginalNode->Pins)
            {
                if(Out->Direction!=EGPD_Output||Out->PinType.PinCategory!=UEdGraphSchema_K2::PC_Exec) continue;
                const bool bAttackRelease=Action==TEXT("IA_Attack")&&(Out->PinName==TEXT("Completed")||Out->PinName==TEXT("Canceled"));
                if(Out->LinkedTo.IsEmpty()&&!bAttackRelease) continue;
                const FName Marker=FName(*(TEXT("CarryRoute_")+OriginalNode->NodeGuid.ToString(EGuidFormats::Digits)+TEXT("_")+Out->PinName.ToString()));
                if(FindObject<UEdGraphNode>(G,*Marker.ToString())) continue;
                const TArray<UEdGraphPin*> Previous=Out->LinkedTo;
                UK2Node_CallFunction* Call=Node<UK2Node_CallFunction>(G,Marker,OriginalNode->NodePosX+260,OriginalNode->NodePosY+Count*60);
                const bool bAbort=Action==TEXT("AbortCarry");
                Call->SetFromFunction(UCarryInputLibrary::StaticClass()->FindFunctionByName(bAbort?GET_FUNCTION_NAME_CHECKED(UCarryInputLibrary,AbortActorCarry):GET_FUNCTION_NAME_CHECKED(UCarryInputLibrary,RouteCarryInput))); Call->AllocateDefaultPins();
                if(!bAbort) { Call->FindPinChecked(TEXT("Action"))->DefaultValue=Action; Call->FindPinChecked(TEXT("Phase"))->DefaultValue=Out->PinName.ToString(); }
                UK2Node_Self* Self=Node<UK2Node_Self>(G,NAME_None,Call->NodePosX-100,Call->NodePosY+100); Self->AllocateDefaultPins();
                Out->BreakAllPinLinks();
                bool Good=Schema->TryCreateConnection(Out,Call->GetExecPin())&&Schema->TryCreateConnection(Self->FindPinChecked(UEdGraphSchema_K2::PN_Self),Call->FindPinChecked(TEXT("Actor")));
                UEdGraphPin* Continue=Call->GetThenPin();
                if(!bAbort)
                {
                    UK2Node_IfThenElse* Branch=Node<UK2Node_IfThenElse>(G,NAME_None,Call->NodePosX+300,Call->NodePosY); Branch->AllocateDefaultPins();
                    Good=Schema->TryCreateConnection(Call->GetThenPin(),Branch->GetExecPin())&&Schema->TryCreateConnection(Call->GetReturnValuePin(),Branch->GetConditionPin())&&Good;
                    Continue=Branch->GetElsePin();
                }
                for(UEdGraphPin* Old:Previous) Good=Schema->TryCreateConnection(Continue,Old)&&Good;
                if(!Good) return TEXT("ERROR carry route connection failed; do not save"); ++Count;
            }
        }
    }
    return Compile(BP,Count);
}
FString UCarryEditorLibrary::InstallCarryOverlay(UAnimBlueprint* BP)
{
    if(!BP) return TEXT("ERROR missing ABP");
    // IK targets read the held actor. Evaluate this player ABP on the game thread.
    BP->bUseMultiThreadedAnimationUpdate=false;
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for(UEdGraph* G:Graphs) if(G->GetFName()==TEXT("AnimGraph"))
    {
        if(FindObject<UEdGraphNode>(G,TEXT("CarryUpperBodySlot"))) return Compile(BP,0);
        UAnimGraphNode_Root* Root=nullptr; for(UEdGraphNode* N:G->Nodes) if(auto* R=Cast<UAnimGraphNode_Root>(N)) Root=R;
        if(!Root||Root->FindPinChecked(TEXT("Result"))->LinkedTo.Num()!=1) return TEXT("ERROR root pose layout unexpected");
        BP->Modify(); const UEdGraphSchema* Schema=G->GetSchema(); UEdGraphPin* Source=Root->FindPinChecked(TEXT("Result"))->LinkedTo[0];
        auto* Slot=Node<UAnimGraphNode_Slot>(G,TEXT("CarryUpperBodySlot"),Root->NodePosX-500,Root->NodePosY+180);
        Slot->Node.SlotName=TEXT("CarryUpperBody"); Slot->AllocateDefaultPins();
        auto* Blend=Node<UAnimGraphNode_LayeredBoneBlend>(G,TEXT("CarryUpperBodyBlend"),Root->NodePosX-220,Root->NodePosY);
        Blend->Node.BlendPoses.SetNum(1); Blend->Node.BlendWeights.SetNum(1); Blend->Node.BlendWeights[0]=1.f; Blend->Node.LayerSetup.SetNum(1);
        FBranchFilter Filter; Filter.BoneName=BP->TargetSkeleton->GetReferenceSkeleton().FindBoneIndex(TEXT("spine_01"))>=0?TEXT("spine_01"):TEXT("Spine"); Filter.BlendDepth=2; Blend->Node.LayerSetup[0].BranchFilters.Add(Filter);
        Blend->Node.bMeshSpaceRotationBlend=true; Blend->AllocateDefaultPins();
        Root->FindPinChecked(TEXT("Result"))->BreakAllPinLinks();
        auto* Cache=Node<UAnimGraphNode_SaveCachedPose>(G,TEXT("CarryBaseCache"),Root->NodePosX-1000,Root->NodePosY);
        Cache->CacheName=TEXT("CarryBase"); Cache->AllocateDefaultPins();
        auto* Base=Node<UAnimGraphNode_UseCachedPose>(G,NAME_None,Root->NodePosX-500,Root->NodePosY);
        Base->SaveCachedPoseNode=Cache; Base->AllocateDefaultPins();
        auto* SlotBase=Node<UAnimGraphNode_UseCachedPose>(G,NAME_None,Root->NodePosX-750,Root->NodePosY+180);
        SlotBase->SaveCachedPoseNode=Cache; SlotBase->AllocateDefaultPins();
        const bool Good=Schema->TryCreateConnection(Source,Cache->FindPinChecked(TEXT("Pose")))&&Schema->TryCreateConnection(SlotBase->FindPinChecked(TEXT("Pose")),Slot->FindPinChecked(TEXT("Source")))&&Schema->TryCreateConnection(Base->FindPinChecked(TEXT("Pose")),Blend->FindPinChecked(TEXT("BasePose")))
            &&Schema->TryCreateConnection(Slot->FindPinChecked(TEXT("Pose")),Blend->FindPinChecked(TEXT("BlendPoses_0")));
        if(!Good) return TEXT("ERROR carry overlay connection failed; do not save");
        UEdGraphPin* Pose=Blend->FindPinChecked(TEXT("Pose"));
        const UEdGraphSchema_K2* K2=CastChecked<UEdGraphSchema_K2>(Schema);
        for(bool bLeft:{true,false})
        {
            auto* IK=Node<UAnimGraphNode_TwoBoneIK>(G,NAME_None,Root->NodePosX+(bLeft?100:450),Root->NodePosY);
            const bool bRefined=BP->TargetSkeleton->GetReferenceSkeleton().FindBoneIndex(TEXT("hand_l"))>=0;
            IK->Node.IKBone.BoneName=bRefined?(bLeft?TEXT("hand_l"):TEXT("hand_r")):(bLeft?TEXT("LeftHand"):TEXT("RightHand"));
            IK->Node.EffectorLocationSpace=BCS_ComponentSpace; IK->Node.JointTargetLocationSpace=BCS_ComponentSpace;
            IK->Node.bAllowStretching=false; IK->Node.bMaintainEffectorRelRot=true;
            for(FOptionalPinFromProperty& Pin:IK->ShowPinForProperties) if(Pin.PropertyName==TEXT("Alpha")) Pin.bShowPin=true;
            IK->AllocateDefaultPins();
            if(!Schema->TryCreateConnection(Pose,IK->FindPinChecked(TEXT("ComponentPose")))) return TEXT("ERROR IK pose connection");
            auto* Self=Node<UK2Node_Self>(G,NAME_None,IK->NodePosX,IK->NodePosY+500); Self->AllocateDefaultPins();
            for(const auto& Pair:TMap<FName,FName>{{TEXT("CarryGrip"),TEXT("EffectorLocation")},{TEXT("CarryElbow"),TEXT("JointTargetLocation")},{TEXT("CarryIKAlpha"),TEXT("Alpha")}})
            {
                auto* Call=Node<UK2Node_CallFunction>(G,NAME_None,IK->NodePosX-150,IK->NodePosY+200);
                Call->SetFromFunction(UCarryInputLibrary::StaticClass()->FindFunctionByName(Pair.Key)); Call->AllocateDefaultPins();
                if(UEdGraphPin* Side=Call->FindPin(TEXT("bLeft"))) Side->DefaultValue=bLeft?TEXT("true"):TEXT("false");
                if(!K2->TryCreateConnection(Self->FindPinChecked(UEdGraphSchema_K2::PN_Self),Call->FindPinChecked(TEXT("AnimInstance")))
                    ||!K2->TryCreateConnection(Call->GetReturnValuePin(),IK->FindPinChecked(Pair.Value))) return TEXT("ERROR IK value connection");
            }
            Pose=IK->FindPinChecked(TEXT("Pose"));
        }
        if(!Schema->TryCreateConnection(Pose,Root->FindPinChecked(TEXT("Result")))) return TEXT("ERROR IK result connection");
        BP->TargetSkeleton->RegisterSlotNode(TEXT("CarryUpperBody")); return Compile(BP,2);
    }
    return TEXT("ERROR no AnimGraph");
}
FString UCarryEditorLibrary::ConfigureCarryBlueprint(UBlueprint* BP,const FString& Folder,UMaterialInterface* Material)
{
    if(!BP||!BP->SimpleConstructionScript) return TEXT("ERROR no SCS");
    for(USCS_Node* Node:BP->SimpleConstructionScript->GetAllNodes()) if(UCarryComponent* Carry=Cast<UCarryComponent>(Node->ComponentTemplate))
    {
        Carry->Modify(); Carry->CarrySocket=NAME_None;
        Carry->PickupMontage=LoadObject<UAnimMontage>(nullptr,*(Folder/TEXT("AM_Carry_Pickup")));
        Carry->PlaceMontage=LoadObject<UAnimMontage>(nullptr,*(Folder/TEXT("AM_Carry_Place")));
        Carry->ThrowMontage=LoadObject<UAnimMontage>(nullptr,*(Folder/TEXT("AM_Carry_Throw")));
        Carry->HoldMontage=LoadObject<UAnimMontage>(nullptr,*(Folder/TEXT("AM_Carry_Hold")));
        Carry->AimMontage=LoadObject<UAnimMontage>(nullptr,*(Folder/TEXT("AM_Carry_Aim")));
        Carry->PreviewMaterial=Material;
        if(!Carry->PickupMontage||!Carry->PlaceMontage||!Carry->ThrowMontage||!Carry->HoldMontage||!Carry->AimMontage||!Material) return TEXT("ERROR missing carry assets");
        return Compile(BP,1);
    }
    return TEXT("ERROR no CarryComponent template");
}
FString UCarryEditorLibrary::ConfigureTestBox(UBlueprint* BP,UClass* HoldableClass)
{
    if(!BP||!BP->SimpleConstructionScript||!HoldableClass||!HoldableClass->IsChildOf(UHoldableComponent::StaticClass())) return TEXT("ERROR invalid box Blueprint");
    USimpleConstructionScript* SCS=BP->SimpleConstructionScript;
    for(USCS_Node* N:SCS->GetAllNodes()) if(UHoldableComponent* Hold=Cast<UHoldableComponent>(N->ComponentTemplate))
    {
        Hold->CarryOffset=FTransform(FRotator::ZeroRotator,FVector(32,0,30));
        for(USCS_Node* M:SCS->GetAllNodes()) if(UStaticMeshComponent* Mesh=Cast<UStaticMeshComponent>(M->ComponentTemplate))
            Mesh->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
        return Compile(BP,1);
    }
    const auto Old=SCS->GetAllNodes(); for(USCS_Node* N:Old) if(N->GetVariableName()==TEXT("DefaultSceneRoot")) SCS->RemoveNode(N);
    USCS_Node* MeshNode=SCS->CreateNode(UStaticMeshComponent::StaticClass(),TEXT("CarryMesh"));
    UStaticMeshComponent* Mesh=CastChecked<UStaticMeshComponent>(MeshNode->ComponentTemplate);
    Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Mesh->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
    Mesh->SetRelativeScale3D(FVector(.36f)); Mesh->SetMobility(EComponentMobility::Movable);
    Mesh->SetCollisionProfileName(TEXT("PhysicsActor")); Mesh->SetSimulatePhysics(true); Mesh->SetUseCCD(true);
    SCS->AddNode(MeshNode);
    USCS_Node* HoldNode=SCS->CreateNode(HoldableClass,TEXT("Ac_Holdable"));
    UHoldableComponent* Hold=CastChecked<UHoldableComponent>(HoldNode->ComponentTemplate);
    Hold->LeftHandGrip=FTransform(FRotator::ZeroRotator,FVector(0,-50,0));
    Hold->RightHandGrip=FTransform(FRotator::ZeroRotator,FVector(0,50,0));
    SCS->AddNode(HoldNode); return Compile(BP,2);
}
