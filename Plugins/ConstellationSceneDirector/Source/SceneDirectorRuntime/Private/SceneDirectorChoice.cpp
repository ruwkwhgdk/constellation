#include "SceneDirectorChoice.h"
bool DirectorChoices::Validate(const TArray<FDirectorChoice>& Choices,FString& Error)
{
    Error.Reset();
    if(Choices.Num()>4){Error=TEXT("선택지는 최대 4개까지 사용할 수 있습니다.");return false;}
    TSet<FName> Keys;
    for(const auto& C:Choices)
    {
        if(C.Key.IsNone()||Keys.Contains(C.Key)){Error=TEXT("선택지 결과 Key는 비어 있거나 중복될 수 없습니다.");return false;}
        if(C.Text.ToString().TrimStartAndEnd().IsEmpty()){Error=TEXT("선택지 문구를 입력하세요.");return false;}
        Keys.Add(C.Key);
    }
    if(!Choices.IsEmpty()&&!Choices.ContainsByPredicate([](const FDirectorChoice& C){return C.bEnabled;})){Error=TEXT("선택 가능한 항목이 하나 이상 필요합니다.");return false;}
    return true;
}
