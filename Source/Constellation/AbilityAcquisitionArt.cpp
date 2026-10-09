#include "AbilityAcquisitionArt.h"
#include "Engine/DataTable.h"
#include "Engine/Texture2D.h"
#include "UObject/UnrealType.h"
bool UAbilityAcquisitionArt::IsReady()const
{
 auto Valid=[](const auto& A,int32 N){if(A.Num()!=N)return false;for(const auto& T:A)if(!T)return false;return true;};
 return Background&&Emblem&&Descriptions&&Valid(Dormant,7)&&Valid(Stars,7)&&Valid(NewStars,7)&&Valid(Lines,6)&&Valid(LitLines,6);
}
FText UAbilityAcquisitionArt::Description(int32 Slot)const
{
 static const FName Rows[]={TEXT("AbandonedSchool_Star_Object_Jump"),TEXT("AbandonedSchool_Star_Object_Combat"),TEXT("AbandonedSchool_Star_Object_Metamorphosis")};
 if(!Descriptions||Slot<0||Slot>2)return FText::GetEmpty();
 const uint8* Row=Descriptions->FindRowUnchecked(Rows[Slot]);if(!Row)return FText::GetEmpty();
 for(TFieldIterator<FTextProperty> It(Descriptions->GetRowStruct());It;++It)if(It->GetName().StartsWith(TEXT("Description_")))return It->GetPropertyValue_InContainer(Row);
 return FText::GetEmpty();
}
