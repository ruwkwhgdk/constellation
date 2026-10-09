// Development-only standalone review. Does not alter abilities, maps, or save data.
#include "AbilityAcquisitionSubsystem.h"
#include "HAL/IConsoleManager.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Kismet/GameplayStatics.h"
#include "Containers/Ticker.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "UnrealClient.h"
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs AbilityUIPreview(TEXT("AbilityUI.Preview"),TEXT("AbilityUI.Preview Slot PreviousMask (0/1/2; mask bits alpha/beta/gamma)"),FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A,UWorld* W){if(W)if(auto* S=W->GetSubsystem<UAbilityAcquisitionSubsystem>())S->Preview(A.Num()?FCString::Atoi(*A[0]):0,A.Num()>1?FCString::Atoi(*A[1]):0);}));
static bool AbilityReviewHeldInputCleared=false;
static double AbilityReviewStart=0;static int32 AbilityReviewStage=0;
static FTSTicker::FDelegateHandle AbilityReviewTicker=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
{
 if(!FParse::Param(FCommandLine::Get(),TEXT("AbilityUIReview")))return false;
 if(!GEngine)return true;UWorld* W=nullptr;for(const auto& C:GEngine->GetWorldContexts())if(C.WorldType==EWorldType::Game)W=C.World();
 if(!W||!W->GetFirstPlayerController())return true;auto* S=W->GetSubsystem<UAbilityAcquisitionSubsystem>();if(!S)return true;
 const double Now=FPlatformTime::Seconds();if(AbilityReviewStage==0){int32 Slot=2;FParse::Value(FCommandLine::Get(),TEXT("AbilityUISlot="),Slot);UPlayerInput* ReviewInput=W->GetFirstPlayerController()->PlayerInput;if(ReviewInput){ReviewInput->InputKey(FInputKeyParams(EKeys::W,IE_Pressed,1.0));if(auto* Key=ReviewInput->GetKeyState(EKeys::W))Key->bDown=true;}S->Preview(Slot,(1<<FMath::Clamp(Slot,0,2))-1);AbilityReviewStart=Now;AbilityReviewStage=1;}
 else if(AbilityReviewStage==1&&Now-AbilityReviewStart>7.5&&S->IsPresenting()){AbilityReviewHeldInputCleared=W->GetFirstPlayerController()->PlayerInput&&!W->GetFirstPlayerController()->PlayerInput->IsPressed(EKeys::W);FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("AbilityAcquisition/Unreal-review.png"),true,false);AbilityReviewStage=2;}
 else if(AbilityReviewStage==2&&Now-AbilityReviewStart>9){S->Dismiss(false);AbilityReviewStage=3;}
 else if(AbilityReviewStage==3&&Now-AbilityReviewStart>10){auto* PC=W->GetFirstPlayerController();const bool OK=AbilityReviewHeldInputCleared&&!S->IsPresenting()&&!UGameplayStatics::IsGamePaused(W)&&!PC->IsMoveInputIgnored()&&!PC->IsLookInputIgnored();FFileHelper::SaveStringToFile(OK?TEXT("PASS: presented, screenshot, dismissed, pause and input restored, held movement cleared"):TEXT("FAIL: UI restoration"),*(FPaths::ProjectSavedDir()/TEXT("AbilityAcquisition/standalone-result.txt")));FPlatformMisc::RequestExit(false);return false;}
 if(Now-AbilityReviewStart>40){FFileHelper::SaveStringToFile(TEXT("FAIL: presentation timeout"),*(FPaths::ProjectSavedDir()/TEXT("AbilityAcquisition/standalone-result.txt")));FPlatformMisc::RequestExit(false);return false;}return true;
}),.1f);
#endif
