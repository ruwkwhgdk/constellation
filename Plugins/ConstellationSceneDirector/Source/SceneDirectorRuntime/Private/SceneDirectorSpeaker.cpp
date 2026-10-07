#include "SceneDirectorSpeaker.h"
#include "SceneDirectorAsset.h"

bool FDirectorStep::ValidateSpeaker(FString& Error) const
{
 if(SpeakerSource==EDirectorSpeakerSource::Direct||SpeakerSource==EDirectorSpeakerSource::None)return true;
 if(SpeakerSource!=EDirectorSpeakerSource::Table){Error=TEXT("화자 표시 방식이 유효하지 않습니다.");return false;}
 const UDataTable* Table=SpeakerRow.DataTable.Get();
 if(!Table||!Table->GetRowStruct()||!Table->GetRowStruct()->IsChildOf(FDirectorSpeakerRow::StaticStruct()))
 {Error=TEXT("등록 화자: DirectorSpeakerRow 형식의 화자 데이터 테이블을 선택하세요.");return false;}
 const auto* Row=Table->FindRow<FDirectorSpeakerRow>(SpeakerRow.RowName,TEXT("Scene Director Speaker"),false);
 if(!Row){Error=TEXT("등록 화자: 테이블에서 존재하는 화자를 선택하세요: ")+SpeakerRow.RowName.ToString();return false;}
 if(Row->DisplayName.ToString().TrimStartAndEnd().IsEmpty())
 {Error=TEXT("등록 화자의 표시명이 비어 있습니다. 이름판을 숨기려면 '화자 없음'을 선택하세요: ")+SpeakerRow.RowName.ToString();return false;}
 return true;
}
FText FDirectorStep::ResolveSpeaker() const
{
 if(SpeakerSource==EDirectorSpeakerSource::None)return FText::GetEmpty();
 if(SpeakerSource==EDirectorSpeakerSource::Direct)return SpeakerName.ToString().TrimStartAndEnd().IsEmpty()?FText::GetEmpty():SpeakerName;
 FString Error;if(!ValidateSpeaker(Error))return FText::GetEmpty();
 return SpeakerRow.DataTable->FindRow<FDirectorSpeakerRow>(SpeakerRow.RowName,TEXT("Scene Director Speaker"),false)->DisplayName;
}
