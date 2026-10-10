#pragma once
#include "SceneDirectorAsset.h"
namespace DirectorNodes
{
inline bool IsScreenEffect(EDirectorNodeType T){return T==EDirectorNodeType::Eyelids||T==EDirectorNodeType::Vision||T==EDirectorNodeType::ClearVision;}
inline bool IsReturn(EDirectorNodeType T){return T==EDirectorNodeType::GameplayReturn||T==EDirectorNodeType::CameraReturn;}
inline bool IsNPC(EDirectorNodeType T){return T==EDirectorNodeType::SpawnNPC||T==EDirectorNodeType::BindNPC;}
inline bool IsCamera(EDirectorNodeType T){return T==EDirectorNodeType::Camera||T==EDirectorNodeType::CameraMove||T==EDirectorNodeType::CameraPreset||T==EDirectorNodeType::CameraSwitch;}
inline bool UsesNPC(EDirectorNodeType T){return T==EDirectorNodeType::Visibility||T==EDirectorNodeType::Animation||T==EDirectorNodeType::CharacterMove||T==EDirectorNodeType::Camera||T==EDirectorNodeType::CameraPreset||T==EDirectorNodeType::LookAt||T==EDirectorNodeType::Expression;}
inline bool IsCue(EDirectorNodeType T){return IsScreenEffect(T)||T==EDirectorNodeType::PlayerHidden||T==EDirectorNodeType::InputLock||T==EDirectorNodeType::HUDHidden||T==EDirectorNodeType::CameraReturn||T==EDirectorNodeType::CloseDialogue||T==EDirectorNodeType::SetInt||T==EDirectorNodeType::SetBool||T==EDirectorNodeType::GameAction||T==EDirectorNodeType::CinematicMode||T==EDirectorNodeType::GameplayReturn||T==EDirectorNodeType::LookAt||T==EDirectorNodeType::Expression||T==EDirectorNodeType::Dialogue;}
}
