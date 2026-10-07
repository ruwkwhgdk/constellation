#pragma once
#include "SceneDirectorAsset.h"
struct FDirectorNodeMenuEntry
{
    const TCHAR* Category;
    const TCHAR* Label;
    EDirectorNodeType Type;
};
inline TArray<FDirectorNodeMenuEntry> DirectorNodeMenuEntries()
{
    return {
        {TEXT("흐름 제어"),TEXT("Integer 변수 설정"),EDirectorNodeType::SetInt},
        {TEXT("캐릭터"),TEXT("NPC 표시·숨김"),EDirectorNodeType::Visibility},
        {TEXT("카메라"),TEXT("화면 페이드"),EDirectorNodeType::Fade},
        {TEXT("캐릭터"),TEXT("NPC 추가"),EDirectorNodeType::SpawnNPC},
        {TEXT("캐릭터"),TEXT("애니메이션"),EDirectorNodeType::Animation},
        {TEXT("캐릭터"),TEXT("캐릭터 이동"),EDirectorNodeType::CharacterMove},
        {TEXT("카메라"),TEXT("카메라 샷"),EDirectorNodeType::Camera},
        {TEXT("카메라"),TEXT("카메라 이동·회전"),EDirectorNodeType::CameraMove},
        {TEXT("흐름 제어"),TEXT("조건 분기"),EDirectorNodeType::Condition},
        {TEXT("흐름 제어"),TEXT("변수 설정"),EDirectorNodeType::SetBool},
        {TEXT("흐름 제어"),TEXT("대기"),EDirectorNodeType::Wait},
        {TEXT("흐름 제어"),TEXT("합류"),EDirectorNodeType::Hub},
        {TEXT("캐릭터"),TEXT("기존 캐릭터 연결"),EDirectorNodeType::BindNPC},
        {TEXT("캐릭터"),TEXT("시선 지정"),EDirectorNodeType::LookAt},
        {TEXT("캐릭터"),TEXT("표정 변경"),EDirectorNodeType::Expression},
        {TEXT("카메라"),TEXT("구도 프리셋"),EDirectorNodeType::CameraPreset},
        {TEXT("카메라"),TEXT("촬영 카메라 전환"),EDirectorNodeType::CameraSwitch},
        {TEXT("대화"),TEXT("대사 출력"),EDirectorNodeType::Dialogue},
        {TEXT("게임 연동"),TEXT("레벨 시퀀스 재생"),EDirectorNodeType::Sequence},
        {TEXT("게임 연동"),TEXT("블루프린트 액션"),EDirectorNodeType::GameAction},
        {TEXT("게임 연동"),TEXT("플레이어 숨김"),EDirectorNodeType::PlayerHidden},
        {TEXT("게임 연동"),TEXT("조작 잠금"),EDirectorNodeType::InputLock},
        {TEXT("게임 연동"),TEXT("게임 HUD 숨김"),EDirectorNodeType::HUDHidden},
        {TEXT("대화"),TEXT("대사창 닫기"),EDirectorNodeType::CloseDialogue},
        {TEXT("카메라"),TEXT("카메라 복귀"),EDirectorNodeType::CameraReturn}
    };
}
