#include "SceneDirectorGraph.h"
#include "SceneDirectorDetails.h"
#include "LevelSequence.h"
#include "SceneDirectorNodeTypes.h"
#include "EdGraph/EdGraphPin.h"
#include "SGraphNodeDefault.h"
class SDirectorGraphNode : public SGraphNodeDefault
{
public:
    SLATE_BEGIN_ARGS(SDirectorGraphNode) {} SLATE_END_ARGS()
    void Construct(const FArguments&,USceneDirectorGraphNode* Node){SGraphNodeDefault::Construct(SGraphNodeDefault::FArguments().GraphNodeObj(Node));}
    virtual void MoveTo(const FVector2f& Position,FNodeSet& Filter,bool bMarkDirty=true) override
    {
        SGraphNodeDefault::MoveTo(Position,Filter,bMarkDirty);
        if(auto* Graph=Cast<USceneDirectorGraph>(GraphNode->GetGraph()))Graph->Sync();
    }
};
TSharedPtr<SGraphNode> USceneDirectorGraphNode::CreateVisualWidget(){return SNew(SDirectorGraphNode,this);}
void USceneDirectorGraph::Load()
{
    bLoading=true; Asset->EnsureCameraDefinitions(); Nodes.Reset();
    TMap<FGuid,USceneDirectorGraphNode*> Map;
    for(const auto& Step:Asset->Steps)
    {
        auto* Node=NewObject<USceneDirectorGraphNode>(this,NAME_None,RF_Transactional);
        Node->Step=Step; Node->CreateNewGuid(); Node->NodePosX=Step.EditorPosition.X; Node->NodePosY=Step.EditorPosition.Y;
        AddNode(Node,false,false); Node->AllocateDefaultPins(); Map.Add(Step.Id,Node);
    }
    for(const auto& Pair:Map)
    {
        auto* Node=Pair.Value;
        auto Link=[&](FName PinName,FGuid Target)
        {auto* Next=Map.FindRef(Target);auto* Pin=Node->FindPin(PinName);if(Next&&Pin&&Next->FindPin(TEXT("In")))Pin->MakeLinkTo(Next->FindPin(TEXT("In")));};
        if(Node->Step.Type==EDirectorNodeType::Condition)
        {Link(TEXT("True"),Node->Step.TrueTarget);Link(TEXT("False"),Node->Step.FalseTarget);}
        else if(Node->HasChoiceOutputs())
        {
            const auto Legacy=Node->Step.Successors();
            for(const auto& Choice:Node->Step.Choices)if(Choice.bEnabled)
                Link(USceneDirectorGraphNode::ChoicePinName(Choice.Key),Node->Step.ChoiceTargets.IsEmpty()&&Legacy.Num()==1?Legacy[0]:Node->Step.ChoiceTargets.FindRef(Choice.Key));
            // Ambiguous legacy parallel successors remain visible until explicitly repaired.
            for(FGuid Next:Legacy)Link(TEXT("Out"),Next);
        }
        else for(FGuid Next:Node->Step.Successors())Link(TEXT("Out"),Next);
    }
    bLoading=false; NotifyGraphChanged();
}
void USceneDirectorGraph::Sync()
{
    if(bLoading || !Asset)return;
    Asset->Modify(); Asset->Steps.Reset();
    for(const auto& Base:Nodes)
    {
        auto* Node=Cast<USceneDirectorGraphNode>(Base); if(!Node)continue;
        if(DirectorNodes::IsCamera(Node->Step.Type))Node->Step.CameraKey=Node->Step.EffectiveCameraKey();
        FDirectorStep Step=Node->Step; Step.Next.Invalidate(); Step.NextNodes.Reset(); Step.ChoiceTargets.Reset();Step.TrueTarget.Invalidate();Step.FalseTarget.Invalidate();
        Step.EditorPosition=FVector2D(Node->NodePosX,Node->NodePosY);
        auto Target=[&](FName Name)->FGuid
        {auto* Pin=Node->FindPin(Name);if(Pin&&Pin->LinkedTo.Num())if(auto* Next=Cast<USceneDirectorGraphNode>(Pin->LinkedTo[0]->GetOwningNode()))return Next->Step.Id;return FGuid();};
        if(Step.Type==EDirectorNodeType::Condition){Step.TrueTarget=Target(TEXT("True"));Step.FalseTarget=Target(TEXT("False"));}
        if(Node->HasChoiceOutputs())for(const auto& Choice:Step.Choices)if(Choice.bEnabled)Step.ChoiceTargets.Add(Choice.Key,Target(USceneDirectorGraphNode::ChoicePinName(Choice.Key)));
        if(auto* Pin=Node->FindPin(TEXT("Out"));Pin && Pin->LinkedTo.Num())
            for(auto* Link:Pin->LinkedTo) if(auto* Next=Cast<USceneDirectorGraphNode>(Link->GetOwningNode()))Step.NextNodes.AddUnique(Next->Step.Id);
        Node->Step=Step;
        Asset->Steps.Add(Step);
    }
    Asset->EnsureCameraDefinitions(); Asset->bNeedsCompile=true; Asset->MarkPackageDirty(); OnChanged.Broadcast();
}
TArray<FString> USceneDirectorGraphNode::GetActionKeys() const
{
    TArray<FString> Keys;if(const auto* Graph=Cast<USceneDirectorGraph>(GetGraph());Graph&&Graph->Asset)
        for(const auto& A:Graph->Asset->Actions)Keys.Add(A.Key.ToString());return Keys;
}
FName USceneDirectorGraphNode::ChoicePinName(FName Key){return FName(*(TEXT("Choice_")+Key.ToString()));}
bool USceneDirectorGraphNode::HasChoiceOutputs() const{return Step.Type==EDirectorNodeType::Dialogue&&!Step.Choices.IsEmpty();}
void USceneDirectorGraphNode::AllocateDefaultPins()
{
    if(Step.Type!=EDirectorNodeType::Start)CreatePin(EGPD_Input,TEXT("exec"),TEXT("In"))->PinFriendlyName=FText::FromString(TEXT("이전"));
    if(Step.Type==EDirectorNodeType::Condition)
    {
        CreatePin(EGPD_Output,TEXT("exec"),TEXT("True"))->PinFriendlyName=FText::FromString(TEXT("참"));
        CreatePin(EGPD_Output,TEXT("exec"),TEXT("False"))->PinFriendlyName=FText::FromString(TEXT("거짓"));
    }
    else if(HasChoiceOutputs())
    {
        for(const auto& Choice:Step.Choices)if(Choice.bEnabled)CreatePin(EGPD_Output,TEXT("exec"),ChoicePinName(Choice.Key))->PinFriendlyName=FText::FromString(Choice.Key.ToString()+TEXT(" · ")+Choice.Text.ToString());
        if(Step.Successors().Num()>1)CreatePin(EGPD_Output,TEXT("exec"),TEXT("Out"))->PinFriendlyName=FText::FromString(TEXT("이전 병렬 연결 · 선택지별 재연결 필요"));
    }
    else if(Step.Type!=EDirectorNodeType::End)CreatePin(EGPD_Output,TEXT("exec"),TEXT("Out"))->PinFriendlyName=FText::FromString(TEXT("다음"));
}
void USceneDirectorGraphNode::RebuildBranchPins(const FDirectorStep& Before)
{
    auto* Graph=CastChecked<USceneDirectorGraph>(GetGraph());
    TGuardValue<bool> Guard(Graph->bLoading,true);
    Modify();
    const auto OldPins=Pins;
    Pins.Reset();AllocateDefaultPins();
    for(auto* Old:OldPins)
    {
        UEdGraphPin* New=FindPin(Old->PinName);
        if(!New&&Before.Type==EDirectorNodeType::Dialogue&&HasChoiceOutputs())
        {
            const int32 Index=Before.Choices.IndexOfByPredicate([&](const FDirectorChoice& C){return ChoicePinName(C.Key)==Old->PinName;});
            // Only a key rename at the same position qualifies; deletion never shifts a connection.
            if(Before.Choices.Num()==Step.Choices.Num()&&Step.Choices.IsValidIndex(Index)&&
                !Before.Choices.ContainsByPredicate([&](const FDirectorChoice& C){return C.Key==Step.Choices[Index].Key;}))
                New=FindPin(ChoicePinName(Step.Choices[Index].Key));
        }
        const auto Links=Old->LinkedTo;
        for(auto* Link:Links)Link->GetOwningNode()->Modify();
        Old->BreakAllPinLinks(false);
        if(New)for(auto* Link:Links)New->MakeLinkTo(Link);
        // Converting ordinary dialogue to choices preserves an unambiguous continuation.
        else if(Old->PinName==TEXT("Out")&&HasChoiceOutputs()&&Links.Num()==1)
            for(auto* Pin:Pins)if(Pin->Direction==EGPD_Output)Pin->MakeLinkTo(Links[0]);
        DestroyPin(Old);
    }
}
FText USceneDirectorGraphNode::GetNodeTitle(ENodeTitleType::Type) const
{
    switch(Step.Type)
    {
    case EDirectorNodeType::Condition:return FText::FromString(TEXT("조건 분기\n")+Step.BoolKey.ToString());
    case EDirectorNodeType::SetInt:return FText::FromString(TEXT("Integer 설정\n")+Step.IntKey.ToString()+FString::Printf(TEXT(" = %d"),Step.IntValue));
    case EDirectorNodeType::SetBool:return FText::FromString(TEXT("변수 설정\n")+Step.BoolKey.ToString()+(Step.BoolValue?TEXT(" = 참"):TEXT(" = 거짓")));
    case EDirectorNodeType::BindNPC:return FText::FromString((DirectorAuthoring::IsCharacterEntry(Step)?TEXT("기존 캐릭터 연결\n"):TEXT("기존 오브젝트 연결\n"))+Step.Role.ToString());
    case EDirectorNodeType::LookAt:return FText::FromString(TEXT("시선 지정\n")+Step.Role.ToString()+TEXT(" → ")+Step.TargetRole.ToString());
    case EDirectorNodeType::Expression:return FText::FromString(TEXT("표정 변경\n")+Step.Role.ToString()+TEXT(" · ")+Step.ExpressionKey.ToString());
    case EDirectorNodeType::Dialogue:return FText::FromString(TEXT("대사 출력\n")+Step.DialogueText.ToString().Left(24));
    case EDirectorNodeType::CameraPreset:return FText::FromString(TEXT("구도 프리셋\n")+Step.CameraKey.ToString()+TEXT(" · ")+Step.Role.ToString());
    case EDirectorNodeType::CameraSwitch:return FText::FromString(TEXT("카메라 전환\n")+Step.CameraKey.ToString());
    case EDirectorNodeType::PlayerHidden:return FText::FromString(Step.bHidePlayer?TEXT("플레이어 숨김 · 켜기"):TEXT("플레이어 숨김 · 해제"));
    case EDirectorNodeType::InputLock:return FText::FromString(Step.bLockInput?TEXT("조작 잠금 · 켜기"):TEXT("조작 잠금 · 해제"));
    case EDirectorNodeType::HUDHidden:return FText::FromString(Step.bHideHUD?TEXT("게임 HUD 숨김 · 켜기"):TEXT("게임 HUD 숨김 · 해제"));
    case EDirectorNodeType::CloseDialogue:return FText::FromString(TEXT("대사창 닫기"));
    case EDirectorNodeType::CinematicMode:return FText::FromString(TEXT("연출 모드 설정"));
    case EDirectorNodeType::Fade:return FText::FromString(TEXT("화면 페이드"));
    case EDirectorNodeType::Visibility:return FText::FromString(TEXT("NPC 표시 · ")+Step.Role.ToString());
    case EDirectorNodeType::CameraReturn:
    case EDirectorNodeType::GameplayReturn:return FText::FromString(FString::Printf(TEXT("카메라 복귀\n시작 전 카메라 · %.2f초"),Step.Duration));
    case EDirectorNodeType::Start:return FText::FromString(TEXT("시작"));
    case EDirectorNodeType::End:return FText::FromString(TEXT("종료"));
    case EDirectorNodeType::SpawnNPC:return FText::FromString(FString::Printf(TEXT("NPC 추가\n%s · %s"),*Step.Role.ToString(),Step.ActorClass?*Step.ActorClass->GetName():TEXT("BP 선택 필요")));
    case EDirectorNodeType::CharacterMove:return FText::FromString(FString::Printf(TEXT("캐릭터 이동\n%s · %s"),*Step.Role.ToString(),Step.MoveTiming==EDirectorMoveTiming::Speed?TEXT("속도 기준"):TEXT("시간 기준")));
    case EDirectorNodeType::CameraMove:return FText::FromString(FString::Printf(TEXT("카메라 이동·회전\n%s · %.2f초"),*Step.CameraKey.ToString(),Step.Duration));
    case EDirectorNodeType::Sequence:return FText::FromString(TEXT("시퀀스 재생\n")+GetNameSafe(Step.SourceSequence)+FString::Printf(TEXT(" · %.2fx"),Step.SequenceSpeed));
    case EDirectorNodeType::GameAction:return FText::FromString(TEXT("BP 액션 · ")+Step.ActionKey.ToString()+TEXT("\n게임 실행 전용"));
    case EDirectorNodeType::Hub:return FText::FromString(TEXT("합류 · 모두 완료 대기"));
    case EDirectorNodeType::Animation:return FText::FromString(FString::Printf(TEXT("애니메이션\n%s · %.2f초 · %s"),*Step.Role.ToString(),Step.Duration,Step.bWaitForCompletion?TEXT("완료 대기"):TEXT("즉시 다음")));
    case EDirectorNodeType::Camera:return FText::FromString(FString::Printf(TEXT("카메라 샷\n%s · %.2f초"),*Step.CameraKey.ToString(),Step.Duration));
    default:return FText::FromString(FString::Printf(TEXT("대기 · %.2f초"),Step.Duration));
    }
}
FLinearColor USceneDirectorGraphNode::GetNodeTitleColor() const
{
    switch(Step.Type){case EDirectorNodeType::SpawnNPC:return FLinearColor(.08f,.5f,.2f);case EDirectorNodeType::Camera:return FLinearColor(.02f,.4f,.65f);case EDirectorNodeType::Wait:return FLinearColor(.65f,.23f,.03f);default:return FLinearColor(.35f,.16f,.5f);}
}
void USceneDirectorGraphNode::NodeConnectionListChanged(){Super::NodeConnectionListChanged(); if(auto* Graph=Cast<USceneDirectorGraph>(GetGraph()))Graph->Sync();}
void USceneDirectorGraphNode::PreEditChange(FProperty* Property){PreviousRole=Step.Role;PreviousStep=Step;Super::PreEditChange(Property);}
void USceneDirectorGraphNode::PostEditUndo()
{
    // UObject::PostEditUndo dispatches PostEditChangeProperty. Transactions restore the
    // asset as well as the pins; writing transient graph state here can overwrite that
    // restored asset (especially old nodes replaced by the toolkit's Graph->Load).
    if(auto* Graph=Cast<USceneDirectorGraph>(GetGraph()))
    {TGuardValue<bool> Guard(Graph->bLoading,true);Super::PostEditUndo();}
    else Super::PostEditUndo();
}
void USceneDirectorGraphNode::PostEditChangeProperty(FPropertyChangedEvent& Event)
{
    Super::PostEditChangeProperty(Event);
    if(auto* Graph=Cast<USceneDirectorGraph>(GetGraph());Graph&&!Graph->bLoading)
    {
        if(DirectorNodes::IsNPC(Step.Type)&&PreviousRole!=Step.Role&&!PreviousRole.IsNone())
        {
            int32 Matches=0;for(auto Base:Graph->Nodes)if(auto* N=Cast<USceneDirectorGraphNode>(Base))if(N!=this&&DirectorNodes::IsNPC(N->Step.Type)&&N->Step.Role==PreviousRole)++Matches;
            if(!Matches)for(auto Base:Graph->Nodes)if(auto* N=Cast<USceneDirectorGraphNode>(Base))
            {
                if(DirectorNodes::UsesNPC(N->Step.Type)&&N->Step.Role==PreviousRole){N->Modify();N->Step.Role=Step.Role;}
                for(auto& R:N->Step.SequenceRoles)if(R.Target==EDirectorSequenceTarget::NPC&&R.Key==PreviousRole){N->Modify();R.Key=Step.Role;}
                if(N->Step.ActionTarget==PreviousRole){N->Modify();N->Step.ActionTarget=Step.Role;}
                if(N->Step.TargetRole==PreviousRole){N->Modify();N->Step.TargetRole=Step.Role;}
            }
        }
        if(Step.Type==EDirectorNodeType::Dialogue&&Event.GetPropertyName()==GET_MEMBER_NAME_CHECKED(FDirectorStep,SpeakerSource)&&Step.SpeakerSource==EDirectorSpeakerSource::Table&&!Step.SpeakerRow.DataTable)
            Step.SpeakerRow.DataTable=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData.DT_SpeakerData"),nullptr,LOAD_NoWarn);
        if(Event.GetPropertyName()==GET_MEMBER_NAME_CHECKED(FDirectorStep,ActorClass))Step.ImportedTemplate=nullptr;
        if(Step.Type==EDirectorNodeType::Sequence)DirectorSequence::RefreshRoles(Step);
        RebuildBranchPins(PreviousStep);
        Graph->Sync();Graph->NotifyGraphChanged();
    }
}
const FPinConnectionResponse USceneDirectorSchema::CanCreateConnection(const UEdGraphPin* A,const UEdGraphPin* B) const
{
    if(!A||!B||A->GetOwningNode()==B->GetOwningNode())return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW,TEXT("다른 노드에 연결하세요."));
    if(A->Direction==B->Direction)return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW,TEXT("다음 핀과 이전 핀을 연결하세요."));
        if(A->LinkedTo.Contains(B))return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW,TEXT("이미 연결되어 있습니다."));
    const UEdGraphNode* Source=(A->Direction==EGPD_Output?A:B)->GetOwningNode();
    TArray<const UEdGraphNode*> Pending{(A->Direction==EGPD_Input?A:B)->GetOwningNode()};TSet<const UEdGraphNode*> Seen;
    while(Pending.Num())
    {
        const UEdGraphNode* Node=Pending.Pop();
        if(Node==Source)return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW,TEXT("순환 연결은 지원하지 않습니다."));
        if(Seen.Contains(Node))continue;Seen.Add(Node);
        for(auto* Pin:Node->Pins)if(Pin->Direction==EGPD_Output)for(auto* Link:Pin->LinkedTo)Pending.Add(Link->GetOwningNode());
    }
    const UEdGraphPin* Output=A->Direction==EGPD_Output?A:B;
    const auto* Owner=Cast<USceneDirectorGraphNode>(Output->GetOwningNode());
    if(Owner&&(Owner->HasChoiceOutputs()||Owner->Step.Type==EDirectorNodeType::Condition)&&Output->PinName!=TEXT("Out")&&!Output->LinkedTo.IsEmpty())
        return FPinConnectionResponse(A==Output?CONNECT_RESPONSE_BREAK_OTHERS_A:CONNECT_RESPONSE_BREAK_OTHERS_B,TEXT("이 분기의 연결을 교체합니다."));
    return FPinConnectionResponse(CONNECT_RESPONSE_MAKE,TEXT("분기: 병렬 실행 / 합류: 모두 완료 대기"));
}
