#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CombatWorkbenchSubsystem.generated.h"
class ACombatLabCharacter;
class FJsonObject;

struct FCombatTuningField
{
    FString Key, Label, Group, ActorKey;
    bool bEnemy=false, bPattern=false, bBoolean=false, bInteger=false;
    double Value=0, DefaultValue=0, Min=0, Max=100000;
    TWeakObjectPtr<UObject> Object;
    FName Property;
    int32 PatternIndex=INDEX_NONE;
};
UCLASS()
class COMBATRUNTIME_API UCombatWorkbenchSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    TArray<FCombatTuningField> Fields;
    void PrepareActor(ACombatLabCharacter* Actor);
    TArray<double> ReadValues() const;
    bool ValidateValues(const TArray<double>& Values,FString& Error);
    bool ApplyValues(const TArray<double>& Values,FString& Error);
    bool SavePreset(const TArray<double>& Values,const FString& Name,FString& Result);
    bool ExportTuningReport(const TArray<double>& Values,const FString& Name,FString& Result);
    bool LoadPreset(const FString& Name,TArray<double>& Values,FString& Error);
    TArray<FString> ListPresets() const;
    bool LoadTuningReport(const FString& Name,TArray<double>& Values,FString& Error);
    TArray<FString> ListTuningReports() const;
private:
    UPROPERTY() TArray<TObjectPtr<UObject>> Copies;
    TWeakObjectPtr<UWorld> FieldWorld;
    TArray<TWeakObjectPtr<ACombatLabCharacter>> Actors;
    TMap<FString,double> Applied;
    TMap<FString,FString> Sources, AppliedSources;
    bool ReadPresetDocument(const TSharedPtr<FJsonObject>& Root,TArray<double>& Values,FString& Error);
    TSharedRef<FJsonObject> MakePresetDocument(const TArray<double>& Values) const;
    double ReadField(const FCombatTuningField& Field) const;
    void WriteField(const FCombatTuningField& Field,double Value);
    void Add(UObject* Object,const TCHAR* Property,const FString& Key,const FString& Label,const FString& Group,
        const FString& ActorKey,bool Enemy,double Min=0,double Max=100000,bool Pattern=false,int32 Index=INDEX_NONE);
};
