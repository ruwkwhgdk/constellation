#include "../Source/Constellation/PhoneMenuState.h"
#include <cassert>
#include <iostream>
using namespace PhoneMenu;
int main()
{
 State s;
 assert(!s.RequestOpen(false,0));
 for(int i=0;i<10;++i)
 {
  assert(s.RequestOpen(true,0)); const auto id=s.Generation;
  assert(!s.RequestOpen(true,0));
  s.Ready(id,0.1); assert(s.Phase==Phase::Drawing);
  s.Drawn(id,1); assert(s.Phase==Phase::Camera);
  s.CameraReady(id,1.4); assert(s.Phase==Phase::Open);
  s.RequestClose(true,2); assert(s.Phase==Phase::Open);
  s.RequestClose(false,2); assert(s.Phase==Phase::Stowing);
  s.Stowed(id,3); assert(s.Phase==Phase::Closed);
 }
 assert(s.RequestOpen(true,0)); auto old=s.Generation;
 s.RequestClose(false,.1); s.RequestClose(false,.1);
 s.Ready(old,.2); s.Drawn(old,1); assert(s.Phase==Phase::Stowing);
 s.Stowed(old,2); assert(s.Phase==Phase::Closed);
 s.RequestOpen(true,3); s.Ready(old,3); assert(s.Phase==Phase::Preparing);
 s.Tick(3.51); assert(s.Phase==Phase::Closed);
 s.RequestOpen(true,4); auto id=s.Generation;
 s.Ready(id,4.1); s.Tick(4.1+State::AnimationTimeout+.01);
 assert(s.Phase==Phase::Closed);
 s.RequestOpen(true,10); id=s.Generation; s.Ready(id,10.1); s.Drawn(id,11);
 s.RequestClose(false,11.1); assert(s.Phase==Phase::Stowing);
 s.Abort(); s.CameraReady(id,11.2); assert(s.Phase==Phase::Closed);
 std::cout<<"Phone menu lifecycle: all assertions passed\n";
}
