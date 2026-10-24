#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PhoneMenuState.h"
#include "PhoneMenuComponent.generated.h"
class ACharacter;
class APlayerController;
class ACameraActor;
class UAnimMontage;
class UStaticMeshComponent;
class UPhoneMenuWidget;
class UInputAction;
class UInputMappingContext;
class UEnhancedInputComponent;
class IInputProcessor;
class SWidget;
class UUserWidget;

UENUM(BlueprintType)
enum class EPhoneMenuEvent : uint8 { Grab, Drawn, Stow, Finished };

// Installation/configuration stays disabled until animation video approval.
UCLASS(ClassGroup=(Player),meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UPhoneMenuComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UPhoneMenuComponent();
 UPROPERTY(EditAnywhere,Category="Phone|Approval") bool bAnimationApproved=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Phone|Gate") bool bGameplayAllowsMenu=false;
 UPROPERTY(EditAnywhere,Category="Phone|Animation") TObjectPtr<UAnimMontage> DrawMontage;
 UPROPERTY(EditAnywhere,Category="Phone|Animation") TObjectPtr<UAnimMontage> HoldMontage;
 UPROPERTY(EditAnywhere,Category="Phone|Animation") TObjectPtr<UAnimMontage> StowMontage;
 UPROPERTY(EditAnywhere,Category="Phone|Prop") FName HandSocket=TEXT("hand_r");
 UPROPERTY(EditAnywhere,Category="Phone|Prop") FTransform PhoneOffset;
 // Baked from the approved saved preview; includes the socket's inherited scale.
 UPROPERTY(EditAnywhere,Category="Phone|Prop") TArray<FTransform> ApprovedPhoneTrack;
 UPROPERTY(EditAnywhere,Category="Phone|Camera") FVector CameraLocal=FVector(16,-8,55);
 UPROPERTY(EditAnywhere,Category="Phone|Camera") FRotator CameraRotation=FRotator(-40,-12,0);
 UPROPERTY(EditAnywhere,Category="Phone|Camera") float CameraFOV=65;
 UPROPERTY(EditAnywhere,Category="Phone|Camera") float BlendSeconds=.35f;
 UFUNCTION(BlueprintCallable,Category="Phone") void ToggleMenu();
 UFUNCTION(BlueprintCallable,Category="Phone") void CancelMenu();
 UFUNCTION(BlueprintCallable,Category="Phone") void NotifyPhoneEvent(EPhoneMenuEvent Event,int32 Token);
 UFUNCTION(BlueprintPure,Category="Phone") int32 GetMenuToken() const {return static_cast<int32>(Flow.Generation);}
 UFUNCTION(BlueprintPure,Category="Phone") bool BlocksGameplay() const {return Flow.Active();}
 bool IsOpen() const {return Flow.Phase==PhoneMenu::Phase::Open;}
 void RequestClose(bool Repeat=false);
 bool CanOpen() const;
 virtual void TickComponent(float,ELevelTick,FActorComponentTickFunction*) override;
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type) override;
private:
 friend class FPhoneMenuCleanupTest;
 bool IsEnvironmentSafe() const;
 bool Play(UAnimMontage*);
 FTransform SamplePhonePose(float SourceFrame) const;
 void UpdateAnimation();
 void ApplyPhase();
 void Cleanup();
 void BindInput();
 bool CreateCamera();
 void ReleaseMenuUI();
 bool CanReleasePause() const {return bReleasingPause;}
 UFUNCTION() void OnOwnerDamaged(AActor* DamagedActor,float Damage,const UDamageType* DamageType,AController* Instigator,AActor* Causer);
 PhoneMenu::State Flow;
 PhoneMenu::Phase Applied=PhoneMenu::Phase::Closed;
 double PhaseStarted=0;
 float LastAnimationPosition=-1.f;
 bool bLocked=false,bPaused=false,bReleasingPause=false,bOldCursor=false,bGrabbed=false;
 TWeakObjectPtr<ACharacter> Character;
 TWeakObjectPtr<APlayerController> Controller;
 TWeakObjectPtr<AActor> PreviousView;
 TWeakPtr<SWidget> PreviousFocus;
 TWeakPtr<SWidget> PreviousCaptor;
 TWeakObjectPtr<class UGameViewportClient> InputViewport;
 uint8 PreviousCaptureMode=0,PreviousLockMode=0;
 bool bMenuUIOwned=false,bCameraSettled=false;
 FDelegateHandle CameraBlendHandle;
 TSharedPtr<IInputProcessor> InputCapture;
 TWeakObjectPtr<UEnhancedInputComponent> BoundInput;
 uint32 InputBinding=0;
 UPROPERTY(Transient) TObjectPtr<UInputAction> MenuAction;
 UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MenuContext;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Phone;
 UPROPERTY(Transient) TObjectPtr<ACameraActor> MenuCamera;
 UPROPERTY(Transient) TObjectPtr<UPhoneMenuWidget> Widget;
 TMap<TWeakObjectPtr<UUserWidget>,uint8> HiddenHUD;
};
