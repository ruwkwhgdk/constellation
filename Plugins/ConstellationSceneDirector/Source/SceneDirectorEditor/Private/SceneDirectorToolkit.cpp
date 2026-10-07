#include "SceneDirectorToolkit.h"
#include "SceneDirectorDetails.h"
#include "GameFramework/Pawn.h"
#include "SceneEventEditor.h"
#include "SceneDirectorImporter.h"
#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "AssetRegistry/AssetData.h"
#include "SceneDirectorNodeTypes.h"
#include "SceneDirectorViewport.h"
#include "SceneDirectorNodeMenu.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "EdGraph/EdGraphPin.h"
#include "Framework/Commands/GenericCommands.h"
#include "Framework/Commands/UICommandList.h"
#include "SceneDirectorGraph.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "GraphEditor.h"
#include "PropertyEditorModule.h"
#include "IDetailsView.h"
#include "PropertyEditorDelegates.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SExpandableArea.h"
#include "Editor.h"
#include "Engine/Selection.h"
#include "LevelEditorViewport.h"
#include "ScopedTransaction.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SSplitter.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "ISequencerModule.h"
#include "ISequencer.h"
#include "Misc/LevelSequenceEditorSpawnRegister.h"
#include "LevelEditorSequencerIntegration.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "Engine/World.h"

static const FName DirectorTab(TEXT("SceneDirector.Main"));
FSceneDirectorToolkit::~FSceneDirectorToolkit(){ClosePreview();if(GEditor)GEditor->UnregisterForUndo(this);FEditorDelegates::MapChange.RemoveAll(this);FEditorDelegates::BeginPIE.RemoveAll(this);}
void FSceneDirectorToolkit::Init(USceneDirectorAsset* InAsset,const TSharedPtr<IToolkitHost>& Host)
{
    RootAsset=InAsset;RootAsset->UpgradeControlNodes();Asset=InAsset; Asset->SetFlags(RF_Transactional);
    Graph=NewObject<USceneDirectorGraph>(GetTransientPackage(),NAME_None,RF_Transactional);
    Graph->OnChanged.AddRaw(this,&FSceneDirectorToolkit::ClosePreview);
    Graph->OnChanged.AddRaw(this,&FSceneDirectorToolkit::RefreshNPCList);
    FEditorDelegates::BeginPIE.AddRaw(this,&FSceneDirectorToolkit::OnBeginPIE);
    Graph->Schema=USceneDirectorSchema::StaticClass(); Graph->Asset=Asset; Graph->Load();
    GEditor->RegisterForUndo(this); FEditorDelegates::MapChange.AddRaw(this,&FSceneDirectorToolkit::OnMapChanged);
    auto Layout=FTabManager::NewLayout("SceneDirector.Layout.v1")->AddArea(FTabManager::NewPrimaryArea()->SetOrientation(Orient_Vertical)->Split(FTabManager::NewStack()->AddTab(DirectorTab,ETabState::OpenedTab)->SetHideTabWell(true)));
    InitAssetEditor(EToolkitMode::Standalone,Host,TEXT("SceneDirector"),Layout,true,true,Asset);
}
void FSceneDirectorToolkit::RegisterTabSpawners(const TSharedRef<FTabManager>& Manager)
{
    FAssetEditorToolkit::RegisterTabSpawners(Manager);
    Manager->RegisterTabSpawner(DirectorTab,FOnSpawnTab::CreateSP(this,&FSceneDirectorToolkit::SpawnTab)).SetDisplayName(FText::FromString(TEXT("연출 그래프")));
}
void FSceneDirectorToolkit::UnregisterTabSpawners(const TSharedRef<FTabManager>& Manager){Manager->UnregisterTabSpawner(DirectorTab);FAssetEditorToolkit::UnregisterTabSpawners(Manager);}
void FSceneDirectorToolkit::AddReferencedObjects(FReferenceCollector& Collector){Collector.AddReferencedObject(RootAsset);Collector.AddReferencedObject(Asset);Collector.AddReferencedObject(Graph);Collector.AddReferencedObject(ComparisonSequence);}
TSharedRef<SDockTab> FSceneDirectorToolkit::SpawnTab(const FSpawnTabArgs&)
{
    FDetailsViewArgs Args; Args.bHideSelectionTip=true;
    Details=FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor").CreateDetailView(Args);
    SGraphEditor::FGraphEditorEvents Events;
    Events.OnSelectionChanged=SGraphEditor::FOnSelectionChanged::CreateLambda([this](const TSet<UObject*>& Objects){TArray<UObject*> Selected;for(auto* O:Objects)Selected.Add(O);Details->SetObjects(Selected);});
    GraphCommands=MakeShared<FUICommandList>();
    GraphCommands->MapAction(FGenericCommands::Get().Delete,FExecuteAction::CreateLambda([this]{DeleteNodes();}));
    Events.OnCreateActionMenuAtLocation=SGraphEditor::FOnCreateActionMenuAtLocation::CreateLambda([this](UEdGraph*,const FVector2f& Location,const TArray<UEdGraphPin*>& Pins,bool,SGraphEditor::FActionMenuClosed OnClosed){auto Menu=CreateNodeMenu(Location,Pins);Menu.OnMenuDismissed.AddLambda([OnClosed]{OnClosed.ExecuteIfBound();});return Menu;});
    SAssignNew(GraphEditor,SGraphEditor).AdditionalCommands(GraphCommands).GraphToEdit(Graph).GraphEvents(Events).IsEditable(true);
    GraphEditor->ZoomToFit(false);
    if(Graph->Nodes.Num()>1)GraphEditor->SetNodeSelection(Graph->Nodes[1],true);
    auto Button=[](const TCHAR* Label,FOnClicked Click){return SNew(SButton).Text(FText::FromString(Label)).OnClicked(Click);};
        FDetailsViewArgs RegistryArgs;RegistryArgs.bHideSelectionTip=true;RegistryArgs.bAllowSearch=false;
    auto CreateRegistry=[&](FName Property)
    {
        auto View=FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor").CreateDetailView(RegistryArgs);
        View->SetIsPropertyVisibleDelegate(FIsPropertyVisible::CreateLambda([Property](const FPropertyAndParent& P)
        {if(Property==TEXT("AuthoringOrigin")&&P.Property.GetFName()==TEXT("bUseInteractionOrigin"))return true;if(P.Property.GetFName()==Property)return true;for(const FProperty* Parent:P.ParentProperties)if(Parent->GetFName()==Property)return true;return false;}));
        View->SetObject(Asset);View->OnFinishedChangingProperties().AddSP(this,&FSceneDirectorToolkit::RegistryChanged);return View;
    };
    RootAsset->RefreshVariableEntries();ConditionDetails=CreateRegistry(TEXT("EntryConditions"));
    ObjectDetails=CreateRegistry(TEXT("Objects"));OriginDetails=CreateRegistry(TEXT("AuthoringOrigin"));CameraDetails=CreateRegistry(TEXT("Cameras"));VectorDetails=CreateRegistry(TEXT("Vectors"));BoolDetails=CreateRegistry(TEXT("Variables"));ActionDetails=CreateRegistry(TEXT("Actions"));
    OriginDetails->SetObject(RootAsset);BoolDetails->SetObject(RootAsset);
    SAssignNew(NPCList,SScrollBox);SAssignNew(CameraList,SScrollBox);SAssignNew(EventList,SScrollBox);RefreshNPCList();RefreshEventList();
    return SNew(SDockTab).TabRole(ETabRole::PanelTab)
    [SNew(SVerticalBox)
        +SVerticalBox::Slot().AutoHeight().Padding(6)
        [SNew(SWrapBox).UseAllottedSize(true)
            +SWrapBox::Slot().Padding(2)[Button(TEXT("이벤트 배치"),FOnClicked::CreateLambda([]{OpenSceneEventTab();return FReply::Handled();}))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("선택 시퀀스 가져오기"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::ImportSelectedSequence))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("선택 삭제"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::DeleteNodes))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("뷰포트 위치 가져오기"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::CapturePosition))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("생성 및 미리보기"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::BuildPreview))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("원본 비교"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::PreviewOriginal))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("미리보기 종료"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::StopPreview))]
            +SWrapBox::Slot().Padding(2)[Button(TEXT("레벨에 실행기 배치"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::PlacePlayer))]
        ]
        +SVerticalBox::Slot().AutoHeight().Padding(8)[SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return FText::FromString(Status);})]
        +SVerticalBox::Slot().FillHeight(1)
        [SNew(SSplitter)
            +SSplitter::Slot().Value(.16f)[SNew(SVerticalBox)
                +SVerticalBox::Slot().AutoHeight().Padding(8)[SNew(STextBlock).Text(FText::FromString(TEXT("이벤트 그래프")))]
                +SVerticalBox::Slot().AutoHeight().Padding(5)[Button(TEXT("+ 이벤트 추가"),FOnClicked::CreateSP(this,&FSceneDirectorToolkit::AddEvent))]
                +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(STextBlock).Text(FText::FromString(TEXT("현재 이벤트 이름")))]
                +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(SEditableTextBox).Text_Lambda([this]{return FText::FromName(Asset->EventKey);})
                    .OnTextCommitted_Lambda([this](const FText& Text,ETextCommit::Type Commit){if(Commit!=ETextCommit::OnCleared)RenameEvent(FName(*Text.ToString().TrimStartAndEnd()));})]
                +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SSeparator)]
                +SVerticalBox::Slot().FillHeight(.5f)[EventList.ToSharedRef()]
                +SVerticalBox::Slot().AutoHeight().Padding(5)[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(TEXT("모든 조건 충족 시 실행 · 여러 그래프가 맞으면 위쪽 우선")))]
                +SVerticalBox::Slot().FillHeight(.5f)[ConditionDetails.ToSharedRef()]]
            +SSplitter::Slot().Value(.56f)[SNew(SSplitter).Orientation(Orient_Vertical)
                +SSplitter::Slot().Value(.55f)[GraphEditor.ToSharedRef()]
                +SSplitter::Slot().Value(.45f)[SAssignNew(PreviewBox,SBox)[SNew(STextBlock).Text(FText::FromString(TEXT("생성 및 미리보기를 누르면 이곳에 씬과 시간 막대가 나타납니다.")))]]]
            +SSplitter::Slot().Value(.28f)[SNew(SSplitter).Orientation(Orient_Vertical)
                +SSplitter::Slot().Value(.5f)[Details.ToSharedRef()]
                +SSplitter::Slot().Value(.5f)[SNew(SScrollBox)+SScrollBox::Slot()[SNew(SVerticalBox)
                    +SVerticalBox::Slot().AutoHeight()[ObjectDetails.ToSharedRef()]
                    +SVerticalBox::Slot().AutoHeight()[OriginDetails.ToSharedRef()]
                    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SSeparator)]
                    +SVerticalBox::Slot().AutoHeight().Padding(6)[SNew(STextBlock).Text(FText::FromString(TEXT("NPC 목록 · Key를 눌러 대상 지정")))]
                    +SVerticalBox::Slot().AutoHeight()[SNew(SBox).MaxDesiredHeight(120)[NPCList.ToSharedRef()]]
                    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SSeparator)]
                    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("카메라 목록 · Key 선택 / 초기값 저장")))]
                    +SVerticalBox::Slot().AutoHeight()[SNew(SBox).MaxDesiredHeight(100)[CameraList.ToSharedRef()]]
                    +SVerticalBox::Slot().AutoHeight()[SNew(SExpandableArea).InitiallyCollapsed(true)
                        .HeaderContent()[SNew(STextBlock).Text(FText::FromString(TEXT("카메라 저장값 편집")))]
                        .BodyContent()[CameraDetails.ToSharedRef()]]
                    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SSeparator)]
                    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("Vector3 목록 · 위치 cm / 회전 도")))]
                    +SVerticalBox::Slot().AutoHeight()[VectorDetails.ToSharedRef()]
                    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SSeparator)]
                    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("공용 변수 · 모든 이벤트에서 사용")))]
                    +SVerticalBox::Slot().AutoHeight()[BoolDetails.ToSharedRef()]
                    +SVerticalBox::Slot().AutoHeight().Padding(0,10)[SNew(SSeparator)]
                    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("게임 액션 · 미리보기에서는 실행하지 않음")))]
                    +SVerticalBox::Slot().AutoHeight()[ActionDetails.ToSharedRef()]]]
            ]
        ]
    ];
}
FReply FSceneDirectorToolkit::AddNode(EDirectorNodeType Type,const FVector2f& Location,UEdGraphPin* FromPin)
{
    ClosePreview(); const FScopedTransaction Transaction(FText::FromString(TEXT("연출 노드 추가"))); Graph->Modify();
    auto* Node=NewObject<USceneDirectorGraphNode>(Graph,NAME_None,RF_Transactional);Node->Step.Type=Type;if(Type==EDirectorNodeType::PlayerHidden)Node->Step.bHidePlayer=true;
    if(DirectorNodes::IsNPC(Type))
    {
        int32 Index=1;FName Key;do{Key=FName(*FString::Printf(TEXT("NPC_%d"),Index++));}while(Asset->Steps.ContainsByPredicate([&](const FDirectorStep& S){return DirectorNodes::IsNPC(S.Type)&&S.Role==Key;}));Node->Step.Role=Key;
    }
        if(DirectorNodes::IsCamera(Type))
    {
        int32 Index=1;FName Key;
        do{Key=FName(*FString::Printf(TEXT("Camera_%d"),Index++));}while(Asset->Cameras.ContainsByPredicate([&](const FDirectorCameraEntry& C){return C.Key==Key;}));
        Node->Step.CameraKey=Asset->Cameras.IsEmpty()?Key:Asset->Cameras[0].Key;Node->Step.Transform.SetLocation(FVector(-300,0,160));
        if(GCurrentLevelEditingViewportClient)Node->Step.Transform=FTransform(GCurrentLevelEditingViewportClient->GetViewRotation(),GCurrentLevelEditingViewportClient->GetViewLocation());
        Node->Step.Destination.Value=Node->Step.Transform.GetLocation();Node->Step.Rotation.Value=Node->Step.Transform.Rotator().Euler();
    }

    Node->NodePosX=FMath::RoundToInt(Location.X);Node->NodePosY=FMath::RoundToInt(Location.Y);Node->CreateNewGuid();Graph->AddNode(Node,true,true);Node->AllocateDefaultPins();
    if(FromPin&&FromPin->GetOwningNode()->GetGraph()==Graph)Graph->GetSchema()->TryCreateConnection(FromPin,Node->FindPin(FromPin->Direction==EGPD_Output?TEXT("In"):TEXT("Out")));
    Graph->Sync();Graph->NotifyGraphChanged();GraphEditor->ClearSelectionSet();GraphEditor->SetNodeSelection(Node,true);
    Status=TEXT("노드가 추가되었습니다. 앞 노드의 '다음' 핀과 연결하고, 오른쪽 속성을 입력하세요.");return FReply::Handled();
}
FReply FSceneDirectorToolkit::DeleteNodes()
{
    ClosePreview();const FScopedTransaction Transaction(FText::FromString(TEXT("연출 노드 삭제")));Graph->Modify();
    const auto Selection=GraphEditor->GetSelectedNodes();
    for(auto* O:Selection)if(auto* Node=Cast<USceneDirectorGraphNode>(O))
    {
        if(Node->Step.Type==EDirectorNodeType::Start||Node->Step.Type==EDirectorNodeType::End)continue;
        Node->Modify();Node->BreakAllNodeLinks();Graph->RemoveNode(Node);
    }
    GraphEditor->ClearSelectionSet();Graph->Sync();Graph->NotifyGraphChanged();return FReply::Handled();
}
FReply FSceneDirectorToolkit::CapturePosition()
{
    if(GraphEditor->GetSelectedNodes().Num()!=1){Status=TEXT("위치를 가져올 노드 하나를 선택하세요.");return FReply::Handled();}
    auto* Node=Cast<USceneDirectorGraphNode>(*GraphEditor->GetSelectedNodes().CreateConstIterator());if(!Node)return FReply::Handled();
    const bool Camera=DirectorNodes::IsCamera(Node->Step.Type)||DirectorNodes::IsReturn(Node->Step.Type);
    const bool NPC=DirectorNodes::IsNPC(Node->Step.Type)||Node->Step.Type==EDirectorNodeType::CharacterMove;
    if(!Camera&&!NPC){Status=TEXT("NPC/카메라 추가 또는 이동 노드를 선택하세요.");return FReply::Handled();}
    ClosePreview();const FScopedTransaction Tx(FText::FromString(TEXT("뷰포트 위치 가져오기")));Node->Modify();Asset->Modify();
    if(Camera&&GCurrentLevelEditingViewportClient)
    {
        FTransform Pose(GCurrentLevelEditingViewportClient->GetViewRotation(),GCurrentLevelEditingViewportClient->GetViewLocation());
        if(DirectorNodes::IsReturn(Node->Step.Type))
        {Node->Step.bUsePreviewReturnView=true;Node->Step.PreviewReturnView=Pose;Node->Step.PreviewReturnFOV=GCurrentLevelEditingViewportClient->ViewFOV;}
        else if(Node->Step.Type==EDirectorNodeType::CameraMove)
        {
            Node->Step.Destination.Mode=EDirectorValueMode::Absolute;Node->Step.Destination.Value=Pose.GetLocation();
            Node->Step.Rotation.Mode=EDirectorValueMode::Absolute;Node->Step.Rotation.Value=Pose.Rotator().Euler();
            if(Node->Step.bUseMotionPath&&!Node->Step.MotionPoints.IsEmpty()){Node->Step.MotionPoints.Last().Position=Pose.GetLocation();Node->Step.MotionPoints.Last().Rotation=Pose.Rotator().Euler();}
        }
        else
        {
            Node->Step.Transform=Pose;Node->Step.FieldOfView=GCurrentLevelEditingViewportClient->ViewFOV;Node->Step.bLookAtTarget=false;
            if(auto* C=Asset->Cameras.FindByPredicate([&](const FDirectorCameraEntry& C){return C.Key==Node->Step.CameraKey;})){C->Transform=Pose;C->FieldOfView=Node->Step.FieldOfView;}
        }
    }
    else if(NPC)
    {
        auto* Actor=Cast<AActor>(GEditor->GetSelectedActors()->GetTop(AActor::StaticClass()));
        if(!Actor){Status=TEXT("레벨에서 기준 Actor를 선택하세요.");return FReply::Handled();}
        if(Node->Step.Type==EDirectorNodeType::CharacterMove){Node->Step.Destination.Mode=EDirectorValueMode::Absolute;Node->Step.Destination.Value=Actor->GetActorLocation();if(Node->Step.bUseMotionPath&&!Node->Step.MotionPoints.IsEmpty())Node->Step.MotionPoints.Last().Position=Actor->GetActorLocation();}
        else Node->Step.Transform=Actor->GetActorTransform();
    }
    else {Status=TEXT("열린 레벨 뷰포트가 없습니다.");return FReply::Handled();}
    Graph->Sync();Details->ForceRefresh();Status=TEXT("위치를 가져왔습니다. 생성 및 미리보기로 확인하세요.");return FReply::Handled();
}
void FSceneDirectorToolkit::ClosePreview()
{
    SceneViewport.Reset();
    if(Sequencer){FLevelEditorSequencerIntegration::Get().RemoveSequencer(Sequencer.ToSharedRef());Sequencer->Close();Sequencer.Reset();}
    ComparisonSequence=nullptr;
    if(PreviewBox)PreviewBox->SetContent(SNew(STextBlock).Text(FText::FromString(TEXT("미리보기가 종료되었습니다."))));
}
FReply FSceneDirectorToolkit::BuildPreview()
{
    if(GEditor->PlayWorld){Status=TEXT("게임 실행을 종료한 다음 편집기 미리보기를 실행하세요.");return FReply::Handled();}
    const double Elapsed=PreviewElapsed();ClosePreview();Graph->Sync();
    if(!FSceneDirectorCompiler::Compile(*Asset,Status))return FReply::Handled();
    OpenPreview(Asset->GeneratedSequence,Asset,Elapsed);
    FString Path;
    for(const auto& Cue:Asset->Cues)if(Cue.Step.Type==EDirectorNodeType::Dialogue&&!Cue.Step.Choices.IsEmpty())
    {
        const int32 Index=Cue.Step.PreviewChoiceIndex-1;
        if(Cue.Step.Choices.IsValidIndex(Index))Path+=FString::Printf(TEXT(" [%s → %d: %s]"),*Cue.Step.DialogueText.ToString().Left(16),Index+1,*Cue.Step.Choices[Index].Text.ToString());
    }
    if(!Path.IsEmpty())Status+=TEXT(" 미리보기 선택 경로:")+Path+TEXT(". 각 대사 노드의 미리보기 선택지 번호로 변경합니다.");
    for(const auto& B:Asset->BoolVariables)Status+=FString::Printf(TEXT(" [%s 초기값=%s]"),*B.Key.ToString(),B.Value?TEXT("참"):TEXT("거짓"));
    if(!Asset->Actions.IsEmpty())Status+=TEXT(" 게임 액션은 미리보기에서 실행하지 않습니다. PIE에서 실행 이력을 확인하세요.");
    if(Asset->Cues.ContainsByPredicate([](const FDirectorCue& C){return DirectorNodes::IsReturn(C.Step.Type);}))Status+=TEXT(" 카메라 복귀 노드: 시간과 미리보기 복귀 구도를 조정할 수 있습니다. 구도 미지정 시 열린 레벨 뷰포트를 사용합니다.");
    Status+=TEXT(" 자동 생성 구간은 여기서 직접 편집하지 마세요. 변경은 노드 속성에서 진행하세요.");
    return FReply::Handled();
}
FReply FSceneDirectorToolkit::StopPreview(){ClosePreview();Status=TEXT("미리보기를 종료하고 임시 객체를 정리했습니다.");return FReply::Handled();}
void FSceneDirectorToolkit::OnMapChanged(uint32){ClosePreview();}
void FSceneDirectorToolkit::OnBeginPIE(bool){ClosePreview();}
void FSceneDirectorToolkit::PostUndo(bool bSuccess)
{
    if(!bSuccess)return;ClosePreview();
    if(Asset!=RootAsset&&!RootAsset->EventGraphs.Contains(Asset))Asset=RootAsset;
    Graph->Asset=Asset;Graph->Load();GraphEditor->ClearSelectionSet();Details->SetObject(nullptr);
    ObjectDetails->SetObject(Asset,true);OriginDetails->SetObject(RootAsset,true);CameraDetails->SetObject(Asset,true);VectorDetails->SetObject(Asset,true);BoolDetails->SetObject(RootAsset,true);ConditionDetails->SetObject(Asset,true);ActionDetails->SetObject(Asset,true);RefreshNPCList();RefreshEventList();
}
void FSceneDirectorToolkit::SaveAsset_Execute()
{
    Graph->Sync();ClosePreview();TArray<USceneDirectorAsset*> Events{RootAsset};for(auto Event:RootAsset->EventGraphs)if(Event)Events.Add(Event);
    FString Failures;for(auto* Event:Events){FString Message;if(!FSceneDirectorCompiler::Compile(*Event,Message))Failures+=Event->EventKey.ToString()+TEXT(": ")+Message+TEXT("\n");}
    Status=Failures.IsEmpty()?TEXT("모든 이벤트 그래프를 생성하고 저장했습니다."):TEXT("편집 내용은 저장합니다. 다음 이벤트의 생성 오류를 수정하세요:\n")+Failures;
    FAssetEditorToolkit::SaveAsset_Execute();
}
FReply FSceneDirectorToolkit::PlacePlayer()
{
    ClosePreview();Graph->Sync();if(!FSceneDirectorCompiler::Compile(*Asset,Status))return FReply::Handled();
    if(GEditor->PlayWorld){Status=TEXT("게임 실행을 종료한 뒤 실행기를 배치하세요.");return FReply::Handled();}
    const FScopedTransaction Transaction(FText::FromString(TEXT("연출 실행기 배치")));
    UWorld* World=GEditor->GetEditorWorldContext().World(); if(!World)return FReply::Handled();
    FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transactional;
    auto* Player=World->SpawnActor<ASceneDirectorPlayer>(ASceneDirectorPlayer::StaticClass(),FTransform::Identity,Params);
    if(Player){Player->Director=RootAsset;Player->EventKey=Asset->EventKey;Player->SetActorLabel(Asset->EventKey.ToString()+TEXT("_실행기"));GEditor->SelectNone(false,true);GEditor->SelectActor(Player,true,true);World->MarkPackageDirty();}
    Status=TEXT("실행기를 배치했습니다. 레벨을 저장하고 PIE로 확인하세요. 기본값은 게임 시작 시 자동 재생입니다.");return FReply::Handled();
}





void FSceneDirectorToolkit::RefreshNPCList()
{
    if(!NPCList||!Graph)return;NPCList->ClearChildren();int32 Count=0;
    if(CameraList)
    {
        CameraList->ClearChildren();
        for(const auto& Camera:Asset->Cameras)
        {
            const FName Key=Camera.Key;
            CameraList->AddSlot().Padding(3)[SNew(SButton).Text(FText::FromName(Key)).OnClicked_Lambda([this,Key]
            {
                if(GraphEditor->GetSelectedNodes().Num()==1)if(auto* Node=Cast<USceneDirectorGraphNode>(*GraphEditor->GetSelectedNodes().CreateConstIterator()))
                    if(DirectorNodes::IsCamera(Node->Step.Type))
                    {
                        const FScopedTransaction Tx(FText::FromString(TEXT("카메라 대상 지정")));Node->Modify();Node->Step.CameraKey=Key;
                        Graph->Sync();Graph->NotifyGraphChanged();Details->ForceRefresh();
                    }
                return FReply::Handled();
            })];
        }
    }
    if(CameraDetails)CameraDetails->ForceRefresh();
    if(BoolDetails){RootAsset->RefreshVariableEntries();BoolDetails->ForceRefresh();}
    if(ActionDetails)ActionDetails->ForceRefresh();
    for(auto Base:Graph->Nodes)if(auto* NPC=Cast<USceneDirectorGraphNode>(Base))if(DirectorAuthoring::IsCharacterEntry(NPC->Step))
    {
        ++Count;const FName Key=NPC->Step.Role;TWeakObjectPtr<USceneDirectorGraphNode> WeakNPC=NPC;
        const FString Label=Key.ToString()+TEXT("\n")+(NPC->Step.ActorClass?NPC->Step.ActorClass->GetName():TEXT("BP 선택 필요"));
        NPCList->AddSlot().Padding(4)[SNew(SButton).Text(FText::FromString(Label)).OnClicked_Lambda([this,Key,WeakNPC]
        {
            if(!WeakNPC.IsValid())return FReply::Handled();
            if(GraphEditor->GetSelectedNodes().Num()==1)
            {
                auto* Node=Cast<USceneDirectorGraphNode>(*GraphEditor->GetSelectedNodes().CreateConstIterator());
                if(Node&&DirectorNodes::UsesNPC(Node->Step.Type))
                {
                    const FScopedTransaction Transaction(FText::FromString(TEXT("대상 NPC 지정")));Node->Modify();Node->Step.Role=Key;
                    Graph->Sync();Graph->NotifyGraphChanged();Details->ForceRefresh();return FReply::Handled();
                }
            }
            GraphEditor->ClearSelectionSet();GraphEditor->SetNodeSelection(WeakNPC.Get(),true);return FReply::Handled();
        })];
    }
    if(!Count)NPCList->AddSlot()[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(TEXT("NPC 추가 노드에서 BP와 String Key를 입력하면 목록에 저장됩니다.")))];
}




void FSceneDirectorToolkit::RegistryChanged(const FPropertyChangedEvent&)
{
    ClosePreview();Asset->bNeedsCompile=true;Asset->MarkPackageDirty();
    Graph->Load();GraphEditor->ClearSelectionSet();Details->SetObject(nullptr);RefreshNPCList();
}




FActionMenuContent FSceneDirectorToolkit::CreateNodeMenu(const FVector2f& Location,const TArray<UEdGraphPin*>& Pins)
{
    FMenuBuilder Menu(true,nullptr);
    const TWeakPtr<FSceneDirectorToolkit> Weak=SharedThis(this);const TWeakObjectPtr<USceneDirectorAsset> Event=Asset;
    const FEdGraphPinReference Pin(Pins.Num()?Pins[0]:nullptr);
    for(const TCHAR* Category:{TEXT("캐릭터"),TEXT("카메라"),TEXT("흐름 제어"),TEXT("대화"),TEXT("게임 연동")})
    {
        const FString Group=Category;
        Menu.AddSubMenu(FText::FromString(Group),FText::FromString(TEXT("노드 종류 선택")),FNewMenuDelegate::CreateLambda([Weak,Event,Pin,Location,Group](FMenuBuilder& Sub)
        {
            for(const auto& Entry:DirectorNodeMenuEntries())if(Group==Entry.Category)
            {
                const auto Type=Entry.Type;
                Sub.AddMenuEntry(FText::FromString(Entry.Label),FText::GetEmpty(),FSlateIcon(),FUIAction(FExecuteAction::CreateLambda([Weak,Event,Pin,Location,Type]
                {
                    if(auto Editor=Weak.Pin())if(Editor->Asset==Event.Get())
                    {
                        UEdGraphPin* From=Pin.Get();if(From&&!Editor->Graph->Nodes.Contains(From->GetOwningNode()))From=nullptr;
                        Editor->AddNode(Type,Location,From);
                    }
                })));
            }
        }),true);
    }
    return FActionMenuContent(Menu.MakeWidget());
}
void FSceneDirectorToolkit::RefreshEventList()
{
    if(!EventList||!RootAsset)return;EventList->ClearChildren();
    TArray<USceneDirectorAsset*> Events{RootAsset};for(auto Event:RootAsset->EventGraphs)if(Event)Events.Add(Event);
    for(auto* Event:Events)
    {
        TWeakObjectPtr<USceneDirectorAsset> WeakEvent=Event;
        EventList->AddSlot().Padding(4)[SNew(SButton)
            .ButtonColorAndOpacity_Lambda([this,WeakEvent]{return Asset==WeakEvent.Get()?FLinearColor(.1f,.45f,.6f):FLinearColor(.2f,.2f,.2f);})
            .Text_Lambda([WeakEvent]{return WeakEvent.IsValid()?FText::FromName(WeakEvent->EventKey):FText::GetEmpty();})
            .OnClicked_Lambda([this,WeakEvent]{if(WeakEvent.IsValid())SelectEvent(WeakEvent.Get());return FReply::Handled();})];
    }
}
void FSceneDirectorToolkit::SelectEvent(USceneDirectorAsset* Event)
{
    if(!Event||Event==Asset)return;
    if(Event!=RootAsset&&!RootAsset->EventGraphs.Contains(Event))return;
    ClosePreview();Graph->Sync();Asset=Event;Asset->SetFlags(RF_Transactional);Graph->Asset=Asset;Graph->Load();
    GraphEditor->ClearSelectionSet();GraphEditor->ZoomToFit(false);Details->SetObject(nullptr);
    ObjectDetails->SetObject(Asset,true);OriginDetails->SetObject(RootAsset,true);CameraDetails->SetObject(Asset,true);VectorDetails->SetObject(Asset,true);BoolDetails->SetObject(RootAsset,true);ConditionDetails->SetObject(Asset,true);ActionDetails->SetObject(Asset,true);RefreshNPCList();RefreshEventList();
    Status=Asset->EventKey.ToString()+TEXT(" 편집 중 · 중앙 그래프 빈 공간에서 우클릭하여 노드를 추가하세요.");
}
FReply FSceneDirectorToolkit::AddEvent()
{
    const FScopedTransaction Tx(FText::FromString(TEXT("이벤트 그래프 추가")));RootAsset->Modify();
    int32 Number=1;FName Key;do{Key=FName(*FString::Printf(TEXT("Event_%d"),Number++));}while(RootAsset->FindEvent(Key));
    auto* Event=NewObject<USceneDirectorAsset>(RootAsset,NAME_None,RF_Transactional);Event->EventKey=Key;
    FDirectorStep Start;Start.Type=EDirectorNodeType::Start;
    FDirectorStep Wait;Wait.Type=EDirectorNodeType::Wait;Wait.EditorPosition=FVector2D(270,0);
    FDirectorStep End;End.Type=EDirectorNodeType::End;End.EditorPosition=FVector2D(540,0);
    Start.NextNodes={Wait.Id};Wait.NextNodes={End.Id};Event->Steps={Start,Wait,End};
    RootAsset->EventGraphs.Add(Event);RootAsset->MarkPackageDirty();SelectEvent(Event);return FReply::Handled();
}
bool FSceneDirectorToolkit::RenameEvent(FName Key)
{
    if(Key.IsNone()){Status=TEXT("이벤트 이름은 비워 둘 수 없습니다.");return false;}
    if(auto* Existing=RootAsset->FindEvent(Key);Existing&&Existing!=Asset){Status=TEXT("이미 사용 중인 이벤트 이름입니다.");return false;}
    if(Key==Asset->EventKey)return true;
    const FScopedTransaction Tx(FText::FromString(TEXT("이벤트 이름 변경")));Asset->Modify();Asset->EventKey=Key;RootAsset->MarkPackageDirty();RefreshEventList();return true;
}


FReply FSceneDirectorToolkit::ImportSelectedSequence()
{
    TArray<FAssetData> Selected;FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser").Get().GetSelectedAssets(Selected);
    if(Selected.Num()!=1){Status=TEXT("콘텐츠 브라우저에서 레벨 시퀀스 하나를 선택한 뒤 가져오기를 누르세요.");return FReply::Handled();}
    auto* Source=Cast<ULevelSequence>(Selected[0].GetAsset());FString Report;
    auto* Converted=FSceneDirectorImporter::Convert(Source,GetTransientPackage(),Report);
    if(!Converted){Status=Report;return FReply::Handled();}
    const FScopedTransaction Transaction(FText::FromString(TEXT("시퀀스를 새 이벤트로 가져오기")));RootAsset->Modify();ClosePreview();
    auto* Event=DuplicateObject<USceneDirectorAsset>(Converted,RootAsset);Event->SetFlags(RF_Transactional);
    const FString Base=TEXT("Imported_")+Source->GetName();FName Key(*Base);int32 Suffix=2;while(RootAsset->FindEvent(Key))Key=FName(*(Base+TEXT("_")+FString::FromInt(Suffix++)));Event->EventKey=Key;
    RootAsset->EventGraphs.Add(Event);RootAsset->MarkPackageDirty();SelectEvent(Event);Status=Report;return FReply::Handled();
}

double FSceneDirectorToolkit::PreviewElapsed() const
{
    if(!Sequencer)return 0;auto* Movie=Sequencer->GetRootMovieSceneSequence()->GetMovieScene();
    return FMath::Max(0.,(Sequencer->GetGlobalTime().Time.AsDecimal()-Movie->GetPlaybackRange().GetLowerBoundValue().Value)/Movie->GetTickResolution().AsDecimal());
}
void FSceneDirectorToolkit::OpenPreview(ULevelSequence* Sequence,USceneDirectorAsset* PreviewAsset,double Seconds)
{
    Sequence->GetMovieScene()->SetReadOnly(true);
    auto SpawnRegister=MakeShared<FLevelSequenceEditorSpawnRegister>();
    FSequencerInitParams Params;Params.RootSequence=Sequence;Params.SpawnRegister=SpawnRegister;
    Params.bEditWithinLevelEditor=false;Params.PlaybackContext=GEditor->GetEditorWorldContext().World();
    Sequencer=FModuleManager::LoadModuleChecked<ISequencerModule>("Sequencer").CreateSequencer(Params);
    SpawnRegister->SetSequencer(Sequencer);
    FLevelEditorSequencerIntegrationOptions Integration;Integration.bRequiresLevelEvents=true;Integration.bRequiresActorEvents=true;
    FLevelEditorSequencerIntegration::Get().AddSequencer(Sequencer.ToSharedRef(),Integration);
    Sequencer->SetPerspectiveViewportCameraCutEnabled(true);
    FVector Focus=FVector::ZeroVector;for(const auto& Step:Asset->Steps)if(DirectorNodes::IsNPC(Step.Type)){Focus=Step.Transform.GetLocation();break;}
    PreviewBox->SetContent(SNew(SSplitter)
        +SSplitter::Slot().Value(.5f)[SNew(SVerticalBox)
            +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("씬 미리보기 · 밝게 보기(Unlit) · 시간 막대에서 재생/탐색")))]
            +SVerticalBox::Slot().FillHeight(1)[SAssignNew(SceneViewport,SDirectorViewport,GEditor->GetEditorWorldContext().World(),Sequencer,Focus,PreviewAsset)]]
        +SSplitter::Slot().Value(.5f)[Sequencer->GetSequencerWidget()]);
    auto* Client=static_cast<FDirectorViewportClient*>(SceneViewport->GetViewportClient().Get());
    Client->GameplayPreviewView=GCurrentLevelEditingViewportClient?FTransform(GCurrentLevelEditingViewportClient->GetViewRotation(),GCurrentLevelEditingViewportClient->GetViewLocation()):FTransform(Client->GetViewRotation(),Client->GetViewLocation());
    Client->GameplayPreviewFOV=GCurrentLevelEditingViewportClient?GCurrentLevelEditingViewportClient->ViewFOV:Client->ViewFOV;
    if(PreviewAsset)for(const auto& Cue:PreviewAsset->Cues)if(DirectorNodes::IsReturn(Cue.Step.Type))
    {
        Sequencer->SetGlobalTime(FFrameTime::FromDecimal(FMath::Max(0.,Cue.StartFrame-.001)));
        Sequencer->ForceEvaluate();Client->Tick(0);Client->CaptureReturnStart(Cue.Step.Id);
    }
    Sequencer->SetGlobalTime(FFrameTime::FromDecimal(Sequence->GetMovieScene()->GetPlaybackRange().GetLowerBoundValue().Value+Seconds*Sequence->GetMovieScene()->GetTickResolution().AsDecimal()));

}
FReply FSceneDirectorToolkit::PreviewOriginal()
{
    if(GEditor->PlayWorld){Status=TEXT("PIE를 종료한 뒤 원본 비교를 실행하세요.");return FReply::Handled();}
    if(!Asset->ImportedFrom){Status=TEXT("시퀀스에서 변환한 이벤트에서 원본 비교를 사용할 수 있습니다.");return FReply::Handled();}
    if(!FSceneDirectorImporter::Convert(Asset->ImportedFrom,GetTransientPackage(),Status))return FReply::Handled();
    const double Elapsed=PreviewElapsed();ClosePreview();ComparisonSequence=DuplicateObject<ULevelSequence>(Asset->ImportedFrom,GetTransientPackage());
    OpenPreview(ComparisonSequence,nullptr,Elapsed);Status=TEXT("원본 비교 중 (읽기 전용 복사본). 생성 및 미리보기를 누르면 같은 시간의 변환 결과로 돌아갑니다.");return FReply::Handled();
}
