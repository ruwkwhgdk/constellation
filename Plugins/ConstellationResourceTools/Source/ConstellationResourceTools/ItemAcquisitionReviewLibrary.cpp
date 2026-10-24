#include "ItemAcquisitionReviewLibrary.h"
#include "ItemAcquisitionSubsystem.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
namespace { TArray<FString> Results; }
FGuid UItemAcquisitionReviewLibrary::ShowReviewCard(UObject* Context,UTexture2D* Sprite,const FText& Name,const FText& Description,int32 Quantity)
{
 if(!Context||!Context->GetWorld())return FGuid();
 auto* S=Context->GetWorld()->GetSubsystem<UItemAcquisitionSubsystem>();if(!S)return FGuid();
 FItemAcquisitionPresentation P;P.Sprite=Sprite;P.Name=Name;P.Description=Description;P.Quantity=Quantity;
 const FString Label=Name.ToString();
 return S->Enqueue(P,FKey(),nullptr,[Label](bool Complete){Results.Add(Label+(Complete?TEXT(":confirmed"):TEXT(":cancelled")));});
}
bool UItemAcquisitionReviewLibrary::SendReviewKey(FKey Key,bool Down)
{
 if(!FSlateApplication::IsInitialized())return false;
 FKeyEvent Event(Key,FModifierKeysState(),0,false,0,0);
 return Down?FSlateApplication::Get().ProcessKeyDownEvent(Event):FSlateApplication::Get().ProcessKeyUpEvent(Event);
}
FString UItemAcquisitionReviewLibrary::ReviewResults(){return FString::Join(Results,TEXT("\n"));}
