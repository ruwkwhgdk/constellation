#include "Misc/AutomationTest.h"
#include "AbilityAcquisitionModel.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAbilityAcquisitionRulesTest,"Constellation.AbilityAcquisition.Rules",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAbilityAcquisitionRulesTest::RunTest(const FString&)
{
 using namespace AbilityAcquisition;
 TestFalse(TEXT("negative slot"),ShouldPresent(-1,0,true));TestFalse(TEXT("reserved slot"),ShouldPresent(3,0,true));
 TestFalse(TEXT("relock ignored"),ShouldPresent(0,0,false));TestFalse(TEXT("duplicate ignored"),ShouldPresent(1,2,true));
 TestTrue(TEXT("out of order gamma allowed"),ShouldPresent(2,1,true));TestTrue(TEXT("beta after gamma allowed"),ShouldPresent(1,4,true));
 TestFalse(TEXT("early input"),CanDismiss(6.19,false,false));TestFalse(TEXT("held repeat"),CanDismiss(7,true,false));TestFalse(TEXT("exit repeated"),CanDismiss(7,false,true));TestTrue(TEXT("fresh input"),CanDismiss(6.2,false,false));
 TestEqual(TEXT("fade before"),Fade(2,2.9,4),0.f);TestEqual(TEXT("fade complete"),Fade(4,2.9,4),1.f);
 TestEqual(TEXT("alpha to beta link"),Link(4),0);TestEqual(TEXT("6 segments 7 points"),Link(6),5);
 TestTrue(TEXT("expanded height"),FMath::IsNearlyEqual(float(Position(3).Y-Position(5).Y),466.7f,.01f));
 return true;
}

#include "AbilityAcquisitionArt.h"
#include "AbilityAcquisitionSubsystem.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/ActorComponent.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAbilityAcquisitionIntegrationTest,"Constellation.AbilityAcquisition.InstalledBlueprint",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAbilityAcquisitionIntegrationTest::RunTest(const FString&)
{
 auto* Art=LoadObject<UAbilityAcquisitionArt>(nullptr,TEXT("/Game/Constellation/UI/AbilityAcquisition/DA_AbilityAcquisition.DA_AbilityAcquisition"));if(!TestNotNull(TEXT("Cookable art bundle"),Art))return false;
 TestTrue(TEXT("All 35 layers and description table"),Art->IsReady());for(int32 I=0;I<3;I++)TestFalse(TEXT("Actual description exists"),Art->Description(I).IsEmpty());
 UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);auto* PC=W->SpawnActor<APlayerController>();auto* Pawn=W->SpawnActor<APawn>();auto* Local=NewObject<ULocalPlayer>(GEngine);Local->PlayerController=PC;PC->Player=Local;W->AddController(PC);PC->Possess(Pawn);
 auto* Class=LoadClass<UActorComponent>(nullptr,TEXT("/Game/Constellation/Gameplay/Interaction/Components/Ac_Ability.Ac_Ability_C"));if(!Class){W->DestroyWorld(false);AddError(TEXT("Ability blueprint missing"));return false;}
 auto* Component=NewObject<UActorComponent>(Pawn,Class);Pawn->AddInstanceComponent(Component);
 auto* S=W->GetSubsystem<UAbilityAcquisitionSubsystem>();if(!S){W->DestroyWorld(false);AddError(TEXT("Subsystem missing"));return false;}
 const FName Flags[]={TEXT("IsJumpUnlocked"),TEXT("IsCombatUnlocked"),TEXT("IsTransformUnlocked")};for(auto Name:Flags)FindFProperty<FBoolProperty>(Class,Name)->SetPropertyValue_InContainer(Component,false);
 auto* Function=Component->FindFunction(TEXT("Unlock Ability"));if(!Function){W->DestroyWorld(false);AddError(TEXT("Unlock function missing"));return false;}
 auto Unlock=[&](int32 Slot,bool Value){FStructOnScope Params(Function);auto* Enum=FindFProperty<FByteProperty>(Function,TEXT("Ability Type"));auto* Flag=FindFProperty<FBoolProperty>(Function,TEXT("Unlock"));check(Enum&&Flag);const TCHAR* Internal[]={TEXT("NewEnumerator0"),TEXT("NewEnumerator1"),TEXT("NewEnumerator2")};Enum->SetPropertyValue_InContainer(Params.GetStructMemory(),uint8(Enum->Enum->GetValueByNameString(Internal[Slot])));Flag->SetPropertyValue_InContainer(Params.GetStructMemory(),Value);Component->ProcessEvent(Function,Params.GetStructMemory());};
 Unlock(2,true);TestEqual(TEXT("Actual Transform grant enqueues"),S->PendingCount(),1);TestTrue(TEXT("Grant remains intact"),FindFProperty<FBoolProperty>(Class,Flags[2])->GetPropertyValue_InContainer(Component));
 Unlock(2,true);TestEqual(TEXT("Duplicate grant suppressed"),S->PendingCount(),1);
 Unlock(0,false);TestEqual(TEXT("Relock ignored"),S->PendingCount(),1);
 Unlock(0,true);Unlock(1,true);TestEqual(TEXT("All three real graph hooks"),S->PendingCount(),3);
 W->DestroyWorld(false);return true;
}
