#include "SceneDirectorSequence.h"
#include "Animation/AnimSequence.h"
#include "Bindings/MovieSceneSpawnableActorBinding.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorNodeTypes.h"
#include "SceneDirectorMotion.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "MovieSceneBindingReferences.h"
#include "MovieScenePossessable.h"
#include "MovieSceneSpawnable.h"
#include "EntitySystem/MovieSceneSharedPlaybackState.h"
#include "Evaluation/MovieSceneEvaluationState.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Tracks/MovieSceneSpawnTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Sections/MovieSceneAudioSection.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Components/ActorComponent.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/Actor.h"

FMovieSceneBindingResolveResult UDirectorSequenceBinding::ResolveBinding(const FMovieSceneBindingResolveParams&,int32,TSharedRef<const UE::MovieScene::FSharedPlaybackState> State) const
{
    FMovieSceneBindingResolveResult Result;
    if(auto* Cache=State->FindCapability<FMovieSceneEvaluationState>())
        for(auto Weak:Cache->FindBoundObjects(RootBinding,MovieSceneSequenceID::Root,State))
            if(auto* Object=Weak.Get())
            {
                if(!bComponent){Result.Objects.Add(Object);continue;}
                if(auto* Actor=Cast<AActor>(Object))
                {
                    TArray<UActorComponent*> Matches;for(auto* C:Actor->GetComponents())if(C->IsA(ObjectClass))Matches.Add(C);
                    if(Matches.Num()==1)Result.Objects.Add(Matches[0]);
                    else for(auto* C:Matches)if(C->GetFName()==ComponentName){Result.Objects.Add(C);break;}
                }
            }
    return Result;
}
namespace DirectorSequence
{
static UMovieSceneSpawnableActorBinding* NativeSpawnable(const ULevelSequence& Sequence,FGuid ID)
{
    if(const auto* Refs=Sequence.GetBindingReferences())
    {
        auto Entries=Refs->GetReferences(ID);
        if(Entries.Num()==1&&Entries[0].CustomBinding&&Entries[0].CustomBinding->GetClass()==UMovieSceneSpawnableActorBinding::StaticClass())return Cast<UMovieSceneSpawnableActorBinding>(Entries[0].CustomBinding);
    }
    return nullptr;
}
static AActor* OriginalTemplate(const ULevelSequence& Sequence,FGuid ID)
{
    if(auto* S=Sequence.GetMovieScene()->FindSpawnable(ID))return Cast<AActor>(S->GetObjectTemplate());
    if(auto* S=NativeSpawnable(Sequence,ID))return Cast<AActor>(S->GetObjectTemplate());
    return nullptr;
}
void RefreshRoles(FDirectorStep& Step)
{
#if WITH_EDITOR
    if(Step.Type!=EDirectorNodeType::Sequence)return;
    auto* Movie=Step.SourceSequence?Step.SourceSequence->GetMovieScene():nullptr;
    if(!Movie){Step.SequenceRoles.Reset();Step.SequenceComponents.Reset();return;}
    const auto Old=Step.SequenceRoles;Step.SequenceRoles.Reset();Step.SequenceComponents.Reset();
    for(const auto& B:static_cast<const UMovieScene*>(Movie)->GetBindings())
    {
        UClass* Class=nullptr;bool Spawnable=false;FString Label;
        if(auto* Spawn=Movie->FindSpawnable(B.GetObjectGuid())){if(Spawn->GetObjectTemplate())Class=Spawn->GetObjectTemplate()->GetClass();Spawnable=true;Label=Spawn->GetName();}
        else if(auto* Possess=Movie->FindPossessable(B.GetObjectGuid()))
        {
            Class=const_cast<UClass*>(Possess->GetPossessedObjectClass());Label=Possess->GetName();
            if(Possess->GetParent().IsValid())
            {
                FDirectorSequenceComponent C;C.Binding=B.GetObjectGuid();C.Parent=Possess->GetParent();C.Name=FName(*Possess->GetName());
                if(Class&&Class->IsChildOf(UActorComponent::StaticClass()))C.ComponentClass=Class;
                Step.SequenceComponents.Add(C);continue;
            }
        }
        if(auto* Template=OriginalTemplate(*Step.SourceSequence,B.GetObjectGuid())){Spawnable=true;Class=Template->GetClass();}
        FDirectorSequenceRole Role;Role.Binding=B.GetObjectGuid();Role.Label=Label;Role.SourceClass=Class;
        Role.Target=Spawnable?EDirectorSequenceTarget::Original:(Class&&Class->IsChildOf(ACameraActor::StaticClass())?EDirectorSequenceTarget::Camera:EDirectorSequenceTarget::NPC);
        if(const auto* Prior=Old.FindByPredicate([&](const FDirectorSequenceRole& R){return R.Binding==Role.Binding;})){Role.Target=Prior->Target;Role.Key=Prior->Key;}
        Step.SequenceRoles.Add(Role);
    }
#endif
}
bool HasCamera(const FDirectorStep& S){return S.Type==EDirectorNodeType::Sequence&&S.SourceSequence&&S.SourceSequence->GetMovieScene()&&S.SourceSequence->GetMovieScene()->GetCameraCutTrack()!=nullptr;}
bool UsesNPC(const FDirectorStep& S,FName Key){return S.Type==EDirectorNodeType::Sequence&&S.SequenceRoles.ContainsByPredicate([&](const FDirectorSequenceRole& R){return R.Target==EDirectorSequenceTarget::NPC&&R.Key==Key;});}
bool UsesCamera(const FDirectorStep& S,FName Key){return S.Type==EDirectorNodeType::Sequence&&S.SequenceRoles.ContainsByPredicate([&](const FDirectorSequenceRole& R){return R.Target==EDirectorSequenceTarget::Camera&&R.Key==Key;});}
static UClass* TargetClass(const FDirectorSequenceRole& R,const USceneDirectorAsset& Asset)
{
    if(R.Target==EDirectorSequenceTarget::Camera){for(const auto& C:Asset.Cameras)if(C.Key==R.Key&&C.ImportedTemplate)return C.ImportedTemplate->GetClass();return ACameraActor::StaticClass();}
    if(R.Target==EDirectorSequenceTarget::Original)return R.SourceClass;
    for(const auto& S:Asset.Steps)if(DirectorNodes::IsNPC(S.Type)&&S.Role==R.Key)return S.ActorClass;
    return nullptr;
}
bool Validate(const FDirectorStep& S,const USceneDirectorAsset& Asset,double& Seconds,FString& Error)
{
    auto Fail=[&](const FString& M){Error=TEXT("시퀀스 재생: ")+M;return false;};
    auto* Movie=S.SourceSequence?S.SourceSequence->GetMovieScene():nullptr;
    if(!Movie)return Fail(TEXT("레벨 시퀀스를 선택하세요."));
    if(!FMath::IsFinite(S.SequenceSpeed)||S.SequenceSpeed<=0)return Fail(TEXT("재생 속도는 0보다 커야 합니다."));
    const auto Range=Movie->GetPlaybackRange();const auto Rate=Movie->GetTickResolution();
    if(!Range.HasLowerBound()||!Range.HasUpperBound()||Rate.Numerator<=0||Rate.Denominator<=0)return Fail(TEXT("원본의 재생 범위와 틱 해상도를 확인하세요."));
    Seconds=(Range.GetUpperBoundValue().Value-Range.GetLowerBoundValue().Value)/Rate.AsDecimal()/S.SequenceSpeed;
    if(!FMath::IsFinite(Seconds)||Seconds<1.0/30.0-1.e-8||Seconds>3600)return Fail(TEXT("재생 시간은 1/30초~3600초 범위여야 합니다."));
    // These tracks have no arbitrary event/Blueprint execution during editor preview or prefix seeking.
    const TSet<FName> Allowed={TEXT("MovieScene3DAttachTrack"),TEXT("MovieSceneCameraShakeTrack"),TEXT("MovieScene3DTransformTrack"),TEXT("MovieSceneSkeletalAnimationTrack"),TEXT("MovieSceneSpawnTrack"),TEXT("MovieSceneCameraCutTrack"),TEXT("MovieSceneFloatTrack"),TEXT("MovieSceneDoubleTrack"),TEXT("MovieSceneBoolTrack"),TEXT("MovieSceneIntegerTrack"),TEXT("MovieSceneColorTrack"),TEXT("MovieSceneFloatVectorTrack"),TEXT("MovieSceneDoubleVectorTrack"),TEXT("MovieSceneVisibilityTrack"),TEXT("MovieSceneAudioTrack")};
    auto CheckTrack=[&](const UMovieSceneTrack* Track)
    {
        if(!Track||!Allowed.Contains(Track->GetClass()->GetFName()))return Fail(TEXT("아직 지원하지 않는 트랙: ")+GetNameSafe(Track?Track->GetClass():nullptr));
        if(Track->ConditionContainer.Condition)return Fail(TEXT("원본 트랙 조건은 지원하지 않습니다. 그래프 조건 분기를 사용하세요."));
        for(auto* Section:Track->GetAllSections())
        {
            const auto* Row=Track->FindTrackRowMetadata(Section->GetRowIndex());
            if(Section->ConditionContainer.Condition||(Row&&Row->ConditionContainer.Condition))return Fail(TEXT("원본 섹션/행 조건은 지원하지 않습니다. 그래프 조건 분기를 사용하세요."));
        }
        return true;
    };
    for(const auto* Track:Movie->GetTracks())if(!CheckTrack(Track))return false;
    if(Movie->GetCameraCutTrack()&&!CheckTrack(Movie->GetCameraCutTrack()))return false;
    TSet<FGuid> IDs;TSet<FName> NPCTargets,CameraTargets;
    for(const auto& R:S.SequenceRoles)
    {
        if(uint8(R.Target)>uint8(EDirectorSequenceTarget::Camera))return Fail(TEXT("연결 방식을 확인하세요."));
        if(IDs.Contains(R.Binding)||!Movie->FindBinding(R.Binding))return Fail(TEXT("역할 목록이 원본과 다릅니다. 원본을 다시 선택하세요."));IDs.Add(R.Binding);
        if(!R.SourceClass||!R.SourceClass->IsChildOf(AActor::StaticClass()))return Fail(TEXT("Actor 역할만 지원합니다: ")+R.Label);
        if(R.Target==EDirectorSequenceTarget::Original){if(!OriginalTemplate(*S.SourceSequence,R.Binding))return Fail(TEXT("기존 Actor 역할은 NPC/카메라 Key에 연결하세요: ")+R.Label);}
        else
        {
            if(R.Key.IsNone())return Fail(TEXT("대상 Key를 입력하세요: ")+R.Label);
            UClass* Class=TargetClass(R,Asset);if(!Class||!Class->IsChildOf(R.SourceClass))return Fail(TEXT("원본 역할과 대상 BP 클래스가 호환되지 않습니다: ")+R.Label);
            if(R.Target==EDirectorSequenceTarget::Camera&&!Asset.Cameras.ContainsByPredicate([&](const FDirectorCameraEntry& C){return C.Key==R.Key;}))return Fail(TEXT("카메라 목록에 Key를 등록하세요: ")+R.Key.ToString());
            auto& Targets=R.Target==EDirectorSequenceTarget::NPC?NPCTargets:CameraTargets;if(Targets.Contains(R.Key))return Fail(TEXT("여러 원본 역할을 같은 대상에 연결할 수 없습니다."));Targets.Add(R.Key);
        }
    }
    for(const auto& C:S.SequenceComponents)
    {
        auto* Role=S.SequenceRoles.FindByPredicate([&](const FDirectorSequenceRole& R){return R.Binding==C.Parent;});
        if(!Role||!C.ComponentClass||IDs.Contains(C.Binding)||!Movie->FindPossessable(C.Binding))return Fail(TEXT("Actor 바로 아래의 컴포넌트 바인딩만 지원합니다."));IDs.Add(C.Binding);
        if(Role->Target==EDirectorSequenceTarget::Original)
            if(const auto* Refs=S.SourceSequence->GetBindingReferences())for(const auto& Ref:Refs->GetReferences(C.Binding))
                if(Ref.CustomBinding)return Fail(TEXT("원본 Spawnable의 동적 컴포넌트 바인딩은 지원하지 않습니다."));
        if(Role->Target!=EDirectorSequenceTarget::Original)
        {
            TArray<const UActorComponent*> Components;AActor::GetActorClassDefaultComponents(TargetClass(*Role,Asset),C.ComponentClass,Components);
            if(Components.Num()!=1&&Components.FilterByPredicate([&](const UActorComponent* Comp){return Comp->GetFName()==C.Name;}).Num()!=1)return Fail(TEXT("대상 컴포넌트를 하나로 정할 수 없습니다: ")+C.Name.ToString());
        }
    }
    if(IDs.Num()!=static_cast<const UMovieScene*>(Movie)->GetBindings().Num())return Fail(TEXT("역할 목록을 갱신하세요. 원본을 다시 선택하고 생성하세요."));
    for(const auto& B:static_cast<const UMovieScene*>(Movie)->GetBindings())for(const auto* Track:B.GetTracks())
    {
        if(!CheckTrack(Track))return false;
        if(Track->IsA<UMovieSceneSkeletalAnimationTrack>())
        {
            FGuid Root=B.GetObjectGuid();if(auto* C=S.SequenceComponents.FindByPredicate([&](const FDirectorSequenceComponent& Entry){return Entry.Binding==Root;}))Root=C->Parent;
            auto* R=S.SequenceRoles.FindByPredicate([&](const FDirectorSequenceRole& Role){return Role.Binding==Root;});
            if(!R)return Fail(TEXT("애니메이션 역할 연결을 확인하세요."));
            const USkeletalMeshComponent* Mesh=nullptr;TArray<const USkeletalMeshComponent*> Meshes;
            if(R->Target==EDirectorSequenceTarget::Original)
            {
                if(auto* Template=OriginalTemplate(*S.SourceSequence,R->Binding))
                    for(auto* Comp:Template->GetComponents())if(auto* Skeletal=Cast<USkeletalMeshComponent>(Comp))Meshes.Add(Skeletal);
            }
            else AActor::GetActorClassDefaultComponents<USkeletalMeshComponent>(TargetClass(*R,Asset),Meshes);
            if(const auto* Component=S.SequenceComponents.FindByPredicate([&](const FDirectorSequenceComponent& C){return C.Binding==B.GetObjectGuid();}))
            {
                if(!Component->ComponentClass->IsChildOf(USkeletalMeshComponent::StaticClass()))return Fail(TEXT("애니메이션 트랙은 스켈레탈 메시 컴포넌트에 연결하세요."));
                Meshes.RemoveAll([&](const USkeletalMeshComponent* Candidate){return !Candidate->IsA(Component->ComponentClass);});
                for(auto* Candidate:Meshes)if(Candidate->GetFName()==Component->Name)Mesh=Candidate;
            }
            if(!Mesh&&Meshes.Num()==1)Mesh=Meshes[0];
            for(auto* Section:Track->GetAllSections())if(auto* Anim=Cast<UMovieSceneSkeletalAnimationSection>(Section))
                if(!DirectorMotion::ValidateAnimationMesh(Mesh,Cast<UAnimSequence>(Anim->Params.Animation),Error))return false;
        }
    }
    return true;
}
bool Add(ULevelSequence& Root,const FDirectorStep& S,int32 Begin,int32 End,const TMap<FName,FGuid>& NPCs,const TMap<FName,FGuid>& Cameras,FString& Error)
{
    auto* Copy=DuplicateObject<ULevelSequence>(S.SourceSequence,&Root);Copy->ClearFlags(RF_Public|RF_Standalone);
    auto* Movie=Copy->GetMovieScene();
#if WITH_EDITORONLY_DATA
    Movie->SetReadOnly(false);
#endif
    auto Bind=[&](FGuid Source,FGuid RootID,UClass* Class,bool Component,FName Name)
    {
        auto* Binding=NewObject<UDirectorSequenceBinding>(Movie);Binding->RootBinding=RootID;Binding->ObjectClass=Class;Binding->bComponent=Component;Binding->ComponentName=Name;
        Copy->UMovieSceneSequence::GetBindingReferences()->RemoveBinding(Source);Copy->UMovieSceneSequence::GetBindingReferences()->AddBinding(Source,Binding);
    };
    for(const auto& R:S.SequenceRoles)if(R.Target!=EDirectorSequenceTarget::Original)
    {
        const FGuid RootID=R.Target==EDirectorSequenceTarget::NPC?NPCs.FindRef(R.Key):Cameras.FindRef(R.Key);
        if(!RootID.IsValid()){Error=TEXT("시퀀스 역할의 부모 바인딩이 없습니다: ")+R.Key.ToString();return false;}
        if(Movie->FindSpawnable(R.Binding))
        {
            const FMovieSceneBinding Saved=*Movie->FindBinding(R.Binding);Movie->RemoveSpawnable(R.Binding);
            FMovieScenePossessable P(R.Label,R.SourceClass);P.SetGuid(R.Binding);Movie->AddPossessable(P,Saved);
        }
        if(auto* Track=Movie->FindTrack<UMovieSceneSpawnTrack>(R.Binding))Movie->RemoveTrack(*Track);
        // Register the cross-sequence dependency so late spawn/despawn invalidates child bindings too.
        if(auto* P=Movie->FindPossessable(R.Binding))P->SetSpawnableObjectBindingID(UE::MovieScene::FRelativeObjectBindingID(RootID,MovieSceneSequenceID::Root,1));
        Bind(R.Binding,RootID,R.SourceClass,false,NAME_None);
        for(const auto& C:S.SequenceComponents)if(C.Parent==R.Binding)Bind(C.Binding,RootID,C.ComponentClass,true,C.Name);
    }
    for(int32 I=0;I<Movie->GetSpawnableCount();++I)Movie->GetSpawnable(I).SetSpawnOwnership(ESpawnOwnership::InnerSequence);
    TArray<UMovieSceneTrack*> CopiedTracks;
    for(auto* T:Movie->GetTracks())CopiedTracks.AddUnique(T);
    if(Movie->GetCameraCutTrack())CopiedTracks.AddUnique(Movie->GetCameraCutTrack());
    for(const auto& B:static_cast<const UMovieScene*>(Movie)->GetBindings())
    {
        if(auto* Spawn=NativeSpawnable(*Copy,B.GetObjectGuid()))Spawn->SpawnOwnership=ESpawnOwnership::InnerSequence;
        for(auto* T:B.GetTracks())CopiedTracks.AddUnique(T);
    }
    const auto SourceRange=Movie->GetPlaybackRange();
    for(auto* T:CopiedTracks)
    {
        T->EvalOptions.bEvalNearestSection=false;T->EvalOptions.bEvaluateInPreroll=false;T->EvalOptions.bEvaluateInPostroll=false;
        const auto Sections=T->GetAllSections();
        for(auto* Sec:Sections)
        {
            Sec->SetIsLocked(false);
            const auto Intersection=TRange<FFrameNumber>::Intersection(Sec->GetRange(),SourceRange);
            if(Intersection.IsEmpty()){T->RemoveSection(*Sec);continue;}
            // Native trim methods retain audio/animation phase when the source play range starts mid-section.
            if(!Sec->GetRange().HasLowerBound()||Sec->GetInclusiveStartFrame()<SourceRange.GetLowerBoundValue())Sec->TrimSection(FQualifiedFrameTime(SourceRange.GetLowerBoundValue(),Movie->GetTickResolution()),true,false);
            if(!Sec->GetRange().HasUpperBound()||Sec->GetExclusiveEndFrame()>SourceRange.GetUpperBoundValue())Sec->TrimSection(FQualifiedFrameTime(SourceRange.GetUpperBoundValue(),Movie->GetTickResolution()),false,false);
            if(Sec->GetRange()!=Intersection){Error=TEXT("시퀀스 원본 재생 범위로 섹션을 제한할 수 없습니다.");return false;}
            Sec->SetPreRollFrames(0);Sec->SetPostRollFrames(0);
            if(auto* Audio=Cast<UMovieSceneAudioSection>(Sec))Audio->SetPlayUntilFinished(false);
            if(auto* Anim=Cast<UMovieSceneSkeletalAnimationSection>(Sec)){Anim->Params.bForceCustomMode=true;Anim->Params.bSkipAnimNotifiers=true;}
        }
        T->MarkAsChanged();
    }
    auto* Track=Root.GetMovieScene()->AddTrack<UMovieSceneSubTrack>();
    auto* Section=Track->AddSequence(Copy,Begin,End-Begin);Section->Parameters.TimeScale.Set(S.SequenceSpeed);
    Section->Parameters.Flags=EMovieSceneSubSectionFlags::OverrideRestoreState;Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;
    return true;
}
}
