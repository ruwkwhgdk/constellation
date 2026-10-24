struct HeightNoise {
 float hash(float2 p) { return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453); }
 float noise(float2 p) { float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y); }
};
HeightNoise n;
float2 q=P.yz;
float lower=1-smoothstep(-35,15,P.z);
float pits=n.noise(q*2.9),grain=n.noise(q*11.3);
float height=(pits-.5)*(.045+.12*lower)+(grain-.5)*.025;
float3 dpdx=ddx(W),dpdy=ddy(W);
float3 normal=normalize(N);
float3 r1=cross(dpdy,normal),r2=cross(normal,dpdx);
float det=dot(dpdx,r1);
float3 grad=sign(det)*(ddx(height)*r1+ddy(height)*r2);
return normalize(max(abs(det),.000001)*normal-grad);
