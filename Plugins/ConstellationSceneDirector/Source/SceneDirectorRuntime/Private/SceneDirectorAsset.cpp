#include "SceneDirectorAsset.h"
#include "SceneDirectorNodeTypes.h"
void USceneDirectorAsset::EnsureCameraDefinitions()
{
    for(auto& Step:Steps)if(DirectorNodes::IsCamera(Step.Type))
    {
        Step.CameraKey=Step.EffectiveCameraKey();
        if(!Cameras.ContainsByPredicate([&](const FDirectorCameraEntry& C){return C.Key==Step.CameraKey;}))
        {
            FDirectorCameraEntry C;C.Key=Step.CameraKey;C.Transform=Step.Transform;C.FieldOfView=Step.FieldOfView;Cameras.Add(C);
        }
    }
}
void USceneDirectorAsset::PostLoad()
{
    Super::PostLoad();RefreshVariableEntries();if(FormatVersion>3)return;
    const bool Legacy=FormatVersion<3||Steps.ContainsByPredicate([](const FDirectorStep& S){return S.Next.IsValid()||((S.Type==EDirectorNodeType::Camera||S.Type==EDirectorNodeType::CameraMove)&&S.CameraKey.IsNone());});
    for(auto& Step:Steps){if(Step.Next.IsValid())Step.NextNodes.AddUnique(Step.Next);Step.Next.Invalidate();}
    EnsureCameraDefinitions();FormatVersion=3;if(Legacy)bNeedsCompile=true;
}
#if WITH_EDITOR
void USceneDirectorAsset::PreEditChange(FProperty* Property)
{PreviousVariables=Variables;PreviousCameras=Cameras;PreviousVectors=Vectors;PreviousBools=BoolVariables;PreviousActions=Actions;Super::PreEditChange(Property);}
void USceneDirectorAsset::PostEditChangeProperty(FPropertyChangedEvent& Event)
{
    Super::PostEditChangeProperty(Event);
    if(Event.MemberProperty&&Event.MemberProperty->GetFName()==GET_MEMBER_NAME_CHECKED(USceneDirectorAsset,Variables))ApplyVariableEntries();
    // The Details array Duplicate operation copies hidden fields too. Keep identity unique before applying renames.
    TSet<FGuid> CameraIDs,VectorIDs,BoolIDs,ActionIDs;
    for(auto& A:Actions){if(!A.Id.IsValid()||ActionIDs.Contains(A.Id))A.Id=FGuid::NewGuid();ActionIDs.Add(A.Id);}
    for(auto& C:Cameras){if(!C.Id.IsValid()||CameraIDs.Contains(C.Id))C.Id=FGuid::NewGuid();CameraIDs.Add(C.Id);}
    for(auto& V:Vectors){if(!V.Id.IsValid()||VectorIDs.Contains(V.Id))V.Id=FGuid::NewGuid();VectorIDs.Add(V.Id);}
    for(auto& B:BoolVariables){if(!B.Id.IsValid()||BoolIDs.Contains(B.Id))B.Id=FGuid::NewGuid();BoolIDs.Add(B.Id);}
    for(const auto& Before:PreviousCameras)
        if(const auto* After=Cameras.FindByPredicate([&](const FDirectorCameraEntry& C){return C.Id==Before.Id;}))
            if(After->Key!=Before.Key&&!After->Key.IsNone()&&!Before.Key.IsNone()&&PreviousCameras.FilterByPredicate([&](const FDirectorCameraEntry& C){return C.Key==Before.Key;}).Num()==1)
                for(auto& Step:Steps){if(Step.CameraKey==Before.Key)Step.CameraKey=After->Key;for(auto& R:Step.SequenceRoles)if(R.Target==EDirectorSequenceTarget::Camera&&R.Key==Before.Key)R.Key=After->Key;}
    for(const auto& Before:PreviousVectors)
        if(const auto* After=Vectors.FindByPredicate([&](const FDirectorVectorEntry& V){return V.Id==Before.Id;}))
            if(After->Key!=Before.Key&&!After->Key.IsNone()&&!Before.Key.IsNone()&&PreviousVectors.FilterByPredicate([&](const FDirectorVectorEntry& V){return V.Key==Before.Key;}).Num()==1)
                for(auto& Step:Steps){if(Step.Destination.Key==Before.Key)Step.Destination.Key=After->Key;if(Step.Rotation.Key==Before.Key)Step.Rotation.Key=After->Key;}
    for(const auto& Before:PreviousBools)
        if(const auto* After=BoolVariables.FindByPredicate([&](const FDirectorBoolEntry& B){return B.Id==Before.Id;}))
            if(After->Key!=Before.Key&&!After->Key.IsNone()&&!Before.Key.IsNone()&&PreviousBools.FilterByPredicate([&](const FDirectorBoolEntry& B){return B.Key==Before.Key;}).Num()==1)
                for(auto& Step:Steps)if((Step.Type==EDirectorNodeType::Condition||Step.Type==EDirectorNodeType::SetBool)&&Step.BoolKey==Before.Key)Step.BoolKey=After->Key;
    for(const auto& Before:PreviousActions)
        if(const auto* After=Actions.FindByPredicate([&](const FDirectorActionEntry& A){return A.Id==Before.Id;}))
            if(After->Key!=Before.Key&&!After->Key.IsNone()&&!Before.Key.IsNone()&&PreviousActions.FilterByPredicate([&](const FDirectorActionEntry& A){return A.Key==Before.Key;}).Num()==1)
                for(auto& Step:Steps)if(Step.Type==EDirectorNodeType::GameAction&&Step.ActionKey==Before.Key)Step.ActionKey=After->Key;
    for(const auto& Before:PreviousBools)if(const auto* After=BoolVariables.FindByPredicate([&](const FDirectorBoolEntry& V){return V.Id==Before.Id;}))if(After->Key!=Before.Key&&!Before.Key.IsNone()&&!After->Key.IsNone())
    {
        TArray<USceneDirectorAsset*> Events{this};for(auto E:EventGraphs)if(E)Events.Add(E);
        for(auto* E:Events){for(auto& C:E->EntryConditions)if(C.Type==EDirectorVariableType::Boolean&&C.Key==Before.Key)C.Key=After->Key;for(auto& S:E->Steps)if((S.Type==EDirectorNodeType::SetBool||S.Type==EDirectorNodeType::Condition)&&S.BoolKey==Before.Key)S.BoolKey=After->Key;}
    }
    for(auto E:EventGraphs)if(E)E->bNeedsCompile=true;
    bNeedsCompile=true;MarkPackageDirty();
}
#endif


USceneDirectorAsset* USceneDirectorAsset::FindEvent(FName Key) const
{
    if(Key==EventKey)return const_cast<USceneDirectorAsset*>(this);
    for(auto Event:EventGraphs)if(Event&&Event->EventKey==Key)return Event;
    return nullptr;
}

USceneDirectorAsset* USceneDirectorAsset::VariableOwner()
{auto* Owner=this;while(auto* Parent=Owner->GetTypedOuter<USceneDirectorAsset>())Owner=Parent;return Owner;}
void USceneDirectorAsset::SyncVariables()
{auto* Root=VariableOwner();if(Root!=this){BoolVariables=Root->BoolVariables;IntVariables=Root->IntVariables;}for(auto E:EventGraphs)if(E)E->SyncVariables();}
USceneDirectorAsset* USceneDirectorAsset::SelectEvent(const TMap<FName,bool>& Bools,const TMap<FName,int32>& Ints,FString& Error)
{
 Error.Reset();TArray<USceneDirectorAsset*> Events{this};for(auto E:EventGraphs)if(E)Events.Add(E);
 USceneDirectorAsset* Selected=nullptr;
 for(auto* Event:Events)
 {
  bool Match=true;
  for(const auto& C:Event->EntryConditions)
  {
   if(C.Type==EDirectorVariableType::Boolean){const bool* V=Bools.Find(C.Key);if(!V){Error=TEXT("실행 조건의 Boolean 변수 없음: ")+C.Key.ToString();return nullptr;}Match&=*V==C.BoolValue;}
   else{const int32* V=Ints.Find(C.Key);if(!V){Error=TEXT("실행 조건의 Integer 변수 없음: ")+C.Key.ToString();return nullptr;}
    switch(C.Comparison){case EDirectorComparison::Equal:Match&=*V==C.IntValue;break;case EDirectorComparison::NotEqual:Match&=*V!=C.IntValue;break;case EDirectorComparison::Greater:Match&=*V>C.IntValue;break;case EDirectorComparison::GreaterEqual:Match&=*V>=C.IntValue;break;case EDirectorComparison::Less:Match&=*V<C.IntValue;break;case EDirectorComparison::LessEqual:Match&=*V<=C.IntValue;break;}}
  }
  if(Match&&!Selected)Selected=Event;
 }
 if(!Selected)Error=TEXT("실행 조건을 만족하는 이벤트가 없습니다.");return Selected;
}

void USceneDirectorAsset::RefreshVariableEntries()
{
    auto Before=Variables;Variables.Reset();
    auto Add=[&](FName Key,EDirectorVariableType Type)->FDirectorVariableEntry&
    {
        FDirectorVariableEntry V;V.Key=Key;V.Type=Type;
        if(auto* Old=Before.FindByPredicate([&](const FDirectorVariableEntry& E){return E.Key==Key&&E.Type==Type;}))V.Id=Old->Id;
        return Variables.Add_GetRef(V);
    };
    for(const auto& V:BoolVariables)Add(V.Key,EDirectorVariableType::Boolean).BoolValue=V.Value;
    for(const auto& V:IntVariables)Add(V.Key,EDirectorVariableType::Integer).IntValue=V.Value;
}
void USceneDirectorAsset::ApplyVariableEntries()
{
#if WITH_EDITOR
    TArray<USceneDirectorAsset*> Events{this};for(auto E:EventGraphs)if(E)Events.Add(E);
    TSet<FGuid> Seen;
    for(auto& V:Variables){if(!V.Id.IsValid()||Seen.Contains(V.Id))V.Id=FGuid::NewGuid();Seen.Add(V.Id);}
    for(const auto& Old:PreviousVariables)
        if(const auto* New=Variables.FindByPredicate([&](const FDirectorVariableEntry& V){return V.Id==Old.Id;}))
            if(Old.Key!=New->Key&&!Old.Key.IsNone()&&!New->Key.IsNone())
                for(auto* E:Events)
                {
                    E->Modify();
                    for(auto& C:E->EntryConditions)if(C.Type==Old.Type&&C.Key==Old.Key)C.Key=New->Key;
                    for(auto& S:E->Steps)
                    {
                        if(Old.Type==EDirectorVariableType::Boolean&&S.BoolKey==Old.Key)S.BoolKey=New->Key;
                        if(Old.Type==EDirectorVariableType::Integer&&S.IntKey==Old.Key)S.IntKey=New->Key;
                    }
                }
#endif
    BoolVariables.Reset();IntVariables.Reset();
    for(const auto& V:Variables)
    {
        if(V.Type==EDirectorVariableType::Boolean){FDirectorBoolEntry E;E.Id=V.Id;E.Key=V.Key;E.Value=V.BoolValue;BoolVariables.Add(E);}
        else{FDirectorIntEntry E;E.Key=V.Key;E.Value=V.IntValue;IntVariables.Add(E);}
    }
    SyncVariables();bNeedsCompile=true;
}
bool USceneDirectorAsset::UpgradeControlNodes()
{
    bool Changed=false;TArray<FDirectorStep> Result;
    // Widen each existing column only once so parallel branches remain aligned.
    TMap<double,int32> ExtraColumns;
    for(const auto& S:Steps)
    {int32 Extra=S.Type==EDirectorNodeType::CinematicMode?2:(S.Type==EDirectorNodeType::GameplayReturn?4:0);if(Extra)ExtraColumns.FindOrAdd(S.EditorPosition.X)=FMath::Max(ExtraColumns.FindRef(S.EditorPosition.X),Extra);}
    for(const auto& Old:Steps)
    {
        FDirectorStep First=Old;double Shift=0;for(const auto& Pair:ExtraColumns)if(Pair.Key<Old.EditorPosition.X)Shift+=Pair.Value*240.;First.EditorPosition.X+=Shift;
        TArray<FDirectorStep> Chain;
        auto Add=[&](EDirectorNodeType Type)->FDirectorStep& {FDirectorStep S=First;S.Type=Type;S.Id=Chain.IsEmpty()?Old.Id:FGuid::NewGuid();S.Next.Invalidate();S.NextNodes.Reset();S.EditorPosition.X+=Chain.Num()*240.;return Chain.Add_GetRef(S);};
        if(Old.Type==EDirectorNodeType::CinematicMode)
        {
            // False flags in legacy CinematicMode were no-ops, not restore operations.
            if(Old.bHidePlayer)Add(EDirectorNodeType::PlayerHidden).bHidePlayer=true;
            if(Old.bLockInput)Add(EDirectorNodeType::InputLock).bLockInput=true;
            if(Old.bLockInput||Old.bHideHUD)Add(EDirectorNodeType::HUDHidden).bHideHUD=true;
            if(Chain.IsEmpty())Add(EDirectorNodeType::Hub);
            Changed=true;
        }
        else if(Old.Type==EDirectorNodeType::GameplayReturn)
        {
            Add(EDirectorNodeType::PlayerHidden).bHidePlayer=false;
            Add(EDirectorNodeType::InputLock).bLockInput=false;
            Add(EDirectorNodeType::HUDHidden).bHideHUD=false;
            Add(EDirectorNodeType::CloseDialogue);
            Add(EDirectorNodeType::CameraReturn);Changed=true;
        }
        else Chain.Add(First);
        for(int32 I=0;I<Chain.Num()-1;++I)Chain[I].NextNodes={Chain[I+1].Id};
        if(Old.Type==EDirectorNodeType::CinematicMode||Old.Type==EDirectorNodeType::GameplayReturn)Chain.Last().NextNodes=Old.Successors();
        Result.Append(Chain);
    }
    if(Changed){Modify();Steps=MoveTemp(Result);bNeedsCompile=true;MarkPackageDirty();}
    for(auto E:EventGraphs)if(E)Changed=E->UpgradeControlNodes()||Changed;
    return Changed;
}
