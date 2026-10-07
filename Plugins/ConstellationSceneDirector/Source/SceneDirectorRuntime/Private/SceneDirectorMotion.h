#pragma once
#include "SceneDirectorAsset.h"
#include "SceneDirectorNodeTypes.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
namespace DirectorMotion
{
inline bool IsCamera(EDirectorNodeType T){return DirectorNodes::IsCamera(T);}
inline bool HasAnimation(EDirectorNodeType T){return T==EDirectorNodeType::Animation||T==EDirectorNodeType::CharacterMove;}
inline bool HasAnimation(const FDirectorStep& S){return S.Type==EDirectorNodeType::Animation||(S.Type==EDirectorNodeType::CharacterMove&&S.bPlayMoveAnimation);}
inline bool CutsCamera(const FDirectorStep& S){return (S.Type==EDirectorNodeType::CameraPreset&&S.bActivateCamera)||S.Type==EDirectorNodeType::CameraSwitch||S.Type==EDirectorNodeType::Camera||(S.Type==EDirectorNodeType::CameraMove&&S.bActivateCamera);}
inline bool Resolve(const FDirectorVectorInput& Input,const TMap<FName,FVector>& Vectors,const FVector& Current,FVector& Result,FString& Error)
{
    if(Input.Mode==EDirectorValueMode::Absolute)Result=Input.Value;
    else if(Input.Mode==EDirectorValueMode::Key)
    {
        const FVector* Value=Vectors.Find(Input.Key);
        if(!Value){Error=TEXT("Vector3 Key를 찾을 수 없습니다: ")+Input.Key.ToString();return false;}
        Result=*Value+Input.Offset+(Input.bAddCurrent?Current:FVector::ZeroVector);
    }
    else if(Input.Mode==EDirectorValueMode::Current)Result=Current+Input.Offset;
    else {Error=TEXT("유효하지 않은 Vector3 입력 방식입니다.");return false;}
    if(Result.ContainsNaN()){Error=TEXT("Vector3 값과 Offset은 유한한 숫자여야 합니다.");return false;}
    return true;
}
inline bool ValidateAnimationMesh(const USkeletalMeshComponent* Mesh,UAnimSequence* Animation,FString& Error)
{
    if(!Mesh||!Mesh->GetSkeletalMeshAsset()){Error=TEXT("대상 NPC에 스켈레탈 메시가 없습니다.");return false;}
    if(!Animation||!Animation->GetSkeleton()||Animation->GetPlayLength()<=0){Error=TEXT("재생할 애니메이션을 지정하세요. 자동 이동은 NPC의 걷기·달리기 기본값을 사용합니다.");return false;}
    if(!FMath::IsFinite(Animation->RateScale)||Animation->RateScale<=0){Error=TEXT("애니메이션 Rate Scale은 양수여야 합니다.");return false;}
    const USkeleton* AnimationSkeleton=Animation->GetSkeleton();
    const USkeleton* MeshSkeleton=Mesh->GetSkeletalMeshAsset()->GetSkeleton();
#if WITH_EDITORONLY_DATA
    const bool Compatible=AnimationSkeleton->IsCompatibleForEditor(MeshSkeleton);
#else
    const bool Compatible=AnimationSkeleton==MeshSkeleton || (MeshSkeleton &&
        (AnimationSkeleton->GetCompatibleSkeletons().Contains(TSoftObjectPtr<USkeleton>(const_cast<USkeleton*>(MeshSkeleton))) ||
         MeshSkeleton->GetCompatibleSkeletons().Contains(TSoftObjectPtr<USkeleton>(const_cast<USkeleton*>(AnimationSkeleton)))));
#endif
    if(!Compatible){Error=TEXT("NPC와 애니메이션의 스켈레톤이 호환되지 않습니다.");return false;}
    return true;
}
inline bool ValidateAnimation(UClass* Class,UAnimSequence* Animation,FString& Error)
{return ValidateAnimationMesh(AActor::GetActorClassDefaultComponent<USkeletalMeshComponent>(Class),Animation,Error);}
}
