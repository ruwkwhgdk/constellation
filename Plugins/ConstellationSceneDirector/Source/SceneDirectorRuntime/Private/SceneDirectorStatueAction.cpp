#include "SceneDirectorStatueAction.h"
#include "SceneDirectorPlayer.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "UObject/StructOnScope.h"
bool USceneDirectorStatueRestoreAction::Execute_Implementation(ASceneDirectorPlayer* Player,AActor*,const FDirectorActionParameters&,FString& Error)
{
 auto* Hero=UGameplayStatics::GetPlayerCharacter(Player,0);if(!Hero){Error=TEXT("회복할 플레이어가 없습니다.");return false;}
 UObject* Stats=nullptr;
 if(auto* Get=Hero->FindFunction(TEXT("Get Ac Stats")))
 {
  FStructOnScope Params(Get);Hero->ProcessEvent(Get,Params.GetStructMemory());
  for(TFieldIterator<FObjectPropertyBase> It(Get);It;++It)if(It->HasAnyPropertyFlags(CPF_OutParm|CPF_ReturnParm)){Stats=It->GetObjectPropertyValue_InContainer(Params.GetStructMemory());if(Stats)break;}
 }
 if(!Stats)if(auto* P=FindFProperty<FObjectPropertyBase>(Hero->GetClass(),TEXT("Ac_Stats")))Stats=P->GetObjectPropertyValue_InContainer(Hero);
 auto* Restore=Stats?Stats->FindFunction(TEXT("Restore HP Full")):nullptr;
 if(!Restore){Error=TEXT("플레이어의 기존 Ac_Stats / Restore HP Full 함수를 찾지 못했습니다.");return false;}
 FStructOnScope Params(Restore);Stats->ProcessEvent(Restore,Params.GetStructMemory());return true;
}
