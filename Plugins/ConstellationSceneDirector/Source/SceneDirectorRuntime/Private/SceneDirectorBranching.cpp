#include "SceneDirectorBranching.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "Algo/Count.h"

namespace DirectorBranching
{
bool HasBranches(const USceneDirectorAsset& A)
{
    if(A.bResolvedBranchPath)return false;
    for(const auto& S:A.Steps)if(S.Type==EDirectorNodeType::Condition||S.Type==EDirectorNodeType::SetBool||!S.ChoiceTargets.IsEmpty())return true;
    return false;
}
bool Resolve(const USceneDirectorAsset& A,const TMap<FGuid,FName>& Decisions,const TMap<FName,bool>& Overrides,USceneDirectorAsset& Out,FGuid& Pending,FString& Error)
{
    Error.Reset();Pending.Invalidate();
    auto Fail=[&](const TCHAR* Message){Error=Message;return false;};
    const int32 N=A.Steps.Num();TMap<FGuid,int32> IDs;TMap<FName,bool> Values;
    TArray<TArray<int32>> Parents,Children;Parents.SetNum(N);Children.SetNum(N);
    int32 Start=INDEX_NONE,End=INDEX_NONE;
    for(const auto& V:A.BoolVariables){if(V.Key.IsNone()||Values.Contains(V.Key))return Fail(TEXT("Bool 변수 Key는 비어 있거나 중복될 수 없습니다."));Values.Add(V.Key,V.Value);}
    for(const auto& V:Overrides){if(!Values.Contains(V.Key))return Fail(TEXT("초기값에 지정한 Bool 변수 Key를 찾을 수 없습니다."));Values[V.Key]=V.Value;}
    for(int32 I=0;I<N;++I)
    {
        const auto& S=A.Steps[I];
        if(!S.Id.IsValid()||IDs.Contains(S.Id))return Fail(TEXT("노드 ID가 비어 있거나 중복되었습니다."));IDs.Add(S.Id,I);
        if(S.Type==EDirectorNodeType::Start){if(Start!=INDEX_NONE)return Fail(TEXT("시작 노드는 하나만 배치하세요."));Start=I;}
        if(S.Type==EDirectorNodeType::End){if(End!=INDEX_NONE)return Fail(TEXT("종료 노드는 하나만 배치하세요."));End=I;}
        if((S.Type==EDirectorNodeType::Condition||S.Type==EDirectorNodeType::SetBool)&&!Values.Contains(S.BoolKey))return Fail(TEXT("조건 또는 변수 설정 노드의 Bool 변수 Key를 찾을 수 없습니다."));
        if(!S.ChoiceTargets.IsEmpty())
        {
            if(S.Type!=EDirectorNodeType::Dialogue||S.Choices.IsEmpty()||S.ChoiceTargets.Num()!=S.Choices.FilterByPredicate([](const FDirectorChoice& C){return C.bEnabled;}).Num())return Fail(TEXT("선택지 출력 Key와 선택지 목록이 일치해야 합니다."));
            if(!DirectorChoices::Validate(S.Choices,Error))return false;
            for(const auto& C:S.Choices)if(C.bEnabled&&!S.ChoiceTargets.Contains(C.Key))return Fail(TEXT("모든 선택지 출력을 연결하세요."));
        }
    }
    if(Start==INDEX_NONE||End==INDEX_NONE)return Fail(TEXT("시작과 종료 노드를 하나씩 배치하세요."));
    for(int32 I=0;I<N;++I)
    {
        for(FGuid Target:A.Steps[I].AllSuccessors())
        {
            const int32* J=IDs.Find(Target);if(!J)return Fail(TEXT("모든 분기 출력을 존재하는 노드에 연결하세요."));
            if(!Children[I].Contains(*J)){Children[I].Add(*J);Parents[*J].Add(I);}
        }
        if(I==End&&!Children[I].IsEmpty())return Fail(TEXT("종료 뒤에는 연결할 수 없습니다."));
        if(I!=End&&Children[I].IsEmpty())return Fail(TEXT("모든 경로는 종료로 이어져야 합니다."));
    }
    TArray<int32> Remaining,Order;for(int32 I=0;I<N;++I){Remaining.Add(Parents[I].Num());if(Parents[I].IsEmpty())Order.Add(I);}
    if(Order.Num()!=1||Order[0]!=Start)return Fail(TEXT("시작에서 연결되지 않은 노드가 있습니다."));
    for(int32 Cursor=0;Cursor<Order.Num();++Cursor)for(int32 J:Children[Order[Cursor]])if(--Remaining[J]==0)Order.Add(J);
    if(Order.Num()!=N)return Fail(TEXT("순환 연결은 지원하지 않습니다."));
    TArray<TSet<int32>> Ancestors;Ancestors.SetNum(N);
    for(int32 I:Order)for(int32 P:Parents[I]){Ancestors[I].Append(Ancestors[P]);Ancestors[I].Add(P);}
    // Node and edge tokens: 0 skipped, 1 active, 2 waiting on an unanswered choice.
    TArray<uint8> State;State.Init(0,N);TArray<TMap<int32,uint8>> Edges;Edges.SetNum(N);
    TArray<int32> ActiveDecisions;
    for(int32 I:Order)
    {
        bool Active=I==Start,Unknown=false;
        for(int32 P:Parents[I]){Active|=Edges[P].FindRef(I)==1;Unknown|=Edges[P].FindRef(I)==2;}
        State[I]=Unknown?2:(Active?1:0);
        const auto& S=A.Steps[I];const bool Choice=!S.ChoiceTargets.IsEmpty();const bool Condition=S.Type==EDirectorNodeType::Condition;
        FGuid Selected;bool Awaiting=false;
        if(State[I]==1)
        {
            if(S.Type==EDirectorNodeType::SetBool)Values[S.BoolKey]=S.BoolValue;
            if(Choice||Condition)
            {
                ActiveDecisions.Add(I);
                if(Condition)Selected=Values.FindChecked(S.BoolKey)?S.TrueTarget:S.FalseTarget;
                else if(const FName* Key=Decisions.Find(S.Id))
                {if(!S.Choices.ContainsByPredicate([&](const FDirectorChoice& C){return C.Key==*Key&&C.bEnabled;}))return Fail(TEXT("비활성 선택지는 실행할 수 없습니다."));const FGuid* Target=S.ChoiceTargets.Find(*Key);if(!Target)return Fail(TEXT("선택 결과의 Key를 선택지 목록에서 찾을 수 없습니다."));Selected=*Target;}
                else {if(Pending.IsValid())return Fail(TEXT("선택지 앞에 합류를 배치하여 병렬 작업을 완료하세요."));Pending=S.Id;Awaiting=true;}
            }
        }
        for(int32 J:Children[I])Edges[I].Add(J,State[I]!=1?State[I]:(Awaiting?2:((Choice||Condition)&&A.Steps[J].Id!=Selected?0:1)));
    }
    // Decisions may only occur after all simultaneously active work has joined.
    for(int32 I:ActiveDecisions)for(int32 J:Order)
        if(State[J]==1&&I!=J&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I))return Fail(TEXT("선택지 또는 조건 앞에 합류를 배치하여 병렬 작업을 완료하세요."));
    for(int32 I:Order)if(State[I]==1&&A.Steps[I].Type==EDirectorNodeType::SetBool)
        for(int32 J:Order)if(State[J]==1&&I!=J&&A.Steps[J].Type==EDirectorNodeType::SetBool&&A.Steps[I].BoolKey==A.Steps[J].BoolKey&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I))return Fail(TEXT("같은 Bool 변수를 설정하는 노드는 순서대로 연결하세요."));
    if(Pending.IsValid())
    {
        int32 P=IDs.FindChecked(Pending);for(int32 I:Order)if(State[I]==1&&I!=P&&!Ancestors[P].Contains(I))return Fail(TEXT("미응답 선택지 앞에 합류를 배치하여 병렬 작업을 완료하세요."));
    }
    else if(State[End]!=1)return Fail(TEXT("선택한 경로가 종료에 도달하지 못했습니다."));
    TArray<FDirectorStep> Steps;
    for(int32 I:Order)if(State[I]==1)
    {
        FDirectorStep S=A.Steps[I];S.Next.Invalidate();S.NextNodes.Empty();S.ChoiceTargets.Empty();S.TrueTarget.Invalidate();S.FalseTarget.Invalidate();
        for(int32 J:Children[I])if(Edges[I].FindRef(J)==1&&State[J]==1)S.NextNodes.Add(A.Steps[J].Id);
        Steps.Add(MoveTemp(S));
    }
    if(Pending.IsValid()){FDirectorStep Terminal;Terminal.Type=EDirectorNodeType::End;Steps.Last().NextNodes={Terminal.Id};Steps.Add(Terminal);}
    Out.Steps=MoveTemp(Steps);Out.Cameras=A.Cameras;Out.Objects=A.Objects;Out.AuthoringOrigin=A.AuthoringOrigin;Out.Vectors=A.Vectors;Out.BoolVariables=A.BoolVariables;Out.IntVariables=A.IntVariables;Out.Actions=A.Actions;Out.FormatVersion=A.FormatVersion;Out.bResolvedBranchPath=true;Out.EventKey=A.EventKey;return true;
}
bool ValidateAll(const USceneDirectorAsset& A,FString& Error)
{
    constexpr int32 MaxRoutes=256;
    struct FRoute {TMap<FGuid,FName> Decisions;TMap<FName,bool> Overrides;};
    TArray<FName> Keys;
    for(const auto& S:A.Steps)if(S.Type==EDirectorNodeType::Condition)Keys.AddUnique(S.BoolKey);
    TArray<FRoute> Routes;Routes.AddDefaulted();
    for(FName Key:Keys)
    {
        const int32 Count=Routes.Num();
        if(Count*2>MaxRoutes){Error=TEXT("분기 검증은 초기값과 선택 경로의 조합을 최대 256개까지 지원합니다. 이벤트를 작은 그래프로 나누세요.");return false;}
        for(int32 I=0;I<Count;++I){FRoute Other=Routes[I];Routes[I].Overrides.Add(Key,false);Other.Overrides.Add(Key,true);Routes.Add(MoveTemp(Other));}
    }
    int32 Complete=0;
    while(!Routes.IsEmpty())
    {
        FRoute Route=Routes.Pop(EAllowShrinking::No);
        auto* Resolved=NewObject<USceneDirectorAsset>(GetTransientPackage(),NAME_None,RF_Transient);FGuid Pending;
        if(!Resolve(A,Route.Decisions,Route.Overrides,*Resolved,Pending,Error))return false;
        FDirectorSchedule Plan;if(!FSceneDirectorCompiler::Schedule(*Resolved,Plan,Error))return false;
        if(!Pending.IsValid()){++Complete;continue;}
        const auto* Step=A.Steps.FindByPredicate([&](const FDirectorStep& S){return S.Id==Pending;});
        if(Complete+Routes.Num()+Step->Choices.Num()>MaxRoutes){Error=TEXT("분기 검증은 초기값과 선택 경로의 조합을 최대 256개까지 지원합니다. 이벤트를 작은 그래프로 나누세요.");return false;}
        for(const auto& C:Step->Choices)if(C.bEnabled){FRoute Next=Route;Next.Decisions.Add(Pending,C.Key);Routes.Add(MoveTemp(Next));}
    }
    return true;
}
}
