#include "TextManagementEditing.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "UObject/UnrealType.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/SecureHash.h"
#include "ScopedTransaction.h"
#include "DataTableEditorUtils.h"
#include "Editor.h"
#include "FileHelpers.h"
#include "SceneDirectorAsset.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "Kismet2/BlueprintEditorUtils.h"

namespace ConstellationText
{
FString SuggestedCategory(const FEntry& Entry)
{
    const FString Path=Entry.Origin.Asset.ToString();
    if(Path.Contains(TEXT("Speaker")))return TEXT("화자");
    if(Path.Contains(TEXT("Region")))return TEXT("지역");
    if(Path.Contains(TEXT("/Quests/")))return TEXT("퀘스트");
    if(Path.Contains(TEXT("/UI/")))return TEXT("UI");
    if(Path.Contains(TEXT("/Interaction/")))return TEXT("상호작용");
    if(Path.Contains(TEXT("/Sequences/"))||Path.Contains(TEXT("/SceneDirector/"))||Entry.Origin.Kind==ELocationKind::Director)return TEXT("대사");
    return TEXT("기타");
}
static FString CategoryKey(const FEntry& Entry){const FTCHARToUTF8 Bytes(*Entry.Origin.Id());return FMD5::HashBytes(reinterpret_cast<const uint8*>(Bytes.Get()),Bytes.Length());}
FString Category(const FEntry& Entry,const FString& Filename)
{
    FConfigFile Config;Config.Read(Filename);FString Value;
    return Config.GetString(TEXT("Categories"),*CategoryKey(Entry),Value)&&!Value.IsEmpty()?Value:SuggestedCategory(Entry);
}
bool SetCategory(const FEntry& Entry,const FString& Value,const FString& Filename,FText& Message)
{
    const FString Clean=Value.TrimStartAndEnd();
    if(Clean.Len()>64||Clean.Contains(TEXT("\n"))||Clean.Contains(TEXT("\r"))||Clean.Contains(TEXT("\t"))){Message=FText::FromString(TEXT("분류는 줄바꿈 없이 64자 이내로 입력하세요."));return false;}
    FConfigFile Config;Config.Read(Filename);Config.SetString(TEXT("Categories"),*CategoryKey(Entry),*Clean);
    if(!Config.Write(Filename)){Message=FText::FromString(TEXT("분류 설정 저장에 실패했습니다. 파일 권한을 확인하세요."));return false;}
    Message=FText::FromString(Clean.IsEmpty()?TEXT("자동 분류로 복원했습니다."):TEXT("분류를 저장했습니다."));return true;
}
// Resolve only supported authored locations, and always resolve again before applying.
struct FResolvedText
{
    UObject* Owner=nullptr;
    FText* Value=nullptr;
    UEdGraphPin* Pin=nullptr;
    UBlueprint* Blueprint=nullptr;
};
static FText* PropertyText(const UStruct* Type,void* Data,const FString& Field)
{
    TArray<FString> Parts;Field.ParseIntoArray(Parts,TEXT("."));
    for(int32 I=0;I<Parts.Num();++I)
    {
        FString Name=Parts[I];int32 Bracket=INDEX_NONE;Name.FindChar('[',Bracket);
        FString IndexText;if(Bracket!=INDEX_NONE){IndexText=Name.Mid(Bracket+1);Name=Name.Left(Bracket);if(!IndexText.RemoveFromEnd(TEXT("]"))||!IndexText.IsNumeric())return nullptr;}
        FProperty* Property=FindFProperty<FProperty>(Type,*Name);if(!Property||Property->HasAnyPropertyFlags(CPF_Transient|CPF_Deprecated))return nullptr;
        void* Value=Property->ContainerPtrToValuePtr<void>(Data);
        if(Bracket!=INDEX_NONE)
        {
            auto* Array=CastField<FArrayProperty>(Property);if(!Array)return nullptr;
            FScriptArrayHelper Helper(Array,Value);const int32 Index=FCString::Atoi(*IndexText);if(!Helper.IsValidIndex(Index))return nullptr;
            Value=Helper.GetRawPtr(Index);Property=Array->Inner;
        }
        if(I==Parts.Num()-1)return CastField<FTextProperty>(Property)?static_cast<FText*>(Value):nullptr;
        auto* Struct=CastField<FStructProperty>(Property);if(!Struct)return nullptr;Type=Struct->Struct;Data=Value;
    }
    return nullptr;
}
static FResolvedText Resolve(const FLocation& Location,FText& Message)
{
    FResolvedText Result;UObject* Object=Location.Asset.ResolveObject();if(!Object)Object=Location.Asset.TryLoad();Result.Owner=Object;
    if(auto* Table=Cast<UDataTable>(Object);Table&&Location.Kind==ELocationKind::DataTable)
    {if(auto* Row=Table->FindRowUnchecked(Location.Row))Result.Value=PropertyText(Table->GetRowStruct(),Row,Location.Field);}
    else if(auto* Root=Cast<USceneDirectorAsset>(Object);Root&&Location.Kind==ELocationKind::Director)
    {
        // An open graph contains its own editable Step copy; editing the asset behind it would be overwritten on sync.
        if(GEditor&&GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(Root,false))
        {Message=FText::FromString(TEXT("열려 있는 연출 그래프에서 수정하거나, 연출 에디터를 닫은 뒤 다시 선택하세요."));return {};}
        auto* Event=Cast<USceneDirectorAsset>(Location.Event.ResolveObject());
        if(Event&&(Event==Root||Event->IsIn(Root)))
        {
            Result.Owner=Event;
            if(auto* Step=Event->Steps.FindByPredicate([&](const FDirectorStep& S){return S.Id==Location.Node;}))
            {
                if(!Location.Choice.IsNone())
                {
                    if(auto* Choice=Step->Choices.FindByPredicate([&](const FDirectorChoice& C){return C.Key==Location.Choice;}))
                    {
                        if(Location.Field==TEXT("Text")&&!Choice->TextRow.DataTable&&Choice->TextRow.RowName.IsNone())Result.Value=&Choice->Text;
                        if(Location.Field==TEXT("DisabledReason")&&!Choice->DisabledReasonRow.DataTable&&Choice->DisabledReasonRow.RowName.IsNone())Result.Value=&Choice->DisabledReason;
                    }
                }
                else if(Location.Field==TEXT("DialogueText")&&!Step->DialogueRow.DataTable&&Step->DialogueRow.RowName.IsNone())Result.Value=&Step->DialogueText;
                else if(Location.Field==TEXT("SpeakerName")&&Step->SpeakerSource==EDirectorSpeakerSource::Direct)Result.Value=&Step->SpeakerName;
            }
        }
    }
    else if(auto* Blueprint=Cast<UBlueprint>(Object))
    {
        Result.Blueprint=Blueprint;
        if(Location.Kind==ELocationKind::BlueprintNode)
        {
            TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
            for(auto* Graph:Graphs)if(FSoftObjectPath(Graph)==Location.Event)for(UEdGraphNode* Node:Graph->Nodes)if(Node&&Node->NodeGuid==Location.Node)
            {
                auto* Pin=Node->FindPin(*Location.Field);
                if(Pin&&Pin->Direction==EGPD_Input&&Pin->LinkedTo.IsEmpty()&&!Pin->bOrphanedPin&&!Pin->bDefaultValueIsIgnored&&!Pin->PinType.IsContainer()&&!Pin->PinType.bIsReference&&Pin->PinType.PinCategory==TEXT("text"))
                {Result.Owner=Node;Result.Pin=Pin;Result.Value=&Pin->DefaultTextValue;}
            }
        }
        // CDO/component/widget propagation belongs to the native Blueprint editor.
    }
    else if(Object&&Location.Kind==ELocationKind::Asset)Result.Value=PropertyText(Object->GetClass(),Object,Location.Field);
    if(!Result.Value)Message=FText::FromString(TEXT("이 위치는 원본 에디터에서 수정하세요. 없어진 행·복합 속성·Blueprint 기본값은 직접 수정하지 않습니다."));
    return Result;
}
bool ReadEdit(const FEntry& Entry,FEditSnapshot& Snapshot,FText& Message)
{
    if(Entry.bShadowed||Entry.Source.StartsWith(TEXT("[연결 오류]"))){Message=FText::FromString(TEXT("가려진 값과 연결 오류는 원본 에디터에서 확인하세요."));return false;}
    Snapshot.Target=Entry.Origin;
    if(Snapshot.Target.Kind==ELocationKind::StringTable)
    {
        auto* Table=Cast<UStringTable>(Snapshot.Target.Asset.TryLoad());
        if(!Table||!Table->GetStringTable()->GetSourceString(Snapshot.Target.Key,Snapshot.Source)){Message=FText::FromString(TEXT("String Table 키를 찾지 못했습니다."));return false;}
        return true;
    }
    auto Resolved=Resolve(Snapshot.Target,Message);if(!Resolved.Value||Resolved.Value->IsFromStringTable())return false;
    Snapshot.Original=*Resolved.Value;
    const FString* Source=FTextInspector::GetSourceString(*Resolved.Value);Snapshot.Source=Source?*Source:Resolved.Value->ToString();return true;
}
bool ApplyEdit(const FEditSnapshot& Snapshot,const FString& NewSource,FText& Message)
{
    FEntry Entry;Entry.Location=Entry.Origin=Snapshot.Target;FEditSnapshot Current;
    if(!ReadEdit(Entry,Current,Message))return false;
    if(Current.Source!=Snapshot.Source||(Snapshot.Target.Kind!=ELocationKind::StringTable&&!Current.Original.IdenticalTo(Snapshot.Original)))
    {Message=FText::FromString(TEXT("원본이 변경됐습니다. 입력 내용을 보관한 뒤 입력 취소를 눌러 최신 원문에서 다시 편집하세요."));return false;}
    if(NewSource==Current.Source){Message=FText::FromString(TEXT("변경된 내용이 없습니다."));return true;}
    const FScopedTransaction Transaction(NSLOCTEXT("TextManagement","Edit","문자열 수정"));
    if(Snapshot.Target.Kind==ELocationKind::StringTable)
    {
        auto* Table=CastChecked<UStringTable>(Snapshot.Target.Asset.ResolveObject());
        const FString Notes=Table->GetStringTable()->FindEntry(Snapshot.Target.Key)->GetDevNotes();
        Table->SetFlags(RF_Transactional);Table->Modify();Table->GetMutableStringTable()->SetSourceString(Snapshot.Target.Key,NewSource,Notes);Table->PostEditChange();Table->MarkPackageDirty();
    }
    else
    {
        auto Resolved=Resolve(Snapshot.Target,Message);if(!Resolved.Value)return false;
        FText NewText=Snapshot.Original.IsCultureInvariant()?FText::AsCultureInvariant(NewSource):FText::FromString(NewSource);
        const auto Namespace=FTextInspector::GetNamespace(Snapshot.Original);const auto Key=FTextInspector::GetKey(Snapshot.Original);
        if(Namespace.IsSet()&&Key.IsSet())NewText=FText::ChangeKey(Namespace.GetValue(),Key.GetValue(),NewText);
        if(Resolved.Pin)
        {
            const FString Error=Resolved.Pin->GetSchema()->IsPinDefaultValid(Resolved.Pin,FString(),nullptr,NewText);
            if(!Error.IsEmpty()){Message=FText::FromString(Error);return false;}
        }
        Resolved.Owner->SetFlags(RF_Transactional);Resolved.Owner->Modify();
        auto* Table=Cast<UDataTable>(Resolved.Owner);
        if(Table)FDataTableEditorUtils::BroadcastPreChange(Table,FDataTableEditorUtils::EDataTableChangeInfo::RowData);
        if(Resolved.Pin)Resolved.Pin->GetSchema()->TrySetDefaultText(*Resolved.Pin,NewText);
        else *Resolved.Value=NewText;
        if(Table)FDataTableEditorUtils::BroadcastPostChange(Table,FDataTableEditorUtils::EDataTableChangeInfo::RowData);
        else Resolved.Owner->PostEditChange();
        if(Resolved.Blueprint)FBlueprintEditorUtils::MarkBlueprintAsModified(Resolved.Blueprint);
        Resolved.Owner->MarkPackageDirty();
    }
    Message=FText::FromString(TEXT("원본에 적용했습니다. Undo로 되돌릴 수 있습니다. 디스크에 보관하려면 원본 저장을 누르세요."));return true;
}
bool SaveEdit(const FLocation& Target,FText& Message)
{
    UObject* Object=Target.Asset.ResolveObject();if(!Object||Object->GetOutermost()==GetTransientPackage()){Message=FText::FromString(TEXT("저장할 원본 에셋을 찾지 못했습니다."));return false;}
    const bool bSaved=UEditorLoadingAndSavingUtils::SavePackagesWithDialog({Object->GetOutermost()},true);
    Message=FText::FromString(bSaved?TEXT("원본 에셋을 저장했습니다."):TEXT("저장하지 못했거나 취소했습니다."));return bSaved;
}
}
