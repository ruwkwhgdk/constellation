#include "RegionTitleEditorLibrary.h"
#include "RegionTitleWidget.h"
#include "Misc/FileHelper.h"
#include "WidgetBlueprint.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Engine/World.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "K2Node_CallFunction.h"
#include "EdGraphSchema_K2.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
UFont* URegionTitleEditorLibrary::CreateRegionFont(const FString& FontFilename)
{
 TArray<uint8> Bytes;if(!FFileHelper::LoadFileToArray(Bytes,*FontFilename))return nullptr;
 auto* FacePackage=CreatePackage(TEXT("/Game/Constellation/UI/RegionTitle/FF_RegionMyeongjo"));
 auto* Face=FindObject<UFontFace>(FacePackage,TEXT("FF_RegionMyeongjo"));
 if(!Face){Face=NewObject<UFontFace>(FacePackage,TEXT("FF_RegionMyeongjo"),RF_Public|RF_Standalone);FAssetRegistryModule::AssetCreated(Face);}
 Face->SourceFilename=FontFilename;Face->LoadingPolicy=EFontLoadingPolicy::Inline;
 Face->FontFaceData=FFontFaceData::MakeFontFaceData(MoveTemp(Bytes));Face->CacheSubFaces();Face->MarkPackageDirty();
 auto* Package=CreatePackage(TEXT("/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo"));
 auto* Font=FindObject<UFont>(Package,TEXT("F_RegionMyeongjo"));
 if(!Font){Font=NewObject<UFont>(Package,TEXT("F_RegionMyeongjo"),RF_Public|RF_Standalone);FAssetRegistryModule::AssetCreated(Font);}
 Font->FontCacheType=EFontCacheType::Runtime;
 auto& Fonts=Font->GetMutableInternalCompositeFont().DefaultTypeface.Fonts;Fonts.Reset();
 FTypefaceEntry Entry(FName("Regular"));Entry.Font=FFontData(Face);Fonts.Add(Entry);Font->MarkPackageDirty();return Font;
}
bool URegionTitleEditorLibrary::ApplyRegionTitle(UBlueprint* Widget,UBlueprint* Trigger,FString& Error)
{
 auto* BP=Cast<UWidgetBlueprint>(Widget);
 if(!BP||BP->GetPathName()!=TEXT("/Game/Constellation/UI/Widgets/WBP_RegionTitle.WBP_RegionTitle")||!Trigger||Trigger->GetPathName()!=TEXT("/Game/Constellation/Gameplay/Interaction/Actors/BP_RegionTrigger.BP_RegionTrigger")){Error=TEXT("Unexpected assets");return false;}
 UK2Node_CallFunction* Play=nullptr;
 for(UEdGraph* Graph:Trigger->UbergraphPages)for(UEdGraphNode* Node:Graph->Nodes)
 if(Node->GetName()==TEXT("K2Node_CallFunction_4"))Play=Cast<UK2Node_CallFunction>(Node);
 if(!Play||Play->FunctionReference.GetMemberName()!=TEXT("PlayAnimation")){Error=TEXT("Unexpected trigger animation graph");return false;}
 BP->Modify();BP->ParentClass=URegionTitleWidget::StaticClass();FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error){Error=TEXT("Widget compile failed");return false;}
 // Keep overlap/DoOnce/string data behavior. Stop only the old display lifecycle after assigning RegionWidget.
 Trigger->Modify();Play->Modify();Play->FindPinChecked(UEdGraphSchema_K2::PN_Execute)->BreakAllPinLinks();
 Play->NodeComment=TEXT("RegionTitleWidget now owns the complete fade and removal lifecycle.");
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Trigger);FKismetEditorUtilities::CompileBlueprint(Trigger);
 if(Trigger->Status==BS_Error){Error=TEXT("Trigger compile failed");return false;}Error.Reset();return true;
}
URegionTitleWidget* URegionTitleEditorLibrary::CreateRegionReview(UWorld* World,FText Title,FText Subtitle)
{
 if(!World||!World->IsGameWorld())return nullptr;
 auto* Class=LoadClass<URegionTitleWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_RegionTitle.WBP_RegionTitle_C"));
 auto* Widget=Class?CreateWidget<URegionTitleWidget>(World->GetFirstPlayerController(),Class):nullptr;
 if(Widget){Widget->SetRegionText(Title,Subtitle);Widget->AddToViewport(10);}return Widget;
}
