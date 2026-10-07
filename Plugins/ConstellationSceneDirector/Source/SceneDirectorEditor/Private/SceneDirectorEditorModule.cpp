#include "SceneEventEditor.h"
#include "SceneDirectorDetails.h"
#include "Modules/ModuleManager.h"
#include "AssetToolsModule.h"
#include "AssetTypeActions_Base.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorToolkit.h"
#include "SceneDirectorFactory.h"
#include "SceneDirectorLibrary.h"
#include "ToolMenus.h"
#include "Editor.h"
#include "Subsystems/AssetEditorSubsystem.h"

class FSceneDirectorActions : public FAssetTypeActions_Base
{
public:
    virtual FText GetName() const override {return FText::FromString(TEXT("연출 그래프 (Scene Director)"));}
    virtual FColor GetTypeColor() const override {return FColor(30,175,210);}
    virtual UClass* GetSupportedClass() const override {return USceneDirectorAsset::StaticClass();}
    virtual uint32 GetCategories() override {return EAssetTypeCategories::Misc;}
    virtual void OpenAssetEditor(const TArray<UObject*>& Objects,TSharedPtr<IToolkitHost> Host) override
    {for(auto* Object:Objects)if(auto* Asset=Cast<USceneDirectorAsset>(Object)){auto Editor=MakeShared<FSceneDirectorToolkit>();Editor->Init(Asset,Host);}}
};
class FSceneDirectorEditorModule : public IModuleInterface
{
    TSharedPtr<IAssetTypeActions> Actions;
public:
    virtual void StartupModule() override
    {
        DirectorAuthoring::RegisterDetails();RegisterSceneEventTab();Actions=MakeShared<FSceneDirectorActions>();FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().RegisterAssetTypeActions(Actions.ToSharedRef());
        UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this,&FSceneDirectorEditorModule::RegisterMenus));
    }
    void RegisterMenus()
    {
        FToolMenuOwnerScoped Owner(this);
        auto* Menu=UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
        Menu->FindOrAddSection("SceneDirector").AddMenuEntry("SceneEventPlacement",FText::FromString(TEXT("Scene Director · 이벤트 배치")),FText(),FSlateIcon(),FUIAction(FExecuteAction::CreateStatic(&OpenSceneEventTab)));
        Menu->FindOrAddSection("SceneDirector").AddMenuEntry("SceneDirectorNew",FText::FromString(TEXT("Scene Director · 새 연출 그래프")),FText::FromString(TEXT("기획자용 노드 기반 연출 그래프를 만듭니다.")),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([]
        {
            auto* Factory=NewObject<USceneDirectorFactory>();
            FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().CreateAssetWithDialog(USceneDirectorAsset::StaticClass(),Factory);
        })));
        Menu->FindOrAddSection("SceneDirector").AddMenuEntry("SceneDirectorConversation",FText::FromString(TEXT("Scene Director · 대화 연출 예제 열기")),FText::FromString(TEXT("두 인물 대화와 기존 캐릭터 연결 예제를 생성합니다.")),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([]
        {
            if(auto* Asset=USceneDirectorLibrary::CreateConversationExample())GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OpenEditorForAsset(Asset);
        })));
        Menu->FindOrAddSection("SceneDirector").AddMenuEntry("SceneDirectorExample",FText::FromString(TEXT("Scene Director · 첫 연출 예제 열기")),FText::FromString(TEXT("예제 BP와 연출을 생성합니다. 기존 예제는 덮어쓰지 않습니다.")),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([]
        {
            if(auto* Asset=USceneDirectorLibrary::CreateExample())GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OpenEditorForAsset(Asset);
        })));
    }
    virtual void ShutdownModule() override
    {
        DirectorAuthoring::UnregisterDetails();UnregisterSceneEventTab();UToolMenus::UnRegisterStartupCallback(this);UToolMenus::UnregisterOwner(this);
        if(Actions&&FModuleManager::Get().IsModuleLoaded("AssetTools"))FModuleManager::GetModuleChecked<FAssetToolsModule>("AssetTools").Get().UnregisterAssetTypeActions(Actions.ToSharedRef());
        Actions.Reset();
    }
};
IMPLEMENT_MODULE(FSceneDirectorEditorModule, SceneDirectorEditor)
