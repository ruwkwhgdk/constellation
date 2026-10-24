#include "SceneDirectorText.h"
#include "SceneDirectorAsset.h"
#include "UObject/UnrealType.h"

namespace
{
    bool IsUnset(const FDataTableRowHandle& Handle)
    {return !Handle.DataTable&&Handle.RowName.IsNone();}

    const FTextProperty* FindTextProperty(const UDataTable* Table)
    {
        if(!Table||!Table->GetRowStruct())return nullptr;
        const FTextProperty* OnlyText=nullptr;
        int32 TextCount=0;
        for(TFieldIterator<FTextProperty> It(Table->GetRowStruct());It;++It)
        {
            const FString Name=It->GetName();
            // Blueprint structs append a generated suffix to their authored property names.
            if(Name==TEXT("Description")||Name.StartsWith(TEXT("Description_")))return *It;
            OnlyText=*It;++TextCount;
        }
        return TextCount==1?OnlyText:nullptr;
    }
}

bool DirectorText::Validate(const FDataTableRowHandle& Handle,FString& Error)
{
    Error.Reset();
    if(IsUnset(Handle))return true;
    if(!Handle.DataTable||Handle.RowName.IsNone())
    {Error=TEXT("문구 데이터 참조에는 데이터 테이블과 행 이름이 모두 필요합니다.");return false;}
    if(!FindTextProperty(Handle.DataTable))
    {Error=TEXT("문구 데이터 테이블에는 FText 형식의 Description 필드 또는 단 하나의 FText 필드가 필요합니다: ")+Handle.DataTable->GetPathName();return false;}
    if(!Handle.DataTable->FindRowUnchecked(Handle.RowName))
    {Error=TEXT("문구 데이터 테이블에 해당 행이 없습니다: ")+Handle.DataTable->GetPathName()+TEXT(" / ")+Handle.RowName.ToString();return false;}
    return true;
}

FText DirectorText::Resolve(const FDataTableRowHandle& Handle,const FText& Direct)
{
    if(IsUnset(Handle))return Direct;
    const auto* Property=FindTextProperty(Handle.DataTable);
    const auto* Row=Property&&!Handle.RowName.IsNone()?Handle.DataTable->FindRowUnchecked(Handle.RowName):nullptr;
    // Return the original FText, retaining its namespace/key and localization history.
    return Row?Property->GetPropertyValue_InContainer(Row):FText::GetEmpty();
}

FText FDirectorStep::ResolveDialogue() const
{return DirectorText::Resolve(DialogueRow,DialogueText);}

bool FDirectorStep::ValidateDialogue(FString& Error) const
{
    if(!DirectorText::Validate(DialogueRow,Error))return false;
    if(ResolveDialogue().IsEmpty()){Error=TEXT("대사 내용을 입력하세요.");return false;}
    return true;
}
