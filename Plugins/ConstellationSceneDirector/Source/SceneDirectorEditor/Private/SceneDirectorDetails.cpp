#include "SceneDirectorDetails.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorGraph.h"
#include "SceneDirectorNodeTypes.h"
#include "GameFramework/Pawn.h"
#include "Camera/CameraActor.h"
#include "Animation/SkeletalMeshActor.h"
#include "IPropertyTypeCustomization.h"
#include "IDetailCustomization.h"
#include "DetailLayoutBuilder.h"
#include "DetailCategoryBuilder.h"
#include "PropertyHandle.h"
#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "IDetailPropertyRow.h"
#include "PropertyEditorModule.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Widgets/Input/SComboButton.h"
#include "Widgets/Text/STextBlock.h"

bool DirectorAuthoring::IsCharacterEntry(const FDirectorStep& S)
{return DirectorNodes::IsNPC(S.Type)&&(S.Type==EDirectorNodeType::SpawnNPC||!S.ActorClass||S.ActorClass->IsChildOf(APawn::StaticClass())||S.ActorClass->IsChildOf(ASkeletalMeshActor::StaticClass()));}
TArray<FName> DirectorAuthoring::ReferenceKeys(const USceneDirectorAsset& A,FName Kind)
{
    TArray<FName> Keys;
    if(Kind==TEXT("NPC")||Kind==TEXT("Actor"))for(const auto& S:A.Steps)
        if(DirectorNodes::IsNPC(S.Type)&&(Kind==TEXT("Actor")||IsCharacterEntry(S)))Keys.AddUnique(S.Role);
    if(Kind==TEXT("Camera"))for(const auto& E:A.Cameras)Keys.AddUnique(E.Key);
    if(Kind==TEXT("Object")||Kind==TEXT("CameraObject"))for(const auto& E:A.Objects)
        if(Kind==TEXT("Object")||(E.ActorClass&&E.ActorClass->IsChildOf(ACameraActor::StaticClass())))Keys.AddUnique(E.Key);
    if(Kind==TEXT("Vector"))for(const auto& E:A.Vectors)Keys.AddUnique(E.Key);
    if(Kind==TEXT("Action"))for(const auto& E:A.Actions)Keys.AddUnique(E.Key);
    auto* Root=const_cast<USceneDirectorAsset&>(A).VariableOwner();
    if(Kind==TEXT("Bool"))for(const auto& E:Root->BoolVariables)Keys.AddUnique(E.Key);
    if(Kind==TEXT("Int"))for(const auto& E:Root->IntVariables)Keys.AddUnique(E.Key);
    Keys.Remove(NAME_None);Keys.Sort(FNameLexicalLess());return Keys;
}
namespace
{
USceneDirectorAsset* GetAsset(const TSharedRef<IPropertyHandle>& H)
{
    TArray<UObject*> Owners;H->GetOuterObjects(Owners);if(Owners.Num()!=1)return nullptr;
    if(auto* N=Cast<USceneDirectorGraphNode>(Owners[0]))if(auto* G=Cast<USceneDirectorGraph>(N->GetGraph()))return G->Asset;
    return Cast<USceneDirectorAsset>(Owners[0]);
}
FName ReferenceKind(const TSharedRef<IPropertyHandle>& Struct,const TSharedRef<IPropertyHandle>& Field)
{
    const FName Name=Field->GetProperty()->GetFName();const auto* P=CastField<FStructProperty>(Struct->GetProperty());if(!P)return NAME_None;
    const auto StructName=P->Struct->GetFName();
    if(StructName==TEXT("DirectorStep"))
    {
        uint8 Type=0;Struct->GetChildHandle(TEXT("Type"))->GetValue(Type);
        if(Name==TEXT("Role")&&!DirectorNodes::IsNPC(EDirectorNodeType(Type)))return TEXT("NPC");
        if(Name==TEXT("TargetRole"))return TEXT("NPC");
        if(Name==TEXT("ActionTarget"))return TEXT("Actor");
        if(Name==TEXT("CameraKey"))return TEXT("Camera");
        if(Name==TEXT("ActionKey"))return TEXT("Action");
        if(Name==TEXT("ObjectKey"))return TEXT("Object");
        if(Name==TEXT("BoolKey"))return TEXT("Bool");
        if(Name==TEXT("IntKey"))return TEXT("Int");
    }
    if(StructName==TEXT("DirectorVectorInput")&&Name==TEXT("Key"))return TEXT("Vector");
    if(StructName==TEXT("DirectorCameraEntry")&&Name==TEXT("ObjectKey"))return TEXT("CameraObject");
    if(StructName==TEXT("DirectorSequenceRole")&&Name==TEXT("Key"))
    {uint8 Type=0;Struct->GetChildHandle(TEXT("Target"))->GetValue(Type);return EDirectorSequenceTarget(Type)==EDirectorSequenceTarget::Camera?TEXT("Camera"):TEXT("Actor");}
    if(StructName==TEXT("DirectorEventCondition")&&Name==TEXT("Key"))
    {uint8 Type=0;Struct->GetChildHandle(TEXT("Type"))->GetValue(Type);return EDirectorVariableType(Type)==EDirectorVariableType::Integer?TEXT("Int"):TEXT("Bool");}
    return NAME_None;
}
void CustomizeReferenceRow(IDetailPropertyRow& Row,TSharedRef<IPropertyHandle> H,TSharedRef<IPropertyHandle> Field)
{
            Row.CustomWidget().NameContent()[Field->CreatePropertyNameWidget()].ValueContent().MinDesiredWidth(200)
            [SNew(SComboButton).OnGetMenuContent_Lambda([H,Field]
            {
                FMenuBuilder Menu(true,nullptr);auto* Asset=GetAsset(H);
                Menu.AddMenuEntry(FText::FromString(TEXT("선택 없음")),FText(),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([Field]{Field->SetValue(NAME_None);} )));
                if(Asset)for(FName Key:DirectorAuthoring::ReferenceKeys(*Asset,ReferenceKind(H,Field)))
                    Menu.AddMenuEntry(FText::FromName(Key),FText(),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([Field,Key]{Field->SetValue(Key);} )));
                return Menu.MakeWidget();
            }).ButtonContent()[SNew(STextBlock).Text_Lambda([H,Field]
            {
                FName Key;Field->GetValue(Key);if(Key.IsNone())return FText::FromString(TEXT("선택 없음"));
                auto* A=GetAsset(H);const bool Valid=A&&DirectorAuthoring::ReferenceKeys(*A,ReferenceKind(H,Field)).Contains(Key);
                return FText::FromString((Valid?FString():TEXT("[등록 없음] "))+Key.ToString());
            })]];
}
class FDirectorReferenceDetails : public IPropertyTypeCustomization
{
public:
    static TSharedRef<IPropertyTypeCustomization> Make(){return MakeShared<FDirectorReferenceDetails>();}
    virtual void CustomizeHeader(TSharedRef<IPropertyHandle> H,FDetailWidgetRow& Row,IPropertyTypeCustomizationUtils&)override
    {Row.NameContent()[H->CreatePropertyNameWidget()].ValueContent()[H->CreatePropertyValueWidget()];}
    virtual void CustomizeChildren(TSharedRef<IPropertyHandle> H,IDetailChildrenBuilder& B,IPropertyTypeCustomizationUtils&)override
    {
        uint32 Count=0;H->GetNumChildren(Count);
        for(uint32 I=0;I<Count;++I)
        {
            auto Field=H->GetChildHandle(I).ToSharedRef();auto& Row=B.AddProperty(Field);
            if(ReferenceKind(H,Field).IsNone())continue;
            CustomizeReferenceRow(Row,H,Field);
        }
    }
};
class FDirectorNodeDetails : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> Make(){return MakeShared<FDirectorNodeDetails>();}
    virtual void CustomizeDetails(IDetailLayoutBuilder& Builder)override
    {
        auto Step=Builder.GetProperty(GET_MEMBER_NAME_CHECKED(USceneDirectorGraphNode,Step));Builder.HideProperty(Step);
        uint32 Count=0;Step->GetNumChildren(Count);
        for(uint32 I=0;I<Count;++I)
        {
            auto Field=Step->GetChildHandle(I).ToSharedRef();
            if(!Field->GetProperty()->HasAnyPropertyFlags(CPF_Edit))continue;
            auto& Row=Builder.EditCategory(FName(*Field->GetProperty()->GetMetaData(TEXT("Category")))).AddProperty(Field);
            if(!ReferenceKind(Step,Field).IsNone())CustomizeReferenceRow(Row,Step,Field);
        }
    }
};
const FName Types[]={TEXT("DirectorVectorInput"),TEXT("DirectorCameraEntry"),TEXT("DirectorSequenceRole"),TEXT("DirectorEventCondition")};
}
void DirectorAuthoring::RegisterDetails()
{
    auto& Module=FModuleManager::LoadModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor"));
    Module.RegisterCustomClassLayout(TEXT("SceneDirectorGraphNode"),FOnGetDetailCustomizationInstance::CreateStatic(&FDirectorNodeDetails::Make));
    for(FName Type:Types)Module.RegisterCustomPropertyTypeLayout(Type,FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FDirectorReferenceDetails::Make));
    Module.NotifyCustomizationModuleChanged();
}
void DirectorAuthoring::UnregisterDetails()
{
    if(auto* M=FModuleManager::GetModulePtr<FPropertyEditorModule>(TEXT("PropertyEditor"))){M->UnregisterCustomClassLayout(TEXT("SceneDirectorGraphNode"));for(FName Type:Types)M->UnregisterCustomPropertyTypeLayout(Type);}
}
