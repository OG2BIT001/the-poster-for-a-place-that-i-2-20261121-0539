# Build session

## Who built it

OG2BIT, a Muse Spark agent, for Mateo — entry for the make.fun bounty
"The Poster for a Place That Isn't There"
(`the-poster-for-a-place-that-i-2-20261121-0539`, $50). Built in one
session from the kit at
`~/workspace/makefun-bounties/kits/the-poster-for-a-place-that-i-2-20261121-0539/the-poster-for-a-place-that-i-2-20261121-0539-kit/`
(`competition.yaml` and `RULES.txt` read in full before building).

## The image idea

**Velmara — the Isles Above the Clouds.** An invented floating-island
destination at dusk, drawn as a vintage travel poster:

- A dusk sky grading from deep indigo through violet and rose to amber,
  with stars overhead.
- One landmark: a great floating island with a meadow cap, pine trees and
  a tall beacon spire, lamp lit, red pennant flying; a waterfall pours off
  the island's edge into the cloud sea below.
- A ringed planet in the upper sky, a low sun on the left, a few birds.
- The place name **VELMARA** set large in cream block capitals across the
  sky, with the line "ISLES ABOVE THE CLOUDS" beneath it — the only copy
  on the poster (no quotes, no ratings).
- A double cream art-deco frame.

## How it was built

`main.py` (Python 3, standard library only) rasterises the scene itself
and hand-encodes the PNG with `zlib` — no Pillow, no numpy, no network,
because the grader's sandbox installs nothing. The lettering uses a
hand-built 5×7 block font. Everything was written in-session; no image or
program was fetched or copied from anywhere.

## Revision

First version rendered and inspected visually, then revised in-session:
the subtitle was unreadable where it crossed the pale planet (given a dark
drop shadow and a deeper gold), a small second islet that crowded the sun
was removed, the sun's glow was smoothed from 5 stepped rings to 8, and
the island's right rock facet was narrowed.

## Verification

- `python3 main.py` runs in ~1 s and writes `/output/entry.png`.
- Output: 768×1024 PNG, 115,541 bytes — inside the caps (≤1,048,576
  bytes, ≤1024×1024 px).
- PNG structure verified: signature, IHDR (768×1024, 8-bit RGB), IDAT
  decompresses to exactly 2,360,320 scanline bytes, all filter bytes zero.
- Run twice: byte-identical output, SHA-256
  `a3e666ce80079234bfebfd70403f181df9490d617c5113019aafce500cd6424e`
  on both runs.
- Imports are stdlib only (`hashlib`, `math`, `os`, `random`, `struct`,
  `sys`, `zlib`); grep confirms no PIL/numpy import.

## Files

- `main.py` — the program (15,600 bytes)
- `README.md` — this entry, how to run it (no badge lines)
- `LICENSE` — MIT, with the literal `SPDX-License-Identifier: MIT` line
- `SESSION.md` — this file
