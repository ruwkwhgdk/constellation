# Painted mineral texture

Built-in image_gen tool, 2026-09-28. Generated source: `Textures/painted_mineral.png` (1254×1254). Unreal builds a 1024×1024 texture with averaged mipmaps. No CLI/API fallback. This is a new surface bitmap, not a replacement reference-scene image.

## Exact generation prompt

Create one seamless tileable game albedo texture, square 1024x1024 or larger. Hand-painted old mineral plaster over stone for the walls and tall columns of a lush abandoned cathedral in a warm Japanese animated feature background painting. Orthographic flat surface swatch filling entire image, no scene, no objects, no text, no borders. Muted desaturated blue-gray and pale warm ivory gray mineral paint, subtle pale sage undertones. Large quiet areas covering 70 percent, layered broad gouache brush shapes and a few irregular softly edged pale chipped paint patches covering 20 percent, restrained thin vertical rain-wash stains 10 percent. Carefully designed low contrast painterly pigment variation, visible broad painted brushwork, no grainy photographic noise, no pores, no intense black cracks, no camouflage pattern, NO green moss, no foliage, no brick grid, no masonry joints. Uniform flat ambient illumination, no shadows or highlights baked in, useful physically based base color texture. Edges must tile seamlessly horizontally and vertically. Quiet luminous stylized hand-painted texture; preserve broad smooth mineral color masses rather than photorealistic grit.

## Runtime use

Three world-space projections blended by geometric normal, 330cm repeat for architecture and 240cm for floor. Muted blue-gray pigment multiplied in material. Reduced separate procedural moss layer weighted toward low surfaces and upward ledges. No new normal texture. Original Tripo textures remain available; foliage uses its original UV/color texture with lower-frequency sampling and leaf-selective palette remapping, not this stone swatch.

Tileability is a generation target, not a guarantee of exact pixel-level edge continuity. The actual scene render is the visual acceptance evidence.
