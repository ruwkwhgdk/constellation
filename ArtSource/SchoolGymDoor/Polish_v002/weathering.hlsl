struct SurfaceNoise {
 float hash(float2 p) { return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453); }
 float noise(float2 p) { float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y); }
 float fbm(float2 p) { return noise(p)*.57+noise(p*2.07+9)*.28+noise(p*4.13+23)*.15; }
};
SurfaceNoise n;
float2 q=float2(P.y,P.z);
float large=n.fbm(q*.16),grain=n.noise(q*7.5),chips=n.fbm(q*2.7);
float edge=min(min(abs(P.y),abs(56.4-P.y)),min(abs(P.z+40),abs(128-P.z)));
float2 window=abs(q-float2(28,42.5))-float2(6.5,57);
float winDist=length(max(window,0))+min(max(window.x,window.y),0);
float seam=min(edge,abs(winDist));
float patches=smoothstep(.32,.68,n.fbm(q*.12+float2(17,3)));
float nearEdge=(1-smoothstep(.04,.45+large*.95,seam))*(.12+.88*patches);
float bottom=1-smoothstep(-40,-4,P.z);
float lowerZone=1-smoothstep(-15,35,P.z);
float handleWear=1-smoothstep(0,1,length((q-float2(46,48))/float2(8,23)));

// Irregular flaked islands with a narrow undercoat rim, concentrated below and near contact areas.
float flakes=n.fbm(q*.92+float2(5,21));
float threshold=.80-.13*lowerZone-.08*handleWear-.10*nearEdge+.045*(1-patches);
float flake=smoothstep(threshold,threshold+.052,flakes);
float primer=smoothstep(threshold-.026,threshold+.015,flakes);
float rust=saturate(nearEdge*smoothstep(.38,.66,chips)*.85+bottom*smoothstep(.38,.67,large)*.9+flake*(.25+.65*lowerZone));
float lowerSeam=(1-smoothstep(.12,1.6,abs(P.z+25)))*smoothstep(.37,.65,chips);
rust=max(rust,lowerSeam*.72);

// Independent randomized short scratches per cell: no repeated diagonal hatch.
float2 cell=floor(q/float2(3.7,6.3));
float seed=n.hash(cell),angle=n.hash(cell+17)*6.283185;
float2 s=frac(q/float2(3.7,6.3))-.5;
s-=float2(n.hash(cell+7),n.hash(cell+29))*.3-.15;
float2 r=float2(dot(s,float2(cos(angle),sin(angle))),dot(s,float2(-sin(angle),cos(angle))));
float scratch=(1-smoothstep(.004,.012,abs(r.x)))*(1-smoothstep(.08+.12*seed,.18+.14*seed,abs(r.y)))*step(.72,seed);
float hairline=(1-smoothstep(.002,.006,abs(r.x+.08)))*(1-smoothstep(.04,.16,abs(r.y+.09)))*step(.88,seed);
scratch=saturate(scratch+hairline*.45);

float drip=pow(n.noise(float2(q.x*1.7,1)),9)*(1-smoothstep(0,17,128-P.z));
float lowerStain=bottom*smoothstep(.32,.67,n.fbm(float2(q.x*.3,q.y*.075)+11));
float runoff=pow(n.noise(float2(q.x*1.1,3)),7)*(1-smoothstep(-25,8,P.z))*.4;
rust=saturate(rust+drip*.45+runoff);
float3 paint=PaintColor*(.68+.48*large+.09*(grain-.5));
float3 metal=float3(.11,.12,.125)*(.63+.47*large+.12*grain);
float isMetal=step(1.5,Finish);
float3 col=lerp(paint,metal,isMetal);
float chip=saturate(primer*.8+nearEdge*smoothstep(.52,.72,chips)*.5);
col=lerp(col,float3(.035,.039,.037),chip*(1-isMetal));
col=lerp(col,float3(.058,.063,.066),flake*(1-isMetal));
float3 oxide=lerp(float3(.038,.014,.007),float3(.19,.069,.021),chips);
col=lerp(col,oxide,rust*.9);
col=lerp(col,float3(.022,.018,.013),lowerStain*.32);
col=lerp(col,float3(.13,.14,.145),scratch*.42*(1-rust*.65));
float dust=(1-large)*.015+lowerZone*n.noise(q*.6)*.055;
col=lerp(col,float3(.18,.165,.14),dust);
float rough=lerp(.61+.16*large,.41+.22*large,isMetal);
rough=lerp(rough,.92,saturate(rust+lowerStain*.25));
rough=lerp(rough,.42,scratch*.5);rough=saturate(rough+dust);
return float4(col,rough);

