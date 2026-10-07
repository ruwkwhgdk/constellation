#include "CombatLabEditorLibrary.h"
#include "CombatLabCharacter.h"
#include "CombatActionDefinition.h"
#include "CombatPatternProfile.h"
#include "CombatEncounterProfile.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/Package.h"
#include "Misc/DateTime.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"

namespace CombatReport
{
    TSharedRef<FJsonObject> Reference(const UObject* Object)
    {
        auto Json=MakeShared<FJsonObject>();
        Json->SetStringField(TEXT("path"),Object?Object->GetPathName():TEXT(""));
        Json->SetBoolField(TEXT("package_dirty"),Object && Object->GetOutermost()->IsDirty());
        return Json;
    }
    void Number(const TSharedRef<FJsonObject>& Json,const TCHAR* Key,float Value)
    {
        if(FMath::IsFinite(Value)) Json->SetNumberField(Key,Value);
        else Json->SetStringField(Key,FMath::IsNaN(Value)?TEXT("NaN"):(Value<0?TEXT("-Infinity"):TEXT("Infinity")));
    }
    TArray<TSharedPtr<FJsonValue>> Strings(const TArray<FString>& Values)
    {
        TArray<TSharedPtr<FJsonValue>> Result;
        for(const auto& Value:Values) Result.Add(MakeShared<FJsonValueString>(Value));
        return Result;
    }
}
bool UCombatLabEditorLibrary::SaveCombatCharacterReport(ACombatLabCharacter* Character,FString& SavedPath,FString& Error)
{
    SavedPath.Reset(); Error.Reset();
    if(!Character || !Character->bTrainingEnemy)
    { Error=TEXT("CombatLabCharacter 몬스터 하나를 선택하세요."); return false; }
    TArray<FString> Errors,Warnings;
    const bool Valid=ValidateCombatCharacter(Character,Errors,Warnings);
    auto Root=CombatReport::Reference(Character);
    Root->SetNumberField(TEXT("report_version"),1);
    Root->SetStringField(TEXT("captured_utc"),FDateTime::UtcNow().ToIso8601());
    Root->SetStringField(TEXT("scope"),TEXT("Live editor data, including unsaved changes. Not a recipe or gameplay test."));
    Root->SetStringField(TEXT("actor_label"),Character->GetActorLabel());
    Root->SetBoolField(TEXT("valid"),Valid);
    Root->SetArrayField(TEXT("errors"),CombatReport::Strings(Errors));
    Root->SetArrayField(TEXT("warnings"),CombatReport::Strings(Warnings));
    Root->SetObjectField(TEXT("mesh"),CombatReport::Reference(Character->GetMesh()->GetSkeletalMeshAsset()));
    Root->SetObjectField(TEXT("idle_animation"),CombatReport::Reference(Character->IdleAnimation));
    Root->SetObjectField(TEXT("move_animation"),CombatReport::Reference(Character->MoveAnimation));
    CombatReport::Number(Root,TEXT("animation_move_speed"),Character->AnimationMoveSpeed);
    auto Encounter=CombatReport::Reference(Character->EncounterProfile);
    if(auto* E=Character->EncounterProfile.Get())
    {
        CombatReport::Number(Encounter,TEXT("detect_radius"),E->DetectRadius);
        CombatReport::Number(Encounter,TEXT("lose_radius"),E->LoseRadius);
        CombatReport::Number(Encounter,TEXT("leash_radius"),E->LeashRadius);
        CombatReport::Number(Encounter,TEXT("attack_distance"),E->AttackDistance);
        CombatReport::Number(Encounter,TEXT("move_speed"),E->MoveSpeed);
        CombatReport::Number(Encounter,TEXT("think_interval"),E->ThinkInterval);
        CombatReport::Number(Encounter,TEXT("lost_sight_time"),E->LostSightTime);
        CombatReport::Number(Encounter,TEXT("home_tolerance"),E->HomeTolerance);
        CombatReport::Number(Encounter,TEXT("retry_delay"),E->RetryDelay);
        CombatReport::Number(Encounter,TEXT("retry_cooldown"),E->RetryCooldown);
        CombatReport::Number(Encounter,TEXT("stuck_timeout"),E->StuckTimeout);
        Encounter->SetNumberField(TEXT("max_move_failures"),E->MaxMoveFailures);
        Encounter->SetBoolField(TEXT("restore_on_return"),E->bRestoreOnReturn);
    }
    Root->SetObjectField(TEXT("encounter"),Encounter);
    Root->SetObjectField(TEXT("pattern_profile"),CombatReport::Reference(Character->PatternProfile));
    TArray<TSharedPtr<FJsonValue>> Patterns;
    if(auto* Profile=Character->PatternProfile.Get())
        for(const auto& P:Profile->Patterns)
        {
            auto Json=MakeShared<FJsonObject>();
            Json->SetStringField(TEXT("id"),P.Id.ToString());
            CombatReport::Number(Json,TEXT("min_distance"),P.MinDistance);
            CombatReport::Number(Json,TEXT("max_distance"),P.MaxDistance);
            CombatReport::Number(Json,TEXT("max_angle"),P.MaxAngle);
            CombatReport::Number(Json,TEXT("weight"),P.Weight);
            Json->SetNumberField(TEXT("max_consecutive"),P.MaxConsecutive);
            Json->SetBoolField(TEXT("require_sight"),P.bRequireSight);
            auto Action=CombatReport::Reference(P.Action);
            if(auto* A=P.Action.Get())
            {
                Action->SetStringField(TEXT("display_name"),A->DisplayName.ToString());
                CombatReport::Number(Action,TEXT("input_window_start"),A->InputWindowStart);
                CombatReport::Number(Action,TEXT("input_window_end"),A->InputWindowEnd);
                CombatReport::Number(Action,TEXT("damage"),A->Damage);
                CombatReport::Number(Action,TEXT("stamina_cost"),A->StaminaCost);
                CombatReport::Number(Action,TEXT("cooldown"),A->Cooldown);
                CombatReport::Number(Action,TEXT("play_rate"),A->PlayRate);
                CombatReport::Number(Action,TEXT("reach"),A->Reach);
                CombatReport::Number(Action,TEXT("radius"),A->Radius);
                Action->SetObjectField(TEXT("montage"),CombatReport::Reference(A->Montage));
                Action->SetObjectField(TEXT("next_action"),CombatReport::Reference(A->NextAction));
            }
            Json->SetObjectField(TEXT("action"),Action);
            Patterns.Add(MakeShared<FJsonValueObject>(Json));
        }
    Root->SetArrayField(TEXT("patterns"),Patterns);
    FString Text;
    if(!FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Text)))
    { Error=TEXT("검사 결과를 JSON으로 변환하지 못했습니다."); return false; }
    const FString Directory=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("CombatAudit/CharacterReports"));
    if(!IFileManager::Get().MakeDirectory(*Directory,true))
    { Error=TEXT("보고서 폴더를 만들지 못했습니다: ")+Directory; return false; }
    const FString Candidate=Directory/(TEXT("Combat-")+FGuid::NewGuid().ToString(EGuidFormats::Digits)+TEXT(".json"));
    if(!FFileHelper::SaveStringToFile(Text,*Candidate,FFileHelper::EEncodingOptions::ForceUTF8,&IFileManager::Get(),FILEWRITE_NoReplaceExisting))
    { Error=TEXT("보고서 저장에 실패했습니다: ")+Candidate; return false; }
    SavedPath=Candidate; return true;
}
