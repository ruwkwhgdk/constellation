#include "TextManagementIndex.h"
#include "SceneDirectorNavigation.h"
#include "SceneDirectorAsset.h"
#include "Editor.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "DataTableEditorUtils.h"
#include "IStringTableEditor.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "AssetRegistry/AssetRegistryModule.h"

namespace ConstellationText
{
bool Navigate(const FLocation& Location,FText& Message)
{
    if(!GEditor){Message=FText::FromString(TEXT("에디터에서 사용할 수 있습니다."));return false;}
    // A package candidate may be a map: never change the user's world implicitly.
    auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
    if(Registry.GetAssetByObjectPath(Location.Asset).AssetClassPath==UWorld::StaticClass()->GetClassPathName())
    {Message=FText::FromString(TEXT("맵 후보입니다. 콘텐츠 브라우저에서 직접 여세요: ")+Location.Asset.ToString());return false;}
    UObject* Object=Location.Asset.TryLoad();
    if(!Object){Message=FText::FromString(TEXT("에셋을 찾지 못했습니다. 다시 검사하세요: ")+Location.Asset.ToString());return false;}
    if(Object->IsA<UWorld>()){Message=FText::FromString(TEXT("맵 전환은 자동으로 수행하지 않습니다. 콘텐츠 브라우저에서 직접 여세요."));return false;}
    auto* Editors=GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    if(Location.Kind==ELocationKind::Director)return OpenDirectorTextLocation(Cast<USceneDirectorAsset>(Object),Location.Event,Location.Node,Location.Choice,FName(*Location.Field),Message);
    if(Location.Kind==ELocationKind::DataTable)
    {
        auto* Table=Cast<UDataTable>(Object);
        if(!Table||!Table->FindRowUnchecked(Location.Row)){Message=FText::FromString(TEXT("행이 삭제되거나 변경됐습니다. 다시 검사하세요."));return false;}
        Editors->OpenEditorForAsset(Table);
        if(!FDataTableEditorUtils::SelectRow(Table,Location.Row)){Message=FText::FromString(TEXT("행 선택에 실패했습니다. 테이블의 필터를 확인하세요."));return false;}
    }
    else if(Location.Kind==ELocationKind::StringTable)
    {
        auto* Table=Cast<UStringTable>(Object);
        if(!Table||!Table->GetStringTable()->FindEntry(Location.Key).IsValid()){Message=FText::FromString(TEXT("String Table 키가 없습니다. 다시 검사하세요."));return false;}
        Editors->OpenEditorForAsset(Table);auto* Instance=Editors->FindEditorForAsset(Table,true);
        if(!Instance||Instance->GetEditorName()!=TEXT("StringTableEditor")){Message=FText::FromString(TEXT("String Table 에디터를 찾지 못했습니다."));return false;}
        static_cast<IStringTableEditor*>(Instance)->RefreshStringTableEditor(Location.Key);
    }
    else if(Location.Kind==ELocationKind::BlueprintNode)
    {
        auto* Blueprint=Cast<UBlueprint>(Object);TArray<UEdGraph*> Graphs;if(Blueprint)Blueprint->GetAllGraphs(Graphs);
        for(auto* Graph:Graphs)if(FSoftObjectPath(Graph)==Location.Event)for(UEdGraphNode* Node:Graph->Nodes)if(Node&&Node->NodeGuid==Location.Node)
        {FKismetEditorUtilities::BringKismetToFocusAttentionOnObject(Node);Message=FText::FromString(TEXT("노드 선택 · 핀: ")+Location.Field);return true;}
        Message=FText::FromString(TEXT("Blueprint 노드가 변경됐습니다. 다시 검사하세요."));return false;
    }
    else Editors->OpenEditorForAsset(Object);
    Message=FText::FromString(TEXT("원본 에디터 열림 · 속성 위치: ")+Location.Label());return true;
}
}
