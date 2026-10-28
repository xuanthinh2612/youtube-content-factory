# Hướng dẫn chuyên biệt tạo Project JSON ảnh

Đọc `videoJsonCommonGuild.md` trước để nắm schema chung, đầu vào, timeline, DAG và quy tắc xuất JSON. Nội dung bên dưới là phần chuyên biệt cho ảnh được tách nguyên văn từ tài liệu gốc.

#### 2.2.2. Cấu hình node `image`: phân biệt ảnh timeline và ảnh tham chiếu

Node `image` có hai vai trò hợp lệ. Bản hợp nhất dùng `properties.asset_role` như **metadata quy ước của project** để phân biệt vai trò:

- `asset_role` không phải `generation` enum, không thay thế `type`, `operation`, model hoặc edges.
- Đây là thuộc tính bổ sung trong `properties`, không được mô tả trong bảng enum lõi của tài liệu gốc. Chỉ giữ trường này nếu Flow Hub Canvas của bạn chấp nhận các thuộc tính mở trong `properties`; nếu implementation thực tế từ chối khóa tùy chỉnh, hãy bỏ `asset_role` và phân biệt ảnh timeline với ảnh tham chiếu bằng sự hiện diện/không hiện diện của bộ trường `start_time`, `end_time`, `duration`.

**A. Ảnh truyện/visual hiển thị trên timeline** — `properties.asset_role: "timeline_visual"`

Dùng khi ảnh là khung hình trực tiếp kể chuyện trong bản dựng. Bắt buộc có đầy đủ các trường:

```json
"properties": {
  "asset_role": "timeline_visual",
  "start_time": 0.0,
  "end_time": 5.0,
  "duration": 5.0,
  "image_file": "images/image_001.png"
}
```

Cấu hình `generation`:
- `backend`: `flow`.
- `aspect_ratio`: `IMAGE_ASPECT_RATIO_SQUARE` (1:1), `IMAGE_ASPECT_RATIO_LANDSCAPE` (16:9), hoặc `IMAGE_ASPECT_RATIO_PORTRAIT` (9:16), tùy mục đích ảnh.
- `model`: `{"family":"image","id":"NANO_BANANA_2"}`.
- `operation`: `gen_image`.
- `resolution`: `null`; `duration_s`: `null`; `variants`: số nguyên 1–4, mặc định `1`.

Quy tắc timeline:
- `start_time`, `end_time`, `duration` là kiểu number tính bằng giây.
- `duration` phải bằng `end_time - start_time`, sai số biểu diễn tối đa 0.01 giây.
- Khi ảnh timeline minh họa trọn một hoặc nhiều segment audio, căn `start_time`/`end_time` theo đúng biên segment: ảnh cho một segment kết thúc tại `segments[id].end_time`; ảnh cho nhiều segment liên tiếp kết thúc tại `end_time` của segment cuối. `duration` tính lại từ hai mốc này. Nếu chỉ minh họa một phần segment, mốc ảnh phải nằm trong khoảng segment và khớp chính xác beat/câu được minh họa.
- Dùng đường dẫn tăng dần `images/image_001.png`, `images/image_002.png`, ... Không dùng cùng một đường dẫn cho hai node output khác nhau.
- Với audio JSON có ID segment, bắt buộc thêm `properties.audio_segment_ids` đúng theo nội dung mà ảnh minh họa; giữ thêm các thuộc tính hữu ích khác như `sceneType`, `timeOfDay`, `mood`.

**B. Ảnh tham chiếu bối cảnh/đạo cụ chỉ làm nguồn đầu vào** — `properties.asset_role: "reference_only"`

Dùng khi ảnh chỉ làm tài nguyên cho I2V/R2V/Video Reference hoặc để cố định thiết kế bối cảnh/đạo cụ, không xuất hiện như một shot độc lập trong timeline. Ví dụ:

```json
"properties": {
  "asset_role": "reference_only",
  "image_file": "images/references/scene_001.png",
  "sceneType": "indoor",
  "timeOfDay": "night"
}
```

- Vẫn phải có `image_file` với đường dẫn tương đối duy nhất.
- Không thêm `start_time`, `end_time`, `duration` nếu ảnh không được hiển thị như một shot timeline. Không tính ảnh này vào độ phủ timeline.
- Prompt bối cảnh tham chiếu bắt buộc mô tả **không có người**: `completely desolate, empty of people, no humans, no human silhouettes`. Chỉ mô tả kiến trúc, nội thất, địa hình, bố cục đồ vật, thời gian, ánh sáng và khí quyển.
- Nếu một ảnh bối cảnh đồng thời được chiếu trên timeline, nó không còn chỉ là `reference_only`; dùng `timeline_visual` và khai báo đủ ba trường thời gian.

Không thêm timeline fields vào node `character`. Ảnh chân dung character là tài nguyên nhận diện, không phải khung hình timeline.

### 8.2. Node image reference-only — có image_file, không tính vào timeline

```json
{
  "id": "node-002",
  "title": "Ảnh 01: Boong-ke chỉ huy",
  "type": "image",
  "prompt": "Empty underground command bunker at midnight, worn wooden map table, old topographic maps, cold teal radar glow, rough concrete walls, a few warm practical lamps, dust motes in narrow beams of light, completely desolate, empty of people, no human, no text, no logos.",
  "generation": {
    "backend": "flow",
    "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    "model": { "family": "image", "id": "NANO_BANANA_2" },
    "resolution": null,
    "duration_s": null,
    "operation": "gen_image",
    "variants": 1
  },
  "properties": {
    "asset_role": "reference_only",
    "image_file": "images/references/scene_001.png",
    "sceneType": "indoor",
    "timeOfDay": "night",
    "mood": "Tense underground command bunker"
  },
  "status": "idle"
}
```

