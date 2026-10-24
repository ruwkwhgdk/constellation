#include "TextManagementIndex.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorSpeaker.h"
#include "AbilityAcquisitionArt.h"
#include "CarryData.h"
#include "InteractionPromptComponent.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "UObject/UnrealType.h"

namespace ConstellationText
{
static const FTextProperty* RowTextProperty(const UDataTable* Table,bool bSpeaker)
{
    if(!Table||!Table->GetRowStruct())return nullptr;
    if(bSpeaker)
    {
        if(!Table->GetRowStruct()->IsChildOf(FDirectorSpeakerRow::StaticStruct()))return nullptr;
        return FindFProperty<FTextProperty>(Table->GetRowStruct(),TEXT("DisplayName"));
    }
    const FTextProperty* Only=nullptr;int32 Count=0;
    for(TFieldIterator<FTextProperty> It(Table->GetRowStruct());It;++It)
    {if(It->GetName()==TEXT("Description")||It->GetName().StartsWith(TEXT("Description_")))return *It;Only=*It;++Count;}
    return Count==1?Only:nullptr;
}
void FIndex::AddRow(const FDataTableRowHandle& Handle,const FLocation& Consumer,const FText& Direct,bool bSpeaker)
{
    if(!bSpeaker&&!Handle.DataTable&&Handle.RowName.IsNone()){AddText(Direct,Consumer,TEXT("직접 입력"));return;}
    const auto* Property=RowTextProperty(Handle.DataTable,bSpeaker);
    const auto* Row=Property?Handle.DataTable->FindRowUnchecked(Handle.RowName):nullptr;
    if(Row&&bSpeaker&&Property->GetPropertyValue_InContainer(Row).ToString().TrimStartAndEnd().IsEmpty())Row=nullptr;
    FLocation Source;Source.Kind=ELocationKind::DataTable;Source.Asset=FSoftObjectPath(Handle.DataTable);Source.Row=Handle.RowName;
    if(Property)Source.Field=Property->GetName();
    const FString Reason=Row?TEXT("DataTable 행 참조"):TEXT("테이블/행/텍스트 필드를 확인하세요. 직접 값으로 대체하지 않습니다.");
    Usages.Add({Source,Consumer,Row?EReferenceKind::Exact:EReferenceKind::Broken,Reason});
    if(Row)
    {
        AddText(Property->GetPropertyValue_InContainer(Row),Consumer,bSpeaker?TEXT("화자 / 행 참조"):TEXT("대사·선택지 / 행 참조"));
        for(auto& Entry:Entries)if(Entry->Location.Id()==Consumer.Id()&&Entry->Origin.Id()==Consumer.Id())Entry->Origin=Source;
    }
    else
    {
        auto Entry=MakeShared<FEntry>();Entry->Location=Entry->Origin=Consumer;Entry->Source=TEXT("[연결 오류] ")+Handle.RowName.ToString();Entry->Display=Entry->Source;Entry->Context=Reason;Entries.Add(Entry);
    }
    if(!Direct.IsEmpty()){FLocation Shadow=Consumer;Shadow.Key=TEXT("__shadowed_direct");AddText(Direct,Shadow,TEXT("현재 표시에는 사용하지 않는 직접 값"),true);}
}
void FIndex::CollectDirector(USceneDirectorAsset* Director,const FSoftObjectPath& Root)
{
    TSet<USceneDirectorAsset*> Seen;
    TFunction<void(USceneDirectorAsset*)> Visit=[&](USceneDirectorAsset* Event)
    {
        if(!Event||Seen.Contains(Event))return;Seen.Add(Event);
        for(const FDirectorStep& Step:Event->Steps)
        {
            if(Step.Type!=EDirectorNodeType::Dialogue)continue;
            FLocation Loc;Loc.Kind=ELocationKind::Director;Loc.Asset=Root;Loc.Event=FSoftObjectPath(Event);Loc.Node=Step.Id;Loc.Field=TEXT("DialogueText");
            const int32 First=Entries.Num();
            AddRow(Step.DialogueRow,Loc,Step.DialogueText);
            Loc.Field=TEXT("SpeakerName");
            if(Step.SpeakerSource==EDirectorSpeakerSource::Direct)AddText(Step.SpeakerName,Loc,TEXT("화자 직접 입력"));
            else if(Step.SpeakerSource==EDirectorSpeakerSource::Table)AddRow(Step.SpeakerRow,Loc,FText::GetEmpty(),true);
            for(const FDirectorChoice& Choice:Step.Choices)
            {
                Loc.Choice=Choice.Key;Loc.Field=TEXT("Text");AddRow(Choice.TextRow,Loc,Choice.Text);
                Loc.Field=TEXT("DisabledReason");AddRow(Choice.DisabledReasonRow,Loc,Choice.DisabledReason);
            }
            for(int32 I=First;I<Entries.Num();++I)Entries[I]->Context+=TEXT(" / ")+Event->EventKey.ToString()+TEXT(" / ")+Step.ResolveSpeaker().ToString();
        }
        for(USceneDirectorAsset* Child:Event->EventGraphs)Visit(Child);
    };Visit(Director);
}
static void AddStringRules(FIndex& Index,UStringTable* Table,const FLocation& Consumer,const TArray<FString>& Keys,const FString& Reason)
{
    if(!Table)return;
    for(const FString& Key:Keys)
    {
        FLocation Source;Source.Kind=ELocationKind::StringTable;Source.Asset=FSoftObjectPath(Table);Source.Key=Key;
        Index.Usages.Add({Source,Consumer,Table->GetStringTable()->FindEntry(Key).IsValid()?EReferenceKind::Exact:EReferenceKind::Broken,Reason});
    }
}
void FIndex::CollectGameRules(UObject* Object,const FLocation& Base)
{
    if(auto* Art=Cast<UAbilityAcquisitionArt>(Object))
    {
        for(const TCHAR* Key:{TEXT("AbandonedSchool_Star_Object_Jump"),TEXT("AbandonedSchool_Star_Object_Combat"),TEXT("AbandonedSchool_Star_Object_Metamorphosis")})
        {
            FLocation Loc=Base;Loc.Field=TEXT("Descriptions / ")+FString(Key);
            FLocation Source;Source.Kind=ELocationKind::DataTable;Source.Asset=FSoftObjectPath(Art->Descriptions);Source.Row=Key;
            const FTextProperty* Property=nullptr;
            if(Art->Descriptions&&Art->Descriptions->GetRowStruct())for(TFieldIterator<FTextProperty> It(Art->Descriptions->GetRowStruct());It;++It)if(It->GetName().StartsWith(TEXT("Description_"))){Property=*It;break;}
            if(Property)Source.Field=Property->GetName();
            const bool bValid=Property&&Art->Descriptions->FindRowUnchecked(Source.Row);
            Usages.Add({Source,Loc,bValid?EReferenceKind::Exact:EReferenceKind::Broken,TEXT("AbilityAcquisitionArt::Description의 고정 행 / Description_ 필드 규칙")});
        }
    }
    if(auto* Prompt=Cast<UInteractionPromptComponent>(Object))
    {
        TArray<FString> Keys;const UEnum* Enum=StaticEnum<EInteractionAction>();for(int32 I=0;I<Enum->NumEnums()-1;++I)if(Enum->GetValueByIndex(I)!=0)Keys.Add(Enum->GetNameStringByIndex(I));
        FLocation Loc=Base;Loc.Field+=TEXT(".ActionStrings");AddStringRules(*this,Prompt->ActionStrings,Loc,Keys,TEXT("GetActionText의 enum 키 조회 규칙 (실행 여부와 별개)"));
    }
    if(auto* Table=Cast<UDataTable>(Object);Table&&Table->GetRowStruct()&&Table->GetRowStruct()->IsChildOf(FCarrySettingsRow::StaticStruct()))
    {
        for(const auto& Pair:Table->GetRowMap())
        {
            const auto* Row=reinterpret_cast<const FCarrySettingsRow*>(Pair.Value);FLocation Loc=Base;Loc.Kind=ELocationKind::DataTable;Loc.Row=Pair.Key;Loc.Field=TEXT("Messages");
            AddStringRules(*this,Row->Messages,Loc,{TEXT("TooHeavy"),TEXT("PickupUnreachable"),TEXT("PlaceBlocked"),TEXT("ThrowBlocked")},TEXT("CarryComponent/CarryThrow의 고정 메시지 키"));
        }
    }
}
}
