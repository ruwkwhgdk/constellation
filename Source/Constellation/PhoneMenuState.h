#pragma once
#include <cstdint>

namespace PhoneMenu
{
enum class Phase { Closed, Preparing, Drawing, Camera, Open, Stowing };
// No engine timing dependency: watchdog uses real time even when the world is paused.
struct State
{
 PhoneMenu::Phase Phase=Phase::Closed;
 std::uint32_t Generation=0;
 double Deadline=0;
 bool PendingClose=false;
 static constexpr double AnimationTimeout=5.0;
 bool Active() const { return Phase!=Phase::Closed; }
 bool RequestOpen(bool Allowed,double Now)
 {
  if(Active()||!Allowed)return false;
  ++Generation;PendingClose=false;Phase=Phase::Preparing;Deadline=Now+.5;return true;
 }
 void RequestClose(bool Repeat,double Now)
 {
  if(Repeat)return;
  if(Phase==Phase::Preparing||Phase==Phase::Drawing)PendingClose=true;
  else if(Phase==Phase::Open||Phase==Phase::Camera)StartStowing(Now);
 }
 void Ready(std::uint32_t Id,double Now)
 { if(Id==Generation&&Phase==Phase::Preparing){Phase=Phase::Drawing;Deadline=Now+AnimationTimeout;} }
 void Drawn(std::uint32_t Id,double Now)
 {
  if(Id!=Generation||Phase!=Phase::Drawing)return;
  if(PendingClose)StartStowing(Now);
  else {Phase=Phase::Camera;Deadline=Now+2;}
 }
 void CameraReady(std::uint32_t Id,double)
 { if(Id==Generation&&Phase==Phase::Camera)Phase=Phase::Open; }
 void Stowed(std::uint32_t Id,double)
 { if(Id==Generation&&Phase==Phase::Stowing)Abort(); }
 void Tick(double Now)
 { if(Active()&&Phase!=Phase::Open&&Now>=Deadline)Abort(); }
 void Abort(){Phase=Phase::Closed;PendingClose=false;}
private:
 void StartStowing(double Now){Phase=Phase::Stowing;Deadline=Now+AnimationTimeout;}
};
}
