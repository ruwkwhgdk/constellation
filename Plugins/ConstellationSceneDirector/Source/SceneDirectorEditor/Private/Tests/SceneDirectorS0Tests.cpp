#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorChoice.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorPlayer.h"
#include "SDirectorChoices.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FS0DisabledChoiceTest,"Constellation.SceneDirector.S0.DisabledChoice",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FS0DisabledChoiceTest::RunTest(const FString&)
{
 auto* Enabled=FindFProperty<FBoolProperty>(FDirectorChoice::StaticStruct(),TEXT("bEnabled"));
 if(!TestNotNull(TEXT("Choices support individual enabled state"),Enabled))return false;
 TArray<FDirectorChoice> C;
 for(int32 I=0;I<3;++I){FDirectorChoice Item;Item.Key=FName(*FString::Printf(TEXT("C%d"),I));Item.Text=FText::FromString(TEXT("Inspect"));C.Add(Item);}
 TestTrue(TEXT("Old choices default enabled"),Enabled->GetPropertyValue_InContainer(&C[0]));
 Enabled->SetPropertyValue_InContainer(&C[0],false);Enabled->SetPropertyValue_InContainer(&C[2],false);
 FString Error;TestTrue(TEXT("One enabled option validates"),DirectorChoices::Validate(C,Error));
 int32 Calls=0;auto W=SNew(SDirectorChoices).Style(GetDefault<ASceneDirectorPlayer>()->DialogueChoiceStyle).Options(C).CanChoose(true).OnChosen_Lambda([&](FName){++Calls;});
 TestEqual(TEXT("Initial focus skips disabled"),W->GetFocusedIndex(),1);
 TestFalse(TEXT("Disabled click rejected"),W->Choose(0));W->MoveFocus(1);TestEqual(TEXT("Down skips disabled and wraps"),W->GetFocusedIndex(),1);
 W->MoveFocus(-1);TestEqual(TEXT("Up skips disabled and wraps"),W->GetFocusedIndex(),1);TestTrue(TEXT("Enabled confirm accepted"),W->Confirm());TestEqual(TEXT("Exactly one result"),Calls,1);
 Enabled->SetPropertyValue_InContainer(&C[1],false);TestFalse(TEXT("All disabled rejected"),DirectorChoices::Validate(C,Error));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FS0DisabledBranchTest,"Constellation.SceneDirector.S0.DisabledBranch",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FS0DisabledBranchTest::RunTest(const FString&)
{
 auto* Enabled=FindFProperty<FBoolProperty>(FDirectorChoice::StaticStruct(),TEXT("bEnabled"));if(!TestNotNull(TEXT("Choice enabled property exists"),Enabled))return false;
 auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(3);A->Steps[0].Type=EDirectorNodeType::Start;A->Steps[1].Type=EDirectorNodeType::Dialogue;A->Steps[2].Type=EDirectorNodeType::End;
 auto& Q=A->Steps[1];Q.DialogueText=FText::FromString(TEXT("Inspect the locker"));A->Steps[0].NextNodes={Q.Id};
 FDirectorChoice C;C.Key=TEXT("Inspect");C.Text=FText::FromString(TEXT("Inspect"));Q.Choices.Add(C);Q.ChoiceTargets.Add(C.Key,A->Steps[2].Id);
 C.Key=TEXT("Open");C.Text=FText::FromString(TEXT("Strength 1"));Enabled->SetPropertyValue_InContainer(&C,false);Q.Choices.Add(C);
 FString Error;TestTrue(TEXT("Disabled option needs no output"),DirectorBranching::ValidateAll(*A,Error));AddInfo(Error);
 TestTrue(TEXT("Disabled branch graph compiles"),FSceneDirectorCompiler::Compile(*A,Error));
 auto* R=NewObject<USceneDirectorAsset>();FGuid Pending;TMap<FGuid,FName> Decisions;Decisions.Add(Q.Id,TEXT("Open"));
 TestFalse(TEXT("Disabled decision cannot be injected"),DirectorBranching::Resolve(*A,Decisions,{},*R,Pending,Error));
 Q.PreviewChoiceIndex=2;TestFalse(TEXT("Preview cannot pick disabled"),FSceneDirectorCompiler::Compile(*A,Error));Q.PreviewChoiceIndex=1;
 Q.ChoiceTargets.Add(TEXT("Open"),A->Steps[2].Id);TestFalse(TEXT("Stale disabled output diagnosed"),DirectorBranching::ValidateAll(*A,Error));
 return true;
}
#endif
