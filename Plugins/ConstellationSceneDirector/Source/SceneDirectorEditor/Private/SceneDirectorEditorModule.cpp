#include "SceneDirectorTesting.h"
#include "Misc/ConfigCacheIni.h"
#include "Styling/AppStyle.h"
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
        bool bSkip=false;
        GConfig->GetBool(TEXT("SceneDirector.Testing"),TEXT("bSkipCinematics"),bSkip,GEditorPerProjectIni);
        DirectorTesting::SetSkipEnabled(bSkip);
        DirectorAuthoring::RegisterDetails();RegisterSceneEventTab();Actions=MakeShared<FSceneDirectorActions>();FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().RegisterAssetTypeActions(Actions.ToSharedRef());
        UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this,&FSceneDirectorEditorModule::RegisterMenus));
    }
    void RegisterMenus()
    {
        FToolMenuOwnerScoped Owner(this);
        auto* Menu=UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
        const FUIAction SkipAction(
            FExecuteAction::CreateLambda([]{
                const bool bSkip=!DirectorTesting::IsSkipEnabled();
                DirectorTesting::SetSkipEnabled(bSkip);
                GConfig->SetBool(TEXT("SceneDirector.Testing"),TEXT("bSkipCinematics"),bSkip,GEditorPerProjectIni);
                GConfig->Flush(false,GEditorPerProjectIni);
            }),
            FCanExecuteAction::CreateLambda([]{return GEditor != nullptr;}),
            FIsActionChecked::CreateLambda([]{return DirectorTesting::IsSkipEnabled();}));
        const auto SkipLabel=TAttribute<FText>::CreateLambda([]{return FText::FromString(DirectorTesting::IsSkipEnabled()?TEXT("연출 스킵 ON"):TEXT("연출 스킵 OFF"));});
        const FText SkipTip=FText::FromString(TEXT("PIE/시뮬레이션 중에도 켜고 끌 수 있습니다. ON이면 이후 요청되는 연출과 내부 액션·보상·완료 기록을 생략하고, OFF이면 이후 요청부터 정상 재생합니다. 이미 재생 중인 연출도 즉시 중단하고 카메라·조작·HUD를 복구합니다. 중단된 연출은 완료로 기록하지 않습니다. 마우스가 게임에 잡혀 있으면 Shift+F1로 해제하세요. 툴 미리보기와 패키지 게임에는 적용되지 않습니다."));
        Menu->FindOrAddSection("SceneDirector").AddMenuEntry("SceneDirectorSkip",SkipLabel,SkipTip,FSlateIcon(),SkipAction,EUserInterfaceActionType::ToggleButton);
        UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar")->FindOrAddSection("SceneDirectorTesting").AddEntry(
            FToolMenuEntry::InitToolBarButton("SceneDirectorSkip",SkipAction,SkipLabel,SkipTip,FSlateIcon(FAppStyle::GetAppStyleSetName(),"Icons.Visible"),EUserInterfaceActionType::ToggleButton));

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
