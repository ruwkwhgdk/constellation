#include "DialogueStyleEditorLibrary.h"
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/Button.h"
#include "Components/RichTextBlock.h"
#include "Engine/Texture2D.h"
#include "Engine/DataTable.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Styling/CoreStyle.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
bool UDialogueStyleEditorLibrary::ApplyQuietNebula(UBlueprint* Blueprint,UTexture2D* Atlas,FString& Error)
{
 auto* BP=Cast<UWidgetBlueprint>(Blueprint);if(!BP||!BP->WidgetTree||!Atlas){Error=TEXT("Missing widget blueprint or atlas");return false;}
 UWidgetTree* Tree=BP->WidgetTree;auto* Root=Cast<UCanvasPanel>(Tree->RootWidget);
 auto* Background=Cast<UImage>(Tree->FindWidget(TEXT("Background")));auto* Name=Cast<URichTextBlock>(Tree->FindWidget(TEXT("Name")));auto* Body=Cast<URichTextBlock>(Tree->FindWidget(TEXT("Description")));auto* Next=Cast<UButton>(Tree->FindWidget(TEXT("NextButton")));
 if(!Root||!Background||!Name||!Body||!Next){Error=TEXT("Legacy dialogue schema mismatch; no changes made");return false;}
 UFont* Font=LoadObject<UFont>(nullptr,TEXT("/Engine/EngineFonts/Roboto.Roboto"));if(!Font){Error=TEXT("Engine composite font missing");return false;}
 BP->Modify();Tree->Modify();
 auto Brush=[Atlas](FVector2f Min,FVector2f Max,FVector2D Size){FSlateBrush B;B.SetResourceObject(Atlas);B.DrawAs=ESlateBrushDrawType::Image;B.ImageSize=FVector2f(Size);B.SetUVRegion(FBox2f(Min/FVector2f(1536,1024),Max/FVector2f(1536,1024)));return B;};
 auto Place=[Root](UWidget* W,FVector2D Pos,FVector2D Size,int32 Z){W->Modify();W->SetRenderTransform(FWidgetTransform());if(W->GetParent()!=Root){W->RemoveFromParent();Root->AddChildToCanvas(W);}auto* S=CastChecked<UCanvasPanelSlot>(W->Slot);S->SetAnchors(FAnchors(.5f,1.f));S->SetAlignment(FVector2D(0,1));S->SetPosition(Pos);S->SetSize(Size);S->SetAutoSize(false);S->SetZOrder(Z);};
 Background->SetBrush(Brush({32,185},{1504,504},{910,184}));Place(Background,{-455,-48},{910,184},0);Background->SetVisibility(ESlateVisibility::HitTestInvisible);
 auto EnsureImage=[Tree](FName N){auto* I=Cast<UImage>(Tree->FindWidget(N));if(!I)I=Tree->ConstructWidget<UImage>(UImage::StaticClass(),N);I->SetVisibility(ESlateVisibility::HitTestInvisible);return I;};
 auto* Plate=EnsureImage(TEXT("QuietNebulaNameplate"));Plate->SetBrush(Brush({35,562},{552,675},{182,36}));Place(Plate,{-351,-214},{182,36},1);
 Place(Name,{-341,-220},{162,26},2);Name->SetJustification(ETextJustify::Center);Name->SetMargin(FMargin(0));Name->SetMinDesiredWidth(0);Name->SetVisibility(ESlateVisibility::HitTestInvisible);
 Place(Body,{-339,-90},{689,80},2);Body->SetAutoWrapText(true);Body->SetMargin(FMargin(0));Body->SetMinDesiredWidth(0);Body->SetVisibility(ESlateVisibility::HitTestInvisible);
 // Private style table keeps other rich-text tags intact without altering shared UI styles.
 UDataTable* TextTable=FindObject<UDataTable>(BP,TEXT("QuietNebulaTextStyles"));
 if(!TextTable){TextTable=Body->GetTextStyleSet()?DuplicateObject<UDataTable>(Body->GetTextStyleSet(),BP,TEXT("QuietNebulaTextStyles")):NewObject<UDataTable>(BP,TEXT("QuietNebulaTextStyles"));TextTable->RowStruct=FRichTextStyleRow::StaticStruct();}
 FRichTextStyleRow TextRow;TextRow.TextStyle=FTextBlockStyle().SetFont(FSlateFontInfo(Font,18,FName("Regular"))).SetColorAndOpacity(FLinearColor(.88f,.85f,.76f));TextTable->AddRow(TEXT("Default"),TextRow);
 Body->SetTextStyleSet(TextTable);Body->SetDefaultTextStyle(TextRow.TextStyle);
 TextRow.TextStyle.SetFont(FSlateFontInfo(Font,14,FName("Regular")));TextTable->AddRow(TEXT("Name"),TextRow);Name->SetTextStyleSet(TextTable);Name->SetDefaultTextStyle(TextRow.TextStyle);
 auto* Arrow=EnsureImage(TEXT("QuietNebulaContinue"));Arrow->SetBrush(Brush({648,682},{888,934},{76,80}));Place(Arrow,{-38,-4},{76,80},2);
 FButtonStyle Style=Next->GetStyle();for(FSlateBrush* B:{&Style.Normal,&Style.Hovered,&Style.Pressed,&Style.Disabled})B->DrawAs=ESlateBrushDrawType::NoDrawType;Next->SetStyle(Style);Place(Next,{-455,-48},{910,184},3);
 Tree->ForEachWidget([BP](UWidget* W){if(!BP->WidgetVariableNameToGuidMap.Contains(W->GetFName()))BP->WidgetVariableNameToGuidMap.Add(W->GetFName(),FGuid::NewGuid());});
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error){Error=TEXT("Compile failed; do not save");return false;}Error.Reset();return true;
}



#include "StardustChoiceWidget.h"
bool UDialogueStyleEditorLibrary::ApplyStardustChoices(UBlueprint* Blueprint,FString& Error)
{
 auto* BP=Cast<UWidgetBlueprint>(Blueprint);
 if(!BP||!BP->WidgetTree||(BP->ParentClass!=UUserWidget::StaticClass()&&BP->ParentClass!=UStardustChoiceWidget::StaticClass())){Error=TEXT("Unexpected choice parent");return false;}
 for(const TCHAR* Name:{TEXT("Choice_Button_A"),TEXT("Choice_Button_B"),TEXT("Choice_Button_C")})if(!Cast<UButton>(BP->WidgetTree->FindWidget(Name))){Error=TEXT("Missing choice button");return false;}
 BP->Modify();BP->ParentClass=UStardustChoiceWidget::StaticClass();
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
 if(BP->Status==BS_Error){Error=TEXT("Choice compile failed; do not save");return false;}Error.Reset();return true;
}

UUserWidget* UDialogueStyleEditorLibrary::CreateChoiceReview(UWorld* World)
{
 if(!World||!World->IsGameWorld())return nullptr;
 UClass* Class=LoadClass<UUserWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_Choice.WBP_Choice_C"));
 return Class?CreateWidget<UUserWidget>(World,Class):nullptr;
}
