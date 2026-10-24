#include "../Source/Constellation/FallMath.h"
#include <cstdio>
#include <cmath>
#include <limits>
int main()
{
 int failed=0;auto check=[&](bool ok,const char* name){if(!ok){++failed;std::printf("FAIL %s\n",name);}};
 FallMath::Settings s;
 auto eval=[&](double h){return FallMath::Evaluate(h,s);};
 check(eval(319).Tier==0,"small ledge has no recovery");
 check(eval(320).Tier==1&&eval(320).DamageRatio==0,"two heights normal landing");
 check(eval(959.99).Tier==1,"below six heights no damage");
 check(eval(960).Tier==2&&std::abs(eval(960).DamageRatio-.05)<1e-8,"six heights five percent");
 check(std::abs(eval(1440).DamageRatio-.075)<1e-8,"weak interpolation");
 check(eval(1920).Tier==3&&std::abs(eval(1920).DamageRatio-.1)<1e-8,"twelve heights ten percent");
 check(std::abs(eval(2880).DamageRatio-.55)<1e-8,"eighteen heights fifty five percent");
 check(eval(3840).DamageRatio==1&&eval(5000).DamageRatio==1,"twenty four heights capped");
 check(eval(-1).Tier==0&&eval(std::numeric_limits<double>::quiet_NaN()).Tier==0,"invalid height safe");
 s.Height=0;check(eval(1000).Tier==0,"invalid settings safe");s=FallMath::Settings{};
 check(FallMath::AppliedDamage(300,300,1)==299,"full health leaves one");
 check(FallMath::AppliedDamage(300,10,.1)==9,"low health leaves one");
 check(FallMath::AppliedDamage(300,1,1)==0,"one HP no further damage");
 check(FallMath::AppliedDamage(300,0,1)==0,"dead actor not resurrected");
 check(FallMath::AppliedDamage(300,.5,1)==0,"fractional low health not healed");
 check(std::abs(FallMath::AppliedDamage(300,300,.075)-22.5)<1e-8,"fractional HP preserved");
 FallMath::Tracker t;double height=0;
 check(!t.Land(0,height),"untracked landing ignored");t.Begin(100);t.Sample(700);t.Sample(650);
 check(t.Land(200,height)&&height==500,"peak used instead of starting height");
 check(!t.Land(200,height),"landing consumed once");t.Begin(1000);t.Reset();check(!t.Land(0,height),"teleport cancellation");
 std::printf("Fall math: %d failures\n",failed);return failed?1:0;
}
