#include "SceneDirectorPlayer.h"
#include "UObject/StrongObjectPtr.h"
bool ASceneDirectorPlayer::ExecuteGameAction(const FDirectorStep& Step)
{
    FDirectorActionResult Result;Result.NodeId=Step.Id;Result.ActionKey=Step.ActionKey;
    const auto Class=ActiveActions.FindRef(Step.ActionKey);
    AActor* Target=Step.ActionTarget.IsNone()?nullptr:FindNPC(Step.ActionTarget);
    if(!Class||Class->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists))Result.Message=TEXT("등록 액션 BP를 찾을 수 없습니다.");
    else if(!Step.ActionTarget.IsNone()&&!IsValid(Target))Result.Message=TEXT("액션 대상 NPC를 찾을 수 없습니다: ")+Step.ActionTarget.ToString();
    else
    {
        TStrongObjectPtr<USceneDirectorAction> Action(NewObject<USceneDirectorAction>(this,Class,NAME_None,RF_Transient));
        TGuardValue<bool> Guard(bExecutingAction,true);
        Result.bSucceeded=Action->Execute(this,Target,Step.ActionParameters,Result.Message);
    }
    ActionResults.Add(Result);
    if(!Result.bSucceeded)
    {
        LastError=FString::Printf(TEXT("액션 실패 [%s]: %s"),*Step.ActionKey.ToString(),Result.Message.IsEmpty()?TEXT("BP 실행 결과가 실패입니다."):*Result.Message);
        StopDirector();return false;
    }
    return SequencePlayer!=nullptr;
}
