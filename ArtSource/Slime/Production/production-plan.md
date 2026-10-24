# Slime approved concept 02 production

Approved design: ../../Concepts/2026-10-13/slime-form-refinement-02.png

Deliver an editable Blender model, skinned FBX with a four-second Idle loop,
and rendered views/video. Work only in this new production directory.
Do not replace game resources during this modeling review.

1. Build a smooth joined dome, liquid crest and flowing foot silhouette;
   project two circular eye patches onto the front. Keep the approved purple palette.
2. Rig body, crest and separate droplet geometry with exportable deform bones.
   Animate a slow body pulse, delayed crest movement, droplet growth, fall and
   shallow spreading/absorption. Keep the floor contact and loop boundary stable.
3. Render front, side and three-quarter views and a complete repeated Idle loop.
   Review silhouette, eyes, seam visibility and actual motion before delivery.
4. Export FBX, reimport in a fresh Blender process, and check scale, animation,
   skinning, mesh counts, finite coordinates and loop closure. Record limitations.

Existing source bounds from Saved/VFXImplementation/slime-contact-audit.json:
192.60 x 182.10 x 168.24 cm, centered pivot near z=0. Game actor/component
scale and offsets differ by use. New source uses meters, floor pivot and -Y front.
Its new rig is not claimed to be compatible with the old skeleton or ABP.
Match engine pivot/orientation and retarget old non-Idle clips during replacement.
