[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/OG2BIT001/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/OG2BIT001/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

# Velmara — The Poster for a Place That Isn't There

A program that draws a travel poster for an invented place and writes it
to `/output/entry.png`.

## The place

**Velmara — the Isles Above the Clouds.** A chain of floating islands
drifting above a sea of cloud at dusk. The poster's one landmark is the
great island's beacon spire, its lamp lit, a red pennant flying. A ringed
planet hangs in the violet sky, the sun sinks low on the left, and a
waterfall pours off the island's edge into the clouds below.

## Run it

```sh
python3 main.py
```

Writes `/output/entry.png`: a 768×1024 PNG, about 115 KB — inside the
competition's caps (at most 1,048,576 bytes, at most 1024×1024 pixels).

## How it is drawn

Pure Python standard library only — `zlib`, `struct`, `math`, `random`.
There is no Pillow, no numpy, no third-party package and no network: the
grader's sandbox installs nothing, so the program rasterises the whole
scene itself (sky gradient, stars, sun glow, ringed planet, island,
waterfall, value-noise cloud sea, a hand-built 5×7 block font for the
lettering) and encodes the PNG by hand with `zlib`.

The output is deterministic: every run writes byte-identical output
(verified — same SHA-256 across runs).

## License

MIT. See `LICENSE`.
