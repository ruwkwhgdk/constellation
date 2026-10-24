#include "TextManagementIndex.h"
#include "Engine/Blueprint.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "K2Node_GetDataTableRow.h"
#include "K2Node_CallFunction.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Widget.h"
#include "UObject/UnrealType.h"
#include "Kismet/KismetTextLibrary.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableRegistry.h"

namespace ConstellationText
{
void FIndex::CollectBlueprint(UBlueprint* Blueprint)
{
    FLocation Base;Base.Asset=FSoftObjectPath(Blueprint);
    TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
    for(auto* Graph:Graphs)for(UEdGraphNode* Node:Graph->Nodes)
    {
        if(!Node)continue;
        FLocation Loc=Base;Loc.Kind=ELocationKind::BlueprintNode;Loc.Event=FSoftObjectPath(Graph);Loc.Node=Node->NodeGuid;
        for(auto* Pin:Node->Pins)
        {
            if(!Pin||Pin->Direction!=EGPD_Input||!Pin->LinkedTo.IsEmpty()||Pin->bOrphanedPin)continue;
            Loc.Field=Pin->PinName.ToString();
            if(Pin->PinType.PinCategory==TEXT("text"))AddText(Pin->DefaultTextValue,Loc,TEXT("Blueprint / ")+Graph->GetName());
            if(Pin->PinType.PinCategory==TEXT("struct")&&Pin->PinType.PinSubCategoryObject==FDataTableRowHandle::StaticStruct())
                Coverage.Add({Base.Asset.ToString(),TEXT("미검사"),TEXT("RowHandle 구조체 핀 기본값: ")+Graph->GetName()+TEXT(" / ")+Loc.Field});
        }
        if(auto* GetRow=Cast<UK2Node_GetDataTableRow>(Node))
        {
            auto* TablePin=GetRow->GetDataTablePin();auto* RowPin=GetRow->GetRowNamePin();Loc.Field=TEXT("RowName");
            UDataTable* Table=TablePin&&TablePin->LinkedTo.IsEmpty()?Cast<UDataTable>(TablePin->DefaultObject):nullptr;
            if(!Table){Coverage.Add({Base.Asset.ToString(),TEXT("미검사"),TEXT("동적으로 지정되는 DataTable: ")+Graph->GetName()+TEXT(" / ")+Node->NodeGuid.ToString()});continue;}
            FLocation Source;Source.Kind=ELocationKind::DataTable;Source.Asset=FSoftObjectPath(Table);
            if(!RowPin||!RowPin->LinkedTo.IsEmpty())Usages.Add({Source,Loc,EReferenceKind::Dynamic,TEXT("행 이름 입력 핀이 연결되어 있습니다.")});
            else
            {
                Source.Row=FName(*RowPin->DefaultValue);
                Usages.Add({Source,Loc,Table->FindRowUnchecked(Source.Row)?EReferenceKind::Exact:EReferenceKind::Broken,TEXT("GetDataTableRow의 상수 테이블/행")});
            }
        }
        if(auto* Call=Cast<UK2Node_CallFunction>(Node);Call&&Call->GetTargetFunction()==UKismetTextLibrary::StaticClass()->FindFunctionByName(TEXT("TextFromStringTable")))
        {
            auto* TablePin=Call->FindPin(TEXT("TableId"));auto* KeyPin=Call->FindPin(TEXT("Key"));Loc.Field=TEXT("Key");
            if(!TablePin||!TablePin->LinkedTo.IsEmpty()){Coverage.Add({Base.Asset.ToString(),TEXT("미검사"),TEXT("동적으로 지정되는 String Table: ")+Graph->GetName()});continue;}
            FLocation Source;Source.Kind=ELocationKind::StringTable;Source.Asset=FSoftObjectPath(TablePin->DefaultValue);
            if(!KeyPin||!KeyPin->LinkedTo.IsEmpty())Usages.Add({Source,Loc,EReferenceKind::Dynamic,TEXT("String Table 키 입력 핀이 연결되어 있습니다.")});
            else
            {
                Source.Key=KeyPin->DefaultValue;
                const auto Table=FStringTableRegistry::Get().FindStringTable(FName(*TablePin->DefaultValue));
                if(Table.IsValid()&&Table->GetOwnerAsset())Source.Asset=FSoftObjectPath(Table->GetOwnerAsset());
                const bool bValid=Table.IsValid()&&Table->FindEntry(Source.Key).IsValid();
                Usages.Add({Source,Loc,bValid?EReferenceKind::Exact:EReferenceKind::Broken,TEXT("TextFromStringTable의 상수 인자")});
                if(!bValid){auto Entry=MakeShared<FEntry>();Entry->Location=Entry->Origin=Loc;Entry->Source=Entry->Display=TEXT("[연결 오류] ")+Source.Asset.ToString()+TEXT(" / ")+Source.Key;Entry->Context=TEXT("등록된 String Table과 키를 확인하세요.");Entries.Add(Entry);}
            }
        }
    }
    // Authored defaults only; never walk arbitrary object references or generated runtime instances.
    if(Blueprint->GeneratedClass)
    {
        if(auto* CDO=Blueprint->GeneratedClass->GetDefaultObject())
        {CollectProperties(Blueprint->GeneratedClass,CDO,Base);CollectGameRules(CDO,Base);}
    }
    if(Blueprint->SimpleConstructionScript)for(auto* Node:Blueprint->SimpleConstructionScript->GetAllNodes())if(Node&&Node->ComponentTemplate)
    {
        FLocation Loc=Base;Loc.Field=Node->GetVariableName().ToString();CollectProperties(Node->ComponentTemplate->GetClass(),Node->ComponentTemplate,Loc);CollectGameRules(Node->ComponentTemplate,Loc);
    }
    if(auto* Widget=Cast<UWidgetBlueprint>(Blueprint);Widget&&Widget->WidgetTree)
    {
        Widget->WidgetTree->ForEachWidget([&](UWidget* Child){FLocation Loc=Base;Loc.Field=TEXT("WidgetTree.")+Child->GetName();CollectProperties(Child->GetClass(),Child,Loc);});
    }
}
}
