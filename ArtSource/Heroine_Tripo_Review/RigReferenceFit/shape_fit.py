"""Landmark fit to the existing heroine, in the source's approximately 1 m space."""
import math
from mathutils import Vector
def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)
def old_fit_point(p):
 q=p.copy();w=smooth((abs(p.x)-.028)/.072)*smooth((p.z-.69)/.080)
 q.x-=math.copysign(.024*w,p.x);q.z-=.008*w;return q
Z=[0,.055,.286,.466,.55,.61,.673,.728,.778,.818,.84,1.0]
V=[0,.055,.309,.497,.577,.635,.693,.746,.800,.838,.8576,1.0]
S=[(V[i+1]-V[i])/(Z[i+1]-Z[i]) for i in range(len(Z)-1)]
D=[S[0]]+[(S[i-1]+S[i])/2 for i in range(1,len(S))]+[.89]
def zfit(z):
 if z<=0:return z
 if z>=1:return 1+(z-1)*.89
 i=next(i for i in range(len(Z)-1) if z<=Z[i+1]);h=Z[i+1]-Z[i];t=(z-Z[i])/h
 return (2*t**3-3*t*t+1)*V[i]+(t**3-2*t*t+t)*h*D[i]+(-2*t**3+3*t*t)*V[i+1]+(t**3-t*t)*h*D[i+1]
def warp_point(p,cloth=False,hair=False):
 x,y,z=p;ax=abs(x);q=Vector((x,y,zfit(z)))
 waist=smooth((z-.54)/.09)*(1-smooth((z-.71)/.06))
 q.x=x*(.96-.055*waist)
 q.y=.006+(y-.006)*(1.0+.10*smooth((z-.46)/.09)*(1-smooth((z-.72)/.06)))
 arm=smooth((ax-.035)/.065)*smooth((z-.70)/.06)
 dx=(.006+.006*smooth((ax-.08)/.24))*smooth((ax-.035)/.05)
 q.x=q.x*(1-arm)+math.copysign(ax-dx,x)*arm
 q.z-=.010*smooth((ax-.10)/.24)*arm
 if cloth:
  puff=smooth((ax-.052)/.065)*(1-smooth((ax-.27)/.065))*smooth((z-.71)/.06)
  q.z+=(z-.778)*.24*puff
  q.y+=(y-.006)*.18*puff
 h=smooth((z-.805)/.035)
 head=Vector((x*.89,y*.89,1-(1-z)*.89))
 q=q.lerp(head,h)
 if hair:q.y+=.015*smooth((y-.015)/.055)*smooth((z-.805)/.055)*(1-smooth((z-.965)/.035))
 return q
