#include "SceneDirectorCompiler.h"
#include "SceneDirectorVision.h"
#include "SceneDirectorNodeTypes.h"
#include "Sound/SoundBase.h"
#include "SceneDirectorMotion.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorAsset.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneVisibilityTrack.h"
#include "Sections/MovieSceneVisibilitySection.h"
#include "Tracks/MovieSceneFadeTrack.h"
#include "Sections/MovieSceneFadeSection.h"
#include "MovieSceneSpawnable.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Tracks/MovieSceneSpawnTrack.h"
#include "Sections/MovieSceneSpawnSection.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieSceneCameraCutSection.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "Channels/MovieSceneChannelProxy.h"

#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"

bool FSceneDirectorCompiler::Schedule(const USceneDirectorAsset& Asset,FDirectorSchedule& Out,FString& Error)
{
    Out=FDirectorSchedule(); Error.Reset();
    auto Fail=[&](const FString& Message){Error=Message;Out=FDirectorSchedule();return false;};
    if(Asset.FormatVersion!=1 && Asset.FormatVersion!=2 && Asset.FormatVersion!=3)return Fail(TEXT("지원하지 않는 데이터 버전입니다."));
    const int32 N=Asset.Steps.Num();
    TMap<FGuid,int32> IDs; TMap<FName,int32> Roles;
    TArray<TArray<int32>> Parents,Children;Parents.SetNum(N);Children.SetNum(N);
    int32 Start=INDEX_NONE,End=INDEX_NONE;
    for(int32 I=0;I<N;++I)
    {
        const auto& S=Asset.Steps[I];
        if(!S.Id.IsValid()||IDs.Contains(S.Id))return Fail(TEXT("노드 ID가 중복되거나 비어 있습니다."));
        IDs.Add(S.Id,I);
        if(S.Type==EDirectorNodeType::Start){if(Start!=INDEX_NONE)return Fail(TEXT("시작은 하나만 배치하세요."));Start=I;}
        if(S.Type==EDirectorNodeType::End){if(End!=INDEX_NONE)return Fail(TEXT("종료는 하나만 배치하세요."));End=I;}
        if(uint8(S.Type)>uint8(EDirectorNodeType::ClearVision))return Fail(TEXT("알 수 없는 노드 종류입니다."));
        if(DirectorNodes::IsNPC(S.Type))
        {
            if(!S.ActorClass||S.ActorClass->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists))return Fail(TEXT("NPC 추가: 생성 가능한 캐릭터 BP를 선택하세요."));
            if(S.Role.IsNone()||Roles.Contains(S.Role))return Fail(TEXT("NPC String Key는 비어 있거나 중복될 수 없습니다. 대소문자는 구분하지 않습니다."));
            if(S.ImportedTemplate&&S.ImportedTemplate->GetClass()!=S.ActorClass){return Fail(TEXT("NPC BP를 변경했다면 원본 생성 템플릿을 초기화하세요."));}
            Roles.Add(S.Role,I);
        }
        if(S.Type==EDirectorNodeType::Camera || DirectorNodes::IsNPC(S.Type))
            if(!S.Transform.IsValid()||S.Transform.GetScale3D().GetAbsMin()<KINDA_SMALL_NUMBER)return Fail(TEXT("위치·회전·스케일이 유효하지 않습니다."));
        if(S.Type==EDirectorNodeType::Camera && (!FMath::IsFinite(S.FieldOfView)||S.FieldOfView<10||S.FieldOfView>170))return Fail(TEXT("카메라 화각은 10~170도여야 합니다."));
    }
    if(Start==INDEX_NONE||End==INDEX_NONE)return Fail(TEXT("시작과 종료를 하나씩 배치하세요."));
    for(int32 I=0;I<N;++I)
    {
        for(FGuid Next:Asset.Steps[I].Successors())
        {
            const int32* J=IDs.Find(Next);
            if(!J||Children[I].Contains(*J))return Fail(TEXT("연결 대상이 없거나 연결이 중복되었습니다."));
            Children[I].Add(*J);Parents[*J].Add(I);
        }
        if(I==End && Children[I].Num())return Fail(TEXT("종료 뒤에는 연결할 수 없습니다."));
        if(I!=End && !Children[I].Num())return Fail(TEXT("다음 노드를 연결하세요. 모든 분기는 종료로 이어져야 합니다."));
    }
    if(Parents[Start].Num())return Fail(TEXT("시작 앞에는 연결할 수 없습니다."));
    TArray<int32> Remaining,Queue;
    for(int32 I=0;I<N;++I){Remaining.Add(Parents[I].Num());if(!Remaining[I])Queue.Add(I);}
    if(Queue.Num()!=1||Queue[0]!=Start)return Fail(TEXT("시작에서 연결되지 않은 노드가 있습니다."));
    for(int32 Cursor=0;Cursor<Queue.Num();++Cursor)
    {int32 I=Queue[Cursor];Out.Order.Add(I);for(int32 J:Children[I])if(--Remaining[J]==0)Queue.Add(J);}
    if(Out.Order.Num()!=N)return Fail(TEXT("순환 연결은 지원하지 않습니다."));
    TSet<FName> VariableKeys;for(const auto& V:Asset.BoolVariables){if(V.Key.IsNone()||VariableKeys.Contains(V.Key))return Fail(TEXT("공용 변수 이름이 비어 있거나 중복됩니다."));VariableKeys.Add(V.Key);}
    for(const auto& V:Asset.IntVariables){if(VariableKeys.Contains(V.Key))return Fail(TEXT("Boolean/Integer 변수 이름을 중복해서 사용할 수 없습니다."));}
    TSet<FName> IntKeys;for(const auto& V:Asset.IntVariables){if(V.Key.IsNone()||IntKeys.Contains(V.Key))return Fail(TEXT("Integer 변수 Key가 비어 있거나 중복됩니다."));IntKeys.Add(V.Key);}
    for(const auto& S:Asset.Steps)if(S.Type==EDirectorNodeType::SetInt&&!IntKeys.Contains(S.IntKey))return Fail(TEXT("Integer 설정 노드의 변수 Key를 확인하세요."));
    TSet<FName> ActionKeys;
    for(const auto& A:Asset.Actions)
    {
        if(A.Key.IsNone()||ActionKeys.Contains(A.Key))return Fail(TEXT("액션 목록: Key는 비어 있거나 중복될 수 없습니다."));
        if(!A.ActionClass||A.ActionClass->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists))return Fail(TEXT("액션 목록: 실행 가능한 액션 BP를 등록하세요: ")+A.Key.ToString());
        ActionKeys.Add(A.Key);
    }
    TSet<FName> ObjectKeys;
    for(const auto& O:Asset.Objects)
    {
        if(O.Key.IsNone()||ObjectKeys.Contains(O.Key))return Fail(TEXT("오브젝트 목록: Key가 비어 있거나 중복됩니다."));
        ObjectKeys.Add(O.Key);
    }
    for(const auto& S:Asset.Steps)if(S.Type==EDirectorNodeType::BindNPC&&S.ActorSource==EDirectorActorSource::Object&&!ObjectKeys.Contains(S.ObjectKey))return Fail(TEXT("등록 오브젝트 Key를 확인하세요: ")+S.ObjectKey.ToString());
    for(const auto& C:Asset.Cameras)if(!C.ObjectKey.IsNone()&&!ObjectKeys.Contains(C.ObjectKey))return Fail(TEXT("카메라의 등록 오브젝트 Key를 확인하세요: ")+C.ObjectKey.ToString());
    TMap<FName,FVector> Vectors;TMap<FName,FDirectorCameraEntry> Cameras;
    for(const auto& V:Asset.Vectors)
    {
        if(V.Key.IsNone()||Vectors.Contains(V.Key)||V.Value.ContainsNaN())return Fail(TEXT("Vector3 목록: Key가 비어 있거나 중복되었거나 값이 유효하지 않습니다."));
        Vectors.Add(V.Key,V.Value);
    }
    for(const auto& C:Asset.Cameras)
    {
        if(C.Key.IsNone()||Cameras.Contains(C.Key)||!C.Transform.IsValid()||!FMath::IsFinite(C.FieldOfView)||C.FieldOfView<10||C.FieldOfView>170)return Fail(TEXT("카메라 목록: Key, 위치·회전, 화각을 확인하세요."));
        Cameras.Add(C.Key,C);
    }
    for(const auto& S:Asset.Steps)if(DirectorMotion::IsCamera(S.Type)&&!Cameras.Contains(S.EffectiveCameraKey()))
    {FDirectorCameraEntry C;C.Key=S.EffectiveCameraKey();C.Transform=S.Transform;C.FieldOfView=S.FieldOfView;Cameras.Add(C.Key,C);}
    Out.StartFrames.SetNumZeroed(N);Out.FinishFrames.SetNumZeroed(N);Out.BranchFinishFrames.SetNumZeroed(N);
    Out.FromPoses.SetNum(N);Out.ToPoses.SetNum(N);Out.EffectiveSpeeds.SetNumZeroed(N);Out.Animations.SetNumZeroed(N);
    TArray<TSet<int32>> Ancestors;Ancestors.SetNum(N);
    for(int32 I:Out.Order)for(int32 P:Parents[I]){Ancestors[I].Append(Ancestors[P]);Ancestors[I].Add(P);}
    // Same-target writers must have an explicit order, even when parallel branches happen to have different lengths.
    for(int32 I=0;I<N;++I)for(int32 J=I+1;J<N;++J)
    {
        const auto& S=Asset.Steps[I];const auto& T=Asset.Steps[J];
        const bool Same=(S.Type==EDirectorNodeType::CharacterMove&&T.Type==S.Type&&S.Role==T.Role)||(DirectorMotion::IsCamera(S.Type)&&S.Type!=EDirectorNodeType::CameraSwitch&&DirectorMotion::IsCamera(T.Type)&&T.Type!=EDirectorNodeType::CameraSwitch&&S.EffectiveCameraKey()==T.EffectiveCameraKey());
        if(S.Type==EDirectorNodeType::SetInt&&T.Type==S.Type&&S.IntKey==T.IntKey&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I))return Fail(TEXT("같은 Integer 변수 설정은 순서대로 연결하세요."));
        if(S.Type==EDirectorNodeType::GameAction&&T.Type==S.Type&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I))return Fail(TEXT("게임 액션은 순서대로 연결하세요. 병렬 액션은 실행 순서가 불명확합니다."));
        if(Same&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I))return Fail(TEXT("동일 NPC/카메라를 변경하는 노드는 순서대로 연결하세요."));
    }
    for(int32 I:Out.Order)
    {
        const auto& S=Asset.Steps[I];int32 Begin=0,Outstanding=0;double Seconds=0;
        const bool Barrier=Parents[I].Num()>1||S.Type==EDirectorNodeType::Hub||S.Type==EDirectorNodeType::End||S.Type==EDirectorNodeType::Condition||(S.Type==EDirectorNodeType::Dialogue&&!S.Choices.IsEmpty());
        for(int32 P:Parents[I])
        {
            Outstanding=FMath::Max(Outstanding,Out.BranchFinishFrames[P]);
            Begin=FMath::Max(Begin,Barrier?Out.BranchFinishFrames[P]:(Asset.Steps[P].bWaitForCompletion?Out.FinishFrames[P]:Out.StartFrames[P]));
        }
        Out.StartFrames[I]=Begin;
        if(S.Type==EDirectorNodeType::GameAction)
        {
            if(!ActionKeys.Contains(S.ActionKey))return Fail(TEXT("등록되지 않은 액션 Key: ")+S.ActionKey.ToString());
            if(!FMath::IsFinite(S.ActionParameters.Value))return Fail(TEXT("액션 수치는 유한한 값이어야 합니다."));
            if(!S.ActionTarget.IsNone())
            {const int32* Target=Roles.Find(S.ActionTarget);if(!Target||!Ancestors[I].Contains(*Target))return Fail(TEXT("액션 대상 NPC를 먼저 연결하세요: ")+S.ActionTarget.ToString());}
        }
        if(S.Type==EDirectorNodeType::Sequence)
        {
            if(!DirectorSequence::Validate(S,Asset,Seconds,Error))return Fail(Error);
            for(const auto& Role:S.SequenceRoles)
            {
                if(Role.Target==EDirectorSequenceTarget::NPC){const int32* Target=Roles.Find(Role.Key);if(!Target||!Ancestors[I].Contains(*Target))return Fail(TEXT("시퀀스 대상 NPC를 먼저 연결하세요: ")+Role.Key.ToString());}
                if(Role.Target==EDirectorSequenceTarget::Camera)
                {bool Found=false;for(int32 P:Ancestors[I])if(DirectorNodes::IsCamera(Asset.Steps[P].Type)&&Asset.Steps[P].EffectiveCameraKey()==Role.Key)Found=true;if(!Found)return Fail(TEXT("시퀀스 대상 카메라를 앞선 카메라 노드에서 준비하세요: ")+Role.Key.ToString());}
            }
        }
        const int32* Spawn=Roles.Find(S.Role);
        if(DirectorNodes::UsesNPC(S.Type)&&!(S.Type==EDirectorNodeType::Camera&&!S.bLookAtTarget))
            if(!Spawn||!Ancestors[I].Contains(*Spawn))return Fail(TEXT("대상 NPC를 먼저 생성한 뒤 이 노드에 연결하세요."));
        if(S.Type==EDirectorNodeType::LookAt || (S.Type==EDirectorNodeType::CameraPreset&&S.Framing==EDirectorFraming::OverShoulder))
        {
            const int32* Target=Roles.Find(S.TargetRole);
            if(!Target||!Ancestors[I].Contains(*Target)||S.Role==S.TargetRole)return Fail(TEXT("대상과 서로 다른 바라볼 NPC를 먼저 연결하세요."));
        }
        if(S.Type==EDirectorNodeType::Expression||S.Type==EDirectorNodeType::LookAt)
        {
            const auto* Profile=Asset.Steps[*Spawn].Profile.Get();
            if(!Profile)return Fail(TEXT("대상 NPC의 연기 프로필을 먼저 지정하세요."));
            auto* Mesh=AActor::GetActorClassDefaultComponent<USkeletalMeshComponent>(Asset.Steps[*Spawn].ActorClass);
            if(!Mesh||!Mesh->GetSkeletalMeshAsset())return Fail(TEXT("연기 대상에 스켈레탈 메시가 필요합니다."));
            if(!Profile->MeshComponent.IsNone()&&Mesh->GetFName()!=Profile->MeshComponent)return Fail(TEXT("현재 연기 프로필은 첫 스켈레탈 메시 컴포넌트 이름과 일치해야 합니다."));
            if(S.Type==EDirectorNodeType::LookAt&&(Mesh->GetSkeletalMeshAsset()->GetRefSkeleton().FindBoneIndex(Profile->HeadBone)==INDEX_NONE||Profile->HeadForwardAxis.ContainsNaN()||Profile->HeadForwardAxis.IsNearlyZero()))return Fail(TEXT("시선 프로필의 머리 본과 정면 축을 확인하세요."));
            if(S.Type==EDirectorNodeType::Expression)
            {
                const auto* Preset=Profile->Expressions.Find(S.ExpressionKey);
                if(!Preset||!Preset->Morphs.Num())return Fail(TEXT("표정 프리셋 Key 또는 모프 설정이 없습니다."));
                for(const auto& M:Preset->Morphs)if(!Mesh->GetSkeletalMeshAsset()->FindMorphTarget(M.Key)||!FMath::IsFinite(M.Value)||M.Value<0||M.Value>1)return Fail(TEXT("표정 프리셋의 모프 이름과 0~1 가중치를 확인하세요."));
            }
            if(!FMath::IsFinite(S.Strength)||S.Strength<0||S.Strength>1||!FMath::IsFinite(S.BlendSeconds)||S.BlendSeconds<0)return Fail(TEXT("연기 강도/전환 시간을 확인하세요."));
        }
        if(DirectorNodes::IsNPC(S.Type)&&S.Profile&&(!FMath::IsFinite(S.Profile->AimHeight)||S.Profile->AimHeight<0))return Fail(TEXT("연기 프로필의 주시 높이는 유한한 양수여야 합니다."));
        if(S.Type==EDirectorNodeType::BindNPC&&S.ActorSource==EDirectorActorSource::Tag&&S.ActorTag.IsNone())return Fail(TEXT("연결할 기존 Actor 태그를 입력하세요."));
        if(S.Type==EDirectorNodeType::Fade&&(!FMath::IsFinite(S.FadeFrom)||!FMath::IsFinite(S.FadeTo)||S.FadeFrom<0||S.FadeFrom>1||S.FadeTo<0||S.FadeTo>1))return Fail(TEXT("페이드는 0~1 값이어야 합니다."));
        if(S.Type==EDirectorNodeType::CameraSwitch&&(!FMath::IsFinite(S.BlendSeconds)||S.BlendSeconds<0||S.BlendSeconds>S.Duration))return Fail(TEXT("카메라 전환 시간은 0~노드 시간 이내로 입력하세요."));
        if(DirectorNodes::IsScreenEffect(S.Type)&&!DirectorVision::Validate(S,Error))return Fail(Error);
        FTransform From=S.Transform;
        if(S.Type==EDirectorNodeType::CharacterMove)
        {
            From=Asset.Steps[*Spawn].Transform;int32 Latest=-1;
            for(int32 P:Ancestors[I])if(Asset.Steps[P].Type==EDirectorNodeType::CharacterMove&&Asset.Steps[P].Role==S.Role)
            {
                if(Out.FinishFrames[P]>Begin)return Fail(TEXT("같은 NPC의 이동이 겹칩니다. 완료 후 다음 실행을 켜거나 합류를 추가하세요."));
                if(Out.FinishFrames[P]>Latest){Latest=Out.FinishFrames[P];From=Out.ToPoses[P];}
            }
            FVector Destination;if(!DirectorMotion::Resolve(S.Destination,Vectors,From.GetLocation(),Destination,Error))return Fail(Error);
            Out.FromPoses[I]=From;Out.ToPoses[I]=From;Out.ToPoses[I].SetLocation(Destination);
            const double Distance=FVector::Distance(From.GetLocation(),Destination);
            if(S.MoveTiming==EDirectorMoveTiming::Speed)
            {
                if(!FMath::IsFinite(S.MoveSpeed)||S.MoveSpeed<=0)return Fail(TEXT("이동 속도는 0보다 커야 합니다."));
                Seconds=FMath::Max(1.0/30.0,Distance/S.MoveSpeed);
            }
            else if(S.MoveTiming==EDirectorMoveTiming::Duration)Seconds=S.Duration;
            else return Fail(TEXT("이동 시간 방식을 선택하세요."));
        }
        else
        {
            Out.FromPoses[I]=From;Out.ToPoses[I]=From;
            if(S.Type==EDirectorNodeType::Fade||DirectorMotion::IsCamera(S.Type)||S.Type==EDirectorNodeType::Wait||S.Type==EDirectorNodeType::Animation||S.Type==EDirectorNodeType::LookAt||S.Type==EDirectorNodeType::Expression||S.Type==EDirectorNodeType::Dialogue||DirectorNodes::IsReturn(S.Type))Seconds=S.Duration;
            if(DirectorNodes::IsScreenEffect(S.Type))Seconds=DirectorVision::Duration(S);
            if(S.Type==EDirectorNodeType::CameraPreset&&!S.bActivateCamera)Seconds=0;
            if(S.Type==EDirectorNodeType::Dialogue)
            {
                if(!S.ValidateSpeaker(Error))return Fail(Error);
                if(!DirectorChoices::Validate(S.Choices,Error))return Fail(Error);
                if(S.DialogueText.IsEmpty())return Fail(TEXT("대사 내용을 입력하세요."));
                if(S.DialogueAdvance==EDirectorDialogueAdvance::Voice&&!S.Voice)return Fail(TEXT("음성 종료 진행에는 음성이 필요합니다."));
                if(S.Voice&&(S.DialogueAdvance==EDirectorDialogueAdvance::Voice||S.DialogueAdvance==EDirectorDialogueAdvance::Click))Seconds=S.Voice->GetDuration();
                if(!S.bWaitForCompletion)return Fail(TEXT("대사는 완료 대기를 사용해야 합니다."));
            }
        }
        if(S.bUseMotionPath&&(S.Type==EDirectorNodeType::CharacterMove||S.Type==EDirectorNodeType::CameraMove))
        {
            if(!DirectorPath::Validate(S,Error))return Fail(Error);
            Seconds=S.MotionPoints.Last().Time;Out.FromPoses[I]=S.MotionPoints[0].Pose();Out.ToPoses[I]=S.MotionPoints.Last().Pose();
        }
        if(S.Type==EDirectorNodeType::Animation)
        {
            for(double V:TArray<double>{S.AnimationRate,S.AnimationStartOffset,S.AnimationEndOffset,S.AnimationFirstOffset,S.AnimationBlendIn,S.AnimationBlendOut,S.AnimationWeight})if(!FMath::IsFinite(V)||V<0)return Fail(TEXT("애니메이션 재생·블렌딩 값은 유한한 양수 또는 0이어야 합니다."));
            if(S.AnimationRate<=0||S.AnimationWeight>1||S.AnimationBlendIn>Seconds+.0001||S.AnimationBlendOut>Seconds+.0001||!S.Animation||S.AnimationStartOffset+S.AnimationEndOffset>=S.Animation->GetPlayLength())return Fail(TEXT("애니메이션 속도·가중치·오프셋·블렌딩 시간을 확인하세요."));
        }
        const bool Timed=(S.Type==EDirectorNodeType::CameraPreset&&!S.bActivateCamera)?false:Seconds!=0||S.Type==EDirectorNodeType::Dialogue||S.Type==EDirectorNodeType::Expression||S.Type==EDirectorNodeType::LookAt||DirectorNodes::IsReturn(S.Type)||S.Type==EDirectorNodeType::CharacterMove||DirectorMotion::IsCamera(S.Type)||S.Type==EDirectorNodeType::Wait||S.Type==EDirectorNodeType::Animation;
        if(Timed&&(!FMath::IsFinite(Seconds)||Seconds<1.0/30.0-1.e-8||Seconds>3600))return Fail(TEXT("시간은 1/30초~3600초로 입력하세요."));
        const int32 Duration=Timed?FMath::Max(1,FMath::RoundToInt(Seconds*30)):0;
        Out.FinishFrames[I]=Begin+Duration;Out.BranchFinishFrames[I]=FMath::Max(Outstanding,Begin+Duration);
        Out.EndFrame=FMath::Max(Out.EndFrame,Out.BranchFinishFrames[I]);
        if(Out.EndFrame>108000)return Fail(TEXT("연출은 1시간까지 지원합니다."));
        if(DirectorMotion::HasAnimation(S))
        {
            UAnimSequence* Animation=S.Animation;
            if(S.Type==EDirectorNodeType::CharacterMove)
            {
                double Distance=FVector::Distance(Out.FromPoses[I].GetLocation(),Out.ToPoses[I].GetLocation());
                if(S.bUseMotionPath){Distance=0;for(int32 Point=1;Point<S.MotionPoints.Num();++Point)Distance+=FVector::Distance(S.MotionPoints[Point-1].Position,S.MotionPoints[Point].Position);}
                Out.EffectiveSpeeds[I]=Distance/(Duration/30.0);
                if(S.bAutoLocomotion)
                {
                    const auto& NPC=Asset.Steps[*Spawn];
                    if(!FMath::IsFinite(NPC.RunThreshold)||NPC.RunThreshold<=0)return Fail(TEXT("NPC의 달리기 전환 속도는 0보다 커야 합니다."));
                    Animation=Out.EffectiveSpeeds[I]>=NPC.RunThreshold?NPC.RunAnimation:NPC.WalkAnimation;
                }
            }
            const auto& NPCStep=Asset.Steps[*Spawn];
            const auto* TemplateMesh=NPCStep.ImportedTemplate?NPCStep.ImportedTemplate->FindComponentByClass<USkeletalMeshComponent>():AActor::GetActorClassDefaultComponent<USkeletalMeshComponent>(NPCStep.ActorClass);
            if(!DirectorMotion::ValidateAnimationMesh(TemplateMesh,Animation,Error))return Fail(Error);
            Out.Animations[I]=Animation;
        }
    }
    // Camera durations do not depend on poses: resolve them after every NPC motion has a schedule.
    for(int32 I:Out.Order)if(DirectorMotion::IsCamera(Asset.Steps[I].Type))
    {
        const auto& S=Asset.Steps[I];FTransform From=Cameras.FindChecked(S.EffectiveCameraKey()).Transform;int32 Latest=-1;
        for(int32 P:Ancestors[I])if(DirectorMotion::IsCamera(Asset.Steps[P].Type)&&Asset.Steps[P].Type!=EDirectorNodeType::CameraSwitch&&S.Type!=EDirectorNodeType::CameraSwitch&&Asset.Steps[P].EffectiveCameraKey()==S.EffectiveCameraKey())
        {
            if(Out.FinishFrames[P]>Out.StartFrames[I])return Fail(TEXT("같은 카메라의 동작이 겹칩니다. 순서대로 실행하세요."));
            if(Out.FinishFrames[P]>Latest){Latest=Out.FinishFrames[P];From=Out.ToPoses[P];}
        }
        Out.FromPoses[I]=From;Out.ToPoses[I]=From;
        if(S.Type==EDirectorNodeType::CameraMove&&S.bUseMotionPath){Out.FromPoses[I]=S.MotionPoints[0].Pose();Out.ToPoses[I]=S.MotionPoints.Last().Pose();}
        else if(S.Type==EDirectorNodeType::CameraMove)
        {
            FVector Position,Rotation;
            if(!DirectorMotion::Resolve(S.Destination,Vectors,From.GetLocation(),Position,Error)||!DirectorMotion::Resolve(S.Rotation,Vectors,From.Rotator().Euler(),Rotation,Error))return Fail(Error);
            Out.ToPoses[I].SetLocation(Position);Out.ToPoses[I].SetRotation(FRotator::MakeFromEuler(Rotation).Quaternion());
        }
        else if(S.Type==EDirectorNodeType::CameraPreset)
        {
            auto PositionAt=[&](FName Role)
            {
                FTransform Pose=Asset.Steps[Roles.FindChecked(Role)].Transform;int32 Last=-1;
                for(int32 J:Out.Order)if(Asset.Steps[J].Type==EDirectorNodeType::CharacterMove&&Asset.Steps[J].Role==Role&&Out.StartFrames[J]<=Out.StartFrames[I]&&Out.StartFrames[J]>Last)
                {Last=Out.StartFrames[J];Pose.Blend(Out.FromPoses[J],Out.ToPoses[J],FMath::Clamp(double(Out.StartFrames[I]-Last)/(Out.FinishFrames[J]-Last),0.,1.));}
                return Pose;
            };
            const auto& NPC=Asset.Steps[Roles.FindChecked(S.Role)];const FTransform TargetPose=PositionAt(S.Role);
            const double Height=NPC.Profile?NPC.Profile->AimHeight:150.;
            const double AimHeight=S.Framing==EDirectorFraming::Full?Height*.55:(S.Framing==EDirectorFraming::Medium?Height*.8:Height);
            const FVector Target=TargetPose.GetLocation()+FVector(0,0,AimHeight);
            const double Distance=S.Framing==EDirectorFraming::CloseUp?100:(S.Framing==EDirectorFraming::Full?380:210);
            FVector Position=Target+FRotator(0,TargetPose.Rotator().Yaw+S.ShotYaw,0).Vector()*Distance+S.ShotOffset;
            if(S.Framing==EDirectorFraming::OverShoulder)
            {
                const auto& ForegroundNPC=Asset.Steps[Roles.FindChecked(S.TargetRole)];
                const double ForegroundHeight=ForegroundNPC.Profile?ForegroundNPC.Profile->AimHeight:150.;
                const FVector Foreground=PositionAt(S.TargetRole).GetLocation()+FVector(0,0,ForegroundHeight);
                const FVector Direction=(Target-Foreground).GetSafeNormal();
                if(Direction.IsNearlyZero())return Fail(TEXT("오버숄더 인물의 위치를 분리하세요."));
                Position=Foreground-Direction*90+FVector::CrossProduct(FVector::UpVector,Direction)*45+S.ShotOffset;
            }
            if(Position.ContainsNaN()||!FMath::IsFinite(S.ShotYaw)||(Target-Position).IsNearlyZero())return Fail(TEXT("구도 위치와 보정값을 확인하세요."));
            Out.ToPoses[I]=FTransform((Target-Position).Rotation(),Position);Out.FromPoses[I]=Out.ToPoses[I];
        }
        else if(S.Type==EDirectorNodeType::Camera&&S.bLookAtTarget)
        {
            FVector Target=Asset.Steps[Roles.FindChecked(S.Role)].Transform.GetLocation();int32 LastStart=-1;
            for(int32 J:Out.Order)if(Asset.Steps[J].Type==EDirectorNodeType::CharacterMove&&Asset.Steps[J].Role==S.Role&&Out.StartFrames[J]<=Out.StartFrames[I]&&Out.StartFrames[J]>LastStart)
            {
                LastStart=Out.StartFrames[J];const double Alpha=FMath::Clamp(double(Out.StartFrames[I]-LastStart)/(Out.FinishFrames[J]-LastStart),0.,1.);
                Target=FMath::Lerp(Out.FromPoses[J].GetLocation(),Out.ToPoses[J].GetLocation(),Alpha);
            }
            const FVector Direction=Target+FVector(0,0,80)-From.GetLocation();
            if(Direction.IsNearlyZero())return Fail(TEXT("카메라와 주시 대상 위치가 같습니다."));
            Out.ToPoses[I].SetRotation(Direction.Rotation().Quaternion());Out.FromPoses[I]=Out.ToPoses[I];
        }
    }
    if(Out.EndFrame<=0&&Asset.Steps.ContainsByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::GameAction;}))Out.EndFrame=1;
    if(Out.EndFrame<=0)return Fail(TEXT("카메라, 대기 또는 애니메이션으로 연출 시간을 지정하세요."));
    for(int32 I=0;I<N;++I)
    {
        const auto& S=Asset.Steps[I];
        if(DirectorNodes::IsNPC(S.Type)&&Out.StartFrames[I]>=Out.EndFrame)return Fail(TEXT("NPC 추가 뒤에 재생 시간을 넣으세요."));
        for(int32 J=I+1;J<N;++J)
        {
            const auto& T=Asset.Steps[J];
            auto SequenceConflict=[&](const FDirectorStep& A,const FDirectorStep& B)
            {
                if(A.Type!=EDirectorNodeType::Sequence)return false;
                if(DirectorSequence::HasCamera(A)&&(DirectorMotion::CutsCamera(B)||DirectorSequence::HasCamera(B)))return true;
                if((DirectorMotion::HasAnimation(B)||B.Type==EDirectorNodeType::CharacterMove||B.Type==EDirectorNodeType::LookAt||B.Type==EDirectorNodeType::Expression)&&DirectorSequence::UsesNPC(A,B.Role))return true;
                if(DirectorNodes::IsCamera(B.Type)&&DirectorSequence::UsesCamera(A,B.EffectiveCameraKey()))return true;
                if(B.Type==EDirectorNodeType::Sequence)for(const auto& R:B.SequenceRoles)
                    if((R.Target==EDirectorSequenceTarget::NPC&&DirectorSequence::UsesNPC(A,R.Key))||(R.Target==EDirectorSequenceTarget::Camera&&DirectorSequence::UsesCamera(A,R.Key)))return true;
                return false;
            };
            const bool Conflict=DirectorVision::Conflicts(S.Type,T.Type)||(S.Type==EDirectorNodeType::Fade&&T.Type==S.Type)||SequenceConflict(S,T)||SequenceConflict(T,S)||(S.Type==EDirectorNodeType::Dialogue&&T.Type==S.Type)||(S.Type==EDirectorNodeType::Expression&&T.Type==S.Type&&S.Role==T.Role)||(S.Type==EDirectorNodeType::LookAt&&T.Type==S.Type&&S.Role==T.Role)||(DirectorMotion::CutsCamera(S)&&DirectorMotion::CutsCamera(T))||(DirectorMotion::HasAnimation(S)&&DirectorMotion::HasAnimation(T)&&S.Role==T.Role&&!(S.Type==EDirectorNodeType::Animation&&T.Type==EDirectorNodeType::Animation&&S.bAllowAnimationBlend&&T.bAllowAnimationBlend));
            const bool Overlap=Out.StartFrames[I]<Out.FinishFrames[J]&&Out.StartFrames[J]<Out.FinishFrames[I];
            const bool InstantScreenConflict=DirectorVision::Conflicts(S.Type,T.Type)&&
                ((Out.StartFrames[I]==Out.FinishFrames[I]&&Out.StartFrames[I]>=Out.StartFrames[J]&&Out.StartFrames[I]<Out.FinishFrames[J]&&!(Out.StartFrames[I]==Out.StartFrames[J]&&Ancestors[J].Contains(I)))||
                 (Out.StartFrames[J]==Out.FinishFrames[J]&&Out.StartFrames[J]>=Out.StartFrames[I]&&Out.StartFrames[J]<Out.FinishFrames[I]&&!(Out.StartFrames[I]==Out.StartFrames[J]&&Ancestors[I].Contains(J)))||
                 (Out.StartFrames[I]==Out.FinishFrames[I]&&Out.StartFrames[J]==Out.FinishFrames[J]&&Out.StartFrames[I]==Out.StartFrames[J]&&!Ancestors[I].Contains(J)&&!Ancestors[J].Contains(I)));
            if(Conflict&&(Overlap||InstantScreenConflict))return Fail(TEXT("대사, 촬영 카메라 또는 동일 NPC의 같은 연기 채널 시간이 겹칩니다."));
        }
    }
    return true;
}
bool FSceneDirectorCompiler::Validate(const USceneDirectorAsset& Asset,TArray<int32>& Order,FString& Error)
{FDirectorSchedule Plan;const bool Result=Schedule(Asset,Plan,Error);Order=Plan.Order;return Result;}
namespace
{
int32 Frames(float Seconds){return FMath::Max(1,FMath::RoundToInt(Seconds*30.f));}
FGuid AddActor(ULevelSequence& Sequence,UClass* Class,const FString& Label,const FTransform& Transform,int32 Start,int32 End,float FOV=50,AActor* SourceTemplate=nullptr)
{
    UMovieScene* Movie=Sequence.GetMovieScene();
    AActor* Template=DuplicateObject<AActor>(SourceTemplate?SourceTemplate:Class->GetDefaultObject<AActor>(),&Sequence,MakeUniqueObjectName(&Sequence,Class,FName(*Label)));
    Template->ClearFlags(RF_Transient|RF_ClassDefaultObject|RF_ArchetypeObject);
    if(auto* Camera=Cast<ACameraActor>(Template)) Camera->GetCameraComponent()->SetFieldOfView(FOV);
    const FGuid Binding=Movie->AddSpawnable(Label,*Template);
    auto* SpawnTrack=Movie->AddTrack<UMovieSceneSpawnTrack>(Binding);
    auto* SpawnSection=CastChecked<UMovieSceneSpawnSection>(SpawnTrack->CreateNewSection());
    SpawnSection->SetRange(TRange<FFrameNumber>(Start,End));
    SpawnSection->GetChannel().SetDefault(true); SpawnTrack->AddSection(*SpawnSection);
    auto* Track=Movie->AddTrack<UMovieScene3DTransformTrack>(Binding);
    Track->SetPropertyNameAndPath(TEXT("Transform"),TEXT("Transform"));
    auto* Section=CastChecked<UMovieScene3DTransformSection>(Track->CreateNewSection());
    Section->SetRange(TRange<FFrameNumber>(Start,End));
    Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;
    auto Channels=Section->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    const FVector P=Transform.GetLocation(),R=Transform.Rotator().Euler(),S=Transform.GetScale3D();
    const double Values[]={P.X,P.Y,P.Z,R.X,R.Y,R.Z,S.X,S.Y,S.Z};
    for(int32 I=0;I<9;++I)Channels[I]->SetDefault(Values[I]);
    Track->AddSection(*Section);
    return Binding;
}
}

namespace
{
void PoseKey(ULevelSequence& Sequence,FGuid Binding,int32 Frame,const FTransform& Pose,bool bLinear)
{
    auto* Track=Sequence.GetMovieScene()->FindTrack<UMovieScene3DTransformTrack>(Binding);
    auto* Section=CastChecked<UMovieScene3DTransformSection>(Track->GetAllSections()[0]);
    auto Channels=Section->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    FVector Rotation=Pose.Rotator().Euler();
    for(int32 I=0;I<3;++I){double Old=Rotation[I];Channels[3+I]->Evaluate(FFrameTime(Frame),Old);Rotation[I]=Old+FMath::FindDeltaAngleDegrees(Old,double(Rotation[I]));}
    const FVector P=Pose.GetLocation(),Scale=Pose.GetScale3D();
    const double Values[]={P.X,P.Y,P.Z,Rotation.X,Rotation.Y,Rotation.Z,Scale.X,Scale.Y,Scale.Z};
    for(int32 I=0;I<9;++I)
        if(bLinear)Channels[I]->AddLinearKey(FFrameNumber(Frame),Values[I]);
        else Channels[I]->AddConstantKey(FFrameNumber(Frame),Values[I]);
}
}
bool FSceneDirectorCompiler::Compile(USceneDirectorAsset& Asset,FString& Error)
{
    Asset.SyncVariables();
    for(const auto& C:Asset.EntryConditions)
    {
        const bool Valid=C.Type==EDirectorVariableType::Boolean?Asset.BoolVariables.ContainsByPredicate([&](const FDirectorBoolEntry& V){return V.Key==C.Key;}):Asset.IntVariables.ContainsByPredicate([&](const FDirectorIntEntry& V){return V.Key==C.Key;});
        if(!Valid){Error=TEXT("이벤트 실행 조건의 변수 Key를 확인하세요: ")+C.Key.ToString();Asset.bNeedsCompile=true;return false;}
    }
#if WITH_EDITOR
    for(auto& Step:Asset.Steps)if(Step.Type==EDirectorNodeType::Sequence)DirectorSequence::RefreshRoles(Step);
#endif
    if(DirectorBranching::HasBranches(Asset))
    {
        Asset.bNeedsCompile=true;
        if(!DirectorBranching::ValidateAll(Asset,Error))return false;
        TMap<FGuid,FName> Decisions;
        for(const auto& S:Asset.Steps)if(!S.ChoiceTargets.IsEmpty())
        {
            if(!S.Choices.IsValidIndex(S.PreviewChoiceIndex-1)||!S.Choices[S.PreviewChoiceIndex-1].bEnabled){Error=TEXT("미리보기 선택지 번호가 선택지 목록 범위를 벗어났습니다.");return false;}
            Decisions.Add(S.Id,S.Choices[S.PreviewChoiceIndex-1].Key);
        }
        auto* Resolved=NewObject<USceneDirectorAsset>(GetTransientPackage(),NAME_None,RF_Transient);FGuid Pending;
        if(!DirectorBranching::Resolve(Asset,Decisions,{},*Resolved,Pending,Error)||!Compile(*Resolved,Error))return false;
        ULevelSequence* Sequence=DuplicateObject<ULevelSequence>(Resolved->GeneratedSequence,&Asset);
        Sequence->ClearFlags(RF_Transient);
        if(!Asset.HasAnyFlags(RF_Transient))Asset.Modify();
        Asset.GeneratedSequence=Sequence;Asset.Cues=Resolved->Cues;Asset.NPCBindings=Resolved->NPCBindings;Asset.CameraBindings=Resolved->CameraBindings;Asset.bNeedsCompile=false;
        if(!Asset.HasAnyFlags(RF_Transient))Asset.MarkPackageDirty();
        return true;
    }
#if WITH_EDITOR
    for(auto& Step:Asset.Steps)if(Step.Type==EDirectorNodeType::Sequence)DirectorSequence::RefreshRoles(Step);
#endif
    FDirectorSchedule Plan;
    if(!Schedule(Asset,Plan,Error)){Asset.bNeedsCompile=true;return false;}
    ULevelSequence* Sequence=NewObject<ULevelSequence>(&Asset,NAME_None,RF_Transactional);
    Sequence->Initialize();auto* Movie=Sequence->GetMovieScene();
    Movie->SetDisplayRate(FFrameRate(30,1));Movie->SetTickResolutionDirectly(FFrameRate(30,1));Movie->SetPlaybackRange(0,Plan.EndFrame);
    TMap<FName,FGuid> NPCs,Cameras;UMovieSceneCameraCutTrack* Cuts=nullptr;
    for(int32 I:Plan.Order)
    {
        const auto& S=Asset.Steps[I];int32 Begin=Plan.StartFrames[I];
        if(DirectorNodes::IsNPC(S.Type))
        {FGuid ID=AddActor(*Sequence,S.ActorClass,*S.Role.ToString(),S.Transform,Begin,Plan.EndFrame,50,S.ImportedTemplate);NPCs.Add(S.Role,ID);PoseKey(*Sequence,ID,Begin,S.Transform,false);}
        if(DirectorMotion::IsCamera(S.Type)&&!Cameras.Contains(S.EffectiveCameraKey()))
        {
            const auto* C=Asset.Cameras.FindByPredicate([&](const FDirectorCameraEntry& Entry){return Entry.Key==S.EffectiveCameraKey();});
            const FTransform Pose=C?C->Transform:S.Transform;
            FGuid ID=AddActor(*Sequence,C&&C->ImportedTemplate?C->ImportedTemplate->GetClass():ACameraActor::StaticClass(),S.EffectiveCameraKey().ToString(),Pose,Begin,Plan.EndFrame,C?C->FieldOfView:S.FieldOfView,C?C->ImportedTemplate.Get():nullptr);
            Cameras.Add(S.EffectiveCameraKey(),ID);PoseKey(*Sequence,ID,Begin,Pose,false);
        }
    }
    // Time ordering also preserves keys when an unrelated branch was visited first in the topological traversal.
    TArray<int32> Timeline=Plan.Order;Timeline.StableSort([&](int32 A,int32 B){return Plan.StartFrames[A]<Plan.StartFrames[B];});
    for(int32 I:Timeline)
    {
        const auto& S=Asset.Steps[I];const int32 Begin=Plan.StartFrames[I],End=Plan.FinishFrames[I];
        if(S.Type==EDirectorNodeType::CharacterMove||S.Type==EDirectorNodeType::CameraMove)
        {
            const FGuid Binding=S.Type==EDirectorNodeType::CharacterMove?NPCs.FindChecked(S.Role):Cameras.FindChecked(S.EffectiveCameraKey());
            if(S.bUseMotionPath)
            {auto* Track=Movie->FindTrack<UMovieScene3DTransformTrack>(Binding);DirectorPath::Write(S,*CastChecked<UMovieScene3DTransformSection>(Track->GetAllSections()[0]),Begin);}
            else {PoseKey(*Sequence,Binding,Begin,Plan.FromPoses[I],true);PoseKey(*Sequence,Binding,End,Plan.ToPoses[I],false);}
        }
        else if(S.Type==EDirectorNodeType::Camera||S.Type==EDirectorNodeType::CameraPreset)PoseKey(*Sequence,Cameras.FindChecked(S.EffectiveCameraKey()),Begin,Plan.ToPoses[I],false);
        if(DirectorMotion::CutsCamera(S))
        {
            if(!Cuts)Cuts=CastChecked<UMovieSceneCameraCutTrack>(Movie->AddCameraCutTrack(UMovieSceneCameraCutTrack::StaticClass()));
            auto* Section=CastChecked<UMovieSceneCameraCutSection>(Cuts->CreateNewSection());
            Section->SetRange(TRange<FFrameNumber>(Begin,End));Section->SetCameraGuid(Cameras.FindChecked(S.EffectiveCameraKey()));
            Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;
            if(S.Type==EDirectorNodeType::CameraSwitch&&S.BlendSeconds>0){Cuts->bCanBlend=true;Section->Easing.bManualEaseIn=true;Section->Easing.ManualEaseInDuration=Frames(S.BlendSeconds);Section->bLockPreviousCamera=true;}
            Cuts->AddSection(*Section);
        }
        if(S.Type==EDirectorNodeType::Visibility)
        {
            auto* Track=Movie->FindTrack<UMovieSceneVisibilityTrack>(NPCs.FindChecked(S.Role));
            if(!Track){Track=Movie->AddTrack<UMovieSceneVisibilityTrack>(NPCs.FindChecked(S.Role));Track->SetPropertyNameAndPath(TEXT("bHidden"),TEXT("bHidden"));auto* Section=CastChecked<UMovieSceneVisibilitySection>(Track->CreateNewSection());Section->SetRange(TRange<FFrameNumber>(0,Plan.EndFrame));Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;Section->GetChannel().SetDefault(true);Track->AddSection(*Section);}
            CastChecked<UMovieSceneVisibilitySection>(Track->GetAllSections()[0])->GetChannel().GetData().UpdateOrAddKey(Begin,S.bVisible);
        }
        if(S.Type==EDirectorNodeType::Fade)
        {
            auto* Track=Movie->FindTrack<UMovieSceneFadeTrack>();if(!Track)Track=Movie->AddTrack<UMovieSceneFadeTrack>();
            auto* Section=CastChecked<UMovieSceneFadeSection>(Track->CreateNewSection());Section->SetRange(TRange<FFrameNumber>(Begin,End));Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;
            Section->FadeColor=FLinearColor::Black;Section->bFadeAudio=false;Section->FloatCurve.AddLinearKey(Begin,S.FadeFrom);Section->FloatCurve.AddLinearKey(End,S.FadeTo);Track->AddSection(*Section);
        }
        if(S.Type==EDirectorNodeType::Sequence&&!DirectorSequence::Add(*Sequence,S,Begin,End,NPCs,Cameras,Error)){Asset.bNeedsCompile=true;return false;}
        if(DirectorMotion::HasAnimation(S))
        {
            auto* Track=Movie->FindTrack<UMovieSceneSkeletalAnimationTrack>(NPCs.FindChecked(S.Role));
            if(!Track)Track=Movie->AddTrack<UMovieSceneSkeletalAnimationTrack>(NPCs.FindChecked(S.Role));
            auto* Section=CastChecked<UMovieSceneSkeletalAnimationSection>(Track->CreateNewSection());UAnimSequence* Anim=Plan.Animations[I];
            Section->SetRange(TRange<FFrameNumber>(Begin,End));Section->Params.Animation=Anim;
            Section->Params.PlayRate.Set(S.Type==EDirectorNodeType::Animation?double(Anim->GetPlayLength())/((End-Begin)/30.0*Anim->RateScale):1.0/Anim->RateScale);
            if(S.Type==EDirectorNodeType::Animation)
            {
                if(S.bExplicitAnimationRate)Section->Params.PlayRate.Set(S.AnimationRate);
                else Section->Params.PlayRate.Set((Anim->GetPlayLength()-S.AnimationStartOffset-S.AnimationEndOffset)/((End-Begin)/30.0*Anim->RateScale));
                Section->Params.StartFrameOffset=FMath::RoundToInt(S.AnimationStartOffset*30);Section->Params.EndFrameOffset=FMath::RoundToInt(S.AnimationEndOffset*30);Section->Params.FirstLoopStartFrameOffset=FMath::RoundToInt(S.AnimationFirstOffset*30);Section->Params.bReverse=S.bAnimationReverse;
                Section->Params.Weight.SetDefault(S.AnimationWeight);
                CastChecked<UMovieSceneBuiltInEasingFunction>(Section->Easing.EaseIn.GetObject())->Type=S.AnimationEaseIn;CastChecked<UMovieSceneBuiltInEasingFunction>(Section->Easing.EaseOut.GetObject())->Type=S.AnimationEaseOut;
                Section->Easing.bManualEaseIn=true;Section->Easing.ManualEaseInDuration=FMath::RoundToInt(S.AnimationBlendIn*30);
                Section->Easing.bManualEaseOut=true;Section->Easing.ManualEaseOutDuration=FMath::RoundToInt(S.AnimationBlendOut*30);
            }
            Section->Params.bForceCustomMode=S.bForceCustomAnimation;Section->Params.bSkipAnimNotifiers=true;
            Section->EvalOptions.CompletionMode=EMovieSceneCompletionMode::RestoreState;Track->AddSection(*Section);
        }
    }
    // A resolved branch prefix can end long after its last camera action. Keep that
    // shot active across dialogue/decision gaps and across later prefix growth.
    if(Asset.bResolvedBranchPath && Cuts)
    {
        TArray<UMovieSceneSection*> Sections=Cuts->GetAllSections();
        Sections.StableSort([](const UMovieSceneSection& A,const UMovieSceneSection& B){return A.GetInclusiveStartFrame()<B.GetInclusiveStartFrame();});
        for(int32 I=0;I<Sections.Num();++I)
        {
            const FFrameNumber HoldUntil=I+1<Sections.Num()?Sections[I+1]->GetInclusiveStartFrame():FFrameNumber(Plan.EndFrame);
            if(Sections[I]->GetExclusiveEndFrame()<HoldUntil)Sections[I]->SetRange(TRange<FFrameNumber>(Sections[I]->GetInclusiveStartFrame(),HoldUntil));
        }
    }
    TArray<FDirectorCue> Cues;for(int32 I:Timeline){FDirectorCue C;C.Step=Asset.Steps[I];C.StartFrame=Plan.StartFrames[I];C.EndFrame=Plan.FinishFrames[I];Cues.Add(C);}
    if(!Asset.HasAnyFlags(RF_Transient))Asset.Modify();Asset.Cues=MoveTemp(Cues);Asset.EnsureCameraDefinitions();Asset.GeneratedSequence=Sequence;Asset.NPCBindings=NPCs;Asset.CameraBindings=Cameras;Asset.bNeedsCompile=false;if(!Asset.HasAnyFlags(RF_Transient))Asset.MarkPackageDirty();
    Error=FString::Printf(TEXT("생성 완료: %.2f초 / %d개 노드"),Plan.EndFrame/30.f,Plan.Order.Num());return true;
}
