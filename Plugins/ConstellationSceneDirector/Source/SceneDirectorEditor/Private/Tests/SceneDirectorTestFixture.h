#pragma once
#include "SceneDirectorAsset.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Engine/Blueprint.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"

inline USceneDirectorAsset* MakeAnimationTestAsset()
{
    auto* BP=FKismetEditorUtilities::CreateBlueprint(ASkeletalMeshActor::StaticClass(),GetTransientPackage(),MakeUniqueObjectName(GetTransientPackage(),UBlueprint::StaticClass(),TEXT("DirectorAnimationTest")),BPTYPE_Normal);
    if(!BP)return nullptr;
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview"));
    auto* Anim=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));
    if(!Mesh||!Anim)return nullptr;
    CastChecked<ASkeletalMeshActor>(BP->GeneratedClass->GetDefaultObject())->GetSkeletalMeshComponent()->SetSkeletalMeshAsset(Mesh);
    FKismetEditorUtilities::CompileBlueprint(BP);
    auto* A=NewObject<USceneDirectorAsset>();
    for(auto Type:{EDirectorNodeType::Start,EDirectorNodeType::SpawnNPC,EDirectorNodeType::Animation,EDirectorNodeType::Camera,EDirectorNodeType::Hub,EDirectorNodeType::End})
    {FDirectorStep S;S.Type=Type;S.Role=TEXT("Heroine");S.ActorClass=BP->GeneratedClass;S.Animation=Anim;S.Duration=2;S.EditorPosition=FVector2D(A->Steps.Num()*230,0);A->Steps.Add(S);}
    A->Steps[0].NextNodes={A->Steps[1].Id};A->Steps[1].NextNodes={A->Steps[2].Id,A->Steps[3].Id};
    A->Steps[2].NextNodes={A->Steps[4].Id};A->Steps[3].NextNodes={A->Steps[4].Id};A->Steps[4].NextNodes={A->Steps[5].Id};
    A->Steps[3].Transform.SetLocation(FVector(-350,100,150));A->Steps[3].EditorPosition=FVector2D(460,220);
    A->Steps[4].EditorPosition=FVector2D(740,90);A->Steps[5].EditorPosition=FVector2D(1000,90);
    return A;
}
