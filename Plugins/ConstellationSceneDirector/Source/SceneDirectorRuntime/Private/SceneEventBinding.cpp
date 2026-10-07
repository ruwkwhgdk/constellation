#include "SceneEventBinding.h"
#include "TimerManager.h"
#include "SceneDirectorInteractionComponent.h"
#include "SceneEventSubsystem.h"
#include "SceneDirectorAsset.h"
#include "Components/BoxComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"
#include "EngineUtils.h"
ASceneEventBinding::ASceneEventBinding()
{
 EventId=FGuid::NewGuid();Area=CreateDefaultSubobject<UBoxComponent>(TEXT("EventArea"));SetRootComponent(Area);
 Area->SetBoxExtent(FVector(150,150,100));Area->SetCollisionProfileName(TEXT("Trigger"));Area->SetGenerateOverlapEvents(true);Area->SetHiddenInGame(true);
}
void ASceneEventBinding::OnConstruction(const FTransform& Transform)
{
 Super::OnConstruction(Transform);if(!EventId.IsValid())EventId=FGuid::NewGuid();
 Area->SetBoxExtent(AreaExtent.GetAbs().ComponentMax(FVector::OneVector));
 Area->SetCollisionEnabled(Trigger==ESceneEventTrigger::Volume&&!Source?ECollisionEnabled::QueryOnly:ECollisionEnabled::NoCollision);
}
#if WITH_EDITOR
void ASceneEventBinding::PostDuplicate(EDuplicateMode::Type Mode){Super::PostDuplicate(Mode);if(Mode!=EDuplicateMode::PIE)EventId=FGuid::NewGuid();}
void ASceneEventBinding::PostEditImport(){Super::PostEditImport();EventId=FGuid::NewGuid();}
#endif
FString ASceneEventBinding::StateKey() const {return StateGroup.IsNone()?EventId.ToString():TEXT("Group:")+StateGroup.ToString();}
FTransform ASceneEventBinding::CaptureOrigin() const
{
 if(Origin==ESceneEventOrigin::Anchor&&IsValid(Anchor))return Anchor->GetActorTransform();
 return Source?Source->GetActorTransform():GetActorTransform();
}
bool ASceneEventBinding::PlayerInside() const
{
 auto* PC=GetWorld()?GetWorld()->GetFirstPlayerController():nullptr;APawn* Pawn=PC?PC->GetPawn():nullptr;
 return Pawn&&(IsValid(Source)?Source->IsOverlappingActor(Pawn):IsOverlappingActor(Pawn));
}
bool ASceneEventBinding::Validate(FString& Error,bool bAfterDestruction) const
{
 Error.Reset();if(Trigger==ESceneEventTrigger::LegacySequence&&!OriginalSequence){Error=TEXT("이관할 기존 시퀀스가 없습니다.");return false;}
 if(!Director){Error=TEXT("실행할 연출을 지정하세요.");return false;}
 if(!EventId.IsValid()){Error=TEXT("이벤트 ID가 없습니다.");return false;}
 if((Trigger==ESceneEventTrigger::Interaction||(Trigger==ESceneEventTrigger::Destroyed&&!bAfterDestruction))&&(!IsValid(Source)||Source==this)){Error=TEXT("유효한 대상 Actor를 지정하세요.");return false;}
 if(Trigger==ESceneEventTrigger::Interaction&&Source&&!Source->FindComponentByClass<USceneDirectorInteractionComponent>()){Error=TEXT("대상에 Ac_SceneDirectorInteraction과 상호작용 전달 연결이 필요합니다.");return false;}
 if(Trigger==ESceneEventTrigger::Combat&&CombatKey.IsNone()){Error=TEXT("전투 Key를 지정하세요.");return false;}
 if(Origin==ESceneEventOrigin::Anchor&&!IsValid(Anchor)){Error=TEXT("기준 앵커가 없습니다.");return false;}
 if(Trigger==ESceneEventTrigger::Destroyed&&Source&&(Anchor==Source||Objects.FindKey(Source))){Error=TEXT("파괴 대상은 연출 오브젝트/앵커로 사용할 수 없습니다.");return false;}
 for(const auto& Pair:Objects)if(Pair.Key.IsNone()||!IsValid(Pair.Value)){Error=TEXT("오브젝트 연결이 비어 있습니다.");return false;}
 for(TActorIterator<ASceneEventBinding> It(GetWorld());It;++It)if(*It!=this&&It->EventId==EventId){Error=TEXT("이벤트 ID가 중복됩니다. 이벤트를 다시 생성하세요.");return false;}
 for(TActorIterator<ASceneEventBinding> It(GetWorld());It;++It)if(*It!=this){if(!StateGroup.IsNone()&&It->StateGroup==StateGroup&&(It->Director!=Director||It->bPersistVariables!=bPersistVariables)){Error=TEXT("상태 공유 그룹은 같은 연출 애셋과 저장 정책을 사용해야 합니다.");return false;}if(bEnabled&&It->bEnabled&&Trigger==ESceneEventTrigger::Interaction&&It->Trigger==Trigger&&It->Source==Source){Error=TEXT("같은 대상에 상호작용 이벤트가 중복되어 있습니다.");return false;}}
 for(TActorIterator<ASceneEventBinding> It(GetWorld());It;++It)if(*It!=this&&Trigger==ESceneEventTrigger::LegacySequence&&It->Trigger==Trigger&&It->OriginalSequence==OriginalSequence){Error=TEXT("같은 원본 시퀀스의 이관 연결이 중복됩니다.");return false;}
 return true;
}
void ASceneEventBinding::BeginPlay()
{
 Super::BeginPlay();auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>();if(!S)return;S->Register(this);
 AActor* Target=Source?Source.Get():this;Watched=Target;
 if(Trigger==ESceneEventTrigger::Volume){Target->OnActorBeginOverlap.AddDynamic(this,&ASceneEventBinding::Enter);Target->OnActorEndOverlap.AddDynamic(this,&ASceneEventBinding::Leave);bInside=PlayerInside();GetWorld()->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this,[this]{bInside=PlayerInside();bVolumeArmed=true;if(auto* Events=GetWorld()->GetSubsystem<USceneEventSubsystem>();Events&&Events->bLevelReady&&bIncludeInitialOverlap&&bInside)Events->Request(this,TEXT("Ready"));}));}
 if(Trigger==ESceneEventTrigger::Destroyed&&IsValid(Source))Source->OnDestroyed.AddDynamic(this,&ASceneEventBinding::SourceDestroyed);
}
void ASceneEventBinding::EndPlay(const EEndPlayReason::Type Reason)
{
 if(auto* Target=Watched.Get()){Target->OnActorBeginOverlap.RemoveDynamic(this,&ASceneEventBinding::Enter);Target->OnActorEndOverlap.RemoveDynamic(this,&ASceneEventBinding::Leave);Target->OnDestroyed.RemoveDynamic(this,&ASceneEventBinding::SourceDestroyed);}
 if(auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>())S->Unregister(this);Super::EndPlay(Reason);
}
void ASceneEventBinding::Enter(AActor*,AActor* Other)
{
 auto* PC=GetWorld()->GetFirstPlayerController();if(!PC||Other!=PC->GetPawn()||bInside||!bVolumeArmed)return;bInside=true;
 if(auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>())S->Request(this);
}
void ASceneEventBinding::Leave(AActor*,AActor* Other)
{
 auto* PC=GetWorld()->GetFirstPlayerController();if(PC&&Other==PC->GetPawn()&&!PlayerInside())bInside=false;
}
void ASceneEventBinding::SourceDestroyed(AActor*){if(!GetWorld()->bIsTearingDown)if(auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>())S->Request(this,TEXT("Destroyed"));}
void ASceneEventBinding::TestSignal(){if(auto* S=GetWorld()->GetSubsystem<USceneEventSubsystem>())S->Request(this);}
