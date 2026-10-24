#include "TextManagementCreation.h"
#include "DataTableEditorUtils.h"
#include "UObject/UnrealType.h"
#include "ScopedTransaction.h"
#include "PropertyCustomizationHelpers.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Misc/MessageDialog.h"
#include "UObject/Package.h"
#include "UObject/StrongObjectPtr.h"
namespace ConstellationText
{
TArray<FString> DialogueFields(UDataTable* Table)
{
    TArray<FString> Result;
    if(Table&&Table->GetRowStruct())for(TFieldIterator<FTextProperty> It(Table->GetRowStruct());It;++It)
        if(It->ArrayDim==1&&!((Table->GetName()==TEXT("DT_SequenceStringData")||Table->GetName()==TEXT("DT_RegionStringData"))&&It->GetName().StartsWith(TEXT("Name_"))))Result.Add(It->GetName());
    return Result;
}
bool CreateDialogueDraft(UDataTable* Table,const FString& Key,const FString& Field,const FString& Content,FTextDraft& Draft,FText& Message)
{
    auto Fail=[&](const TCHAR* Text){Message=FText::FromString(Text);return false;};
    if(!Table||!DialogueFields(Table).Contains(Field))return Fail(TEXT("대사를 저장할 테이블과 텍스트 필드를 선택하세요."));
    if(Key.IsEmpty()||Key.Len()>=NAME_SIZE||Key!=Key.TrimStartAndEnd()||Key.Contains(TEXT("\n"))||Key.Contains(TEXT("\r"))||Key.Contains(TEXT("\t"))||FName(*Key).IsNone())return Fail(TEXT("키는 앞뒤 공백이나 줄바꿈 없이 입력하세요. None은 사용할 수 없습니다."));
    if(Table->GetRowMap().Contains(FName(*Key)))return Fail(TEXT("같은 키가 이미 존재합니다. 대소문자만 다른 키도 사용할 수 없습니다."));
    if(Content.TrimStartAndEnd().IsEmpty())return Fail(TEXT("대사 내용을 입력하세요."));
    FScopedTransaction Transaction(FText::FromString(TEXT("대사 추가")));
    uint8* Row=FDataTableEditorUtils::AddRow(Table,FName(*Key));
    if(!Row)return Fail(TEXT("행을 추가하지 못했습니다."));
    // New rows use schema defaults, never a copy of another dialogue's data or localization identity.
    auto* Property=FindFProperty<FTextProperty>(Table->GetRowStruct(),*Field);
    Property->SetPropertyValue_InContainer(Row,FText::ChangeKey(Table->GetPathName(),FGuid::NewGuid().ToString(),FText::FromString(TEXT(""))));
    Table->MarkPackageDirty();
    FDataTableEditorUtils::BroadcastPostChange(Table,FDataTableEditorUtils::EDataTableChangeInfo::RowData);
    FEntry Entry;Entry.Origin.Kind=ELocationKind::DataTable;Entry.Origin.Asset=FSoftObjectPath(Table);Entry.Origin.Row=FName(*Key);Entry.Origin.Field=Field;Entry.Location=Entry.Origin;
    FTextDraft NewDraft;if(!ReadEdit(Entry,NewDraft.Base,Message))return false;
    NewDraft.Text=Content;Draft=MoveTemp(NewDraft);return true;
}
bool ShowCreateDialogue(UDataTable* Initial,FTextDraft& Draft,FText& Message)
{
    TStrongObjectPtr<UDataTable> Table(Initial);
    TArray<TSharedPtr<FString>> Fields;TSharedPtr<FString> Field;
    TSharedPtr<SComboBox<TSharedPtr<FString>>> FieldCombo;
    auto UpdateFields=[&]{Fields.Reset();Field.Reset();for(const FString& Name:DialogueFields(Table.Get()))Fields.Add(MakeShared<FString>(Name));
        if(Fields.Num())Field=Fields[0];for(auto Option:Fields)if(Option->StartsWith(TEXT("Description")))Field=Option;
        if(FieldCombo){FieldCombo->RefreshOptions();FieldCombo->SetSelectedItem(Field);}};
    UpdateFields();FString Key=TEXT("Dialogue_")+FGuid::NewGuid().ToString(EGuidFormats::Digits),Content;FText Error;bool Created=false;
    auto Window=SNew(SWindow).Title(FText::FromString(TEXT("대사 추가"))).ClientSize(FVector2D(620,440)).SupportsMaximize(false).SupportsMinimize(false);
    Window->SetContent(SNew(SVerticalBox)
        +SVerticalBox::Slot().AutoHeight().Padding(12)[SNew(STextBlock).Text(FText::FromString(TEXT("기존 DataTable에 새 행을 추가합니다. 다른 필드는 기본값을 사용합니다.\n키는 순서와 무관한 고정 ID입니다. 중간에 추가해도 기존 키는 변경하지 않습니다.\n재생 순서와 이벤트 연결은 이벤트 에디터에서 지정하세요. 연결 전에는 사용처 미확인으로 표시됩니다."))).AutoWrapText(true)]
        +SVerticalBox::Slot().AutoHeight().Padding(12,4)[SNew(SObjectPropertyEntryBox).AllowedClass(UDataTable::StaticClass())
            .OnShouldFilterAsset_Lambda([](const FAssetData& Asset){const FString Path=Asset.PackageName.ToString();return Path.Contains(TEXT("/Examples/"))||Path.Contains(TEXT("/Review/"))||(!Path.StartsWith(TEXT("/Game/Constellation/"))&&!Path.StartsWith(TEXT("/Game/SceneDirector/")));})
            .ObjectPath_Lambda([&]{return Table.IsValid()?Table->GetPathName():FString();})
            .OnObjectChanged_Lambda([&](const FAssetData& Asset){Table.Reset(Cast<UDataTable>(Asset.GetAsset()));UpdateFields();})]
        +SVerticalBox::Slot().AutoHeight().Padding(12,4)[SAssignNew(FieldCombo,SComboBox<TSharedPtr<FString>>).OptionsSource(&Fields).InitiallySelectedItem(Field)
            .OnGenerateWidget_Lambda([](TSharedPtr<FString> Value){return SNew(STextBlock).Text(FText::FromString(*Value));})
            .OnSelectionChanged_Lambda([&](TSharedPtr<FString> Value,ESelectInfo::Type){Field=Value;})[SNew(STextBlock).Text_Lambda([&]{return FText::FromString(Field?*Field:TEXT("대사 필드 선택"));})]]
        +SVerticalBox::Slot().AutoHeight().Padding(12,4)[SNew(SEditableTextBox).Text(FText::FromString(Key)).HintText(FText::FromString(TEXT("고정 대사 키 (의미 있는 이름으로 변경 가능)"))).OnTextChanged_Lambda([&](const FText& Value){Key=Value.ToString();})]
        +SVerticalBox::Slot().FillHeight(1).Padding(12,4)[SNew(SMultiLineEditableTextBox).HintText(FText::FromString(TEXT("대사 내용"))).OnTextChanged_Lambda([&](const FText& Value){Content=Value.ToString();})]
        +SVerticalBox::Slot().AutoHeight().Padding(12,4)[SNew(STextBlock).Text_Lambda([&]{return Error;}).AutoWrapText(true)]
        +SVerticalBox::Slot().AutoHeight().Padding(12)[SNew(SButton).Text(FText::FromString(TEXT("추가하고 저장"))).OnClicked_Lambda([&]{
            if(Table.IsValid()&&Table->GetOutermost()->IsDirty()&&FMessageDialog::Open(EAppMsgType::YesNo,FText::FromString(TEXT("테이블의 다른 미저장 변경도 함께 저장됩니다. 계속할까요?")))!=EAppReturnType::Yes)return FReply::Handled();
            if(CreateDialogueDraft(Table.Get(),Key,Field?*Field:FString(),Content,Draft,Error)){Created=true;Window->RequestDestroyWindow();}return FReply::Handled();})]);
    FSlateApplication::Get().AddModalWindow(Window,FSlateApplication::Get().GetActiveTopLevelWindow());
    if(Created)Message=FText::FromString(TEXT("새 행을 추가했습니다."));return Created;
}
}
