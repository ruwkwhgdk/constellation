#include "SceneDirectorPerformance.h"
#include "SceneDirectorGaze.h"
#include "SceneDirectorNodeTypes.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
struct FDirectorPerformance::FState
{
    struct FMeshState
    {
        TWeakObjectPtr<USkeletalMeshComponent> Mesh;
        TMap<FName,float> OriginalMorphs;
        TUniquePtr<FDirectorGazeDriver> Gaze;
    };
    TMap<FName,TSharedPtr<FMeshState>> Meshes;
};
FDirectorPerformance::FDirectorPerformance():State(MakeUnique<FState>()){}
FDirectorPerformance::~FDirectorPerformance(){Reset();}
void FDirectorPerformance::Reset()
{
    for(auto& Pair:State->Meshes)if(auto* Mesh=Pair.Value->Mesh.Get())
    {for(const auto& M:Pair.Value->OriginalMorphs)Mesh->SetMorphTarget(M.Key,M.Value);Pair.Value->Gaze.Reset();}
    State->Meshes.Reset();
}
bool FDirectorPerformance::Evaluate(const TArray<FDirectorCue>& Cues,double Frame,TFunctionRef<AActor*(FName)> Resolve,FString& Error)
{
    for(auto& Pair:State->Meshes)if(auto* Mesh=Pair.Value->Mesh.Get())
    {for(const auto& M:Pair.Value->OriginalMorphs)Mesh->SetMorphTarget(M.Key,M.Value);if(Pair.Value->Gaze)Pair.Value->Gaze->Update(Mesh->GetComponentLocation()+FVector(100,0,0),0);}
    for(const auto& Cue:Cues)
    {
        const auto& S=Cue.Step;
        if((S.Type!=EDirectorNodeType::Expression&&S.Type!=EDirectorNodeType::LookAt)||Frame<Cue.StartFrame||Frame>=Cue.EndFrame)continue;
        AActor* Actor=Resolve(S.Role);if(!Actor)continue;
        const FDirectorCue* NPC=Cues.FindByPredicate([&](const FDirectorCue& C){return DirectorNodes::IsNPC(C.Step.Type)&&C.Step.Role==S.Role;});
        const auto* Profile=NPC?NPC->Step.Profile.Get():nullptr;
        if(!Profile){Error=TEXT("연기 프로필이 없습니다: ")+S.Role.ToString();return false;}
        auto* Mesh=Actor->FindComponentByClass<USkeletalMeshComponent>();
        if(!Mesh||!Mesh->GetSkeletalMeshAsset()||(!Profile->MeshComponent.IsNone()&&Mesh->GetFName()!=Profile->MeshComponent)){Error=TEXT("연기 메시를 찾을 수 없습니다: ")+S.Role.ToString();return false;}
        auto& Entry=State->Meshes.FindOrAdd(S.Role);
        if(Entry&&Entry->Mesh!=Mesh){Entry->Gaze.Reset();Entry.Reset();}
        if(!Entry){Entry=MakeShared<FState::FMeshState>();Entry->Mesh=Mesh;}
        const float Ramp=S.BlendSeconds>0?FMath::Clamp(float(FMath::Min(Frame-Cue.StartFrame,Cue.EndFrame-Frame)/(S.BlendSeconds*30)),0.f,1.f):1.f;
        const float Weight=S.Strength*Ramp;
        if(S.Type==EDirectorNodeType::Expression)
        {
            const auto* Preset=Profile->Expressions.Find(S.ExpressionKey);if(!Preset){Error=TEXT("표정 프리셋을 찾을 수 없습니다.");return false;}
            for(const auto& M:Preset->Morphs)
            {
                if(!Mesh->GetSkeletalMeshAsset()->FindMorphTarget(M.Key)){Error=TEXT("실제 캐릭터에 표정 모프가 없습니다: ")+M.Key.ToString();return false;}
                if(!Entry->OriginalMorphs.Contains(M.Key))Entry->OriginalMorphs.Add(M.Key,Mesh->GetMorphTarget(M.Key));
                Mesh->SetMorphTarget(M.Key,FMath::Lerp(Entry->OriginalMorphs[M.Key],M.Value,Weight));
            }
        }
        else
        {
            AActor* Target=Resolve(S.TargetRole);if(!Target)continue;
            if(!Entry->Gaze){Entry->Gaze=MakeUnique<FDirectorGazeDriver>();if(!Entry->Gaze->Initialize(Mesh,Profile->HeadBone,Profile->HeadForwardAxis,Error)){Entry->Gaze.Reset();return false;}}
            const auto* TargetNPC=Cues.FindByPredicate([&](const FDirectorCue& C){return DirectorNodes::IsNPC(C.Step.Type)&&C.Step.Role==S.TargetRole;});
            const float Height=TargetNPC&&TargetNPC->Step.Profile?TargetNPC->Step.Profile->AimHeight:150;
            Entry->Gaze->Update(Target->GetActorLocation()+FVector(0,0,Height),Weight);
        }
    }
    return true;
}
