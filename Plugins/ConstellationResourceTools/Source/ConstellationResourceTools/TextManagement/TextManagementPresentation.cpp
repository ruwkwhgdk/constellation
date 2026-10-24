#include "TextManagementPresentation.h"
#include "SceneDirectorAsset.h"

namespace ConstellationText
{
FString DisplayKey(const FLocation& Location)
{
    if(!Location.Row.IsNone())return Location.Row.ToString();
    if(!Location.Key.IsEmpty())return Location.Key;
    if(Location.Kind==ELocationKind::Director)
    {
        FString Label=TEXT("대사");
        if(auto* Event=Cast<USceneDirectorAsset>(Location.Event.ResolveObject()))
        {
            const int32 Index=Event->Steps.IndexOfByPredicate([&](const FDirectorStep& Step){return Step.Id==Location.Node;});
            if(Index!=INDEX_NONE)Label+=FString::Printf(TEXT(" %d"),Index+1);
        }
        if(!Location.Choice.IsNone())Label+=TEXT(" / 선택지 ")+Location.Choice.ToString();
        else if(Location.Field==TEXT("SpeakerName"))Label+=TEXT(" / 화자");
        if(Location.Field==TEXT("DisabledReason"))Label+=TEXT(" / 선택 불가 사유");
        return Label;
    }
    return Location.Field.IsEmpty()?Location.Asset.GetAssetName():Location.Field;
}
FString UsageGroup(const FLocation& Location)
{
    FString Name=Location.Asset.GetAssetName();Name.RemoveFromStart(TEXT("DA_"));Name.RemoveFromStart(TEXT("BP_"));
    if(Location.Kind==ELocationKind::Director)
    {
        if(auto* Event=Cast<USceneDirectorAsset>(Location.Event.ResolveObject());Event&&!Event->EventKey.IsNone())Name=Event->EventKey.ToString();
        const FString Path=Location.Asset.ToString();
        const bool bSchool=Path.Contains(TEXT("/School/"))||Path.Contains(TEXT("AbandonedSchool"))||Path.Contains(TEXT("DA_S0_"));
        // Friendly aliases change only presentation, never the source key or asset name.
        if(bSchool)
        {
            if(Name.StartsWith(TEXT("S0_"))||Name==TEXT("S0"))Name=TEXT("S0");
            return TEXT("폐교 (AbandonedSchool)/")+Name;
        }
        return TEXT("이벤트/")+Name;
    }
    return TEXT("에셋/")+Name;
}
static bool IsIdentifierField(const FEntry& Entry)
{
    const FString Name=Entry.Location.Asset.GetAssetName();
    return Entry.Location.Kind==ELocationKind::DataTable&&(Name==TEXT("DT_SequenceStringData")||Name==TEXT("DT_RegionStringData"))&&Entry.Location.Field.StartsWith(TEXT("Name_"));
}
TArray<TSharedPtr<FTextItem>> BuildTextItems(const FIndex& Index,bool bIncludeExamples,bool bIncludeHidden)
{
    TArray<TSharedPtr<FTextItem>> Items;TMap<FString,TSharedPtr<FTextItem>> ByOrigin;
    for(const auto& Entry:Index.Entries)
    {
        if(!bIncludeHidden&&(Entry->bShadowed||IsIdentifierField(*Entry)))continue;
        if(!bIncludeExamples&&(Entry->Location.Asset.ToString().Contains(TEXT("/Examples/"))||Entry->Location.Asset.ToString().Contains(TEXT("/Review/"))))continue;
        const FString Id=Entry->Origin.Id();auto* Existing=ByOrigin.Find(Id);
        TSharedPtr<FTextItem> Item;
        if(Existing)Item=*Existing;
        else {Item=MakeShared<FTextItem>();Item->Entry=Entry;Item->Key=DisplayKey(Entry->Origin);ByOrigin.Add(Id,Item);Items.Add(Item);}
        if(Entry->Location.Id()==Id)Item->Entry=Entry;
        Item->Locations.Add(Entry->Location);
    }
    for(auto& Item:Items)
    {
        FEntry Source=*Item->Entry;Source.Location=Source.Origin;
        Item->Usages=Index.FindUsages(Source);
        for(const auto& Location:Item->Locations)
        {
            if(Location.Kind==ELocationKind::Director||Location.Kind==ELocationKind::BlueprintNode||Location.Kind==ELocationKind::Asset)Item->Groups.AddUnique(UsageGroup(Location));
        }
        for(const auto& Use:Item->Usages)
        {
            if(Use.Kind!=EReferenceKind::Exact)continue;
            if(!bIncludeExamples&&(Use.Consumer.Asset.ToString().Contains(TEXT("/Examples/"))||Use.Consumer.Asset.ToString().Contains(TEXT("/Review/"))))continue;
            if(Use.Consumer.Kind!=ELocationKind::DataTable&&Use.Consumer.Kind!=ELocationKind::StringTable)Item->Groups.AddUnique(UsageGroup(Use.Consumer));
        }
        if(Item->Groups.IsEmpty())Item->Groups.Add(TEXT("사용처 미확인"));
        Item->Groups.Sort();
    }
    Items.Sort([](const TSharedPtr<FTextItem>& A,const TSharedPtr<FTextItem>& B){return A->Key==B->Key?A->Entry->Origin.Id()<B->Entry->Origin.Id():A->Key<B->Key;});
    return Items;
}
}
