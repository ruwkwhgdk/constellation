#pragma once
#include "CoreMinimal.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphSchema.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorGraph.generated.h"

UCLASS()
class USceneDirectorGraph : public UEdGraph
{
    GENERATED_BODY()
public:
    UPROPERTY() TObjectPtr<USceneDirectorAsset> Asset;
    bool bLoading = false;
    FSimpleMulticastDelegate OnChanged;
    void Load();
    void Sync();
};
UCLASS()
class USceneDirectorGraphNode : public UEdGraphNode
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="노드", meta=(ShowOnlyInnerProperties)) FDirectorStep Step;
    virtual TSharedPtr<SGraphNode> CreateVisualWidget() override;
    virtual void AllocateDefaultPins() override;
    virtual FText GetNodeTitle(ENodeTitleType::Type Type) const override;
    virtual FLinearColor GetNodeTitleColor() const override;
    virtual void NodeConnectionListChanged() override;
    static FName ChoicePinName(FName Key);
    bool HasChoiceOutputs() const;
    void RebuildBranchPins(const FDirectorStep& Before);
    UFUNCTION() TArray<FString> GetActionKeys() const;
    FDirectorStep PreviousStep;
    FName PreviousRole;
    virtual void PreEditChange(FProperty* Property) override;
    virtual void PostEditUndo() override;
    virtual void PostEditChangeProperty(FPropertyChangedEvent& Event) override;
};
UCLASS()
class USceneDirectorSchema : public UEdGraphSchema
{
    GENERATED_BODY()
public:
    virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A,const UEdGraphPin* B) const override;
    virtual FLinearColor GetPinTypeColor(const FEdGraphPinType&) const override {return FLinearColor::White;}
};
