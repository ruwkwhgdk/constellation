#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ToolMenus.h"
#include "CombatLabEditorLibrary.h"
#include "CombatLabCharacter.h"
#include "CombatActionDefinition.h"
#include "CombatAbilitySystem.h"
#include "CombatEncounterProfile.h"
#include "CombatPatternProfile.h"
#include "Engine/World.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatAuthoringTest,"Constellation.CombatCore.EditorCharacterValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatAuthoringTest::RunTest(const FString&)
{
    auto* Menu=UToolMenus::Get()->FindMenu("LevelEditor.MainMenu.Tools");
    auto* Section=Menu?Menu->FindSection("ConstellationCombat"):nullptr;
    TestTrue(TEXT("Selected enemy validation menu registered"),Section && Section->FindEntry("CombatValidateSelectedEnemy"));
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    auto* Enemy=World->SpawnActor<ACombatLabCharacter>();
    Enemy->bTrainingEnemy=true;
    Enemy->GetMesh()->SetSkeletalMeshAsset(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal")));
    Enemy->IdleAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Idle"));
    Enemy->MoveAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Move"));
    Enemy->EncounterProfile=NewObject<UCombatEncounterProfile>(Enemy);
    auto* Source=LoadObject<UCombatPatternProfile>(nullptr,TEXT("/Game/Constellation/Review/CombatCore/DA_SlimePatterns"));
    TestNotNull(TEXT("Fixture profile"),Source);
    if(!Source) { World->DestroyWorld(false); return false; }
    Enemy->PatternProfile=DuplicateObject<UCombatPatternProfile>(Source,Enemy);
    TArray<FString> Errors,Warnings;
    TestTrue(TEXT("Complete enemy accepted"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    auto* Profile=Enemy->PatternProfile.Get();
    const auto SavedPatterns=Profile->Patterns;
    for(auto& Pattern:Profile->Patterns)
    {
        Pattern.Action=DuplicateObject<UCombatActionDefinition>(Pattern.Action,Enemy);
        Pattern.Action->Montage=nullptr;
    }
    TestFalse(TEXT("Multiple invalid actions rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    for(const auto& Pattern:Profile->Patterns)
        TestTrue(TEXT("Every broken action identified"),FString::Join(Errors,TEXT(" ")).Contains(Pattern.Id.ToString()));
    Profile->Patterns=SavedPatterns;
    for(auto& Pattern:Profile->Patterns) Pattern.MaxDistance=100;
    TestFalse(TEXT("Unreachable stop range rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    TestTrue(TEXT("Range error explains field"),FString::Join(Errors,TEXT(" ")).Contains(TEXT("AttackDistance")));
    for(auto& Pattern:Profile->Patterns) { Pattern.MaxDistance=180; Pattern.Weight=0; }
    TestFalse(TEXT("All disabled rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    Profile->Patterns[0].Weight=1; Profile->Patterns[0].MaxConsecutive=2;
    TestTrue(TEXT("Repeat issue is a warning"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    TestTrue(TEXT("Repeat warning supplied"),FString::Join(Warnings,TEXT(" ")).Contains(TEXT("MaxConsecutive")));
    auto* Action=DuplicateObject<UCombatActionDefinition>(Profile->Patterns[0].Action,Enemy);
    Profile->Patterns[0].Action=Action; Action->StaminaCost=101;
    TestFalse(TEXT("Impossible cost rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    TestTrue(TEXT("Cost error identifies field"),FString::Join(Errors,TEXT(" ")).Contains(TEXT("StaminaCost")));
    Enemy->Combat->MaxStamina=200;Action->StaminaCost=150;
    TestTrue(TEXT("Configured SP capacity accepted"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    Action->StaminaCost=201;
    TestFalse(TEXT("Configured SP capacity enforced"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    Action->StaminaCost=0;
    auto* Move=Enemy->MoveAnimation.Get();
    Enemy->MoveAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft"));
    TestFalse(TEXT("Incompatible locomotion rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    TestTrue(TEXT("Locomotion error identifies field"),FString::Join(Errors,TEXT(" ")).Contains(TEXT("MoveAnimation")));
    Enemy->MoveAnimation=Move; Enemy->bTrainingEnemy=false;
    TestFalse(TEXT("Player not treated as enemy"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    Enemy->bTrainingEnemy=true; Enemy->MoveAnimation=nullptr;
    TestFalse(TEXT("Missing move animation rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    Enemy->PatternProfile=nullptr; Enemy->EncounterProfile=nullptr;
    TestFalse(TEXT("Missing profiles rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(Enemy,Errors,Warnings));
    TestTrue(TEXT("Multiple errors collected"),Errors.Num()>=3);
    TestFalse(TEXT("Null selection rejected"),UCombatLabEditorLibrary::ValidateCombatCharacter(nullptr,Errors,Warnings));
    TestEqual(TEXT("Prior report cleared"),Errors.Num(),1);
    World->DestroyWorld(false); return true;
}
#endif
