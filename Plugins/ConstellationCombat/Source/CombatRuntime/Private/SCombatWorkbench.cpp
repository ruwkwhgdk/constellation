#include "SCombatWorkbench.h"
#include "CombatWorkbenchSubsystem.h"
#include "CombatLabCharacter.h"
#include "CombatEncounterDirector.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "CombatAttackInput.h"
#include "CombatObservation.h"
#include "CombatEnemyAgent.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Engine/UserInterfaceSettings.h"
#include "UnrealClient.h"
#include "InputKeyEventArgs.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "Kismet/GameplayStatics.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SNumericEntryBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Styling/CoreStyle.h"
#include "Brushes/SlateColorBrush.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformFileManager.h"
#include "HighResScreenshot.h"

namespace {
FText Text(const FString& S){return FText::FromString(S);}
FSlateFontInfo Font(int32 Size=18){return FCoreStyle::GetDefaultFontStyle("Regular",Size);}
const FProgressBarStyle& BarStyle()
{
    static FProgressBarStyle Style=FProgressBarStyle().SetBackgroundImage(FSlateColorBrush(FLinearColor(.1f,.12f,.16f))).SetFillImage(FSlateColorBrush(FLinearColor::White));
    return Style;
}
const FLinearColor Ink(.86f,.91f,.96f),Accent(.18f,.85f,.76f),Panel(.018f,.027f,.045f,.97f);
TSharedRef<STextBlock> Label(const FString& S,int32 Size=18)
{return SNew(STextBlock).Text(Text(S)).Font(Font(Size)).ColorAndOpacity(Ink).AutoWrapText(true);}
TSharedRef<SButton> Button(const FString& S,TFunction<FReply()> Click)
{return SNew(SButton).ContentPadding(FMargin(14,9)).OnClicked_Lambda(MoveTemp(Click))[SNew(STextBlock).Text(Text(S)).Font(Font()).ColorAndOpacity(Ink)];}
}

void SCombatWorkbench::Construct(const FArguments&,ACombatLabCharacter* InPlayer)
{
    Player=InPlayer;
    OriginalTimeScale=UGameplayStatics::GetGlobalTimeDilation(InPlayer);
    Model=InPlayer->GetGameInstance()->GetSubsystem<UCombatWorkbenchSubsystem>();
    ChildSlot[
        SNew(SDPIScaler).DPIScale_Lambda([this]{
            auto* P=Player.Get(); auto* V=P && P->GetGameInstance()?P->GetGameInstance()->GetGameViewportClient():nullptr;
            const float Scale=V && V->Viewport?GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(V->Viewport->GetSizeXY()):1.f;
            return 1.f/FMath::Min(1.f,FMath::Max(.1f,Scale));
        })[
        SNew(SOverlay)
        +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(24)[Card(false)]
        +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(24)[Card(true)]
        +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Bottom).Padding(24,0,24,120)[
            SNew(SBox).WidthOverride(460).Visibility_Lambda([this]{return bOpen?EVisibility::Collapsed:EVisibility::HitTestInvisible;})[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Panel).Padding(14)
            [SNew(STextBlock).Font(Font()).ColorAndOpacity(Ink).AutoWrapText(true)
                .Text(this,&SCombatWorkbench::InputStatus)]]]
        +SOverlay::Slot().VAlign(VAlign_Bottom).Padding(24)[
            SNew(SBorder).Visibility_Lambda([this]{return bOpen?EVisibility::Collapsed:EVisibility::HitTestInvisible;}).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Panel).Padding(12)
            [SNew(STextBlock).Font(Font(16)).ColorAndOpacity(Ink).AutoWrapText(true)
                .Text_Lambda([this]{return Text(FString::Printf(TEXT("WASD 이동 · 마우스 시점 · 좌클릭 공격 · Space 회피 · Tab 락온 · Q 스킬 · E 궁극기\nF1 조정 / 관찰 · R 재시작 · 우클릭 취소 · 관찰 속도 %s"),bSlow?TEXT("0.25×"):TEXT("1×")));})]]
        +SOverlay::Slot().Padding(24)[
            SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Panel).Padding(22)
            .Visibility_Lambda([this]{return bOpen?EVisibility::Visible:EVisibility::Collapsed;})
            [
                SNew(SVerticalBox)
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)[Label(TEXT("전투 워크벤치"),26)]
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)[
                    SNew(STextBlock).Font(Font()).ColorAndOpacity(Accent)
                    .Text_Lambda([this]{const TCHAR* Tabs[]={TEXT("플레이어"),TEXT("슬라임"),TEXT("공격 · 패턴"),TEXT("상세 상태"),TEXT("변경 내역")};
                        return Text(FString::Printf(TEXT("전투 일시정지  ·  %s  ·  %s"),Tabs[Tab],Dirty()?TEXT("적용 전 변경 있음"):TEXT("현재 적용값")));})]
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)[
                    SNew(SHorizontalBox)
                    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("플레이어"),[this]{Tab=0;Rebuild();return FReply::Handled();})]
                    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("슬라임"),[this]{Tab=1;Rebuild();return FReply::Handled();})]
                    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("공격 · 패턴"),[this]{Tab=2;Rebuild();return FReply::Handled();})]
                    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("상세 상태"),[this]{Tab=3;Rebuild();return FReply::Handled();})]
                    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("변경 내역"),[this]{Tab=4;Rebuild();return FReply::Handled();})]]
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)[
                    SNew(SHorizontalBox)
                    +SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Font(Font()).ColorAndOpacity(Ink).AutoWrapText(true)
                        .Text_Lambda([this]{return Text(TEXT("몬스터 대상: ")+(Enemy()?Enemy()->GetName():TEXT("없음")));})]
                    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("다음 대상"),[this]{return NextEnemy();})]]
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)[
                    SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,6))
                    +SWrapBox::Slot()[Button(TEXT("정상 속도"),[this]{return SetObservationSpeed(false);})]
                    +SWrapBox::Slot()[Button(TEXT("0.25배 관찰"),[this]{return SetObservationSpeed(true);})]
                    +SWrapBox::Slot()[Button(TEXT("판정 범위 켜기 / 끄기"),[this]{return ToggleHitVolumes();})]
                    +SWrapBox::Slot()[SNew(STextBlock).Font(Font()).ColorAndOpacity(Accent)
                        .Text_Lambda([this]{return Text(FString::Printf(TEXT("속도 %s · 판정 %s"),bSlow?TEXT("0.25×"):TEXT("1×"),bShowHitVolumes?TEXT("표시"):TEXT("숨김")));})]]
                +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[
                    SNew(STextBlock).Font(Font()).ColorAndOpacity(FLinearColor(1,.7f,.35f)).AutoWrapText(true)
                    .Visibility_Lambda([this]{return Message.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;})
                    .Text_Lambda([this]{return Text(Message);})]
                +SVerticalBox::Slot().FillHeight(1)[SNew(SScrollBox)+SScrollBox::Slot()[SAssignNew(Rows,SVerticalBox)]]
                +SVerticalBox::Slot().AutoHeight().Padding(0,12,0,6)[
                    SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,6))
                    +SWrapBox::Slot()[SNew(SBox).WidthOverride(220)[SAssignNew(PresetName,SEditableTextBox).Font(Font()).Text(Text(TEXT("Trial_01")))
                        .HintText(Text(TEXT("파일 이름 (영문)")))]]
                    +SWrapBox::Slot()[SNew(SButton).ContentPadding(FMargin(14,9)).OnClicked_Lambda([this]{
                        bReportInput=!bReportInput;Message=bReportInput?TEXT("Saved/CombatTuningReports의 preset.values를 읽습니다. fields는 참고 기록입니다."):TEXT("Saved/CombatTuning의 프리셋을 읽습니다.");
                        return FReply::Handled();
                    })[SNew(STextBlock).Font(Font()).ColorAndOpacity(Ink).Text_Lambda([this]{return Text(bReportInput?TEXT("입력: AI 파일"):TEXT("입력: 프리셋"));})]]]
                +SVerticalBox::Slot().AutoHeight()[
                    SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,6))
                    +SWrapBox::Slot()[Button(TEXT("프리셋 저장"),[this]{return Save();})]
                    +SWrapBox::Slot()[Button(TEXT("목록 순환"),[this]{return NextPreset();})]
                    +SWrapBox::Slot()[Button(TEXT("불러오기"),[this]{return Load();})]
                    +SWrapBox::Slot()[Button(TEXT("초기 설정 복원"),[this]{return Restore();})]
                    +SWrapBox::Slot()[Button(TEXT("AI 전달 파일"),[this]{
                        if(Model.IsValid()) Model->ExportTuningReport(Draft,PresetName->GetText().ToString(),Message);
                        return FReply::Handled();
                    })]]
                +SVerticalBox::Slot().AutoHeight().Padding(0,10,0,6)[Label(TEXT("적용하면 양측 HP/SP·위치·쿨다운을 초기화합니다. 닫으면 미적용 변경은 버립니다."),16)]
                +SVerticalBox::Slot().AutoHeight()[
                    SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,6))
                    +SWrapBox::Slot()[Button(TEXT("적용 후 전투 재시작"),[this]{return Apply();})]
                    +SWrapBox::Slot()[Button(TEXT("변경 취소 후 계속 (F1)"),[this]{return Close();})]]
            ]]
    ]];
}
bool SCombatWorkbench::Dirty() const
{
    return Model.IsValid() && bOpen && Draft!=Model->ReadValues();
}
ACombatLabCharacter* SCombatWorkbench::Enemy() const
{
    auto* P=Player.Get(); if(!P) return nullptr;
    for(TActorIterator<ACombatLabCharacter> It(P->GetWorld());It;++It)
        if(It->bTrainingEnemy && (EnemyKey.IsEmpty() || EnemyKey.EndsWith(TEXT("/")+It->GetName()))) return *It;
    return nullptr;
}
FText SCombatWorkbench::Status(ACombatLabCharacter* A) const
{
    if(!A) return Text(TEXT("대상 없음"));
    auto* C=A->Combat.Get();
    const TCHAR* State=C->GetHealth()<=0?TEXT("사망 · R 또는 F1에서 재시작"):
        C->IsHitReacting()?TEXT("피격 경직"):C->IsDodging()?TEXT("회피"):C->IsActing()?TEXT("공격 중"):TEXT("대기 / 이동");
    const auto O=C->ObserveAction();
    const FString Phase=O.bActive?FString::Printf(TEXT("%s  %.2f / %.2fs"),*O.Phase,O.Position,O.Duration):FString(State);
    return Text(FString::Printf(TEXT("HP  %.0f / %.0f     SP  %.0f / %.0f\n%s"),C->GetHealth(),C->GetMaxHealth(),C->GetStamina(),C->GetMaxStamina(),*Phase));
}
TSharedRef<SWidget> SCombatWorkbench::Card(bool EnemyCard)
{
    return SNew(SBox).WidthOverride(380).Visibility_Lambda([this]{return bOpen?EVisibility::Collapsed:EVisibility::HitTestInvisible;})[
        SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Panel).Padding(16)[
            SNew(SVerticalBox)
            +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)[Label(EnemyCard?TEXT("슬라임"):TEXT("플레이어"),22)]
            +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)[SNew(STextBlock).Font(Font()).ColorAndOpacity(Ink).AutoWrapText(true)
                .Text_Lambda([this,EnemyCard]{return Status(EnemyCard?Enemy():Player.Get());})]
            +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[SNew(SProgressBar).Style(&BarStyle()).FillColorAndOpacity(FLinearColor(.85f,.23f,.32f))
                .Percent_Lambda([this,EnemyCard]()->TOptional<float>{auto* A=EnemyCard?Enemy():Player.Get();return A?A->Combat->GetHealth()/A->Combat->GetMaxHealth():0.f;})]
            +SVerticalBox::Slot().AutoHeight()[SNew(SProgressBar).Style(&BarStyle()).FillColorAndOpacity(Accent)
                .Percent_Lambda([this,EnemyCard]()->TOptional<float>{auto* A=EnemyCard?Enemy():Player.Get();return A?A->Combat->GetStamina()/A->Combat->GetMaxStamina():0.f;})]
            +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(STextBlock).Font(Font(16)).ColorAndOpacity(Accent).AutoWrapText(true)
                .Visibility(EnemyCard?EVisibility::Collapsed:EVisibility::HitTestInvisible).Text(this,&SCombatWorkbench::SpecialActionsStatus)]
            +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(STextBlock).Font(Font(16)).ColorAndOpacity(Ink).AutoWrapText(true)
                .Text_Lambda([this,EnemyCard]{
                    auto* A=EnemyCard?Enemy():Player.Get(); if(!A) return FText();
                    const TCHAR* States[]={TEXT("대기"),TEXT("추적"),TEXT("탐색"),TEXT("교전"),TEXT("복귀"),TEXT("이동 막힘"),TEXT("사망")};
                    FString Info=EnemyCard?FString::Printf(TEXT("AI  %s  ·  패턴  %s"),States[int32(A->EnemyAgent->State)],*A->Combat->LastSelectedPattern.ToString()):TEXT("F1을 눌러 수치 조정");
                    if(EnemyCard && A->EncounterDirector){auto* D=A->EncounterDirector.Get();const TCHAR* Outcome=D->Outcome==ECombatEncounterOutcome::Completed?TEXT("승리"):D->Outcome==ECombatEncounterOutcome::Failed?TEXT("패배"):TEXT("교전 진행");Info+=FString::Printf(TEXT("\n%s · 남은 적 %d · 공격 %d/%d"),Outcome,D->LivingEnemies(),D->ActiveAttackers(),D->MaxAttackers);}
                    return Text(Info);
                })]
        ]];
}
void SCombatWorkbench::SetOpen(bool Open)
{
    auto* P=Player.Get(); if(!P || !Model.IsValid()) return;
    auto* PC=Cast<APlayerController>(P->GetController()); if(!PC) return;
    if(Open)
    {
        // A failed pause must not expose mutable settings while combat keeps running.
        if(!PC->SetPause(true)) return;
        Draft=Model->ReadValues(); Message.Reset();
        if(EnemyKey.IsEmpty()) for(const auto& F:Model->Fields) if(F.bEnemy) {EnemyKey=F.ActorKey;break;}
    }
    bOpen=Open; P->bWorkbenchOpen=Open;
    P->ConsumeMovementInputVector();
    PC->FlushPressedKeys(); PC->bShowMouseCursor=Open;
    if(Open)
    {
        Rebuild();
        FInputModeUIOnly Mode; Mode.SetWidgetToFocus(SharedThis(this)); Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        PC->SetInputMode(Mode);
        FSlateApplication::Get().SetKeyboardFocus(SharedThis(this),EFocusCause::SetDirectly);
    }
    else
    {
        PC->SetPause(false); PC->SetInputMode(FInputModeGameOnly());
        FSlateApplication::Get().SetAllUserFocusToGameViewport();
    }
}
FReply SCombatWorkbench::OnKeyDown(const FGeometry& G,const FKeyEvent& E)
{
    if(bOpen && (E.GetKey()==EKeys::F1 || E.GetKey()==EKeys::Escape)) return Close();
    return SCompoundWidget::OnKeyDown(G,E);
}
void SCombatWorkbench::Rebuild()
{
    if(!Rows || !Model.IsValid()) return;
    Rows->ClearChildren();
    if(Tab==4)
    {
        const auto Current=Model->ReadValues();
        const auto Changed=ChangedFields();
        Rows->AddSlot().AutoHeight()[Label(FString::Printf(TEXT("전체 대상 변경 %d건 · 현재 적용값 → 변경값"),Changed.Num()),18)];
        Rows->AddSlot().AutoHeight().Padding(0,6)[Label(TEXT("변경 취소는 현재 적용값으로 돌아갑니다. 초기 설정 복원과 다릅니다."),16)];
        FString LastActor,LastGroup;
        for(int32 I:Changed)
        {
            const auto& F=Model->Fields[I];
            if(LastActor!=F.ActorKey || LastGroup!=F.Group)
            {
                LastActor=F.ActorKey;LastGroup=F.Group;
                const FString Target=F.bEnemy?TEXT("슬라임 · ")+FPaths::GetCleanFilename(F.ActorKey):TEXT("플레이어");
                Rows->AddSlot().AutoHeight().Padding(0,8,0,4)[Label(Target+TEXT(" / ")+F.Group,18)];
            }
            const auto ValueText=[&F](double V){return F.bBoolean?FString(V?TEXT("켜짐"):TEXT("꺼짐")):FString::Printf(TEXT("%.9g"),V);};
            Rows->AddSlot().AutoHeight().Padding(0,4)[
                SNew(SHorizontalBox)
                +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[Label(F.Label+TEXT("   ")+ValueText(Current[I])+TEXT(" → ")+ValueText(Draft[I]))]
                +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Button(TEXT("이 변경 취소"),[this,I]{return UndoDraftField(I);})]];
        }
        if(Changed.IsEmpty()) Rows->AddSlot().AutoHeight().Padding(0,14)[Label(TEXT("현재 적용값과 같습니다. 적용 전 변경이 없습니다."))];
        return;
    }
    if(Tab==3)
    {
        Rows->AddSlot().AutoHeight()[Label(TEXT("기록 시각은 게임 시간 · 공격 위치는 몽타주 시간 · 주황색은 요청한 타격 범위"),18)];
        Rows->AddSlot().AutoHeight().Padding(0,12)[SNew(STextBlock).Font(Font()).ColorAndOpacity(Ink).AutoWrapText(true)
            .Text_Lambda([this]{
                auto* P=Player.Get();auto* E=Enemy();
                return Text(FString::Printf(TEXT("플레이어 최근 피해 (최대 12건)\n%s\n\n슬라임 최근 피해 (최대 12건)\n%s\n\n슬라임 AI\n%s\n\n패턴 판단\n%s"),
                    *DamageHistory(P).ToString(),*DamageHistory(E).ToString(),E?*E->EnemyAgent->Decision:TEXT("-"),E?*E->Combat->LastPatternDecision:TEXT("-")));
            })];
        return;
    }
    FString LastGroup;
    int32 Count=0;
    for(int32 I=0;I<Model->Fields.Num();++I)
    {
        const auto& F=Model->Fields[I];
        const bool SelectedEnemy=F.bEnemy && F.ActorKey==EnemyKey;
        const bool Show=Tab==0?!F.bEnemy:Tab==1?(SelectedEnemy&&!F.bPattern):(SelectedEnemy&&F.bPattern);
        if(!Show) continue;
        ++Count;
        if(F.Group!=LastGroup)
        {
            LastGroup=F.Group;
            Rows->AddSlot().AutoHeight().Padding(0,18,0,8)[Label(F.Group,22)];
            if(const auto* Action=Cast<UCombatActionDefinition>(F.Object.Get());Action && Action->NextAction && Action->Montage)
                Rows->AddSlot().AutoHeight().Padding(0,0,0,6)[Label(FString::Printf(TEXT("다음 공격: %s · 몽타주 %.2fs · 선입력은 다음 공격을 예약하는 구간"),*Action->NextAction->DisplayName.ToString(),Action->Montage->GetPlayLength()),16)];
        }
        TSharedPtr<SWidget> Entry;
        if(F.bBoolean)
            Entry=SNew(SCheckBox).IsChecked_Lambda([this,I]{return Draft.IsValidIndex(I)&&Draft[I]!=0?ECheckBoxState::Checked:ECheckBoxState::Unchecked;})
                .OnCheckStateChanged_Lambda([this,I](ECheckBoxState S){Draft[I]=S==ECheckBoxState::Checked?1:0;Message.Reset();});
        else
            Entry=SNew(SNumericEntryBox<double>).Font(Font()).AllowSpin(false).MinDesiredValueWidth(160)
                .Value_Lambda([this,I]()->TOptional<double>{return Draft.IsValidIndex(I)?TOptional<double>(Draft[I]):TOptional<double>();})
                .OnValueCommitted_Lambda([this,I](double V,ETextCommit::Type){if(Draft.IsValidIndex(I)){Draft[I]=V;Message.Reset();}});
        Rows->AddSlot().AutoHeight().Padding(0,3)[
            SNew(SHorizontalBox)
            +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[
                SNew(STextBlock).Font(Font()).AutoWrapText(true)
                .ColorAndOpacity_Lambda([this,I]{
                    const auto& F=Model->Fields[I]; const double V=Draft[I];
                    return (!FMath::IsFinite(V) || V<F.Min || V>F.Max || ((F.bInteger||F.bBoolean)&&V!=FMath::FloorToDouble(V)))?FSlateColor(FLinearColor(1,.4f,.3f)):FSlateColor(Ink);
                })
                .Text_Lambda([this,I]{
                    const auto& F=Model->Fields[I]; const double V=Draft[I];
                    const bool Bad=!FMath::IsFinite(V)||V<F.Min||V>F.Max||((F.bInteger||F.bBoolean)&&V!=FMath::FloorToDouble(V));
                    return Text(Bad?F.Label+FString::Printf(TEXT("  [범위 %g ~ %g%s]"),F.Min,F.Max,F.bInteger?TEXT(", 정수"):TEXT("")):F.Label);
                })]
            +SHorizontalBox::Slot().AutoWidth().Padding(8,0)[SNew(SBox).WidthOverride(180)[Entry.ToSharedRef()]]
            +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8,0)[SNew(SBox).WidthOverride(180)[Label(F.bBoolean?(F.DefaultValue?TEXT("초기 켜짐"):TEXT("초기 꺼짐")):FString::Printf(TEXT("초기 %g"),F.DefaultValue),16)]]
            +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("원복"),[this,I]{Draft[I]=Model->Fields[I].DefaultValue;return FReply::Handled();})]];
    }
    if(!Count) Rows->AddSlot().AutoHeight()[Label(TEXT("편집할 대상이 없습니다."))];
}
TArray<int32> SCombatWorkbench::ChangedFields() const
{
    TArray<int32> Result;
    if(!Model.IsValid()) return Result;
    const auto Current=Model->ReadValues();
    if(Draft.Num()!=Current.Num()) return Result;
    for(int32 I=0;I<Draft.Num();++I) if(Draft[I]!=Current[I]) Result.Add(I);
    return Result;
}
FReply SCombatWorkbench::UndoDraftField(int32 Index)
{
    if(Model.IsValid())
    {
        const auto Current=Model->ReadValues();
        if(Draft.IsValidIndex(Index) && Current.IsValidIndex(Index)) Draft[Index]=Current[Index];
        Message.Reset();Rebuild();
    }
    return FReply::Handled();
}
FReply SCombatWorkbench::Close(){SetOpen(false);return FReply::Handled();}
FReply SCombatWorkbench::Apply()
{
    if(Model.IsValid() && Model->ApplyValues(Draft,Message))
    {
        auto* P=Player.Get(); SetOpen(false);
        if(P) if(auto* PC=Cast<APlayerController>(P->GetController())) PC->ConsoleCommand(TEXT("RestartLevel"));
    }
    return FReply::Handled();
}
FReply SCombatWorkbench::Restore()
{
    if(Model.IsValid()) {Draft.Reset();for(const auto& F:Model->Fields) Draft.Add(F.DefaultValue);Message=TEXT("초기 설정을 초안에 복원했습니다. 적용 버튼으로 재시작하세요.");Rebuild();}
    return FReply::Handled();
}
FReply SCombatWorkbench::Save()
{
    if(Model.IsValid()) Model->SavePreset(Draft,PresetName->GetText().ToString(),Message);
    return FReply::Handled();
}
FReply SCombatWorkbench::Load()
{
    if(Model.IsValid())
    {
        const FString Name=PresetName->GetText().ToString();
        const bool Loaded=bReportInput?Model->LoadTuningReport(Name,Draft,Message):Model->LoadPreset(Name,Draft,Message);
        if(Loaded)
        {
            const FString Notice=Message;
            Tab=4;Message=bReportInput?TEXT("AI 파일의 preset.values를 읽었습니다. 변경 내역 확인 후 적용하세요."):TEXT("불러오기 완료. 변경 내역 확인 후 적용하세요.");
            if(!Notice.IsEmpty()) Message+=TEXT("\n")+Notice;
            Rebuild();
        }
    }
    return FReply::Handled();
}
FReply SCombatWorkbench::NextPreset()
{
    if(Model.IsValid())
    {
        auto Names=bReportInput?Model->ListTuningReports():Model->ListPresets();
        if(Names.IsEmpty()) Message=TEXT("선택한 입력 종류에 저장된 파일이 없습니다.");
        else {int32 I=Names.IndexOfByKey(PresetName->GetText().ToString());PresetName->SetText(Text(Names[(I+1)%Names.Num()]));Message=FString::Printf(TEXT("선택한 종류의 파일 %d개 · 불러오기 버튼으로 초안에 읽습니다."),Names.Num());}
    }
    return FReply::Handled();
}
FReply SCombatWorkbench::NextEnemy()
{
    if(Model.IsValid())
    {
        TArray<FString> Keys;
        for(const auto& F:Model->Fields) if(F.bEnemy) Keys.AddUnique(F.ActorKey);
        if(!Keys.IsEmpty()) {EnemyKey=Keys[(Keys.IndexOfByKey(EnemyKey)+1)%Keys.Num()];Rebuild();}
    }
    return FReply::Handled();
}
void SCombatWorkbench::Tick(const FGeometry& G,double Time,float Delta)
{
    SCompoundWidget::Tick(G,Time,Delta);
#if !UE_BUILD_SHIPPING
    if(!FParse::Param(FCommandLine::Get(),TEXT("CombatWorkbenchReview"))) return;
    if(ReviewStart==0) ReviewStart=Time;
    const double Elapsed=Time-ReviewStart;
    static bool RequestedRestart=false, CheckedRestart=false, RequestedDeathRestart=false;
    static TWeakObjectPtr<UWorld> DeathWorld;
    if(RequestedDeathRestart)
    {
        if(DeathWorld.Get()==Player->GetWorld()) return;
        FString Reason;
        const bool OK=Player->Combat->GetHealth()==Player->Combat->GetMaxHealth() &&
            Player->Combat->CanStart(Player->Action,Reason) && !UGameplayStatics::IsGamePaused(Player.Get()) &&
            FMath::IsNearlyEqual(UGameplayStatics::GetGlobalTimeDilation(Player.Get()),1.f);
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchDeathRestartReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        FPlatformMisc::RequestExit(false);return;
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("CombatWorkbenchApplyReview")) && Elapsed>1)
    {
        if(!RequestedRestart)
        {
            RequestedRestart=true; SetOpen(true);
            for(int32 I=0;I<Model->Fields.Num();++I)
            {
                const auto& F=Model->Fields[I];
                if(F.Property==TEXT("MaxHealth")) Draft[I]=F.bEnemy?200:175;
                if(F.Property==TEXT("MaxStamina") && !F.bEnemy) Draft[I]=80;
                if(F.Property==TEXT("InputWindowStart") && !F.bEnemy) Draft[I]=.25;
                if(F.Property==TEXT("bAllowDodgeCancel") && !F.bEnemy) Draft[I]=1;
            }
            FString Preset;
            if(FParse::Value(FCommandLine::Get(),TEXT("CombatWorkbenchPreset="),Preset))
            {
                const bool Loading=FParse::Param(FCommandLine::Get(),TEXT("CombatWorkbenchLoadPreset"));
                const bool OK=Loading?Model->LoadPreset(Preset,Draft,Message):Model->SavePreset(Draft,Preset,Message);
                UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchPreset%sReview: %s"),Loading?TEXT("Load"):TEXT("Save"),OK?TEXT("PASS"):TEXT("FAIL"));
            }
            Apply(); return;
        }
        if(!CheckedRestart)
        {
            CheckedRestart=true;
            auto* P=Player.Get(); auto* E=Enemy();
            const bool OK=P && E && P->Combat->GetMaxHealth()==175 && P->Combat->GetMaxStamina()==80 && E->Combat->GetMaxHealth()==200;
            UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchRestartReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
            const bool WindowOK=P && P->Action && P->Action->NextAction && FMath::IsNearlyEqual(P->Action->InputWindowStart,.25f);
            UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchInputWindowReview: %s"),WindowOK?TEXT("PASS"):TEXT("FAIL"));
        }
    }
    if(ReviewStep==0 && Elapsed>3)
    {
        auto* V=Player->GetGameInstance()->GetGameViewportClient();
        ReviewViewMode=V->ViewModeIndex;
        // Enter through the same viewport/player-input path as a gameplay key, including debug exec bindings.
        V->InputKey(FInputKeyEventArgs(V->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),EKeys::F1,IE_Pressed,FPlatformTime::Cycles64()));
        ++ReviewStep;
    }
    else if(ReviewStep==1 && Elapsed>5)
    {
        auto* V=Player->GetGameInstance()->GetGameViewportClient();
        V->InputKey(FInputKeyEventArgs(V->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),EKeys::F1,IE_Released,FPlatformTime::Cycles64()));
        const bool OK=bOpen && Player->bWorkbenchOpen && UGameplayStatics::IsGamePaused(Player.Get()) && V->ViewModeIndex==ReviewViewMode;
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchF1OpenReview: %s (open=%d, view=%d, before=%d)"),OK?TEXT("PASS"):TEXT("FAIL"),bOpen,V->ViewModeIndex,ReviewViewMode);
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Workbench-panel.png"),true,false);
        // Closing F1 must bubble even when a text field owns keyboard focus.
        if(bOpen) FSlateApplication::Get().SetKeyboardFocus(PresetName,EFocusCause::SetDirectly);
        ReviewStep=20;
    }
    else if(ReviewStep==20 && Elapsed>6)
    {
        ReviewChangeIndex=INDEX_NONE;
        for(int32 I=0;I<Model->Fields.Num();++I)
            if(!Model->Fields[I].bEnemy && Model->Fields[I].Property==TEXT("MaxHealth")) {ReviewChangeIndex=I;break;}
        float ExpectedSourceHealth=100;FParse::Value(FCommandLine::Get(),TEXT("CombatWorkbenchExpectedHealth="),ExpectedSourceHealth);
        const auto Before=Model->ReadValues();
        bool OK=ChangedFields().IsEmpty() && ReviewChangeIndex!=INDEX_NONE;
        if(ReviewChangeIndex!=INDEX_NONE)
        {
            Draft[ReviewChangeIndex]=200;
            const auto Changed=ChangedFields();
            OK=OK && Changed.Num()==1 && Changed[0]==ReviewChangeIndex &&
                Before[ReviewChangeIndex]==175 && Model->Fields[ReviewChangeIndex].DefaultValue==ExpectedSourceHealth &&
                Model->ReadValues()==Before;
        }
        Tab=4;Rebuild();
        FString ReviewPreset;
        if(FParse::Value(FCommandLine::Get(),TEXT("CombatWorkbenchPreset="),ReviewPreset))
        {
            const FString ReportName=ReviewPreset+(FParse::Param(FCommandLine::Get(),TEXT("CombatWorkbenchLoadPreset"))?TEXT("_Load"):TEXT("_Save"));
            FString ReportResult;
            const auto BeforeExport=Model->ReadValues();
            const bool Exported=Model->ExportTuningReport(Draft,ReportName,ReportResult);
            UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchTuningReportReview: %s"),Exported && Model->ReadValues()==BeforeExport?TEXT("PASS"):TEXT("FAIL"));
            const auto Expected=Draft;
            const FText PreviousName=PresetName->GetText();
            PresetName->SetText(Text(ReportName));bReportInput=true;
            Draft=BeforeExport;Load();
            const bool Loaded=Draft==Expected && Model->ReadValues()==BeforeExport && Tab==4;
            UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchReportImportReview: %s"),Loaded?TEXT("PASS"):TEXT("FAIL"));
            PresetName->SetText(PreviousName);Message.Reset();

        }
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchChangesReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Workbench-changes.png"),true,false);
        ReviewStep=2;
    }
    else if(ReviewStep==2 && Elapsed>7)
    {
        UndoDraftField(ReviewChangeIndex);
        const bool OK=ChangedFields().IsEmpty() && Draft==Model->ReadValues() &&
            Draft.IsValidIndex(ReviewChangeIndex) && Draft[ReviewChangeIndex]==175;
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchUndoChangeReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(EKeys::F1,FModifierKeysState(),0,false,0,0));
        FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(EKeys::F1,FModifierKeysState(),0,false,0,0));
        ++ReviewStep;
    }
    else if(ReviewStep==3 && Elapsed>9)
    {
        auto* V=Player->GetGameInstance()->GetGameViewportClient();
        const bool OK=!bOpen && !Player->bWorkbenchOpen && !UGameplayStatics::IsGamePaused(Player.Get()) && V->ViewModeIndex==ReviewViewMode;
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchF1CloseReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Workbench-hud.png"),true,false);
        ++ReviewStep;
    }
    else if(ReviewStep==4 && Elapsed>11)
    {
        SetObservationSpeed(true);
        const bool OK=FMath::IsNearlyEqual(UGameplayStatics::GetGlobalTimeDilation(Player.Get()),OriginalTimeScale*.25f);
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchSlowReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        SetObservationSpeed(false);
        auto* C=Player->Combat.Get();
        C->ResetAfterReturn();
        // Isolate keyboard handoff from unrelated monster hits for this review only.
        if(auto* E=Enemy()) {E->EnemyAgent->SetComponentTickEnabled(false);E->Combat->CancelAction();}
        ReviewDodgeAttackStarted=C->TryStartAction(Player->Action);
        if(ReviewDodgeAttackStarted) Player->GetMesh()->GetAnimInstance()->Montage_SetPosition(Player->Action->Montage,.55f);
        auto* DodgeViewport=Player->GetGameInstance()->GetGameViewportClient();
        DodgeViewport->InputKey(FInputKeyEventArgs(DodgeViewport->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),EKeys::SpaceBar,IE_Pressed,FPlatformTime::Cycles64()));
        ReviewDodgeInputTime=Time;ReviewStep=40;
    }
    else if(ReviewStep==40 && Time-ReviewDodgeInputTime>.1)
    {
        auto* C=Player->Combat.Get();
        auto* DodgeViewport=Player->GetGameInstance()->GetGameViewportClient();
        DodgeViewport->InputKey(FInputKeyEventArgs(DodgeViewport->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),EKeys::SpaceBar,IE_Released,FPlatformTime::Cycles64()));
        const bool DodgeOK=ReviewDodgeAttackStarted && C->IsDodging() && !C->IsActing() &&
            FMath::IsNearlyEqual(C->GetStamina(),C->GetMaxStamina()-Player->Action->StaminaCost-C->DodgeStaminaCost);
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchDodgeCancelReview: %s (started=%d dodge=%d attack=%d sp=%.1f reason=%s)"),DodgeOK?TEXT("PASS"):TEXT("FAIL"),ReviewDodgeAttackStarted,C->IsDodging(),C->IsActing(),C->GetStamina(),*C->LastReason);
        C->CancelDodge();
        Player->Combat->ReceiveCombatDamage(Player->Combat->GetMaxHealth()*10,Enemy());
        auto* V=Player->GetGameInstance()->GetGameViewportClient();
        V->InputKey(FInputKeyEventArgs(V->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),EKeys::F1,IE_Pressed,FPlatformTime::Cycles64()));
        ReviewStep=5;
    }
    else if(ReviewStep==5 && Elapsed>13)
    {
        const bool OK=bOpen && Player->Combat->GetHealth()==0 && UGameplayStatics::IsGamePaused(Player.Get());
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchDeathOpenReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        Tab=3;Rebuild();
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Workbench-history.png"),true,false);
        ++ReviewStep;
    }
    else if(ReviewStep==6 && Elapsed>15)
    {
        FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(EKeys::F1,FModifierKeysState(),0,false,0,0));
        FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(EKeys::F1,FModifierKeysState(),0,false,0,0));
        const bool OK=!bOpen && !UGameplayStatics::IsGamePaused(Player.Get()) && FMath::IsNearlyEqual(UGameplayStatics::GetGlobalTimeDilation(Player.Get()),OriginalTimeScale);
        UE_LOG(LogTemp,Display,TEXT("CombatWorkbenchDeathCloseReview: %s"),OK?TEXT("PASS"):TEXT("FAIL"));
        ++ReviewStep;
    }
    else if(ReviewStep==7 && Elapsed>17)
    {
        DeathWorld=Player->GetWorld();RequestedDeathRestart=true;
        Apply(); ++ReviewStep;
    }
#endif
}


FReply SCombatWorkbench::SetObservationSpeed(bool Slow)
{
    if(auto* P=Player.Get())
    {
        UGameplayStatics::SetGlobalTimeDilation(P,OriginalTimeScale*(Slow?.25f:1.f));
        bSlow=Slow;
    }
    return FReply::Handled();
}
FReply SCombatWorkbench::ToggleHitVolumes()
{
    bShowHitVolumes=!bShowHitVolumes;
    if(auto* P=Player.Get()) for(TActorIterator<ACombatLabCharacter> It(P->GetWorld());It;++It)
    {
        if(!OriginalHitDebug.Contains(*It)) OriginalHitDebug.Add(*It,It->Combat->bDrawHitDebug);
        It->Combat->bDrawHitDebug=bShowHitVolumes;
    }
    return FReply::Handled();
}
void SCombatWorkbench::RestoreObservation()
{
    if(auto* P=Player.Get()) UGameplayStatics::SetGlobalTimeDilation(P,OriginalTimeScale);
    for(const auto& Pair:OriginalHitDebug) if(auto* A=Pair.Key.Get()) A->Combat->bDrawHitDebug=Pair.Value;
    OriginalHitDebug.Reset();bSlow=false;
}
FText SCombatWorkbench::DamageHistory(ACombatLabCharacter* A) const
{
    if(!A) return Text(TEXT("대상 없음"));
    const auto& Records=A->Combat->GetDamageHistory();
    if(Records.IsEmpty()) return Text(TEXT("피해 기록 없음"));
    FString Result;
    for(int32 I=Records.Num()-1;I>=0;--I)
    {
        const auto& R=Records[I];
        Result+=FString::Printf(TEXT("%.2fs  %s  %s %.0f  → HP %.0f\n"),R.GameTime,*R.Source,
            R.bAvoided?TEXT("무적 회피 · 피해"):TEXT("피해"),R.Damage,R.HealthAfter);
    }
    return Text(Result);
}
FText SCombatWorkbench::InputStatus() const
{
    auto* P=Player.Get();if(!P) return FText();
    auto* C=P->Combat.Get(); const auto O=C->ObserveAction();
    FString Ready;
    if(O.bActive)
    {
        Ready=O.bHasFollowup?FString::Printf(TEXT("선입력 시간 %s  %.2f~%.2fs"),O.bInputOpen?TEXT("열림"):TEXT("닫힘"),O.InputStart,O.InputEnd):TEXT("후속 공격 없음");
        Ready+=C->IsDodgeCancelWindowOpen()?TEXT("\n회피 전환 구간 열림 · SP/지상 조건 필요"):TEXT("\n회피 전환 구간 닫힘");
    }
    else
    {
        FString Reason;
        if(C->CanStart(P->Action,Reason)) Ready=TEXT("기본 공격 가능");
        else if(Reason==TEXT("Cooldown")) Ready=FString::Printf(TEXT("쿨다운 %.2fs"),C->GetCooldownRemaining(P->Action));
        else if(Reason==TEXT("Not enough stamina") && P->Action)
            Ready=FString::Printf(TEXT("SP 부족  %.0f / 필요 %.0f"),C->GetStamina(),P->Action->StaminaCost);
        else Ready=CombatObservation::ExplainReason(Reason);
    }
    FString LastDamage=TEXT("피해 기록 없음");
    if(!C->GetDamageHistory().IsEmpty())
    {
        const auto& R=C->GetDamageHistory().Last();
        LastDamage=FString::Printf(TEXT("최근 피격  %s %.0f · HP %.0f"),R.bAvoided?TEXT("무적 회피"):TEXT("피해"),R.Damage,R.HealthAfter);
    }
    return Text(FString::Printf(TEXT("%s\n선입력 예약 %s · 판정 %s\n입력 결과: %s\n%s"),*Ready,
        P->AttackInput->HasBufferedAttack()?TEXT("있음"):TEXT("없음"),O.bHitOpen?TEXT("활성"):TEXT("닫힘"),
        *CombatObservation::ExplainReason(P->AttackInput->LastInputReason),*LastDamage));
}

FText SCombatWorkbench::SpecialActionsStatus() const
{
    auto* P=Player.Get(); if(!P) return FText();
    auto* C=P->Combat.Get();
    auto Availability=[C](const UCombatActionDefinition* A)->FString
    {
        if(!A) return TEXT("미지정");
        const float Cooldown=C->GetCooldownRemaining(A);
        if(Cooldown>0) return FString::Printf(TEXT("쿨다운 %.1fs"),Cooldown);
        if(C->GetUltimateCharge()<A->UltimateCost) return FString::Printf(TEXT("게이지 %.0f 필요"),A->UltimateCost);
        FString Reason;
        return C->CanStart(A,Reason)?FString(TEXT("사용 가능")):CombatObservation::ExplainReason(Reason);
    };
    return Text(FString::Printf(TEXT("궁극기 %.0f / 100\nQ 스킬: %s\nE 궁극기: %s"),
        C->GetUltimateCharge(),*Availability(P->SkillAction),*Availability(P->UltimateAction)));
}
