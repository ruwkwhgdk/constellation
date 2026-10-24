struct SurfaceNoise {
 float hash(float2 p) { return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453); }
 float noise(float2 p) { float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y); }
 float fbm(float2 p) { return noise(p)*.57+noise(p*2.07+9)*.28+noise(p*4.13+23)*.15; }
};
SurfaceNoise n;
float2 q=float2(P.y,P.z);
float large=n.fbm(q*.16),grain=n.noise(q*7.5),chips=n.fbm(q*2.7);
float edge=min(min(abs(P.y),abs(56.4-P.y)),min(abs(P.z+40),abs(128-P.z)));
// The window perimeter is in mesh-local centimetres, so the wear rotates with the door.
float2 window=abs(q-float2(28,42.5))-float2(6.5,57);
float winDist=length(max(window,0))+min(max(window.x,window.y),0);
float seam=min(edge,abs(winDist));
float patches=smoothstep(.35,.69,n.fbm(q*.12+float2(17,3)));
float nearEdge=(1-smoothstep(.035,.25+large*.7,seam))*(.15+.85*patches);
float bottom=(1-smoothstep(-40,-15,P.z));
float rust=saturate(nearEdge*smoothstep(.41,.70,chips)*.85+bottom*smoothstep(.50,.72,large)*.65);
float lowerSeam=(1-smoothstep(.15,1.7,abs(P.z+25)))*smoothstep(.48,.7,chips);
rust=max(rust,lowerSeam*.55);
// Sparse, irregular scratches, never a uniform grunge overlay.
float2 cell=floor(q*float2(.65,.25));
float h=n.hash(cell);
float scratch=(1-smoothstep(.009,.04,abs(frac((q.x+q.y*.22)*.65)-.5)))*step(.985,h)*smoothstep(.1,.35,frac(q.y*.25))*(1-smoothstep(.65,.9,frac(q.y*.25)));
float drip=pow(n.noise(float2(q.x*2.5,1)),14)*(1-smoothstep(0,13,128-P.z));
rust=saturate(rust+drip*.5);
float3 paint=PaintColor*(.78+.34*large+.045*(grain-.5));
float3 metal=float3(.11,.12,.125)*(.72+.38*large+.07*grain);
float3 col=lerp(paint,metal,step(1.5,Finish));
float chipped=saturate(nearEdge*smoothstep(.55,.75,chips)*.35+scratch*.20);
col=lerp(col,float3(.09,.095,.095),chipped*(1-step(1.5,Finish)));
float3 oxide=lerp(float3(.035,.012,.006),float3(.12,.039,.012),chips);
col=lerp(col,oxide,rust);
float dust=(1-large)*.008+bottom*n.noise(q*.6)*.025;
col=lerp(col,float3(.21,.195,.165),dust);
float rough=lerp(.58+.12*large,.36+.17*large,step(1.5,Finish));
rough=lerp(rough,.89,rust);rough=saturate(rough+dust);
return float4(col,rough);
