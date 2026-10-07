#include "Modules/ModuleManager.h"
#include "ToolMenus.h"
#include "Editor.h"
#include "Engine/Selection.h"
#include "CombatLabCharacter.h"
#include "CombatLabEditorLibrary.h"
#include "Misc/MessageDialog.h"

class FCombatEditorModule : public IModuleInterface
{
    static void ValidateSelection()
    {
        if(!GEditor || GEditor->PlayWorld) return;
        auto* Selection=GEditor->GetSelectedActors();
        auto* Character=Selection && Selection->Num()==1
            ? Cast<ACombatLabCharacter>(Selection->GetTop(AActor::StaticClass())) : nullptr;
        TArray<FString> Errors,Warnings;
        const bool Valid=UCombatLabEditorLibrary::ValidateCombatCharacter(Character,Errors,Warnings);
        FString Report=Character ? Character->GetActorLabel()+TEXT("\n\n") : FString();
        Report+=Valid?TEXT("검사 통과"):TEXT("수정 필요");
        Report+=FString::Printf(TEXT(" — 오류 %d개 / 참고 %d개\n"),Errors.Num(),Warnings.Num());
        for(const auto& Error:Errors) Report+=TEXT("\n[오류] ")+Error;
        for(const auto& Warning:Warnings) Report+=TEXT("\n[참고] ")+Warning;
        UE_LOG(LogTemp,Display,TEXT("COMBAT_AUTHORING_VALIDATION %s"),*Report);
        FMessageDialog::Open(EAppMsgType::Ok,FText::FromString(Report));
    }
    static void SaveSelectionReport()
    {
        if(!GEditor || GEditor->PlayWorld) return;
        auto* Selection=GEditor->GetSelectedActors();
        auto* Character=Selection && Selection->Num()==1
            ? Cast<ACombatLabCharacter>(Selection->GetTop(AActor::StaticClass())) : nullptr;
        FString Path,Error;
        const bool Saved=UCombatLabEditorLibrary::SaveCombatCharacterReport(Character,Path,Error);
        const FString Message=Saved?TEXT("검사 보고서 저장 완료 (설정 통과 여부는 보고서의 valid 항목 확인)\n\n")+Path:Error;
        UE_LOG(LogTemp,Display,TEXT("COMBAT_REPORT %s"),*Message);
        FMessageDialog::Open(EAppMsgType::Ok,FText::FromString(Message));
    }
    void RegisterMenus()
    {
        FToolMenuOwnerScoped Owner(this);
        auto* Menu=UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
        Menu->FindOrAddSection("ConstellationCombat").AddMenuEntry(
            "CombatSaveSelectedReport",FText::FromString(TEXT("Combat · 검사 보고서 저장")),
            FText::FromString(TEXT("선택 몬스터의 현재 설정과 오류를 AI 전달용 JSON으로 저장합니다.")),FSlateIcon(),
            FUIAction(FExecuteAction::CreateStatic(&SaveSelectionReport),
                FCanExecuteAction::CreateLambda([] { return GEditor && !GEditor->PlayWorld; })));
        Menu->FindOrAddSection("ConstellationCombat").AddMenuEntry(
            "CombatValidateSelectedEnemy",FText::FromString(TEXT("Combat · 선택 몬스터 검사")),
            FText::FromString(TEXT("선택한 몬스터의 저장 전 전투 설정과 연결을 검사합니다.")),FSlateIcon(),
            FUIAction(FExecuteAction::CreateStatic(&ValidateSelection),
                FCanExecuteAction::CreateLambda([] { return GEditor && !GEditor->PlayWorld; })));
    }
public:
    virtual void StartupModule() override
    {
        if(!IsRunningCommandlet())
            UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this,&FCombatEditorModule::RegisterMenus));
    }
    virtual void ShutdownModule() override
    {
        if(!IsRunningCommandlet())
        { UToolMenus::UnRegisterStartupCallback(this); UToolMenus::UnregisterOwner(this); }
    }
};
IMPLEMENT_MODULE(FCombatEditorModule,CombatEditor)
