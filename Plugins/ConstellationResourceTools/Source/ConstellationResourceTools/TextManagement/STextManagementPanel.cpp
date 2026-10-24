#include "TextManagementIndex.h"
#include "TextManagementEditing.h"
#include "TextManagementPresentation.h"
#include "TextManagementHistory.h"
#include "TextManagementCreation.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SSearchBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Layout/SSplitter.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SExpandableArea.h"
#include "Widgets/Views/SListView.h"
#include "Widgets/Views/STreeView.h"
#include "Widgets/Views/STableRow.h"
#include "Widgets/Views/SHeaderRow.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Docking/SDockTab.h"
#include "Styling/AppStyle.h"
#include "ToolMenus.h"
#include "Framework/Docking/TabManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "HAL/PlatformApplicationMisc.h"
#include "Misc/Paths.h"
#include "Misc/MessageDialog.h"
#include "Misc/ConfigCacheIni.h"
#include "UObject/Package.h"
#include "Modules/ModuleManager.h"
#include "UObject/UObjectGlobals.h"

namespace ConstellationText
{
static const FName TextTab(TEXT("Constellation.TextManagement"));
static FDelegateHandle MenuStartupHandle;
struct FUsageNode
{
    FString Id,Label;
    TSet<FString> Sources;
    TArray<TSharedPtr<FUsageNode>> Children;
};
class STextItemRow : public SMultiColumnTableRow<TSharedPtr<FTextItem>>
{
public:
    SLATE_BEGIN_ARGS(STextItemRow){} SLATE_ARGUMENT(TSharedPtr<FTextItem>,Item) SLATE_END_ARGS()
    void Construct(const FArguments& Args,const TSharedRef<STableViewBase>& Owner)
    {Item=Args._Item;FSuperRowType::Construct(FTableRowArgs().Padding(6),Owner);}
    virtual TSharedRef<SWidget> GenerateWidgetForColumn(const FName& Column)override
    {
        const FString Value=Column==TEXT("Key")?Item->Key:Item->Entry->Source;
        FSlateFontInfo Font=FAppStyle::GetFontStyle("NormalFont");Font.Size=Column==TEXT("Key")?10:12;
        return SNew(SBox).MaxDesiredHeight(68).Padding(4)[SNew(STextBlock).Text(FText::FromString(Value)).ToolTipText(FText::FromString(Value)).AutoWrapText(true)
            .Font(Font)];
    }
private:TSharedPtr<FTextItem> Item;
};
class STextManagementPanel : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(STextManagementPanel){} SLATE_END_ARGS()
    void Construct(const FArguments&)
    {
        for(const TCHAR* Value:{TEXT("내용 + 키"),TEXT("내용"),TEXT("키")})SearchModes.Add(MakeShared<FString>(Value));SearchMode=SearchModes[0];
        for(const TCHAR* Value:{TEXT("모든 저장 위치"),TEXT("DataTable"),TEXT("String Table"),TEXT("직접 입력")})StorageModes.Add(MakeShared<FString>(Value));StorageMode=StorageModes[0];
        for(const TCHAR* Value:{TEXT("모든 참조 상태"),TEXT("확인된 사용처"),TEXT("실행 중 키 결정"),TEXT("패키지 연결만 확인"),TEXT("연결 오류")})ReferenceModes.Add(MakeShared<FString>(Value));ReferenceMode=ReferenceModes[0];
        FSlateFontInfo EditFont=FAppStyle::GetFontStyle("NormalFont");EditFont.Size=14;
        LoadLayout();
        ChildSlot[SNew(SVerticalBox)
            +SVerticalBox::Slot().AutoHeight().Padding(10,8)[SNew(SHorizontalBox)
                +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[SNew(SButton).Text(FText::FromString(TEXT("대사 추가"))).IsEnabled_Lambda([this]{return !bBusy&&!Index.IsScanning();}).OnClicked_Lambda([this]{AddDialogue();return FReply::Handled();})]
                +SHorizontalBox::Slot().FillWidth(1)[SAssignNew(SearchBox,SSearchBox).HintText(FText::FromString(TEXT("대사 내용이나 키 검색"))).OnTextChanged_Lambda([this](const FText& Value){Query=Value.ToString();SearchAt=FPlatformTime::Seconds()+.15;})]
                +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[Combo(SearchModes,SearchMode)]
                +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[SNew(SCheckBox).OnCheckStateChanged_Lambda([this](ECheckBoxState State){bSearchAll=State==ECheckBoxState::Checked;Refresh();})[SNew(STextBlock).Text(FText::FromString(TEXT("전체 사용처 검색")))]]
                +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("새로고침"))).OnClicked_Lambda([this]{Start();return FReply::Handled();})]]
            +SVerticalBox::Slot().AutoHeight().Padding(10,0)[SNew(SExpandableArea).InitiallyCollapsed(true).HeaderContent()[SNew(STextBlock).Text(FText::FromString(TEXT("고급 필터 · 개발자 점검")))]
                .BodyContent()[SNew(SVerticalBox)
                    +SVerticalBox::Slot().AutoHeight().Padding(4)[SNew(SHorizontalBox)
                        +SHorizontalBox::Slot().AutoWidth()[Combo(StorageModes,StorageMode)]
                        +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[Combo(ReferenceModes,ReferenceMode)]
                        +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("미검사·실패 목록"))).OnClicked_Lambda([this]{ShowCoverage();return FReply::Handled();})]
                        +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[SNew(SButton).Text(FText::FromString(TEXT("검사 중단"))).IsEnabled_Lambda([this]{return Index.IsScanning();}).OnClicked_Lambda([this]{Index.Cancel();Rebuild();return FReply::Handled();})]]
                    +SVerticalBox::Slot().AutoHeight().Padding(4)[SNew(SHorizontalBox)
                        +SHorizontalBox::Slot().AutoWidth()[SNew(SCheckBox).OnCheckStateChanged_Lambda([this](ECheckBoxState S){bExamples=S==ECheckBoxState::Checked;Rebuild();})[SNew(STextBlock).Text(FText::FromString(TEXT("예제·Review 포함")))]]
                        +SHorizontalBox::Slot().AutoWidth().Padding(12,0)[SNew(SCheckBox).OnCheckStateChanged_Lambda([this](ECheckBoxState S){bHidden=S==ECheckBoxState::Checked;Rebuild();})[SNew(STextBlock).Text(FText::FromString(TEXT("식별용 필드·가려진 직접 값 포함")))]]]]]
            +SVerticalBox::Slot().AutoHeight().Padding(10,8)[SNew(STextBlock).Text_Lambda([this]{FString Path=TreeSelection;Path.ReplaceInline(TEXT("\t"),TEXT(" / "));return FText::FromString(bSearchAll?TEXT("전체 사용처"):Path.IsEmpty()?TEXT("전체 문자열"):Path);})]
            +SVerticalBox::Slot().FillHeight(1).Padding(10,0)[SNew(SSplitter).OnSplitterFinishedResizing_Lambda([this]{SaveLayout();})
                +SSplitter::Slot().Value_Lambda([this]{return PaneSizes[0];}).OnSlotResized_Lambda([this](float Value){PaneSizes[0]=Value;})[SAssignNew(Tree,STreeView<TSharedPtr<FUsageNode>>).TreeItemsSource(&Roots)
                    .OnGenerateRow_Lambda([](TSharedPtr<FUsageNode> Node,const TSharedRef<STableViewBase>& Owner){return SNew(STableRow<TSharedPtr<FUsageNode>>,Owner).Padding(5)[SNew(STextBlock).Text(FText::FromString(Node->Label+FString::Printf(TEXT(" (%d)"),Node->Sources.Num())))];})
                    .OnGetChildren_Lambda([](TSharedPtr<FUsageNode> Node,TArray<TSharedPtr<FUsageNode>>& Out){Out=Node->Children;})
                    .OnSelectionChanged_Lambda([this](TSharedPtr<FUsageNode> Node,ESelectInfo::Type){if(Node&&TreeSelection!=Node->Id){TreeSelection=Node->Id;Refresh();}})]
                +SSplitter::Slot().Value_Lambda([this]{return PaneSizes[1];}).OnSlotResized_Lambda([this](float Value){PaneSizes[1]=Value;})[SAssignNew(List,SListView<TSharedPtr<FTextItem>>).ListItemsSource(&Visible).SelectionMode(ESelectionMode::Single)
                    .HeaderRow(SNew(SHeaderRow)+SHeaderRow::Column(TEXT("Key")).DefaultLabel(FText::FromString(TEXT("대사 키"))).FillWidth(.37f)+SHeaderRow::Column(TEXT("Content")).DefaultLabel(FText::FromString(TEXT("대사 내용"))).FillWidth(.63f))
                    .OnGenerateRow_Lambda([](TSharedPtr<FTextItem> Item,const TSharedRef<STableViewBase>& Owner){return SNew(STextItemRow,Owner).Item(Item);})
                    .OnSelectionChanged_Lambda([this](TSharedPtr<FTextItem> Item,ESelectInfo::Type){if(Item){PreferredId=Item->Entry->Origin.Id();Selected=Item;ShowEntry();}})]
                +SSplitter::Slot().Value_Lambda([this]{return PaneSizes[2];}).OnSlotResized_Lambda([this](float Value){PaneSizes[2]=Value;})[SNew(SVerticalBox)
                    +SVerticalBox::Slot().AutoHeight().Padding(10,0,0,6)[SNew(STextBlock).Text_Lambda([this]{return FText::FromString(Selected?Selected->Key:TEXT("문자열을 선택하세요"));}).AutoWrapText(true)]
                    +SVerticalBox::Slot().FillHeight(.45f).Padding(10,0,0,6)[SAssignNew(Editor,SMultiLineEditableTextBox).Font(EditFont)
                        .IsReadOnly_Lambda([this]{return !bEditable;}).OnTextChanged_Lambda([this](const FText& Value){if(!bSettingText&&Selected)if(auto* Draft=Drafts.Find(Selected->Entry->Origin.Id()))Draft->Text=Value.ToString();})]
                    +SVerticalBox::Slot().AutoHeight().Padding(10,0,0,8)[SNew(SHorizontalBox)
                        +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("저장"))).IsEnabled_Lambda([this]{return CanSave();}).OnClicked_Lambda([this]{SaveSelected();return FReply::Handled();})]
                        +SHorizontalBox::Slot().FillWidth(1).Padding(10,0)[SNew(STextBlock).Text_Lambda([this]{return FText::FromString(EditStatus());}).AutoWrapText(true)]]
                    +SVerticalBox::Slot().FillHeight(.55f).Padding(10,0,0,0)[SAssignNew(Details,SScrollBox)]]]
            +SVerticalBox::Slot().AutoHeight().Padding(10,8)[SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return FText::FromString(Status());})]
            +SVerticalBox::Slot().AutoHeight().Padding(10,0,10,8)[SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return Message;})]];
        FCoreUObjectDelegates::OnObjectPropertyChanged.AddSP(this,&STextManagementPanel::ObjectChanged);
        FCoreUObjectDelegates::OnObjectTransacted.AddSP(this,&STextManagementPanel::ObjectTransacted);
        FCoreUObjectDelegates::OnObjectModified.AddSP(this,&STextManagementPanel::ObjectModified);
        auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
        Registry.OnAssetAdded().AddSP(this,&STextManagementPanel::AssetChanged);Registry.OnAssetRemoved().AddSP(this,&STextManagementPanel::AssetChanged);
        Registry.OnAssetUpdated().AddSP(this,&STextManagementPanel::AssetChanged);Registry.OnAssetRenamed().AddSP(this,&STextManagementPanel::AssetRenamed);
        Start();
    }
    virtual ~STextManagementPanel()
    {
        FCoreUObjectDelegates::OnObjectPropertyChanged.RemoveAll(this);FCoreUObjectDelegates::OnObjectTransacted.RemoveAll(this);FCoreUObjectDelegates::OnObjectModified.RemoveAll(this);
        if(auto* Module=FModuleManager::GetModulePtr<FAssetRegistryModule>("AssetRegistry")){Module->Get().OnAssetAdded().RemoveAll(this);Module->Get().OnAssetRemoved().RemoveAll(this);Module->Get().OnAssetUpdated().RemoveAll(this);Module->Get().OnAssetRenamed().RemoveAll(this);}
    }
    bool CanClose()
    {
        if(bBusy)return false;
        if(!HasDrafts())return true;
        TGuardValue<bool> Busy(bBusy,true);
        const auto Choice=FMessageDialog::Open(EAppMsgType::YesNoCancel,FText::FromString(TEXT("미저장 초안이 있습니다. 모두 저장하고 닫을까요?\n예: 저장 후 닫기 / 아니요: 초안을 버리고 닫기 / 취소: 계속 편집\n저장 시 해당 에셋의 다른 미저장 변경도 함께 저장됩니다.\n원본에 적용된 저장 실패 항목은 아니요를 눌러도 에셋의 미저장 변경으로 남습니다.")));
        if(Choice==EAppReturnType::Cancel)return false;
        if(Choice==EAppReturnType::No)return true;
        for(auto& Pair:Drafts)if(Pair.Value.IsDirty())if(!CommitTextDraft(Pair.Value,HistoryDirectory(),Message,SaveEdit))return false;
        return true;
    }
    virtual void Tick(const FGeometry& Geometry,double Time,float Delta)override
    {
        SCompoundWidget::Tick(Geometry,Time,Delta);if(bBusy)return;bool bAdvanced;
        {TGuardValue<bool> Guard(bCollecting,true);bAdvanced=Index.Tick();}
        if(bAdvanced&&(FPlatformTime::Seconds()>NextRefresh||!Index.IsScanning())){Rebuild();NextRefresh=FPlatformTime::Seconds()+.5;}
        if(SearchAt>0&&FPlatformTime::Seconds()>=SearchAt){SearchAt=0;Refresh();}
    }
private:
    TSharedPtr<SSearchBox> SearchBox;
    void AddDialogue()
    {
        TGuardValue<bool> Busy(bBusy,true);
        UDataTable* Initial=Selected?Cast<UDataTable>(Selected->Entry->Origin.Asset.TryLoad()):nullptr;
        if(!Initial)Initial=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.DT_SequenceStringData"));
        FTextDraft Draft;if(!ShowCreateDialogue(Initial,Draft,Message))return;
        const FString Id=Draft.Base.Target.Id();
        CommitTextDraft(Draft,HistoryDirectory(),Message,SaveEdit);
        Drafts.Add(Id,MoveTemp(Draft));PreferredId=Id;
        TreeSelection.Reset();Tree->ClearSelection();SearchBox->SetText(FText::GetEmpty());Query.Reset();
        StorageMode=StorageModes[0];ReferenceMode=ReferenceModes[0];
        const FText Result=Message;Start();Message=Result;
    }
    FIndex Index;
    TArray<TSharedPtr<FTextItem>> Items,Visible;
    TArray<TSharedPtr<FUsageNode>> Roots;
    TSharedPtr<STreeView<TSharedPtr<FUsageNode>>> Tree;
    TSharedPtr<SListView<TSharedPtr<FTextItem>>> List;
    TSharedPtr<SMultiLineEditableTextBox> Editor;
    TSharedPtr<SScrollBox> Details;
    TSharedPtr<FTextItem> Selected;
    TMap<FString,FTextDraft> Drafts;
    TMap<FString,FString> CategoryCache;
    TArray<TSharedPtr<FString>> SearchModes,StorageModes,ReferenceModes;
    TSharedPtr<FString> SearchMode,StorageMode,ReferenceMode;
    FString Query,TreeSelection,PreferredId;
    FText Message;
    bool bExamples=false,bHidden=false,bStale=false,bCollecting=false,bSearchAll=false,bSettingText=false,bEditable=false,bBusy=false;
    double NextRefresh=0,SearchAt=0;
    float PaneSizes[3]={.21f,.40f,.39f};
    FString LayoutFile()const{return FPaths::ProjectSavedDir()/TEXT("Config/StringManagementLayout.ini");}
    void LoadLayout()
    {
        FConfigFile File;File.Read(LayoutFile());
        for(int32 I=0;I<3;++I){float Value;if(File.GetFloat(TEXT("Layout"),*FString::Printf(TEXT("Pane%d"),I),Value)&&FMath::IsFinite(Value)&&Value>.05f&&Value<.9f)PaneSizes[I]=Value;}
    }
    void SaveLayout()
    {
        FConfigFile File;for(int32 I=0;I<3;++I)File.SetFloat(TEXT("Layout"),*FString::Printf(TEXT("Pane%d"),I),PaneSizes[I]);File.Write(LayoutFile());
    }
    FString CategoryFile()const{return FPaths::ProjectConfigDir()/TEXT("StringManagement.ini");}
    FString HistoryDirectory()const{return FPaths::ProjectSavedDir()/TEXT("StringManagementHistory");}
    FString ItemCategory(const FEntry& E){if(auto* Found=CategoryCache.Find(E.Origin.Id()))return *Found;const FString Value=Category(E,CategoryFile());CategoryCache.Add(E.Origin.Id(),Value);return Value;}
    TSharedRef<SWidget> Combo(TArray<TSharedPtr<FString>>& Values,TSharedPtr<FString>& Current)
    {
        auto* ValuePtr=&Current;
        return SNew(SComboBox<TSharedPtr<FString>>).OptionsSource(&Values).InitiallySelectedItem(Current)
            .OnGenerateWidget_Lambda([](TSharedPtr<FString> Value){return SNew(STextBlock).Text(FText::FromString(*Value));})
            .OnSelectionChanged_Lambda([this,ValuePtr](TSharedPtr<FString> Value,ESelectInfo::Type){if(Value){*ValuePtr=Value;Refresh();}})
            [SNew(STextBlock).Text_Lambda([ValuePtr]{return FText::FromString(**ValuePtr);})];
    }
    bool HasDrafts()const{for(const auto& Pair:Drafts)if(Pair.Value.IsDirty())return true;return false;}
    bool CanSave()const{return !bBusy&&bEditable&&Selected&&!Index.IsScanning()&&Drafts.Contains(Selected->Entry->Origin.Id())&&Drafts.FindChecked(Selected->Entry->Origin.Id()).IsDirty();}
    FString EditStatus()const
    {
        if(!Selected)return TEXT("선택한 문구를 편집할 수 있습니다");
        if(const auto* Draft=Drafts.Find(Selected->Entry->Origin.Id()))
        {if(!Draft->PendingId.IsEmpty())return TEXT("디스크 저장 대기 · 저장으로 재시도");if(Draft->IsDirty())return TEXT("수정 중 · 다른 항목을 선택해도 초안 유지");}
        return bEditable?TEXT("변경 없음"):TEXT("원본 에디터에서 수정");
    }
    void Start(){CategoryCache.Reset();bStale=false;Index.Start();Rebuild();Message=FText::FromString(TEXT("사용처를 검사하고 있습니다. 미저장 초안은 유지됩니다."));}
    bool InScope(const FString& Path)const{return Path.StartsWith(TEXT("/Game/Constellation/"))||Path.StartsWith(TEXT("/Game/SceneDirector/"));}
    void ObjectChanged(UObject* Object,FPropertyChangedEvent&){ObjectModified(Object);}
    void ObjectModified(UObject* Object){if(!bCollecting&&Object&&InScope(Object->GetOutermost()->GetName()))bStale=true;}
    void ObjectTransacted(UObject* Object,const FTransactionObjectEvent&){ObjectModified(Object);}
    void AssetChanged(const FAssetData& Asset){if(!bCollecting&&InScope(Asset.PackageName.ToString()))bStale=true;}
    void AssetRenamed(const FAssetData& Asset,const FString& Old){if(InScope(Old)||InScope(Asset.PackageName.ToString()))bStale=true;}
    void Rebuild()
    {
        // Empty new rows are omitted by the scanner. Keep their unsaved drafts reachable,
        // including when the history journal could not be written before applying text.
        for(const auto& Pair:Drafts)if(Pair.Value.IsDirty()&&!Index.Entries.ContainsByPredicate([&](const TSharedPtr<FEntry>& E){return E->Origin.Id()==Pair.Key;}))
        {
            auto Entry=MakeShared<FEntry>();Entry->Origin=Entry->Location=Pair.Value.Base.Target;
            FEditSnapshot Current;FText Error;
            if(ReadEdit(*Entry,Current,Error)){Entry->Source=Current.Source;Entry->Display=Current.Source;Index.Entries.Add(Entry);}
        }
        Items=BuildTextItems(Index,bExamples,bHidden);Roots.Reset();
        TMap<FString,TSharedPtr<FUsageNode>> Nodes;
        auto All=MakeShared<FUsageNode>();All->Label=TEXT("전체 문자열");Roots.Add(All);Nodes.Add(TEXT(""),All);
        for(const auto& Item:Items)
        {
            const FString SourceId=Item->Entry->Origin.Id(),Cat=ItemCategory(*Item->Entry);All->Sources.Add(SourceId);
            auto Ensure=[&](const FString& Id,const FString& Label,TArray<TSharedPtr<FUsageNode>>& Parent)->TSharedPtr<FUsageNode>
            {if(auto* Existing=Nodes.Find(Id))return *Existing;auto Node=MakeShared<FUsageNode>();Node->Id=Id;Node->Label=Label;Nodes.Add(Id,Node);Parent.Add(Node);return Node;};
            auto CatNode=Ensure(Cat,Cat,Roots);CatNode->Sources.Add(SourceId);
            for(const FString& Group:Item->Groups)
            {
                TArray<FString> Parts;Group.ParseIntoArray(Parts,TEXT("/"));auto Parent=CatNode;FString Path;
                for(const FString& Part:Parts){Path+=(Path.IsEmpty()?TEXT(""):TEXT("/"))+Part;Parent=Ensure(Cat+TEXT("\t")+Path,Part,Parent->Children);Parent->Sources.Add(SourceId);}
            }
        }
        if(Tree){Tree->RequestTreeRefresh();for(const auto& Root:Roots)Tree->SetItemExpansion(Root,true);if(auto* Node=Nodes.Find(TreeSelection))Tree->SetSelection(*Node,ESelectInfo::Direct);}
        Refresh();

    }
    void Refresh()
    {
        Visible.Reset();
        for(const auto& Item:Items)
        {
            const auto& E=*Item->Entry;
            if(!bSearchAll&&!TreeSelection.IsEmpty())
            {
                FString Cat,Group;if(!TreeSelection.Split(TEXT("\t"),&Cat,&Group))Cat=TreeSelection;
                if(ItemCategory(E)!=Cat)continue;
                if(!Group.IsEmpty()&&!Item->Groups.ContainsByPredicate([&](const FString& Value){return Value==Group||Value.StartsWith(Group+TEXT("/"));}))continue;
            }
            FEntry Search;Search.Source=SearchMode==SearchModes[2]?FString():E.Source;Search.Context=SearchMode==SearchModes[1]?FString():Item->Key;
            if(!FIndex::Matches(Search,Query))continue;
            if(StorageMode==StorageModes[1]&&E.Origin.Kind!=ELocationKind::DataTable)continue;
            if(StorageMode==StorageModes[2]&&E.Origin.Kind!=ELocationKind::StringTable)continue;
            if(StorageMode==StorageModes[3]&&(E.Origin.Kind==ELocationKind::DataTable||E.Origin.Kind==ELocationKind::StringTable))continue;
            const int32 Ref=ReferenceModes.IndexOfByKey(ReferenceMode);
            if(Ref>0)
            {
                const EReferenceKind Wanted=Ref==1?EReferenceKind::Exact:Ref==2?EReferenceKind::Dynamic:Ref==3?EReferenceKind::Candidate:EReferenceKind::Broken;
                if(!Item->Usages.ContainsByPredicate([&](const FUsage& Use){return Use.Kind==Wanted;})&&!(Ref==4&&E.Source.StartsWith(TEXT("[연결 오류]"))))continue;
            }
            Visible.Add(Item);
        }
        if(List)
        {
            List->RequestListRefresh();
            const auto* Match=Visible.FindByPredicate([&](const TSharedPtr<FTextItem>& Item){return Item->Entry->Origin.Id()==PreferredId;});
            if(Match){if(Selected!=*Match){Selected=*Match;List->SetSelection(Selected,ESelectInfo::Direct);} }
            else {Selected.Reset();List->ClearSelection();ShowEntry();}
        }
    }
    FString Status()const
    {
        int32 Unscanned=0;for(const auto& C:Index.Coverage)if(C.State!=TEXT("검사 완료"))++Unscanned;
        return FString::Printf(TEXT("%d개 문구 · %s · 미검사/실패 %d · 사용처 미확인은 미사용 판정이 아닙니다.%s"),Visible.Num(),Index.IsScanning()?TEXT("검사 중 — 부분 결과"):TEXT("검사 종료"),Unscanned,bStale?TEXT(" · 원본 변경 감지: 새로고침 권장"):TEXT(""));
    }
    void Text(const TSharedRef<SVerticalBox>& Box,const FString& Value){Box->AddSlot().AutoHeight().Padding(0,4)[SNew(STextBlock).Text(FText::FromString(Value)).AutoWrapText(true)];}
    void Navigation(const TSharedRef<SVerticalBox>& Box,const FString& Label,const FLocation& Loc)
    {Box->AddSlot().AutoHeight().Padding(0,3)[SNew(SButton).Text(FText::FromString(Label)).OnClicked_Lambda([this,Loc]{Navigate(Loc,Message);return FReply::Handled();})];}
    void Section(const FString& Label,const TSharedRef<SWidget>& Content,bool bCollapsed)
    {Details->AddSlot().Padding(0,6)[SNew(SExpandableArea).InitiallyCollapsed(bCollapsed).HeaderContent()[SNew(STextBlock).Text(FText::FromString(Label))].BodyContent()[Content]];}
    void SaveSelected()
    {
        if(!Selected||bBusy)return;auto* Draft=Drafts.Find(Selected->Entry->Origin.Id());if(!Draft)return;
        TGuardValue<bool> Busy(bBusy,true);
        UObject* Object=Draft->Base.Target.Asset.ResolveObject();
        if(Object&&Object->GetOutermost()->IsDirty()&&Draft->PendingId.IsEmpty())
        {
            if(FMessageDialog::Open(EAppMsgType::YesNo,FText::FromString(TEXT("원본 에셋에 다른 미저장 변경이 있습니다. 이 문구와 함께 저장할까요?")))!=EAppReturnType::Yes)return;
        }
        bool bSaved;{TGuardValue<bool> Guard(bCollecting,true);bSaved=CommitTextDraft(*Draft,HistoryDirectory(),Message,SaveEdit);}
        if(bSaved)
        {
            for(auto& E:Index.Entries)if(E->Origin.Id()==Draft->Base.Target.Id()){E->Source=Draft->Base.Source;E->Display=Draft->Base.Source;}
            Rebuild();
        }
        else ShowEntry();
    }
    void ShowEntry()
    {
        Details->ClearChildren();Details->ScrollToStart();bEditable=false;
        if(!Selected){TGuardValue<bool> Guard(bSettingText,true);Editor->SetText(FText::GetEmpty());return;}
        const auto Current=Selected;const FString Id=Current->Entry->Origin.Id();FEditSnapshot Snapshot;FText Reason;
        if(ReadEdit(*Current->Entry,Snapshot,Reason))
        {
            bEditable=true;
            if(!Drafts.Contains(Id)){FTextDraft Draft;Draft.Base=Snapshot;Draft.Text=Snapshot.Source;Drafts.Add(Id,Draft);}
            auto& Draft=Drafts.FindChecked(Id);
            if(!Draft.IsDirty()){Draft.Base=Snapshot;Draft.Text=Snapshot.Source;}
            {TGuardValue<bool> Guard(bSettingText,true);if(Editor->GetText().ToString()!=Draft.Text)Editor->SetText(FText::FromString(Draft.Text));}
            if(Draft.Base.Source!=Snapshot.Source||(Snapshot.Target.Kind!=ELocationKind::StringTable&&!Draft.Base.Original.IdenticalTo(Snapshot.Original)))
            {
                auto Conflict=SNew(SVerticalBox);Text(Conflict,TEXT("외부 수정 감지 · 내 초안은 유지됩니다. 최신 원문:\n")+Snapshot.Source);
                Conflict->AddSlot().AutoHeight()[SNew(SButton).Text(FText::FromString(TEXT("초안을 버리고 최신 원문 불러오기"))).OnClicked_Lambda([this,Id]
                {if(FMessageDialog::Open(EAppMsgType::YesNo,FText::FromString(TEXT("이 문구의 미저장 초안을 버릴까요?")))==EAppReturnType::Yes){Drafts.Remove(Id);ShowEntry();}return FReply::Handled();})];
                Section(TEXT("원문 충돌"),Conflict,false);
            }
        }
        else {TGuardValue<bool> Guard(bSettingText,true);Editor->SetText(FText::FromString(Current->Entry->Source));auto Info=SNew(SVerticalBox);Text(Info,Reason.ToString());Navigation(Info,TEXT("원본 에디터 열기"),Current->Entry->Origin);Section(TEXT("편집 안내"),Info,false);}
        auto Classification=SNew(SVerticalBox);auto CategoryDraft=MakeShared<FString>(ItemCategory(*Current->Entry));
        Text(Classification,TEXT("용도 분류"));Classification->AddSlot().AutoHeight()[SNew(SEditableTextBox).Text(FText::FromString(*CategoryDraft)).OnTextChanged_Lambda([CategoryDraft](const FText& Value){*CategoryDraft=Value.ToString();})];
        Classification->AddSlot().AutoHeight().Padding(0,4)[SNew(SHorizontalBox)
            +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("분류 변경"))).OnClicked_Lambda([this,Current,CategoryDraft]{if(SetCategory(*Current->Entry,*CategoryDraft,CategoryFile(),Message)){CategoryCache.Reset();Rebuild();}return FReply::Handled();})]
            +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[SNew(SButton).Text(FText::FromString(TEXT("자동 분류"))).OnClicked_Lambda([this,Current]{if(SetCategory(*Current->Entry,TEXT(""),CategoryFile(),Message)){CategoryCache.Reset();Rebuild();}return FReply::Handled();})]];
        Text(Classification,TEXT("사용처: ")+FString::Join(Current->Groups,TEXT(", ")));
        TSet<FString> Exact;bool bDynamic=false;
        for(const auto& Use:Current->Usages){if(Use.Kind==EReferenceKind::Exact)Exact.Add(Use.Consumer.Id());bDynamic|=Use.Kind==EReferenceKind::Dynamic;}
        Text(Classification,FString::Printf(TEXT("확인된 참조 위치 %d개%s · 같은 원본의 문구가 함께 바뀝니다."),Exact.Num(),bDynamic?TEXT(" / 실행 중 결정되는 참조도 있음"):TEXT("")));
        Section(TEXT("분류 · 사용처"),Classification,false);
        auto History=SNew(SVerticalBox);Text(History,TEXT("이 도구에서 저장한 로컬 변경 이력입니다. 외부 에디터·다른 작업자의 변경 전체를 기록하지는 않습니다. 시간은 UTC입니다."));
        const auto Revisions=ReadTextHistory(HistoryDirectory(),Id);
        if(Revisions.IsEmpty())Text(History,TEXT("아직 저장 이력이 없습니다."));
        for(const auto& Revision:Revisions)
        {
            Text(History,Revision.Time+TEXT(" · ")+(Revision.State==TEXT("Saved")?TEXT("저장 완료"):TEXT("저장 미완료/확인 필요")));
            Text(History,TEXT("변경 전\n")+Revision.Before+TEXT("\n변경 후\n")+Revision.After);
            if(Revision.State==TEXT("Saved"))History->AddSlot().AutoHeight().Padding(0,4)[SNew(SButton).Text(FText::FromString(TEXT("변경 전 복원·저장"))).IsEnabled_Lambda([this]{return bEditable&&!Index.IsScanning();})
                .OnClicked_Lambda([this,Id,Revision]
                {
                    auto* Draft=Drafts.Find(Id);if(Draft&&StageTextRestore(*Draft,Revision,Message)){ShowEntry();SaveSelected();}return FReply::Handled();
                })];
            if(Revision.State==TEXT("Saved"))History->AddSlot().AutoHeight().Padding(0,4)[SNew(SButton).Text(FText::FromString(TEXT("이 버전(변경 후) 복원·저장"))).IsEnabled_Lambda([this]{return bEditable&&!Index.IsScanning();})
                .OnClicked_Lambda([this,Id,Revision]{auto* Draft=Drafts.Find(Id);if(Draft&&StageTextRestore(*Draft,Revision,Message,false)){ShowEntry();SaveSelected();}return FReply::Handled();})];
        }
        Section(FString::Printf(TEXT("변경 이력 (%d)"),Revisions.Num()),History,true);
        auto Technical=SNew(SVerticalBox);Text(Technical,TEXT("수정 원본: ")+Current->Entry->Origin.Label());Text(Technical,Current->Entry->Context);
        Navigation(Technical,TEXT("원본 에디터 열기"),Current->Entry->Origin);
        for(const auto& Use:Current->Usages){Text(Technical,ReferenceLabel(Use.Kind)+TEXT(" · ")+Use.Reason);Navigation(Technical,Use.Consumer.Label(),Use.Consumer);}
        const FString Path=Current->Entry->Origin.Id();Technical->AddSlot().AutoHeight()[SNew(SButton).Text(FText::FromString(TEXT("원본·속성 식별 경로 복사"))).OnClicked_Lambda([Path]{FPlatformApplicationMisc::ClipboardCopy(*Path);return FReply::Handled();})];
        Section(TEXT("기술 정보 · 원본/사용처 이동"),Technical,true);
    }
    void ShowCoverage()
    {
        Details->ClearChildren();auto Coverage=SNew(SVerticalBox);
        for(const auto& C:Index.Coverage)if(C.State!=TEXT("검사 완료"))Text(Coverage,C.State+TEXT(" · ")+C.Asset+TEXT("\n")+C.Reason);
        Section(TEXT("미검사·실패 목록"),Coverage,false);
    }
};
void RegisterTextManagement()
{
    FGlobalTabmanager::Get()->RegisterNomadTabSpawner(TextTab,FOnSpawnTab::CreateLambda([](const FSpawnTabArgs&)
    {
        TSharedRef<STextManagementPanel> Panel=SNew(STextManagementPanel);
        TSharedRef<SDockTab> Tab=SNew(SDockTab).TabRole(ETabRole::NomadTab)[Panel];
        Tab->SetCanCloseTab(SDockTab::FCanCloseTab::CreateSP(Panel,&STextManagementPanel::CanClose));return Tab;
    })).SetDisplayName(FText::FromString(TEXT("문자열 관리")));
    MenuStartupHandle=UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateLambda([]
    {
        FToolMenuOwnerScoped Owner(TextTab);auto* Menu=UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
        Menu->FindOrAddSection("Constellation",FText::FromString(TEXT("Constellation"))).AddMenuEntry("ConstellationTextManagement",FText::FromString(TEXT("문자열 관리")),FText::FromString(TEXT("사용처별 대사 편집과 변경 이력")),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([]{FGlobalTabmanager::Get()->TryInvokeTab(TextTab);}))); 
    }));
}
void UnregisterTextManagement()
{
    UToolMenus::UnRegisterStartupCallback(MenuStartupHandle);
    if(auto Tab=FGlobalTabmanager::Get()->FindExistingLiveTab(TextTab))Tab->RequestCloseTab();
    FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(TextTab);UToolMenus::UnregisterOwner(TextTab);
}
}
