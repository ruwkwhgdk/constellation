#pragma once
#include "CoreMinimal.h"
#include "Toolkits/AssetEditorToolkit.h"
#include "EditorUndoClient.h"
#include "UObject/GCObject.h"
#include "SceneDirectorAsset.h"
class USceneDirectorGraph;
class SGraphEditor;
class IDetailsView;
class ISequencer;
class SBox;
class SScrollBox;
class FUICommandList;
class SDirectorViewport;
struct FActionMenuContent;
class UEdGraphPin;
class FSceneDirectorToolkit : public FAssetEditorToolkit, public FEditorUndoClient, public FGCObject
{
public:
    virtual ~FSceneDirectorToolkit();
    FReply BuildPreview();
    void Init(USceneDirectorAsset* InAsset, const TSharedPtr<IToolkitHost>& Host);
    virtual FName GetToolkitFName() const override {return TEXT("SceneDirector");}
    virtual FText GetBaseToolkitName() const override {return FText::FromString(TEXT("Scene Director"));}
    virtual FString GetWorldCentricTabPrefix() const override {return TEXT("Scene Director");}
    virtual FLinearColor GetWorldCentricTabColorScale() const override {return FLinearColor(.1f,.5f,.7f);}
    virtual void RegisterTabSpawners(const TSharedRef<FTabManager>& Manager) override;
    virtual void UnregisterTabSpawners(const TSharedRef<FTabManager>& Manager) override;
    virtual void AddReferencedObjects(FReferenceCollector& Collector) override;
    virtual FString GetReferencerName() const override {return TEXT("SceneDirectorToolkit");}
    virtual void PostUndo(bool bSuccess) override;
    virtual void PostRedo(bool bSuccess) override {PostUndo(bSuccess);}
    virtual void SaveAsset_Execute() override;
private:
    friend class FDirectorDeleteKeyTest;
    friend class FDirectorPreviewVisibilityTest;
    friend class FDirectorPreviewReturnTest;
    friend class FDirectorEditorCapture;
    friend class FDirectorEditorSmokeTest;
    friend class FDirectorEventGraphsTest;
    friend class FDirectorContextMenuTest;
    TObjectPtr<USceneDirectorAsset> RootAsset=nullptr;
    TObjectPtr<USceneDirectorAsset> Asset=nullptr;
    TObjectPtr<USceneDirectorGraph> Graph=nullptr;
    TSharedPtr<FUICommandList> GraphCommands;
    TSharedPtr<SGraphEditor> GraphEditor;
    TSharedPtr<IDetailsView> Details, ConditionDetails,IntDetails, ObjectDetails,OriginDetails,CameraDetails, VectorDetails, BoolDetails, ActionDetails;
    TSharedPtr<ISequencer> Sequencer;
    TSharedPtr<SBox> PreviewBox;
    TSharedPtr<SDirectorViewport> SceneViewport;
    TSharedPtr<SScrollBox> NPCList,CameraList,EventList;
    void RefreshEventList();
    void SelectEvent(USceneDirectorAsset* Event);
    FReply AddEvent();
    FReply ImportSelectedSequence();
    FReply PreviewOriginal();
    void OpenPreview(ULevelSequence* Sequence,USceneDirectorAsset* PreviewAsset,double Seconds);
    double PreviewElapsed() const;
    TObjectPtr<ULevelSequence> ComparisonSequence=nullptr;
    bool RenameEvent(FName Key);
    FActionMenuContent CreateNodeMenu(const FVector2f& Location,const TArray<UEdGraphPin*>& Pins);
    void RegistryChanged(const FPropertyChangedEvent& Event);
    void RefreshNPCList();
    FString Status=TEXT("중앙 그래프 빈 공간에서 우클릭 → 대분류 → 노드 종류를 선택하세요.");
    TSharedRef<SDockTab> SpawnTab(const FSpawnTabArgs& Args);
    FReply AddNode(EDirectorNodeType Type,const FVector2f& Location,UEdGraphPin* FromPin=nullptr);
    FReply DeleteNodes();
    FReply CapturePosition();

    FReply StopPreview();
    void ClosePreview();
    void OnMapChanged(uint32 Flags);
    void OnBeginPIE(bool bSimulating);
    FReply PlacePlayer();
};
