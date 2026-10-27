# Mini Meadow grass asset review

This is a development-only review. No runtime files or game code were changed.

## Candidates

The manifest and actual PNG pixels confirm that only `grass_a.png` and `grass_b.png` are seamless, opaque 16×16 grass ground tiles. Both use the same three-green palette; their individual flecks repeat every 16 pixels.

- `edge_grass_*`: boundary tiles with a second terrain material and outline. Unsuitable for continuous grass.
- `tuft.png`, bushes, flowers, mushrooms and rocks: transparent props. Unsuitable as base grass and unused.
- No quieter third continuous grass ground tile exists in this pack.

## Preview

`mini-meadow-grass-review.svg` contains three 32×18 tile panels, in order: `grass_a` only, `grass_b` only, and the current deterministic 80% A / 20% B mix.

## Finding and recommendation

The repeated appearance comes from the limited source set, not an unused base-grass candidate. The current mix reduces regularity, but cannot make an even lawn because both tiles have noticeable flecks. Choose from the preview whether to keep the mix, use just the quieter tile, or obtain additional compatible seamless grass ground tiles. No game change is recommended until that choice is made.
