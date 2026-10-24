#include "TextManagementIndex.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Blueprint.h"
#include "Engine/DataAsset.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "SceneDirectorAsset.h"
#include "UObject/UnrealType.h"
#include "Modules/ModuleManager.h"
#include "Misc/PackageName.h"

namespace ConstellationText
{
FString FLocation::Id() const
{
    return FString::Printf(TEXT("%d|%s|%s|%s|%s|%s|%s|%s"),int32(Kind),*Asset.ToString(),*Event.ToString(),*Row.ToString().ToLower(),*Key,*Field,*Node.ToString(),*Choice.ToString());
}
FString FLocation::Label() const
{
    FString Result=Asset.GetAssetName();
    if(!Row.IsNone())Result+=TEXT(" / ")+Row.ToString();
    if(!Key.IsEmpty())Result+=TEXT(" / ")+Key;
    if(!Event.IsNull()&&Event!=Asset)Result+=TEXT(" / ")+Event.ToString();
    if(Node.IsValid())Result+=TEXT(" / ")+Node.ToString().Left(8);
    if(!Choice.IsNone())Result+=TEXT(" / ")+Choice.ToString();
    if(!Field.IsEmpty())Result+=TEXT(" / ")+Field;
    return Result;
}
FString ReferenceLabel(EReferenceKind Kind)
{
    switch(Kind){case EReferenceKind::Exact:return TEXT("확정");case EReferenceKind::Dynamic:return TEXT("동적 참조");case EReferenceKind::Candidate:return TEXT("패키지 후보");default:return TEXT("연결 오류");}
}
bool FIndex::Matches(const FEntry& Entry,const FString& Query)
{
    const FString Haystack=Entry.Source+TEXT(" ")+Entry.Display+TEXT(" ")+Entry.Context+TEXT(" ")+Entry.Location.Label()+TEXT(" ")+Entry.Location.Asset.ToString();
    TArray<FString> Tokens;FString Current;bool bQuoted=false;
    for(TCHAR C:Query){if(C=='"'){bQuoted=!bQuoted;continue;}if(FChar::IsWhitespace(C)&&!bQuoted){if(!Current.IsEmpty()){Tokens.Add(Current);Current.Reset();}}else Current+=C;}
    if(!Current.IsEmpty())Tokens.Add(Current);
    for(const FString& Token:Tokens)if(!Haystack.Contains(Token,ESearchCase::IgnoreCase))return false;
    return true;
}
void FIndex::AddText(const FText& Text,const FLocation& Location,const FString& Context,bool bShadowed)
{
    if(Text.IsEmpty())return;
    auto Entry=MakeShared<FEntry>();Entry->Location=Entry->Origin=Location;Entry->Display=Text.ToString();Entry->Context=Context;Entry->bShadowed=bShadowed;
    if(const FString* Source=FTextInspector::GetSourceString(Text))Entry->Source=*Source;else Entry->Source=Entry->Display;
    FName TableId;FString Key;
    if(FTextInspector::GetTableIdAndKey(Text,TableId,Key))
    {
        FLocation Source;Source.Kind=ELocationKind::StringTable;Source.Asset=FSoftObjectPath(TableId.ToString());Source.Key=Key;
        const auto Table=FStringTableRegistry::Get().FindStringTable(TableId);
        if(Table.IsValid())
        {
            if(auto* Owner=Table->GetOwnerAsset())Source.Asset=FSoftObjectPath(Owner);
            Table->GetSourceString(Key,Entry->Source);
        }
        Entry->Origin=Source;
        if(!bShadowed)Usages.Add({Source,Location,Table.IsValid()&&Table->FindEntry(Key).IsValid()?EReferenceKind::Exact:EReferenceKind::Broken,TEXT("FText String Table 참조")});
    }
    if(!Entries.ContainsByPredicate([&](const TSharedPtr<FEntry>& E){return E->Location.Id()==Location.Id();}))Entries.Add(Entry);
}
void FIndex::Collect(UObject* Object)
{
    if(!Object||Visited.Contains(Object->GetPathName()))return;
    Visited.Add(Object->GetPathName());FLocation Base;Base.Asset=FSoftObjectPath(Object);
    if(auto* Table=Cast<UStringTable>(Object))
    {
        Base.Kind=ELocationKind::StringTable;
        Table->GetStringTable()->EnumerateKeysAndSourceStrings([&](const FTextKey& Key,const FString& Source)
        {
            auto Entry=MakeShared<FEntry>();Entry->Location=Base;Entry->Location.Key=Key.ToString();Entry->Origin=Entry->Location;
            Entry->Source=Source;Entry->Display=FText::FromStringTable(Table->GetStringTableId(),Key.ToString()).ToString();Entry->Context=TEXT("String Table");Entries.Add(Entry);return true;
        });
    }
    else if(auto* DataTable=Cast<UDataTable>(Object))
    {
        Base.Kind=ELocationKind::DataTable;
        for(const auto& Row:DataTable->GetRowMap()){Base.Row=Row.Key;CollectProperties(DataTable->GetRowStruct(),Row.Value,Base);}
        CollectGameRules(DataTable,Base);
    }
    else if(auto* Director=Cast<USceneDirectorAsset>(Object))CollectDirector(Director,Base.Asset);
    else if(auto* Blueprint=Cast<UBlueprint>(Object))CollectBlueprint(Blueprint);
    else {CollectProperties(Object->GetClass(),Object,Base);CollectGameRules(Object,Base);}
    for(const auto& Use:Usages)if(Use.Kind==EReferenceKind::Broken&&!Entries.ContainsByPredicate([&](const TSharedPtr<FEntry>& Entry){return Entry->Location.Id()==Use.Consumer.Id();}))
    {
        auto Entry=MakeShared<FEntry>();Entry->Location=Entry->Origin=Use.Consumer;
        Entry->Source=Entry->Display=TEXT("[연결 오류] ")+Use.Source.Label();Entry->Context=Use.Reason;Entries.Add(Entry);
    }
}
void FIndex::CollectProperties(const UStruct* Type,const void* Data,const FLocation& Base,int32 Depth)
{
    if(!Type||!Data||Depth>12)return;
    TFunction<void(const FProperty*,const void*,const FLocation&,int32)> Visit;
    Visit=[&](const FProperty* Property,const void* Value,const FLocation& Loc,int32 Level)
    {
        if(Level>12)return;
        if(const auto* Text=CastField<FTextProperty>(Property)){AddText(Text->GetPropertyValue(Value),Loc,TEXT("직접 FText / ")+Type->GetName());return;}
        if(const auto* Struct=CastField<FStructProperty>(Property))
        {
            if(Struct->Struct==FDataTableRowHandle::StaticStruct())
            {
                const auto& Handle=*static_cast<const FDataTableRowHandle*>(Value);
                // General row handles also point at physics/settings rows; these are not text references.
                if(Handle.DataTable&&Handle.DataTable->GetRowStruct())
                {
                    for(TFieldIterator<FTextProperty> It(Handle.DataTable->GetRowStruct());It;++It)
                    {
                        FLocation Source;Source.Kind=ELocationKind::DataTable;Source.Asset=FSoftObjectPath(Handle.DataTable);Source.Row=Handle.RowName;
                        Usages.Add({Source,Loc,Handle.DataTable->FindRowUnchecked(Handle.RowName)?EReferenceKind::Exact:EReferenceKind::Broken,TEXT("RowHandle 행 참조 (사용 필드 미확정)")});break;
                    }
                }
            }
            else CollectProperties(Struct->Struct,Value,Loc,Level+1);
        }
        else if(const auto* Array=CastField<FArrayProperty>(Property))
        {
            FScriptArrayHelper Values(Array,Value);for(int32 I=0;I<Values.Num();++I){FLocation Child=Loc;Child.Field+=FString::Printf(TEXT("[%d]"),I);Visit(Array->Inner,Values.GetRawPtr(I),Child,Level+1);}
        }
        else if(const auto* Map=CastField<FMapProperty>(Property))
        {
            FScriptMapHelper Values(Map,Value);for(int32 I=0;I<Values.GetMaxIndex();++I)if(Values.IsValidIndex(I))
            {FLocation Child=Loc;FString Key;Map->KeyProp->ExportTextItem_Direct(Key,Values.GetKeyPtr(I),nullptr,nullptr,PPF_None);Child.Field+=TEXT("[")+Key+TEXT("]");Visit(Map->ValueProp,Values.GetValuePtr(I),Child,Level+1);}
        }
        else if(const auto* Set=CastField<FSetProperty>(Property))
        {
            FScriptSetHelper Values(Set,Value);for(int32 I=0;I<Values.GetMaxIndex();++I)if(Values.IsValidIndex(I)){FLocation Child=Loc;Child.Field+=FString::Printf(TEXT("{element %d}"),I);Visit(Set->ElementProp,Values.GetElementPtr(I),Child,Level+1);}
        }
    };
    for(TFieldIterator<FProperty> It(Type);It;++It)
    {
        if(It->HasAnyPropertyFlags(CPF_Transient|CPF_Deprecated))continue;
        if(Type->IsA<UClass>()&&!It->HasAnyPropertyFlags(CPF_Edit|CPF_BlueprintVisible))continue;
        FLocation Loc=Base;Loc.Field+=(Loc.Field.IsEmpty()?TEXT(""):TEXT("."))+It->GetName();
        if(const auto* Class=Cast<UClass>(Type);Class&&static_cast<const UObject*>(Data)->HasAnyFlags(RF_ClassDefaultObject))
        {
            const UClass* Owner=Class;
            while(const UClass* Parent=Owner->GetSuperClass())
            {
                if(!Parent->IsChildOf(It->GetOwnerClass())||!It->Identical_InContainer(Owner->GetDefaultObject(),Parent->GetDefaultObject()))break;
                Owner=Parent;
            }
            if(Owner!=Class)
            {
                // Native inherited defaults have no editable Blueprint authoring location.
                if(!Owner->ClassGeneratedBy)continue;
                Loc.Asset=FSoftObjectPath(Owner->ClassGeneratedBy);
            }
        }
        for(int32 I=0;I<It->ArrayDim;++I){FLocation Element=Loc;if(It->ArrayDim>1)Element.Field+=FString::Printf(TEXT("[%d]"),I);Visit(*It,It->ContainerPtrToValuePtr<void>(Data,I),Element,Depth);}
        if(Loc.Asset!=Base.Asset)
        {
            for(const auto& Entry:Entries)if(Entry->Location.Asset==Loc.Asset&&(Entry->Location.Field==Loc.Field||Entry->Location.Field.StartsWith(Loc.Field+TEXT("."))||Entry->Location.Field.StartsWith(Loc.Field+TEXT("["))))
            {
                FLocation Consumer=Entry->Location;Consumer.Asset=Base.Asset;
                Usages.Add({Entry->Location,Consumer,EReferenceKind::Exact,TEXT("부모 Blueprint 기본값 상속 (동일 값)")});
            }
        }
    }
}
void FIndex::Start()
{
    Entries.Reset();Usages.Reset();Coverage.Reset();Queue.Reset();Visited.Reset();Cursor=0;
    auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
    TArray<FAssetData> Assets;Registry.GetAssetsByPath(TEXT("/Game/Constellation"),Assets,true);Registry.GetAssetsByPath(TEXT("/Game/SceneDirector"),Assets,true);
    TSet<FTopLevelAssetPath> Derived;Registry.GetDerivedClassNames({UDataAsset::StaticClass()->GetClassPathName()},{},Derived);
    for(const auto& Asset:Assets)
    {
        const FName Class=Asset.AssetClassPath.GetAssetName();
        if(Class==TEXT("World")){Coverage.Add({Asset.GetSoftObjectPath().ToString(),TEXT("미검사"),TEXT("맵/Level Blueprint/배치 액터는 이번 검사 범위 밖입니다.")});continue;}
        if(Class==TEXT("DataTable")||Class==TEXT("StringTable")||Class==TEXT("Blueprint")||Class==TEXT("WidgetBlueprint")||Class==TEXT("SceneDirectorAsset")||Derived.Contains(Asset.AssetClassPath))Queue.Add(Asset);
    }
    Queue.Sort([](const FAssetData& A,const FAssetData& B){auto Rank=[](const FAssetData& X){return X.AssetClassPath.GetAssetName()==TEXT("StringTable")?0:X.AssetClassPath.GetAssetName()==TEXT("DataTable")?1:2;};return Rank(A)!=Rank(B)?Rank(A)<Rank(B):A.PackageName.LexicalLess(B.PackageName);});
    for(const auto& Asset:Queue)
    {
        Coverage.Add({Asset.GetSoftObjectPath().ToString(),TEXT("미검사"),TEXT("검사 대기")});
        if(Asset.AssetClassPath.GetAssetName()!=TEXT("DataTable")&&Asset.AssetClassPath.GetAssetName()!=TEXT("StringTable"))continue;
        TArray<FName> Referencers;Registry.GetReferencers(Asset.PackageName,Referencers);
        for(FName Package:Referencers)
        {
            FLocation Source;Source.Asset=Asset.GetSoftObjectPath();FLocation Consumer;Consumer.Asset=FSoftObjectPath(Package.ToString()+TEXT(".")+FPackageName::GetShortName(Package));
            Usages.Add({Source,Consumer,EReferenceKind::Candidate,TEXT("패키지 의존성만 확인됨. 개별 행 사용을 의미하지 않습니다.")});
        }
    }
}
bool FIndex::Tick()
{
    if(!IsScanning())return false;
    const FAssetData Asset=Queue[Cursor++];UObject* Object=Asset.GetAsset();
    for(auto& Item:Coverage)if(Item.Asset==Asset.GetSoftObjectPath().ToString())
    {Item.State=Object?TEXT("검사 완료"):TEXT("검사 실패");Item.Reason=Object?TEXT("지원되는 작성 필드/정적 참조 검사. 동적 키의 실행값은 추적하지 않습니다."):TEXT("에셋을 읽지 못했습니다. Output Log를 확인하세요.");break;}
    if(Object)Collect(Object);
    return true;
}
void FIndex::Cancel()
{
    for(int32 I=Cursor;I<Queue.Num();++I)for(auto& Item:Coverage)if(Item.Asset==Queue[I].GetSoftObjectPath().ToString())Item.Reason=TEXT("사용자가 검사를 중단했습니다.");
    Cursor=Queue.Num();
}
TArray<FUsage> FIndex::FindUsages(const FEntry& Entry) const
{
    TArray<FUsage> Result;TSet<FString> Seen;
    TFunction<void(const FLocation&,int32)> Follow=[&](const FLocation& Location,int32 Depth)
    {
        if(Depth>8||Seen.Contains(Location.Id()))return;Seen.Add(Location.Id());
        for(const auto& Use:Usages)
        {
            const bool bWhole=Use.Kind==EReferenceKind::Dynamic||Use.Kind==EReferenceKind::Candidate;
            if(Use.Source.Asset!=Location.Asset)continue;
            if(!bWhole&&(Use.Source.Event!=Location.Event||Use.Source.Node!=Location.Node||Use.Source.Choice!=Location.Choice))continue;
            if(!bWhole&&(Use.Source.Row!=Location.Row||Use.Source.Key!=Location.Key||(!Use.Source.Field.IsEmpty()&&Use.Source.Field!=Location.Field)))continue;
            if(Use.Kind==EReferenceKind::Candidate&&Usages.ContainsByPredicate([&](const FUsage& Other){return Other.Source.Asset==Location.Asset&&Other.Consumer.Asset==Use.Consumer.Asset&&Other.Kind!=EReferenceKind::Candidate;}))continue;
            if(!Result.ContainsByPredicate([&](const FUsage& Existing){return Existing.Consumer.Id()==Use.Consumer.Id()&&Existing.Kind==Use.Kind;}))Result.Add(Use);
            if(Use.Kind==EReferenceKind::Exact)Follow(Use.Consumer,Depth+1);
        }
    };
    Follow(Entry.Location,0);
    return Result;
}
}
