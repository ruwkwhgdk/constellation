#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SchoolGateOpeningComponent.generated.h"
class ACharacter; class APlayerController; class UAnimMontage; class UAudioComponent; class USceneComponent;
UCLASS(ClassGroup=(Interaction),meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API USchoolGateOpeningComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 USchoolGateOpeningComponent();
 UFUNCTION(BlueprintCallable,Category="School Gate") static bool BeginOpening(AActor* Gate,AActor* Interactor);
 UFUNCTION(BlueprintPure,Category="School Gate") static float OpeningAngle(float Seconds);
 UPROPERTY(BlueprintReadOnly) bool bOpening=false;
 UPROPERTY(BlueprintReadOnly) bool bCompleted=false;
 UPROPERTY(BlueprintReadOnly) bool bCharacterReleased=false;
 UPROPERTY(BlueprintReadOnly) float PlaybackSeconds=0;
 virtual void TickComponent(float,ELevelTick,FActorComponentTickFunction*) override;
 virtual void EndPlay(const EEndPlayReason::Type) override;
private:
 bool Start(ACharacter*);
 void Finish(bool bInterrupted);
 void ReleaseCharacter(bool bInterrupted);
 void ApplyAngle(float);
 UPROPERTY() TObjectPtr<ACharacter> Character;
 UPROPERTY() TObjectPtr<APlayerController> Controller;
 UPROPERTY() TObjectPtr<UAnimMontage> Montage;
 UPROPERTY() TObjectPtr<UAudioComponent> Audio;
 UPROPERTY() TObjectPtr<USceneComponent> Left;
 UPROPERTY() TObjectPtr<USceneComponent> Right;
 bool bInputWasEnabled=false,bUseControllerYaw=false,bOrientToMovement=false,bUseDesiredRotation=false;
 bool bMoveLock=false,bLookLock=false;
 float Elapsed=0;
 float PushRadius=446.f,LeafHalfThickness=25.7175f;
 FVector StartLocation,TravelDirection;
};
