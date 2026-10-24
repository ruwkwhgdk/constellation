#include "MinimapWorldSubsystem.h"
#include "MinimapExplorationSubsystem.h"
#include "MinimapWidget.h"
#include "QuestSubsystem.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
AMinimapRegionActor::AMinimapRegionActor(){PrimaryActorTick.bCanEverTick=false;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Region"));}
void UMinimapWorldSubsystem::Tick(float Delta)
{
 auto* W=GetWorld();if(!W||!W->HasBegunPlay())return;
 auto* PC=W->GetFirstPlayerController();APawn* Pawn=PC?PC->GetPawn():nullptr;if(!Pawn)return;
 PawnPosition=Pawn->GetActorLocation();bool bAirborne=false;
 FVector Ground=PawnPosition;bool bGrounded=false;
 if(auto* Character=Cast<ACharacter>(Pawn))
 {
  PawnPosition.Z-=Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
  const auto* Movement=Character->GetCharacterMovement();bAirborne=Movement->IsFalling();
  bGrounded=Movement->IsMovingOnGround()&&Movement->CurrentFloor.IsWalkableFloor();
  Ground=bGrounded?FVector(Movement->CurrentFloor.HitResult.ImpactPoint):PawnPosition;
 }
 HeadingYaw=Pawn->GetActorRotation().Yaw;CameraYaw=PC->PlayerCameraManager?PC->PlayerCameraManager->GetCameraRotation().Yaw:HeadingYaw;CameraFOV=PC->PlayerCameraManager?PC->PlayerCameraManager->GetFOVAngle():70;
 Accumulator+=Delta;if(Accumulator<.2f)return;const float Elapsed=Accumulator;Accumulator=0;
 auto* GI=W->GetGameInstance();auto* Memory=GI?GI->GetSubsystem<UMinimapExplorationSubsystem>():nullptr;if(!Memory)return;Memory->TickFlush(Elapsed);
 auto Connected=[&](FVector Candidate)
 {
  FCollisionQueryParams Query(SCENE_QUERY_STAT(MinimapFloorRecovery),false,Pawn);
  TArray<AActor*> Attached;Pawn->GetAttachedActors(Attached);Query.AddIgnoredActors(Attached);
  FHitResult Hit;
  return !W->LineTraceSingleByChannel(Hit,Ground+FVector(0,0,55),Candidate+FVector(0,0,55),ECC_Visibility,Query);
 };
 if(!Region)
 {
  UMinimapRegionData* OnlyRegion=nullptr;int32 Count=0;
  for(TActorIterator<AMinimapRegionActor> It(W);It;++It)if(It->Data)
  {
   OnlyRegion=It->Data;++Count;
   if(It->Data->FindFloor(Ground,INDEX_NONE,40,75)!=INDEX_NONE||(bGrounded&&It->Data->FindNearbyFloor(Ground,INDEX_NONE,Connected)!=INDEX_NONE)){Region=It->Data;break;}
  }
  if(!Region&&Count==1)Region=OnlyRegion;
  if(Region)Markers=Region->ResolveMarkers();
 }
 if(!Region)return;
 const int32 ExactFloor=Region->FindFloor(Ground,FloorIndex,40,75);
 int32 NewFloor=ExactFloor;
 if(NewFloor==INDEX_NONE&&bGrounded)NewFloor=Region->FindNearbyFloor(Ground,FloorIndex,Connected);
 bCanReveal=bGrounded&&ExactFloor!=INDEX_NONE;
 if(bCanReveal)ConfirmedGround=Ground;
 if(bGrounded&&NewFloor!=INDEX_NONE)
 {
  FloorIndex=NewFloor;UnresolvedSeconds=0;
 }
 else if(!bAirborne||FloorIndex==INDEX_NONE)
 {
  UnresolvedSeconds+=Elapsed;
  if(UnresolvedSeconds>1.f)FloorIndex=INDEX_NONE;
 }
 if(!Widget){Widget=CreateWidget<UMinimapWidget>(PC);if(Widget){Widget->SetVisibility(ESlateVisibility::HitTestInvisible);Widget->AddToViewport(5);}}
 if(Region->RevealMode==EMinimapRevealMode::Exploration&&bCanReveal)RevealNearby(Region->RevealRadius);
 UpdateObjective();
}
void UMinimapWorldSubsystem::Deinitialize()
{
 if(Widget){Widget->RemoveFromParent();Widget=nullptr;}if(auto* GI=GetWorld()->GetGameInstance())if(auto* Memory=GI->GetSubsystem<UMinimapExplorationSubsystem>())Memory->Flush();Region=nullptr;Super::Deinitialize();
}
bool UMinimapWorldSubsystem::IsDiscovered(const FMinimapFloorData& F,int32 I)const
{
 if(!Region||!F.Cells.IsValidIndex(I))return false;auto* GI=GetWorld()->GetGameInstance();auto* Memory=GI?GI->GetSubsystem<UMinimapExplorationSubsystem>():nullptr;
 return Memory&&(Memory->IsRegionUnlocked(Region->RegionId)||Memory->IsRevealed(Region->RegionId,F.FloorId,FMath::RoundToInt(F.CellSize),F.GlobalCell(I)));
}
void UMinimapWorldSubsystem::RevealNearby(float Radius)
{
 if(!bCanReveal)return;
 const auto* F=GetFloor();if(!F||!FMath::IsFinite(Radius)||Radius<=0)return;auto* W=GetWorld();auto* Memory=W->GetGameInstance()->GetSubsystem<UMinimapExplorationSubsystem>();if(!Memory)return;
 auto* PC=W->GetFirstPlayerController();APawn* Pawn=PC?PC->GetPawn():nullptr;
 TArray<FIntPoint> Cells;FCollisionQueryParams Query(SCENE_QUERY_STAT(MinimapReveal),false,Pawn);
 if(Pawn){TArray<AActor*> Attached;Pawn->GetAttachedActors(Attached);Query.AddIgnoredActors(Attached);}
 const FVector Start=ConfirmedGround+FVector(0,0,55);
 for(int32 I:F->VisibleCells(FVector2D(ConfirmedGround),Radius))
 {
  const float Z=F->SurfaceZ.IsValidIndex(I)?F->SurfaceZ[I]:F->ReferenceZ;
  // A different elevated platform never inherits discovery merely through matching XY.
  if(F->Cells[I]==1&&FMath::Abs(Z-ConfirmedGround.Z)>150)continue;
  const FVector2D XY=F->Center(I);const FVector End(XY.X,XY.Y,Z+55);FHitResult Hit;
  const bool Blocked=W->LineTraceSingleByChannel(Hit,Start,End,ECC_Visibility,Query);
  if(Blocked&&(F->Cells[I]!=2||F->IndexAt(FVector2D(Hit.Location))!=I))continue;
  Cells.Add(F->GlobalCell(I));
 }
 Memory->RevealCells(Region->RegionId,F->FloorId,FMath::RoundToInt(F->CellSize),Cells);
}
void UMinimapWorldSubsystem::UnlockRegion(FName Id){if(auto* GI=GetWorld()->GetGameInstance())if(auto* M=GI->GetSubsystem<UMinimapExplorationSubsystem>())M->UnlockRegion(Id);}
void UMinimapWorldSubsystem::SetObjectiveOverride(FName R,FName F,FVector P){if(P.ContainsNaN())return;bOverride=true;OverrideRegion=R;OverrideFloor=F;OverridePosition=P;UpdateObjective();}
void UMinimapWorldSubsystem::ClearObjectiveOverride(){bOverride=false;UpdateObjective();}
FName UMinimapWorldSubsystem::GetCurrentFloorId()const{const auto* F=GetFloor();return F?F->FloorId:NAME_None;}
int32 UMinimapWorldSubsystem::GetDiscoveredCellCount()const{const auto* F=GetFloor();if(!F)return 0;int32 Count=0;for(int32 I=0;I<F->Cells.Num();++I)if(F->Cells[I]&&IsDiscovered(*F,I))++Count;return Count;}
void UMinimapWorldSubsystem::UpdateObjective()
{
 Objective=FMinimapObjectiveView();if(!Region||!GetFloor())return;
 FVector Position;FName TargetFloor;
 if(bOverride){if(OverrideRegion!=Region->RegionId)return;Position=OverridePosition;TargetFloor=OverrideFloor;}
 else
 {
  auto* Quests=GetWorld()->GetGameInstance()->GetSubsystem<UQuestSubsystem>();if(!Quests)return;const auto Info=Quests->GetTrackedQuestDisplayInfo();const FName Quest=Quests->GetTrackedQuestID();

  const auto* Binding=Region->Objectives.FindByPredicate([&](const FMinimapObjectiveBinding& B){return B.QuestId==Quest&&B.Progress==Info.Progress&&B.InnerProgress==Info.InnerProgress;});
  if(!Binding||(!Binding->bOverridePosition&&!Info.TargetPositions.IsValidIndex(Info.InnerProgress)))return;Position=Binding->bOverridePosition?Binding->Position:Info.TargetPositions[Info.InnerProgress];TargetFloor=Binding->FloorId;
 }
 const auto* F=Region->Floors.FindByPredicate([&](const FMinimapFloorData& Item){return Item.FloorId==TargetFloor;});if(Position.ContainsNaN())return;
 Objective.bValid=true;Objective.bSameFloor=TargetFloor==GetFloor()->FloorId;Objective.Position=Position;Objective.FloorId=TargetFloor;Objective.FloorLabel=F?F->Label:FText::FromString(FString::Printf(TEXT("층 미지정 · 높이 %.1fm"),Position.Z/100));
}

