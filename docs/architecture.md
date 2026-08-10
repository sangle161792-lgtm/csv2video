# Architecture
`episode.yaml → Zod validation → TTS provider → audio duration analysis → semantic timeline compiler → timeline.json/SRT/lip-sync → Remotion composition → MP4`.
The frame is the only animation clock, making rendering deterministic. `src/library` owns reusable rigs, environments, cameras, typography and future effects/audio components.
