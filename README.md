# Vietnamese Fables 2D Animation Engine
A code-first, reusable **real frame animation** pipeline for Vietnamese fables. The included 64-second “Ếch ngồi đáy giếng” demo uses a multipart SVG frog rig, breathing/blinking/head/mouth/jump/emotion animation, animated water/clouds, ten directed shots, six camera behaviors, transitions, Vietnamese voice and subtitles. It is not a slideshow.

## Requirements and setup
Node 20+, npm, Python 3, Chromium (Remotion downloads one when needed), and network access for Edge TTS. FFmpeg is embedded/downloaded by Remotion, so a system FFmpeg is optional.
```bash
npm install
python3 -m pip install edge-tts
npm run validate -- episodes/001-ech-ngoi-day-gieng
npm run voice -- episodes/001-ech-ngoi-day-gieng
npm run timeline -- episodes/001-ech-ngoi-day-gieng
npm run preview -- episodes/001-ech-ngoi-day-gieng
npm run render -- episodes/001-ech-ngoi-day-gieng
# complete pipeline
npm run episode -- 001-ech-ngoi-day-gieng --voice edge
```
Output is `output/001-ech-ngoi-day-gieng/demo.mp4`. Voice audio is deliberately ignored; small timeline/subtitle metadata remains as reproducible documentation.

## Render on GitHub Actions

GitHub Actions is optional: use it when your local machine cannot access npm/PyPI,
does not have enough render capacity, or when you want a repeatable CI render. The
workflow is manual so that ordinary pushes do not unexpectedly consume runner
minutes.

1. Push this repository to GitHub. Commit `package-lock.json` once npm can create
   it, then change the workflow install command from `npm install` to `npm ci`.
2. Open **Actions → Render fable demo → Run workflow**.
3. Keep `001-ech-ngoi-day-gieng` and `edge`, then start the run.
4. After the `render` job succeeds, download the
   `001-ech-ngoi-day-gieng-render` artifact from the workflow run summary.

The artifact contains `demo.mp4`, `timeline.json`, `subtitles.json`, and
`subtitles.srt`. Edge TTS needs outbound network access but no API secret. Future
paid providers should read credentials from GitHub Actions secrets, never from
YAML or committed files. The workflow deliberately runs validation, tests, and
type checking before spending time rendering.

## Design
YAML is the source of directing intent. Zod validates it; Edge voice files are measured; the compiler derives dialogue, shot, subtitle and heuristic lip-sync timing; Remotion resolves it to frames. Replacing a voice therefore needs no hand animation edits:
```bash
npm run voice -- episodes/001-ech-ngoi-day-gieng --provider elevenlabs
npm run rebuild-timeline -- episodes/001-ech-ngoi-day-gieng
npm run render -- episodes/001-ech-ngoi-day-gieng
```
Implement the provider contract in `src/engine/tts/types.ts` and register it in the CLI (ElevenLabs is intentionally not bundled).

See [architecture](docs/architecture.md), [YAML](docs/yaml-schema.md), [characters](docs/character-system.md), [animation](docs/animation-system.md), [voice](docs/voice-pipeline.md), and [adding an episode](docs/adding-an-episode.md). HyperFrames was not added: Remotion already covers title/lesson motion and avoiding a second renderer keeps the vertical slice reliable. Current demo art/SFX are procedural and intentionally simple; future work should add phoneme visemes, richer rain/particles, a mixer/ducking module and more character rigs.
