#pragma once
#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
class ACombatLabCharacter;
class UCombatWorkbenchSubsystem;
class SVerticalBox;
class SEditableTextBox;

class SCombatWorkbench : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SCombatWorkbench) {} SLATE_END_ARGS()
    void Construct(const FArguments& Args,ACombatLabCharacter* InPlayer);
    void SetOpen(bool Open);
    void RestoreObservation();
    bool IsOpen() const {return bOpen;}
    virtual bool SupportsKeyboardFocus() const override {return true;}
    virtual FReply OnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
    virtual void Tick(const FGeometry& Geometry,double Time,float Delta) override;
private:
    TWeakObjectPtr<ACombatLabCharacter> Player;
    TWeakObjectPtr<UCombatWorkbenchSubsystem> Model;
    TArray<double> Draft;
    TSharedPtr<SVerticalBox> Rows;
    TSharedPtr<SEditableTextBox> PresetName;
    FString Message,EnemyKey;
    int32 Tab=0;
    bool bReportInput=false;
    bool bOpen=false, bSlow=false, bShowHitVolumes=true;
    float OriginalTimeScale=1.f;
    TMap<TWeakObjectPtr<ACombatLabCharacter>,bool> OriginalHitDebug;
    FReply SetObservationSpeed(bool Slow);
    FReply ToggleHitVolumes();
    FText InputStatus() const;
    FText SpecialActionsStatus() const;
    FText DamageHistory(ACombatLabCharacter* Actor) const;
    double ReviewStart=0;
    int32 ReviewStep=0;
    bool ReviewDodgeAttackStarted=false;
    double ReviewDodgeInputTime=0;
    int32 ReviewViewMode=INDEX_NONE;
    void Rebuild();
    FReply Apply();
    FReply Close();
    FReply Restore();
    FReply Save();
    FReply Load();
    FReply NextPreset();
    FReply NextEnemy();
    TArray<int32> ChangedFields() const;
    FReply UndoDraftField(int32 Index);
    int32 ReviewChangeIndex=INDEX_NONE;
    bool Dirty() const;
    ACombatLabCharacter* Enemy() const;
    FText Status(ACombatLabCharacter* A) const;
    TSharedRef<SWidget> Card(bool EnemyCard);
};
