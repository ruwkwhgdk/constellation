#include "SceneDirectorImporter.h"
#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "MovieSceneBindingReferences.h"
#include "Bindings/MovieSceneSpawnableActorBinding.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Tracks/MovieSceneSpawnTrack.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Sections/MovieSceneSpawnSection.h"
#include "Sections/MovieSceneCameraCutSection.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"
namespace
{
bool OnGrid(double Frame){return FMath::IsFinite(Frame)&&FMath::IsNearlyEqual(Frame,FMath::RoundToDouble(Frame),.0001);}
AActor* TemplateFor(ULevelSequence* Source,FGuid ID)
{
    if(auto* S=Source->GetMovieScene()->FindSpawnable(ID))return Cast<AActor>(S->GetObjectTemplate());
    if(const auto* Refs=Source->GetBindingReferences())
    {auto Entries=Refs->GetReferences(ID);if(Entries.Num()==1&&Entries[0].CustomBinding&&Entries[0].CustomBinding->GetClass()==UMovieSceneSpawnableActorBinding::StaticClass())return Cast<AActor>(CastChecked<UMovieSceneSpawnableActorBinding>(Entries[0].CustomBinding)->GetObjectTemplate());}
    return nullptr;
}
bool Active(const UMovieSceneTrack* T,const UMovieSceneSection* S){return !T->IsEvalDisabled()&&S->IsActive()&&!T->IsRowEvalDisabled(S->GetRowIndex());}
}
USceneDirectorAsset* FSceneDirectorImporter::Convert(ULevelSequence* Source,UObject* Outer,FString& Report)
{
    auto Fail=[&](const FString& Message)->USceneDirectorAsset*{Report=TEXT("변환 중단: ")+Message+TEXT("\n원본과 기존 그래프는 변경하지 않았습니다. 해당 구간은 레벨 시퀀스 재생 노드로 사용할 수 있습니다.");return nullptr;};
    if(!Source||!Source->GetMovieScene())return Fail(TEXT("레벨 시퀀스를 선택하세요."));
    auto* M=Source->GetMovieScene();const auto Range=M->GetPlaybackRange();const FFrameRate Rate=M->GetTickResolution();
    if(!Range.HasLowerBound()||!Range.HasUpperBound()||Rate.Numerator<=0||Rate.Denominator<=0)return Fail(TEXT("유한한 원본 재생 범위가 필요합니다."));
    const int32 First=Range.GetLowerBoundValue().Value,Last=Range.GetUpperBoundValue().Value;
    const double Scale=30./Rate.AsDecimal(),Length=(Last-First)/Rate.AsDecimal();
    if(Length<1./30||Length>3600||!OnGrid(Length*30))return Fail(TEXT("원본 재생 길이는 30fps 프레임 단위, 1/30초~1시간이어야 합니다."));
    // Work in a disposable asset; publish only after every track and generated graph has validated.
    auto* A=NewObject<USceneDirectorAsset>(GetTransientPackage());A->EventKey=FName(*Source->GetName());
    FDirectorStep Start;Start.Type=EDirectorNodeType::Start;A->Steps.Add(Start);
    TMap<FGuid,FName> Keys;TMap<FGuid,bool> IsCamera;TArray<TPair<double,FDirectorStep>> Actions;TArray<FString> Notes;
    FDirectorStep SourceCheck;SourceCheck.Type=EDirectorNodeType::Sequence;SourceCheck.SourceSequence=Source;DirectorSequence::RefreshRoles(SourceCheck);double Seconds;FString Error;
    if(!DirectorSequence::Validate(SourceCheck,*A,Seconds,Error))return Fail(Error);
    for(auto* T:M->GetTracks())return Fail(TEXT("전역 트랙은 아직 노드 변환을 지원하지 않습니다: ")+T->GetClass()->GetName());
    for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())
    {
        AActor* Template=TemplateFor(Source,B.GetObjectGuid());
        if(!Template)return Fail(TEXT("기존 Actor/컴포넌트 바인딩은 아직 자동 변환하지 않습니다: ")+B.GetName());
        const bool Camera=Template->IsA<ACameraActor>();FName Key(*FString::Printf(TEXT("%s_%d"),Camera?TEXT("Camera"):TEXT("NPC"),Keys.Num()+1));Keys.Add(B.GetObjectGuid(),Key);IsCamera.Add(B.GetObjectGuid(),Camera);
        FTransform Initial=Template->GetActorTransform();
        FDirectorStep Move;Move.Type=Camera?EDirectorNodeType::CameraMove:EDirectorNodeType::CharacterMove;Move.Role=Key;Move.CameraKey=Key;Move.bUseMotionPath=true;Move.bActivateCamera=false;Move.bPlayMoveAnimation=false;Move.MoveTiming=EDirectorMoveTiming::Duration;Move.Duration=Length;
        int32 TransformTracks=0;
        for(auto* T:B.GetTracks())
        {
            if(T->IsEvalDisabled()){Notes.Add(TEXT("비활성 트랙 제외: ")+T->GetClass()->GetName());continue;}
            if(auto* Spawn=Cast<UMovieSceneSpawnTrack>(T))
            {
                if(Spawn->GetAllSections().Num()!=1)return Fail(B.GetName()+TEXT(": 생성 구간은 하나만 지원합니다."));
                auto* S=Cast<UMovieSceneSpawnSection>(Spawn->GetAllSections()[0]);
                if(!S||!Active(T,S)||!S->GetRange().Contains(Range))return Fail(B.GetName()+TEXT(": 재생 중 생성/제거 전환은 아직 지원하지 않습니다."));
                bool Value=false;S->GetChannel().Evaluate(FFrameTime(First),Value);if(!Value)return Fail(B.GetName()+TEXT(": 시작부터 생성되는 Actor만 지원합니다."));
                for(bool V:S->GetChannel().GetData().GetValues())if(!V)return Fail(B.GetName()+TEXT(": Spawn 키 전환을 먼저 분리하세요."));
                continue;
            }
            if(auto* Track=Cast<UMovieScene3DTransformTrack>(T))
            {
                if(++TransformTracks>1||Track->GetAllSections().Num()!=1)return Fail(B.GetName()+TEXT(": Transform은 전체 구간의 단일 섹션만 지원합니다."));
                auto* S=Cast<UMovieScene3DTransformSection>(Track->GetAllSections()[0]);
                if(!S||!Active(T,S)||!S->GetRange().Contains(Range)||S->GetUseQuaternionInterpolation()||S->GetBlendType()!=EMovieSceneBlendType::Absolute||S->Easing.GetEaseInDuration()||S->Easing.GetEaseOutDuration())return Fail(B.GetName()+TEXT(": Transform 블렌딩/쿼터니언/부분 구간은 아직 지원하지 않습니다."));
                auto Channels=S->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
                if(Channels.Num()<9||S->GetMask().GetChannels()!=EMovieSceneTransformChannel::AllTransform)return Fail(B.GetName()+TEXT(": Transform의 위치·회전·스케일 전체 채널이 필요합니다."));
                TArray<FMovieSceneDoubleChannel> Copies;TSet<int32> Times;Times.Add(0);Times.Add(FMath::RoundToInt(Length*30));
                for(int32 Axis=0;Axis<9;++Axis)
                {
                    if(Channels[Axis]->PreInfinityExtrap!=RCCE_Constant||Channels[Axis]->PostInfinityExtrap!=RCCE_Constant)return Fail(B.GetName()+TEXT(": 반복/선형 외삽은 아직 지원하지 않습니다."));
                    for(FFrameNumber K:Channels[Axis]->GetData().GetTimes())if(K.Value<First||K.Value>Last||!OnGrid((K.Value-First)*Scale))return Fail(B.GetName()+TEXT(": 범위 밖 키 또는 30fps로 정확히 표현되지 않는 키가 있습니다."));
                    Copies.Add(*Channels[Axis]);TArray<FFrameNumber> ConvertedTimes;TArray<FMovieSceneDoubleValue> ConvertedValues;
                    const auto OriginalData=Channels[Axis]->GetData();
                    for(int32 K=0;K<OriginalData.GetTimes().Num();++K)
                    {
                        ConvertedTimes.Add(FFrameNumber(int32(FMath::RoundToInt((OriginalData.GetTimes()[K].Value-First)*Scale))));
                        auto V=OriginalData.GetValues()[K];V.Tangent.ArriveTangent/=Scale;V.Tangent.LeaveTangent/=Scale;ConvertedValues.Add(V);
                    }
                    Copies.Last().Set(ConvertedTimes,ConvertedValues);Copies.Last().SetTickResolution(FFrameRate(30,1));
                    for(FFrameNumber K:Copies.Last().GetData().GetTimes())Times.Add(K.Value);
                }
                TArray<int32> Ordered=Times.Array();Ordered.Sort();
                for(int32 Frame:Ordered)
                {
                    FDirectorMotionPoint P;P.Time=Frame/30.;P.Position=Initial.GetLocation();P.Rotation=Initial.Rotator().Euler();P.Scale=Initial.GetScale3D();P.Interpolation=EDirectorPathInterpolation::Original;P.OriginalValues.SetNum(9);
                    for(int32 Axis=0;Axis<9;++Axis)
                    {
                        double Value=P.Value(Axis);Copies[Axis].Evaluate(FFrameTime(Frame),Value);
                        if(Axis<3)P.Position[Axis]=Value;else if(Axis<6)P.Rotation[Axis-3]=Value;else P.Scale[Axis-6]=Value;
                        const auto Data=Copies[Axis].GetData();const int32 Index=Data.GetTimes().Find(FFrameNumber(Frame));
                        if(Index!=INDEX_NONE){P.OriginalMask|=1<<Axis;P.OriginalValues[Axis]=Data.GetValues()[Index];}
                        else {P.OriginalValues[Axis]=FMovieSceneDoubleValue(Value);P.OriginalValues[Axis].InterpMode=RCIM_Constant;if(Frame==0)P.OriginalMask|=1<<Axis;}
                    }
                    P.OriginalPosition=P.Position;P.OriginalRotation=P.Rotation;P.OriginalScale=P.Scale;Move.MotionPoints.Add(P);
                }
                Initial=Move.MotionPoints[0].Pose();continue;
            }
            if(auto* Track=Cast<UMovieSceneSkeletalAnimationTrack>(T))
            {
                if(Camera)return Fail(B.GetName()+TEXT(": 카메라 애니메이션 트랙은 지원하지 않습니다."));
                if(Track->ShouldUseRootMotions()||Track->bUseLegacySectionIndexBlend||Track->EvalOptions.bEvalNearestSection)return Fail(B.GetName()+TEXT(": 트랙 루트 모션, 가장 가까운 섹션 평가 또는 구형 블렌딩 설정은 지원하지 않습니다."));
                for(auto* Base:Track->GetAllSections())
                {
                    if(!Active(T,Base))continue;auto* S=Cast<UMovieSceneSkeletalAnimationSection>(Base);
                    if(!S||!S->HasStartFrame()||!S->HasEndFrame()||!Range.Contains(S->GetRange()))return Fail(B.GetName()+TEXT(": 애니메이션 섹션은 재생 범위 내부여야 합니다."));
                    if(S->EvalOptions.CompletionMode!=EMovieSceneCompletionMode::RestoreState||S->GetPreRollFrames()||S->GetPostRollFrames())return Fail(B.GetName()+TEXT(": 애니메이션은 Restore State 종료 방식과 프리롤/포스트롤 없는 구간만 변환합니다."));
                    auto* Anim=Cast<UAnimSequence>(S->Params.Animation);auto* Default=GetDefault<UMovieSceneSkeletalAnimationSection>();
                    if(!Anim||S->Params.PlayRate.GetType()!=EMovieSceneTimeWarpType::FixedPlayRate||S->Params.MirrorDataTable||S->Params.SwapRootBone!=Default->Params.SwapRootBone||S->Params.SlotName!=Default->Params.SlotName||S->Params.bLinearPlaybackWhenScaled!=Default->Params.bLinearPlaybackWhenScaled||S->Params.Weight.GetNumKeys()||!S->StartLocationOffset.IsNearlyZero()||!S->StartRotationOffset.IsNearlyZero()||!S->MatchedLocationOffset.IsNearlyZero()||!S->MatchedRotationOffset.IsNearlyZero())return Fail(B.GetName()+TEXT(": 시간 왜곡/모션 매칭/가중치 곡선 등 고급 애니메이션은 아직 지원하지 않습니다."));
                    if(!S->Params.bSkipAnimNotifiers&&Anim->Notifies.Num())return Fail(B.GetName()+TEXT(": 애니메이션 Notify가 있습니다. 게임 동작을 BP 액션으로 옮긴 뒤 변환하세요."));
                    for(int32 F:{S->GetInclusiveStartFrame().Value-First,S->GetExclusiveEndFrame().Value-First,S->Params.StartFrameOffset.Value,S->Params.EndFrameOffset.Value,S->Params.FirstLoopStartFrameOffset.Value,S->Easing.GetEaseInDuration(),S->Easing.GetEaseOutDuration()})if(!OnGrid(F*Scale))return Fail(B.GetName()+TEXT(": 애니메이션 경계/오프셋은 30fps 단위여야 합니다."));
                    auto* EaseIn=Cast<UMovieSceneBuiltInEasingFunction>(S->Easing.EaseIn.GetObject());auto* EaseOut=Cast<UMovieSceneBuiltInEasingFunction>(S->Easing.EaseOut.GetObject());
                    if(!EaseIn||!EaseOut)return Fail(B.GetName()+TEXT(": 사용자 정의 블렌드 함수는 지원하지 않습니다."));
                    FDirectorStep Step;Step.Type=EDirectorNodeType::Animation;Step.Role=Key;Step.Animation=Anim;Step.bForceCustomAnimation=S->Params.bForceCustomMode;Step.Duration=(S->GetExclusiveEndFrame().Value-S->GetInclusiveStartFrame().Value)/Rate.AsDecimal();Step.bExplicitAnimationRate=true;Step.AnimationRate=S->Params.PlayRate.AsFixedPlayRate();Step.AnimationStartOffset=S->Params.StartFrameOffset.Value/Rate.AsDecimal();Step.AnimationEndOffset=S->Params.EndFrameOffset.Value/Rate.AsDecimal();Step.AnimationFirstOffset=S->Params.FirstLoopStartFrameOffset.Value/Rate.AsDecimal();Step.bAnimationReverse=S->Params.bReverse;Step.AnimationWeight=S->Params.Weight.GetDefault().Get(1.f);Step.AnimationBlendIn=S->Easing.GetEaseInDuration()/Rate.AsDecimal();Step.AnimationBlendOut=S->Easing.GetEaseOutDuration()/Rate.AsDecimal();Step.AnimationEaseIn=EaseIn->Type;Step.AnimationEaseOut=EaseOut->Type;Step.bAllowAnimationBlend=true;
                    Actions.Emplace((S->GetInclusiveStartFrame().Value-First)/Rate.AsDecimal(),Step);
                }
                continue;
            }
            return Fail(B.GetName()+TEXT(": 미지원 노드 변환 트랙: ")+T->GetClass()->GetName());
        }
        if(Move.MotionPoints.IsEmpty())for(double Time:{0.,Length}){FDirectorMotionPoint P;P.Time=Time;P.Position=Initial.GetLocation();P.Rotation=Initial.Rotator().Euler();P.Scale=Initial.GetScale3D();Move.MotionPoints.Add(P);}
        if(Camera)
        {FDirectorCameraEntry C;C.Key=Key;C.Transform=Initial;C.FieldOfView=CastChecked<ACameraActor>(Template)->GetCameraComponent()->FieldOfView;C.ImportedTemplate=DuplicateObject<AActor>(Template,A);A->Cameras.Add(C);}
        else
        {FDirectorStep Spawn;Spawn.Type=EDirectorNodeType::SpawnNPC;Spawn.Role=Key;Spawn.ActorClass=Template->GetClass();Spawn.Transform=Initial;Spawn.ImportedTemplate=DuplicateObject<AActor>(Template,A);A->Steps.Last().NextNodes={Spawn.Id};A->Steps.Add(Spawn);}
        Actions.Emplace(0.,Move);
    }
    if(auto* Cuts=M->GetCameraCutTrack())for(auto* Base:Cuts->GetAllSections())
    {
        if(!Active(Cuts,Base))continue;auto* S=Cast<UMovieSceneCameraCutSection>(Base);
        if(!S||!S->HasStartFrame()||!S->HasEndFrame()||!Range.Contains(S->GetRange())||S->Easing.GetEaseInDuration()||S->Easing.GetEaseOutDuration())return Fail(TEXT("카메라 컷은 범위 내부의 하드 컷만 변환합니다. 블렌드 컷은 아직 지원하지 않습니다."));
        const FGuid ID=S->GetCameraBindingID().GetGuid();if(!Keys.Contains(ID)||!IsCamera.FindRef(ID))return Fail(TEXT("카메라 컷의 생성 카메라를 찾을 수 없습니다."));
        if(!OnGrid((S->GetInclusiveStartFrame().Value-First)*Scale)||!OnGrid((S->GetExclusiveEndFrame().Value-First)*Scale))return Fail(TEXT("카메라 컷 경계가 30fps 단위가 아닙니다."));
        FDirectorStep Step;Step.Type=EDirectorNodeType::CameraSwitch;Step.CameraKey=Keys[ID];Step.Duration=(S->GetExclusiveEndFrame().Value-S->GetInclusiveStartFrame().Value)/Rate.AsDecimal();Step.BlendSeconds=0;Actions.Emplace((S->GetInclusiveStartFrame().Value-First)/Rate.AsDecimal(),Step);
    }
    const int32 Setup=A->Steps.Num()-1;FDirectorStep End;End.Type=EDirectorNodeType::End;
    int32 Lane=0;
    // Every lane starts after actor registration; delay nodes retain source section start times.
    for(auto& Pair:Actions)
    {
        auto& Step=Pair.Value;Step.EditorPosition=FVector2D(800+Pair.Key*100,Lane*180);
        if(Pair.Key>0){FDirectorStep Delay;Delay.Type=EDirectorNodeType::Wait;Delay.Duration=Pair.Key;Delay.EditorPosition=FVector2D(520,Lane*180);Delay.NextNodes={Step.Id};A->Steps[Setup].NextNodes.Add(Delay.Id);A->Steps.Add(Delay);}
        else A->Steps[Setup].NextNodes.Add(Step.Id);
        Step.NextNodes={End.Id};A->Steps.Add(Step);++Lane;
    }
    if(Actions.IsEmpty())return Fail(TEXT("변환할 Actor 트랙이 없습니다."));
    for(int32 I=0;I<=Setup;++I)A->Steps[I].EditorPosition=FVector2D(I*240,-200);End.EditorPosition=FVector2D(1250,Lane*90);A->Steps.Add(End);
    if(!FSceneDirectorCompiler::Compile(*A,Error))return Fail(Error);
    A->ImportedFrom=Source;A->ImportReport=FString::Printf(TEXT("%s → %d개 노드, %.3f초. 원본 보존. 이동의 축별 키·탄젠트, 애니메이션 속도·오프셋·이징을 보존했습니다.\n%s"),*Source->GetPathName(),A->Steps.Num(),Length,*FString::Join(Notes,TEXT("\n")));
    Report=A->ImportReport;return DuplicateObject<USceneDirectorAsset>(A,Outer?Outer:GetTransientPackage());
}
USceneDirectorAsset* USceneDirectorLibrary::ImportSequence(ULevelSequence* Source,const FString& AssetPath,FString& Report)
{
    if(!AssetPath.StartsWith(TEXT("/Game/"))||!FPackageName::IsValidLongPackageName(AssetPath)){Report=TEXT("새 애셋 경로는 /Game/.../DA_Name 형식이어야 합니다.");return nullptr;}
    auto* ExistingPackage=FindPackage(nullptr,*AssetPath);
    if(FPackageName::DoesPackageExist(AssetPath)||(ExistingPackage&&!UPackage::IsEmptyPackage(ExistingPackage))){Report=TEXT("이미 존재하는 애셋은 덮어쓰지 않습니다. 새 경로를 지정하세요.");return nullptr;}
    auto* Converted=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);if(!Converted)return nullptr;
    auto* Asset=DuplicateObject<USceneDirectorAsset>(Converted,CreatePackage(*AssetPath),*FPackageName::GetLongPackageAssetName(AssetPath));Asset->SetFlags(RF_Public|RF_Standalone|RF_Transactional);
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    if(!UPackage::SavePackage(Asset->GetOutermost(),Asset,*FPackageName::LongPackageNameToFilename(AssetPath,FPackageName::GetAssetPackageExtension()),Args)){Report=TEXT("변환 애셋 저장 실패: ")+AssetPath;Asset->ClearFlags(RF_Public|RF_Standalone);return nullptr;}
    FAssetRegistryModule::AssetCreated(Asset);return Asset;
}
