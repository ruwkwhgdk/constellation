#include "SceneDirectorAction.h"
#include "GameFramework/Actor.h"
UWorld* USceneDirectorAction::GetWorld() const
{
    if(HasAnyFlags(RF_ClassDefaultObject))return nullptr;
    return GetOuter()?GetOuter()->GetWorld():nullptr;
}
bool USceneDirectorAction::Execute_Implementation(ASceneDirectorPlayer*,AActor*,const FDirectorActionParameters&,FString& Error)
{Error=TEXT("액션 BP의 액션 실행 함수를 구현하세요.");return false;}
bool USceneDirectorAction::ApplyActorTag(AActor* Target,const FDirectorActionParameters& Parameters,FString& Error)
{
    Error.Reset();
    if(!IsValid(Target)||Parameters.Identifier.IsNone()){Error=TEXT("태그 액션의 대상 NPC와 ID를 입력하세요.");return false;}
    if(Parameters.Flag)Target->Tags.AddUnique(Parameters.Identifier);else Target->Tags.Remove(Parameters.Identifier);
    return true;
}
