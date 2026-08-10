# Báo cáo trạng thái — Vietnamese Fables 2D Animation Engine

> Cập nhật: 2026-08-10  
> Episode thử nghiệm: `001-ech-ngoi-day-gieng`  
> Trạng thái tổng thể: **prototype source code, chưa có bản render được xác minh**

## 1. Mục tiêu của dự án

Dự án hướng tới một animation engine 2D có thể tái sử dụng lâu dài để sản
xuất series truyện ngụ ngôn Việt Nam, thay vì viết riêng một video cho mỗi tập.

Các mục tiêu chính:

1. Dùng TypeScript, React, Remotion, SVG và YAML để tạo hoạt hình theo từng
   frame một cách deterministic.
2. Tách nội dung và ý đồ đạo diễn của từng episode khỏi implementation của
   engine. Story, dialogue, shot, camera và semantic action phải nằm trong YAML.
3. Xây thư viện có thể tái sử dụng gồm character rig, environment, prop,
   animation, camera, transition, typography và audio.
4. Hỗ trợ nhân vật có rig gồm nhiều bộ phận có thể chuyển động độc lập, không
   dùng ảnh tĩnh hoặc slideshow để thay thế hoạt hình.
5. Tạo voice tự động, đo duration audio và biên dịch timeline, subtitle và
   lip-sync metadata từ source YAML và audio.
6. Cho phép thay nhà cung cấp TTS hoặc thay voice mà không phải viết lại
   animation theo frame bằng tay.
7. Cung cấp workflow end-to-end từ validate, voice, timeline, preview đến
   render MP4.
8. Chứng minh pipeline bằng demo 60–90 giây cho truyện **Ếch ngồi đáy giếng**.

## 2. Definition of Done của demo

Demo chỉ được coi là hoàn thành khi có thể xác minh tất cả các điểm sau:

- YAML validate thành công bằng CLI của dự án.
- Edge TTS tạo được voice tiếng Việt thật.
- Timeline được rebuild từ duration audio thật.
- SRT và subtitle JSON được tạo từ compiled timeline.
- Remotion composition bundle và preview được.
- Frog có rig nhiều bộ phận và có blink, idle/breathing, head movement, jump,
  talk/lip movement và ít nhất một emotion/reaction.
- Có nhiều shot, nhiều camera composition/movement và transition.
- Environment có ambient animation.
- Voice, subtitle, SFX và audio mixing hoạt động trong video.
- Test và TypeScript typecheck chạy thành công.
- Render MP4 thành công và được kiểm tra trực quan.
- File cuối tồn tại tại `output/001-ech-ngoi-day-gieng/demo.mp4`.
- Một episode khác có thể render mà không hard-code story ID vào engine.

## 3. Những gì đã làm được

### 3.1. Cấu trúc dự án và source episode

- Đã thêm project TypeScript/React/Remotion với các command dự kiến trong
  `package.json`.
- Đã tạo `episode.yaml` cho demo gồm 10 shot, tổng duration khai báo 64 giây.
- YAML có dialogue ID, speaker, camera shot/movement, environment và semantic
  action như `idle`, `blink`, `look_up`, `jump`, `talk`, `proud`, `surprised`.
- Đã thêm Zod schema và loader để parse/validate episode source.

### 3.2. Character prototype

- Đã tạo Frog bằng SVG code, không dùng AI image generation.
- Frog có các group riêng cho legs, body, arms, head, eyes và mouth.
- Đã viết biểu thức animation deterministic theo frame cho breathing, blink,
  jump, head rotation, mouth movement, proud pose và surprised expression.

### 3.3. Camera, environment và subtitle prototype

- Đã tạo camera component với `static`, `pan`, `tilt`, `push_in`, `pull_out`,
  `follow` và `shake`.
- Đã tạo environment vector/procedural cho village, well và outside, có cloud
  movement và water ripple đơn giản.
- Đã tạo subtitle overlay có safe margin, background và text shadow cơ bản.

### 3.4. Timeline và lip-sync metadata prototype

- Đã viết timeline compiler có thể đọc duration audio bằng `music-metadata`
  nếu audio tồn tại.
- Compiler tính shot/dialogue start, end và duration.
- Đã viết output cho `timeline.json`, `subtitles.json` và `subtitles.srt`.
- Đã có heuristic lip-sync bốn trạng thái: `closed`, `small`, `medium`, `wide`.
- Repository có metadata mẫu để mô tả shape của generated output.

### 3.5. TTS và CLI prototype

- Đã định nghĩa interface `TTSProvider`, `TTSInput` và `TTSResult`.
- Đã viết `EdgeTTSProvider` dùng voice nữ `vi-VN-HoaiMyNeural`.
- Đã thêm CLI prototype cho `validate`, `voice`, `timeline`, `preview`,
  `render` và `episode`.

### 3.6. Test, documentation và CI skeleton

- Đã thêm test source cho YAML validation, invalid action, seconds-to-frame,
  lip-sync states và timeline ordering.
- Đã thêm tài liệu kiến trúc, YAML, character, animation, voice và cách thêm
  episode.
- Đã thêm GitHub Actions workflow chạy thủ công, dự kiến cài dependency,
  generate voice, validate, test, typecheck, render và upload artifact.
- Đã thêm `AGENTS.md` để yêu cầu tái sử dụng component và không hard-code story
  content vào engine.

## 4. Những gì mới làm một phần

| Hạng mục | Đã có | Còn thiếu |
|---|---|---|
| YAML-driven episode | Episode và schema cơ bản | Model actor/prop/layout/cue đầy đủ và error suggestion |
| Semantic animation | Tên action và một số state trong Frog | Resolver cho `start`, `end`, `at`, `duration` và dialogue-relative timing |
| Frog rig | SVG groups và motion formulas | Pose mixer, action registry, walk/turn/look-at/enter/exit và staging tốt hơn |
| Camera | Preset transform cơ bản | Target thật, actor tracking, framing và parallax |
| Environment | Một component procedural | Registry/layers, rain, foreground/midground/background và reusable props |
| Lip-sync | Timing heuristic | Phân tích waveform/amplitude hoặc phoneme/viseme |
| Voice replacement | Interface và duration-aware compiler | CLI dùng provider registry thật và metadata/checksum/provider config |
| Subtitle | SRT/JSON và overlay cơ bản | Line breaking, font Vietnamese, theme và collision/safe-area logic |
| Audio | Audio dialogue trong composition | Mixer abstraction, ducking, ambience, music và SFX cues |
| CI | Workflow YAML | Một GitHub Actions run thành công và artifact MP4 đã kiểm tra |
| Tests | Một số unit test source | Missing asset, provider, auto timing, bundle, frame render và MP4 smoke tests |

## 5. Những gì chưa làm được hoặc chưa được xác minh

### 5.1. Chưa có deliverable cuối

- Chưa có Edge TTS audio thật trong episode.
- Chưa có MP4 tại `output/001-ech-ngoi-day-gieng/demo.mp4`.
- Chưa có video để review animation, composition, subtitle sync hoặc audio.
- Chưa chứng minh output trông như hoạt hình thay vì một composition sơ sài.

### 5.2. Chưa xác minh runtime

- Trong môi trường triển khai ban đầu, `npm install`, PyPI và apt bị proxy trả
  HTTP 403.
- Vì dependency không được cài trong lần triển khai đó, chưa có bằng chứng đáng
  tin rằng TypeScript typecheck, Vitest, Remotion bundle, preview và render đã
  chạy thành công.
- Workflow GitHub Actions mới chỉ được cấu hình; repository chưa lưu kết quả
  của một workflow run thành công.

### 5.3. Còn hard-code làm giảm reuse

- `src/index.tsx` import trực tiếp timeline và episode path của episode 001.
- `Composition.tsx` suy luận title card từ tên shot chứa `title` hoặc environment
  có giá trị `lesson`.
- CLI gọi trực tiếp `python3 -m edge_tts`, chưa sử dụng `TTSProvider` đã định
  nghĩa.
- Environment đang là một component có nhánh điều kiện thay vì registry.
- Camera `follow` là motion formula, chưa follow actor target thật.
- Action trong composition chỉ được bật theo sự tồn tại; các trường timing như
  `at`, `start`, `end`, `duration` chưa được resolve.

### 5.4. Voice replacement chưa đạt yêu cầu

- Compiler chỉ kéo shot theo audio khi shot dùng `duration: auto`.
- Demo hiện dùng duration số cố định cho tất cả shot.
- Voice dài hơn có thể bị giới hạn vào cuối shot thay vì làm các shot tiếp theo
  dịch chuyển đúng cách.
- Chưa có implementation ElevenLabs/OpenAI/Google/Azure; đây là mục tiêu mở
  rộng, không phải tính năng hiện có.

### 5.5. Animation và production feature còn thiếu

- Chưa có rain animation đầy đủ.
- Chưa có splash/landing/transition SFX hoạt động.
- Chưa có background music và automatic ducking.
- Chưa có actor registry, prop system hoặc nhiều nhân vật.
- Chưa có walk/run/action blending.
- Chưa có transition library thực sự; mới có fade logic đơn giản.
- Chưa có automated visual regression hoặc screenshot/frame smoke test.

## 6. Đánh giá tính khả thi

### 6.1. Demo 60–90 giây

**Khả thi cao về mặt công nghệ.** Remotion phù hợp cho deterministic rendering,
React/SVG phù hợp cho vector rig đơn giản, còn YAML và compiled timeline phù hợp
cho content-driven production. Phạm vi demo một nhân vật và khoảng 10 shot là
hợp lý.

Tuy nhiên tính khả thi chỉ được chứng minh khi có voice thật, bundle thành công
và MP4 được xem trực quan. Source code hiện tại chưa đủ để kết luận chất lượng
đầu ra.

### 6.2. Series nhiều episode

**Khả thi có điều kiện.** Engine chỉ mang lại lợi ích dài hạn nếu episode mới
không cần sửa code theo story ID. Cần hoàn thành registry cho character,
environment và shot layout; action timing resolver; pose mixer; camera target;
audio mixer; dynamic Remotion input props và test pipeline.

Khả năng reuse hiện tại ở mức thấp đến trung bình. Utility time, schema,
subtitle và ý tưởng camera có thể reuse; composition, episode loading, voice
wiring, character action và environment vẫn gắn chặt với demo đầu tiên.

## 7. Việc cần làm tiếp theo

### Ưu tiên 0 — Có video thật

1. Cài dependency và tạo/commit `package-lock.json`.
2. Chạy `npm run typecheck`, `npm test` và sửa toàn bộ lỗi.
3. Sửa Remotion entry để nhận episode/timeline qua input props.
4. Cho CLI sử dụng `TTSProvider` registry thay vì gọi Edge trực tiếp.
5. Generate Edge TTS thật.
6. Chuyển các shot có dialogue sang auto/minimum duration phù hợp.
7. Rebuild timeline và subtitle từ audio thật.
8. Render MP4, kiểm tra duration bằng `ffprobe` và xem toàn bộ video.

### Ưu tiên 1 — Đạt chất lượng demo

1. Thêm rain, splash, landing và ambience.
2. Thêm audio mixer và music ducking.
3. Cải thiện anticipation, jump arc, landing squash và facial acting.
4. Cải thiện shot composition, parallax và transition.
5. Kiểm tra subtitle safe area, font và sync.

### Ưu tiên 2 — Chứng minh reuse

1. Thêm character/environment/layout registry.
2. Thêm semantic action resolver và pose mixer.
3. Thêm actor positioning và camera target/follow thật.
4. Tạo episode thứ hai có ít nhất hai nhân vật.
5. Xác nhận episode thứ hai render mà không thêm điều kiện theo story ID trong
   engine.

## 8. Cách chạy dự kiến

### Local

```bash
npm install
python3 -m pip install edge-tts
npm run validate -- episodes/001-ech-ngoi-day-gieng
npm run voice -- episodes/001-ech-ngoi-day-gieng --provider edge
npm run timeline -- episodes/001-ech-ngoi-day-gieng
npm run preview -- episodes/001-ech-ngoi-day-gieng
npm run render -- episodes/001-ech-ngoi-day-gieng
```

### GitHub Actions

1. Mở tab **Actions** trong GitHub repository.
2. Chọn **Render fable demo**.
3. Chọn **Run workflow**.
4. Dùng episode `001-ech-ngoi-day-gieng` và provider `edge`.
5. Nếu job thành công, tải artifact `001-ech-ngoi-day-gieng-render`.

## 9. Kết luận

Dự án hiện đã có một số building block đúng hướng, nhưng mới ở trạng thái
prototype. Kết quả hiện tại không đáp ứng Definition of Done vì chưa có voice
thật và chưa có MP4 được render, kiểm tra và xem trực quan.

Milestone tiếp theo không nên là thêm nhiều abstraction hoặc tài liệu. Milestone
phải là một vertical slice chạy thật:

```text
YAML → Edge TTS thật → audio duration → timeline/SRT → Remotion → MP4
```

Sau đó cần làm episode thứ hai mà không sửa engine theo story ID để chứng minh
khả năng tái sử dụng.
