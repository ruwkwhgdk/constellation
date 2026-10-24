#pragma once
#include <algorithm>
#include <cmath>

namespace FallMath
{
struct Settings { double Height=160,Normal=2,Weak=6,Strong=12,Maximum=24; };
struct Result { int Tier=0; double DamageRatio=0; };
inline Result Evaluate(double Distance,const Settings& S)
{
 if(!std::isfinite(Distance)||!std::isfinite(S.Height)||!std::isfinite(S.Normal)||!std::isfinite(S.Weak)||!std::isfinite(S.Strong)||!std::isfinite(S.Maximum)
    ||S.Height<=0||S.Normal<=0||S.Weak<=S.Normal||S.Strong<=S.Weak||S.Maximum<=S.Strong) return {};
 const double H=Distance/S.Height;
 if(H<S.Normal)return {};
 if(H<S.Weak)return {1,0};
 if(H<S.Strong)return {2,.05+.05*(H-S.Weak)/(S.Strong-S.Weak)};
 return {3,.1+.9*std::clamp((H-S.Strong)/(S.Maximum-S.Strong),0.0,1.0)};
}
inline double AppliedDamage(double MaxHP,double CurrentHP,double Ratio)
{
 if(!std::isfinite(MaxHP)||!std::isfinite(CurrentHP)||!std::isfinite(Ratio)||MaxHP<=0||CurrentHP<=1)return 0;
 return std::min(CurrentHP-1,MaxHP*std::clamp(Ratio,0.0,1.0));
}
struct Tracker
{
 bool Active=false;double Peak=0;
 void Begin(double Height){Active=std::isfinite(Height);Peak=Active?Height:0;}
 void Sample(double Height){if(Active&&std::isfinite(Height))Peak=std::max(Peak,Height);}
 void Reset(){Active=false;Peak=0;}
 bool Land(double Height,double& Distance)
 {
  if(!Active||!std::isfinite(Height)){Reset();return false;}
  Distance=std::max(0.0,Peak-Height);Reset();return true;
 }
};
}
