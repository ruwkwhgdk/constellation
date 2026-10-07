#include "SceneEventEditor.h"
#include "SceneEventBinding.h"
#include "SceneEventSubsystem.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "Editor.h"
#include "EngineUtils.h"
#include "Engine/Selection.h"
#include "PropertyEditorModule.h"
#include "IDetailsView.h"
#include "ScopedTransaction.h"
#include "FileHelpers.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "Framework/Docking/TabManager.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SSplitter.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SComboButton.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
static const FName EventTabName(TEXT("SceneDirectorEventPlacement"));
class SSceneEventEditor:public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SSceneEventEditor){} SLATE_END_ARGS()
 void Construct(const FArguments&)
 {
  FDetailsViewArgs Args;Args.bHideSelectionTip=true;Details=FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor").CreateDetailView(Args);
  Details->SetIsPropertyVisibleDelegate(FIsPropertyVisible::CreateLambda([](const FPropertyAndParent& P){static const TSet<FName> Fields={TEXT("bEnabled"),TEXT("Trigger"),TEXT("Source"),TEXT("Director"),TEXT("Repeat"),TEXT("OriginalSequence"),TEXT("bPersistVariables"),TEXT("StateGroup"),TEXT("bIncludeInitialOverlap"),TEXT("AreaExtent"),TEXT("CombatKey"),TEXT("CombatResult"),TEXT("StartOrder"),TEXT("Origin"),TEXT("Anchor"),TEXT("Objects")};if(Fields.Contains(P.Property.GetFName()))return true;for(const auto* Parent:P.ParentProperties)if(Fields.Contains(Parent->GetFName()))return true;return false;}));
  auto Button=[](const TCHAR* Label,FOnClicked OnClick){return SNew(SButton).Text(FText::FromString(Label)).OnClicked(OnClick);};
  ChildSlot[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(TEXT("이벤트 배치 · 현재 레벨 | 레벨 뷰포트와 나란히 도킹하여 사용하세요. 레벨을 저장하면 설정도 저장됩니다.")))]
   +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth()[SNew(SComboButton).ButtonContent()[SNew(STextBlock).Text(FText::FromString(TEXT("+ 이벤트 추가")))].OnGetMenuContent_Lambda([this]{FMenuBuilder Menu(true,nullptr);for(int32 I=0;I<5;++I){auto T=static_cast<ESceneEventTrigger>(I);Menu.AddMenuEntry(StaticEnum<ESceneEventTrigger>()->GetDisplayNameTextByValue(I),FText(),FSlateIcon(),FUIAction(FExecuteAction::CreateSP(this,&SSceneEventEditor::Add,T)));}return Menu.MakeWidget();})]
    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("새로고침"),FOnClicked::CreateLambda([this]{Refresh();return FReply::Handled();}))]
    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("전체 검사"),FOnClicked::CreateLambda([this]{ValidateAll();return FReply::Handled();}))]
    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("레벨 저장"),FOnClicked::CreateLambda([]{if(!GEditor->PlayWorld)FEditorFileUtils::SaveCurrentLevel();return FReply::Handled();}))]]
   +SVerticalBox::Slot().FillHeight(1)[SNew(SSplitter)
    +SSplitter::Slot().Value(.35f)[SAssignNew(List,SScrollBox)]
    +SSplitter::Slot().Value(.65f)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("선택 Actor를 대상으로"),FOnClicked::CreateLambda([this]{SetSource();return FReply::Handled();}))]
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("대상 찾기"),FOnClicked::CreateLambda([this]{if(auto* B=Selected.Get()){auto* A=B->Source?B->Source.Get():B;GEditor->SelectNone(false,true);GEditor->SelectActor(A,true,true);GEditor->MoveViewportCamerasToActor(*A,false);}return FReply::Handled();}))]
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("삭제"),FOnClicked::CreateLambda([this]{if(auto* B=Selected.Get();B&&!GEditor->PlayWorld){FScopedTransaction Tx(FText::FromString(TEXT("연출 이벤트 삭제")));B->GetWorld()->EditorDestroyActor(B,true);Selected.Reset();Details->SetObject(nullptr);Refresh();}return FReply::Handled();}))]]
     +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("연출 열기"),FOnClicked::CreateLambda([this]{if(auto* B=Selected.Get();B&&B->Director)GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OpenEditorForAsset(B->Director);return FReply::Handled();}))]
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("연출 생성·검사"),FOnClicked::CreateLambda([this]{if(auto* B=Selected.Get();B&&B->Director&&!GEditor->PlayWorld){FString Error;Message=FSceneDirectorCompiler::Compile(*B->Director,Error)?TEXT("연출 생성 완료"):Error;}return FReply::Handled();}))]
      +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("PIE 발동 시험"),FOnClicked::CreateLambda([this]{Test();return FReply::Handled();}))]]
     +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(TEXT("발동 시험은 실제 조건을 적용하며 게임 액션을 실행합니다. 레벨 준비/전투 완료는 시스템의 명시적 알림이 필요합니다.")))]
     +SVerticalBox::Slot().FillHeight(1)[Details.ToSharedRef()]]]
   +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return FText::FromString(Message);})]
   +SVerticalBox::Slot().AutoHeight()[SNew(SBox).MaxDesiredHeight(150)[SNew(SScrollBox)+SScrollBox::Slot()[SNew(STextBlock).AutoWrapText(true).Text_Lambda([]{UWorld* W=GEditor->PlayWorld;auto* S=W?W->GetSubsystem<USceneEventSubsystem>():nullptr;return FText::FromString(S?FString::Join(S->History,TEXT("\n")):TEXT("PIE 실행 중 최근 발동 기록이 표시됩니다."));})]]]
  ];Refresh();
 }
 virtual void Tick(const FGeometry& G,double Time,float Delta) override
 {SCompoundWidget::Tick(G,Time,Delta);if(Time-LastRefresh>1){LastRefresh=Time;Refresh();}}
private:
 TSharedPtr<IDetailsView> Details;TSharedPtr<SScrollBox> List;TWeakObjectPtr<ASceneEventBinding> Selected;TWeakObjectPtr<UWorld> DisplayWorld;FString Message;double LastRefresh=0;
 UWorld* World() const{return GEditor->GetEditorWorldContext().World();}
 void Refresh()
 {
  if(DisplayWorld!=World()){Selected.Reset();Details->SetObject(nullptr);DisplayWorld=World();}
  if(!Selected.IsValid())Details->SetObject(nullptr);List->ClearChildren();if(!World())return;
  for(TActorIterator<ASceneEventBinding> It(World());It;++It){TWeakObjectPtr<ASceneEventBinding> Weak=*It;if(!Selected.IsValid()){Selected=Weak;Details->SetObject(Weak.Get());}
   List->AddSlot().Padding(4)[SNew(SButton).OnClicked_Lambda([this,Weak]{Selected=Weak;Details->SetObject(Weak.Get());return FReply::Handled();})[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(It->GetActorLabel()+TEXT("\n")+StaticEnum<ESceneEventTrigger>()->GetDisplayNameTextByValue(static_cast<int64>(It->Trigger)).ToString()+TEXT(" · ")+(It->Director?It->Director->GetName():TEXT("연출 미지정"))))]];
  }
 }
 void Add(ESceneEventTrigger Type)
 {
  if(!World()||GEditor->PlayWorld){Message=TEXT("PIE를 종료하고 추가하세요.");return;}FScopedTransaction Tx(FText::FromString(TEXT("연출 이벤트 추가")));World()->GetCurrentLevel()->Modify();
  FActorSpawnParameters P;P.ObjectFlags|=RF_Transactional;auto* B=World()->SpawnActor<ASceneEventBinding>(P);B->Modify();B->Trigger=Type;B->Repeat=Type==ESceneEventTrigger::Interaction?ESceneEventRepeat::EveryTime:ESceneEventRepeat::OncePerVisit;B->SetActorLabel(TEXT("연출_")+StaticEnum<ESceneEventTrigger>()->GetDisplayNameTextByValue(static_cast<int64>(Type)).ToString());
  Selected=B;SetSource();B->RerunConstructionScripts();B->MarkPackageDirty();Details->SetObject(B);Refresh();
 }
 void SetSource()
 {
  auto* B=Selected.Get();if(!B||GEditor->PlayWorld)return;auto* A=Cast<AActor>(GEditor->GetSelectedActors()->GetTop(AActor::StaticClass()));if(!A||A==B){Message=TEXT("뷰포트에서 대상 Actor를 선택하세요. 영역은 배치 Actor의 Box를 사용할 수 있습니다.");return;}
  FScopedTransaction Tx(FText::FromString(TEXT("연출 발동 대상 설정")));B->Modify();B->Source=A;B->SetActorLocation(A->GetActorLocation());B->RerunConstructionScripts();B->MarkPackageDirty();Details->ForceRefresh();
 }
 void ValidateAll()
 {
  int32 Count=0;TArray<FString> Errors;if(World())for(TActorIterator<ASceneEventBinding> It(World());It;++It){++Count;FString Error;if(!It->Validate(Error))Errors.Add(It->GetActorLabel()+TEXT(": ")+Error);}
  Message=Errors.IsEmpty()?FString::Printf(TEXT("%d개 이벤트 설정 검사 통과 · 연출 내부는 ‘연출 생성·검사’로 확인하세요."),Count):FString::Join(Errors,TEXT("\n"));
 }
 void Test()
 {
  auto* B=Selected.Get();if(!B||!GEditor->PlayWorld){Message=TEXT("이벤트를 선택하고 PIE를 실행하세요.");return;}
  for(TActorIterator<ASceneEventBinding> It(GEditor->PlayWorld);It;++It)if(It->EventId==B->EventId){It->TestSignal();Message=It->Status;return;}Message=TEXT("PIE에 해당 이벤트가 없습니다. 레벨 저장 후 다시 실행하세요.");
 }
};
void RegisterSceneEventTab(){FGlobalTabmanager::Get()->RegisterNomadTabSpawner(EventTabName,FOnSpawnTab::CreateLambda([](const FSpawnTabArgs&){return SNew(SDockTab).TabRole(ETabRole::NomadTab)[SNew(SSceneEventEditor)];})).SetDisplayName(FText::FromString(TEXT("Scene Director · 이벤트 배치")));}
void UnregisterSceneEventTab(){FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(EventTabName);}
void OpenSceneEventTab(){FGlobalTabmanager::Get()->TryInvokeTab(EventTabName);}

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Tests/AutomationCommon.h"
static TSharedPtr<SWindow> SceneEventReviewWindow;
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FSceneEventCapture,FAutomationTestBase*,Test);
bool FSceneEventCapture::Update()
{
 TArray<FColor> Pixels;FIntVector Size;
 if(Test->TestTrue(TEXT("Event authoring screenshot"),FSlateApplication::Get().TakeScreenshot(SceneEventReviewWindow.ToSharedRef(),Pixels,Size)))
 {TArray64<uint8> PNG;FImageUtils::PNGCompressImageArray(Size.X,Size.Y,Pixels,PNG);Test->TestTrue(TEXT("Save event panel"),FFileHelper::SaveArrayToFile(PNG,*(FPaths::ProjectSavedDir()/TEXT("SceneEventAuthoring/panel.png"))));}
 SceneEventReviewWindow->RequestDestroyWindow();SceneEventReviewWindow.Reset();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSceneEventEditorTest,"Constellation.SceneDirector.EventEditor",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSceneEventEditorTest::RunTest(const FString&)
{
 auto Widget=SNew(SSceneEventEditor);Widget->SlatePrepass();TestTrue(TEXT("Panel has layout"),Widget->GetDesiredSize().X>0);
 if(!FParse::Param(FCommandLine::Get(),TEXT("SceneEventCapture")))return true;
 SceneEventReviewWindow=SNew(SWindow).Title(FText::FromString(TEXT("이벤트 배치"))).ClientSize(FVector2D(1300,850))[Widget];FSlateApplication::Get().AddWindow(SceneEventReviewWindow.ToSharedRef());
 ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.f));ADD_LATENT_AUTOMATION_COMMAND(FSceneEventCapture(this));return true;
}
#endif
