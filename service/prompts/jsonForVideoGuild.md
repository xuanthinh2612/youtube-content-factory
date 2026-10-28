# Hướng dẫn chuyên biệt tạo Project JSON video

Đọc `videoJsonCommonGuild.md` trước để nắm schema chung, đầu vào, timeline, DAG và quy tắc xuất JSON. Nội dung bên dưới là phần chuyên biệt cho video được tách nguyên văn từ tài liệu gốc.

#### 2.2.3. Cấu hình node `video` và thuộc tính bắt buộc `properties`

Mọi node `type: "video"` trong project đều là một clip video timeline/nguồn video đã được tạo trong DAG và bắt buộc có `start_time`, `end_time`, `duration`, `video_file`. Đối với video, dùng `video_file`, **không dùng `image_file`**.

```json
"properties": {
  "asset_role": "timeline_visual",
  "start_time": 0.0,
  "end_time": 8.0,
  "duration": 8.0,
  "video_file": "videos/video_001.mp4"
}
```

Quy tắc:
- `start_time`: thời điểm bắt đầu clip trên timeline dự án, tính bằng giây tuyệt đối từ đầu project/audio.
- `end_time`: thời điểm kết thúc clip trên timeline dự án, tính bằng giây tuyệt đối từ đầu project/audio.
- `duration`: luôn bằng `end_time - start_time`.
- **Phân biệt hai loại timestamp:** thời gian trong `properties` là vị trí tuyệt đối trên timeline dự án; timestamp mô tả hành động bên trong `prompt` video là thời gian cục bộ của clip render, bắt đầu từ `00:00` và kết thúc đúng tại `generation.duration_s`. Ví dụ, clip đặt ở project timeline `6.34–10.84` nhưng render 5 giây thì prompt nội bộ phải dùng khoảng `00:00–00:05`, không dùng `00:06.34–00:10.84`. Sau render, clip được trim/đặt trên timeline để khớp khoảng tuyệt đối.
- `video_file`: đường dẫn tương đối `videos/video_001.mp4`, `videos/video_002.mp4`, ...
- Giữ mọi thuộc tính hữu ích đã có trong `properties`, ví dụ `charVibe`, `action`, `cameraDetail`, `audio_segment_ids`; không xoá thuộc tính cũ khi thêm timeline.
- `generation.duration_s` phải thuộc whitelist model (Veo: 5/6/8; Omni: 4/6/8/10). `properties.duration` có thể ngắn hơn `generation.duration_s` nếu cần trim output để khớp timeline audio; không đặt `generation.duration_s` thành 2.3 chỉ vì timeline shot cần 2.3 giây.
- Với video extension hoặc last-frame continuation, thời gian trên timeline phải theo chuỗi dựng; extension nối ngay sau clip trước, trừ khi ý đồ người dùng yêu cầu khác.
- `video_file` là đường dẫn output được quy hoạch, không phải `mediaId`, `source_media_id` hoặc UUID backend.

## 3. MA TRẬN MODEL VÀ OPERATION CHO VIDEO

### 3.1. Google Veo 3.1

| `video_mode` | Model family / quality | Model ID | Operation |
|---|---|---|---|
| `t2v` | `veo`, `lite` | `veo_3_1_t2v_lite` | `gen_video_text` (hoặc `gen_video` nếu backend yêu cầu) |
| `t2v` | `veo`, `fast` 16:9 | `veo_3_1_t2v_fast` | `gen_video_text` |
| `t2v` | `veo`, `fast` 9:16 | `veo_3_1_t2v_fast_portrait` | `gen_video_text` |
| `t2v` | `veo`, `fast_ultra` | `veo_3_1_t2v_fast_ultra` | `gen_video_text` |
| `i2v` | `veo`, `lite` | `veo_3_1_i2v_lite` | `gen_video` |
| `i2v` | `veo`, `fast` 16:9 | `veo_3_1_i2v_s_fast` | `gen_video` |
| `i2v` | `veo`, `fast` 9:16 | `veo_3_1_i2v_s_fast_portrait` | `gen_video` |
| `i2v` | `veo`, `fast_ultra` | `veo_3_1_i2v_s_fast_ultra` | `gen_video` |
| `r2v` | `veo`, `lite` | `veo_3_1_r2v_lite` | `gen_video` |
| `r2v` | `veo`, `fast` 16:9 | `veo_3_1_r2v_fast_landscape` | `gen_video` |
| `r2v` | `veo`, `fast` 9:16 | `veo_3_1_r2v_fast` | `gen_video` |
| `r2v` | `veo`, `fast_ultra` | `veo_3_1_r2v_fast_ultra` | `gen_video` |
| `extend_video` | `veo`, `lite` | `veo_3_1_extension_lite` | `gen_video_extend` |

**Veo quality:** `generation.model.quality` phải khớp preset trong bảng (ví dụ `lite`, `fast`, hoặc `fast_ultra` khi ID tương ứng được hỗ trợ). Mặc định dùng `lite`. Không suy ra `quality` chỉ từ chuỗi ID; giữ đồng cấp `quality`/`id` mà Flow Hub export hoặc catalog hỗ trợ.

> [!CAUTION]
> **QUY TẮC BẮT BUỘC ĐỐI VỚI MODEL VEO:**
> **Veo quality:** `generation.model.quality` phải khớp preset trong bảng (ví dụ `lite`, `fast`, hoặc `fast_ultra` khi ID tương ứng được hỗ trợ). Mặc định dùng `lite`. Không suy ra `quality` chỉ từ chuỗi ID; giữ đồng cấp `quality`/`id` mà Flow Hub export hoặc catalog hỗ trợ.
> Ví dụ đúng: `{"family": "veo", "quality": "lite", "id": "veo_3_1_r2v_lite"}`.
> Nếu thiếu trường `quality`, hàm nhận diện của Flow Hub (`videoFrame.ts`) sẽ coi nguồn không có marker Veo hợp lệ, dẫn đến việc các node nối phía sau **không thể kích hoạt được tính năng Extend Video**!


### 3.2. Omni Flash

| `video_mode` | Model family | Model ID | Operation |
|---|---|---|---|
| `t2v` | `omni_flash` | `abra_t2v_{duration_s}s` hoặc suffix `_360p` khi dùng 360p | `gen_video_omni` |
| `i2v` | `omni_flash` | `abra_i2v_{duration_s}s` hoặc suffix `_360p` | `gen_video_omni` |
| `r2v` | `omni_flash` | `abra_r2v_{duration_s}s` hoặc suffix `_360p` | `gen_video_omni` |
| `video_reference` | `omni_flash` | `abra_edit` | `gen_video_video_reference` |

Omni hỗ trợ resolution `720p` hoặc `360p`, duration `4`, `6`, `8`, hoặc `10` giây. Với chế độ `video_reference`, khai báo `resolution` là `720p` hoặc `360p` và `duration_s` là `8` để tránh lỗi export như quy định tại schema này.

### 3.3. Giá trị generation hợp lệ

- Video aspect ratio: `VIDEO_ASPECT_RATIO_LANDSCAPE` (16:9) hoặc `VIDEO_ASPECT_RATIO_PORTRAIT` (9:16).
- Veo resolution: luôn `720p`.
- Veo duration: `5`, `6`, hoặc `8` giây; mặc định khuyến nghị `8` giây.
- Omni duration: `4`, `6`, `8`, hoặc `10` giây.
- `generation.camera`: `dynamic` hoặc `static`; phải khớp chuyển động được mô tả trong prompt.
- `generation.variants`: số nguyên từ `1` đến `4`, mặc định `1`.
- Ảnh/character: `resolution` và `duration_s` là `null`.

---

## 4. CHI TIẾT CÁC CHẾ ĐỘ VIDEO VÀ ĐIỀU KIỆN EDGE

### 4.1. T2V — Text to Video

- Dùng khi tạo video từ văn bản không có ảnh/video tham chiếu.
- Bắt buộc **0 edge đi vào** node video.
- Trọng tâm: đại cảnh, môi trường, thời tiết, phong cảnh, establishing shot hoặc chủ thể không cần khóa nhận diện bằng asset.
- Model mặc định Veo: `veo_3_1_t2v_lite`; operation `gen_video_text`.

### 4.2. I2V — Image to Video / Last-Frame Continuation

Có hai trường hợp:

**A. Nguồn là ảnh:** dùng một ảnh/character làm khung hình bắt đầu; đúng **1 edge** từ node `character` hoặc `image`. Dùng `video_mode: "i2v"`, `connected_video_mode: "i2v"`, operation `gen_video`, model Veo `veo_3_1_i2v_lite`.

**B. Nguồn là video trước:** trích xuất frame cuối của một video để mở đầu shot mới, thường dùng khi đổi góc máy/ngắt nhịp hoặc khi clip trước là Omni Flash. Đúng **1 edge** từ node `video`; dùng `video_mode: "i2v"`, `connected_video_mode: "i2v"`, operation `gen_video` với Veo hoặc `gen_video_omni` theo model hợp lệ. Không dùng Extend nếu mục tiêu là đổi góc máy/ngắt hành động.

### 4.3. R2V — Reference to Video / Ingredients

- Dùng khi cần kết hợp nhiều ảnh tham chiếu như character + bối cảnh, nhiều nhân vật hoặc nhân vật + đạo cụ.
- Bắt buộc có **từ 2 edge trở lên** đi vào node video.
- Edge có thể xuất phát từ `character`, `image`, hoặc node `video` khi hệ thống cần trích frame làm tham chiếu.
  * Node `video` (hệ thống sẽ tự động trích xuất frame từ video đó qua `extract_video_ids` làm tham chiếu).
- Veo: `veo_3_1_r2v_lite`, operation `gen_video`.
- Omni: `abra_r2v_{duration_s}s` (thêm `_360p` nếu cần), operation `gen_video_omni`.

### 4.4. Extend Video — `extend_video` (Veo fZytfe)

Dùng để nối dài liền mạch cùng một cú máy/action từ clip Veo trước.
  * Khi hành động của nhân vật diễn ra dài hơn 8 giây trong cùng một góc máy (ví dụ: Nhân vật ngồi giải mã tín hiệu radio suốt 16 giây; hoặc bước đi dọc hành lang dài).
  * Shot quay tiếp tục diễn biến mà không cắt cảnh (continuous long take).

- Nguồn phải là video đã tạo bởi Google Veo (`model.family: "veo"`); không extend video Omni Flash.
- Bắt buộc **đúng 1 edge** duy nhất từ node video Veo trước; không nối thêm image/character hay video khác.
- Bắt buộc có đủ:
  - `video_mode: "extend_video"`
  - `connected_video_mode: "extend"`
  - `video_extend_mode: "extend"`
- Model: `{"family":"veo","quality":"lite","id":"veo_3_1_extension_lite"}`.
- Operation: `gen_video_extend`.
- Prompt kế thừa camera, bối cảnh, ánh sáng, trang phục và quán tính của clip nguồn; không đổi shot hoặc nhảy bối cảnh đột ngột.
- Timeline `properties` của extension phải bắt đầu ngay sau clip nguồn trong mạch nối, trừ khi người dùng yêu cầu dựng timeline khác.

### 4.5. Video Reference — `video_reference` (Omni jIps6)

Dùng để giữ chuyển động/bố cục của một video nguồn nhưng thay nhân vật hoặc phong cách theo ảnh tham chiếu.

- Chỉ dùng Omni Flash: `{"family":"omni_flash","id":"abra_edit"}`.
- Bắt buộc đúng **1 edge từ một node video** làm video nguồn.
- Có thể nối thêm 0 hoặc nhiều edge từ node `character`/`image` làm tham chiếu ảnh.
  * **Ràng buộc Edge Image kèm theo:** Được phép nối 0 hoặc nhiều edge từ node `character` hoặc `image` để làm ảnh chỉ dẫn phong cách/nhân vật (`ref_media_ids`). Mọi node ảnh này phải là image (backend kiểm tra nghiêm ngặt `kind == "image"`).
- Không nối hai video nguồn vào một `video_reference`; nếu có từ hai video nguồn, chọn R2V theo mục 5.
- Bắt buộc khai báo `video_mode: "video_reference"`, `connected_video_mode: "video_reference"`, operation `gen_video_video_reference`.
- `resolution` phải là `720p` hoặc `360p`; `duration_s` phải là `8`.
- Chỉ dùng khi ý đồ là giữ motion/camera từ video gốc và tái diễn giải chủ thể/style, không chọn thay cho R2V nếu muốn tổng hợp nội dung mới từ nhiều nguồn.

---

## 5. CÂY QUYẾT ĐỊNH CHỌN VIDEO MODE

Trước khi cấu hình từng node video, đếm edge đi vào và xác định loại nguồn:

1. **0 edge:** chọn T2V (`video_mode: "t2v"`, `operation: "gen_video_text"`, mặc định model Veo `veo_3_1_t2v_lite`).
2. **1 edge từ `character` hoặc `image`:** chọn I2V (`video_mode: "i2v"`, `connected_video_mode: "i2v"`, operation `gen_video`).
3. **1 edge từ `video`:**
   - Nếu clip nguồn là Veo và mục tiêu là tiếp tục cùng cú máy liền mạch: chọn `extend_video` với ba cờ bắt buộc và đúng model Extend.
   - Nếu cần chuyển góc máy/ngắt nhịp hoặc nguồn là Omni Flash: chọn I2V Last-Frame.
   - Nếu giữ chuyển động video gốc và thay nhân vật/style: chỉ khi dùng Omni Flash, chọn `video_reference` và thêm ảnh tham chiếu cần thiết.
4. **Từ 2 edge trở lên:**
   - Chỉ có ảnh (character + bối cảnh/đạo cụ): chọn R2V.
   - Có video và ảnh, muốn giữ nguyên motion nguồn, thay nhân dạng/style: chọn `video_reference` trên Omni Flash, với đúng một edge video và các edge ảnh tùy chọn.
   - Muốn tạo một video mới bằng cách kết hợp nhiều nguồn hoặc có từ 2 video tham chiếu: chọn R2V.
5. **Không vi phạm DAG:** không tạo edge quay ngược làm chu trình; mọi `source`/`target` phải tồn tại.
6. **Mọi edge:** phải có `relation: "canvas"`.

---

## 6. AUTO_GEN VÀ TIÊM MEDIA NGẦM (`canvas_dependencies`)

1. Không tự điền `mediaId`, `source_media_id`, `ref_media_ids` hoặc `start_media_ids` giả vào JSON; backend sẽ gán khi media thực sự được tạo.
2. Mọi node bắt đầu với `status: "idle"`.
3. **Thực thi theo thứ tự tô-pô (DAG Topological Chain):**
   * Khi import với `"auto_gen": true`, Canvas tự động gọi lệnh `runAll()`.
   * Hệ thống duyệt từ các node gốc (không có cha) như `character`, `image`, `t2v`.
   * Các node gốc được tạo job trước.
4. **Cơ chế giữ hàng đợi và tự động tiêm Media (`_wait_canvas_dependencies`):**
   * Khi đến lượt node con (ví dụ node video phụ thuộc node character), hệ thống gửi request lên backend.
   * Backend phát hiện node cha đang chạy, sẽ tự động đăng ký `canvas_dependencies`.
   * Job con được đưa vào trạng thái chờ an toàn: **Ngay khi node cha hoàn thành và xuất ra media thật, backend tự động lấy ID media đó gắn vào `start_media_ids`, `ref_media_ids` hoặc `source_media_id` của node con rồi mới tiến hành render.**
5. **Cơ chế chống cascade lỗi:** Nếu một node cha bị lỗi render, toàn bộ các node con phía sau sẽ tự động dừng lại ở trạng thái `idle`, không làm tiêu hao credits của người dùng.
6. `properties.image_file`/`properties.video_file` là đường dẫn file đầu ra dự kiến cho mục đích dự án/timeline, không phải mã media backend.

---

## 7. BỘ QUY TẮC PROMPT ĐIỆN ẢNH CHUYÊN SÂU CHO VEO 3.1 & OMNI FLASH

Mọi prompt của node `video` phải viết bằng tiếng Anh cho phần mô tả hình ảnh/chuyển động và kết thúc bằng đúng ba dòng bổ trợ `VO`, `SFX`, `Continuity`. Nếu dự án không có audio script, viết nội dung VO/SFX theo ngôn ngữ người dùng yêu cầu; mặc định là tiếng Việt. Nếu audio JSON có sẵn, không dịch hoặc sáng tác lời thoại mới: trong `VO`, giữ một trích đoạn ngắn nguyên văn đúng ngôn ngữ nguồn và/hoặc ghi rõ dùng audio segment ID tương ứng; `SFX` chỉ mô tả âm thanh môi trường phù hợp, không được ghi đè lời thoại gốc. Nếu người dùng yêu cầu không thoại/không VO, dùng giá trị chỉ dẫn `None — no dialogue or voice-over; visual storytelling only.` chứ không bịa lời thoại. Dù nhãn hướng dẫn là `VO`, nội dung thoại phải theo ngôn ngữ audio input khi đã có.

### Yêu cầu bắt buộc về độ chi tiết của prompt ảnh và video

Prompt là chỉ dẫn trực tiếp cho model tạo media, vì vậy **mọi node `image` và `video` phải có prompt riêng, cụ thể cho đúng nội dung của node đó**. Không dùng prompt chung chung, prompt mẫu lặp lại giữa nhiều node, hoặc chỉ ghi tên cảnh/cảm xúc mà không mô tả hình ảnh có thể quan sát được. Những cụm như “nhân vật đang buồn trong căn phòng”, “cảnh phim điện ảnh”, “cô ấy hành động”, “một khung cảnh đẹp” là chưa đủ nếu không có chi tiết cụ thể đi kèm.

Prompt cho từng ảnh/video phải mô tả, theo mức độ phù hợp với cảnh:

1. **Bối cảnh cụ thể:** địa điểm và loại không gian; thời điểm/thời tiết khi có ý nghĩa; chi tiết môi trường, đạo cụ, vật liệu, bố cục hoặc vị trí tương đối liên quan đến hành động. Tránh mô tả mơ hồ như “một nơi tối tăm” nếu có thể xác định đó là hành lang bê tông ẩm, căn bếp nhỏ lúc bình minh hay sân ga vắng dưới mưa.
2. **Nhân vật và cảm xúc thể hiện được:** nêu đúng nhân vật/handle, vị trí và hướng nhìn; mô tả cảm xúc qua dấu hiệu nhìn thấy được như ánh mắt, chân mày, cơ mặt, tư thế, nhịp thở hoặc cử chỉ. Không chỉ ghi nhãn “buồn”, “sợ” hay “tức giận” mà không nói cảm xúc biểu hiện ra sao.
3. **Hành động cụ thể trong bối cảnh:** nói rõ nhân vật đang làm gì, dùng bộ phận cơ thể/đạo cụ nào, ở đâu và tương tác với môi trường ra sao. Hành động phải phù hợp cốt truyện, tư thế đầu/cuối, thời lượng clip và continuity; tránh các động từ chung như “di chuyển”, “khám phá”, “đối mặt” nếu chưa chỉ rõ chuyển động hoặc đối tượng tương tác.
4. **Hình ảnh và camera:** chọn framing/góc nhìn, bố cục chủ thể, chiều sâu, ánh sáng, màu sắc và chất liệu có chủ đích. Chỉ thêm chi tiết hữu ích, không mâu thuẫn với reference, generation settings hoặc node liên quan.

**Khác biệt theo loại media:**
- Với `image`, mô tả một khoảnh khắc tĩnh duy nhất: hành động đang ở pha nào, pose của nhân vật, biểu cảm, vị trí đạo cụ và chi tiết bối cảnh nhìn thấy trong khung hình. Không viết chuỗi hành động như thể ảnh là video.
- Với `video`, mô tả diễn tiến có thứ tự: trạng thái mở đầu, hành động chính và tương tác vật lý, phản ứng hoặc kết quả ở cuối clip. Chia nhịp bằng timestamp cục bộ khi cần; số hành động phải vừa với `generation.duration_s`.
- Với ảnh `reference_only` về bối cảnh, mô tả chi tiết không gian/ánh sáng/đạo cụ nhưng vẫn tuân thủ quy tắc không có người tại mục 2.2.2.

Độ chi tiết không có nghĩa là tự thêm tình tiết. Chỉ suy luận chi tiết hình ảnh hợp lý từ kịch bản, audio, character/world/prop bible và asset tham chiếu; không đổi sự kiện, quan hệ nhân vật, đạo cụ cốt lõi hoặc cảm xúc trái với nguồn. Khi nguồn không xác định chi tiết không thiết yếu, chọn phương án hình ảnh trung tính, nhất quán thay vì bịa thêm diễn biến.

**Thông tin thoại và người nói là bắt buộc khi có thoại:** Với từng cảnh, xác định câu/đoạn thoại nào xảy ra trong khoảng cảnh đó, ai là người nói theo kịch bản hoặc `speaker_id`, và người nói có thực sự xuất hiện trong khung hình hay chỉ nói ngoài khung/voice-over. Prompt phải gọi đúng handle của người nói đang hiện diện và mô tả hành động nói/biểu cảm phù hợp; không gán lời thoại cho nhân vật khác, không mặc định người đọc voice-over xuất hiện trong ảnh. Với ảnh tĩnh, nếu có thoại trong khoảnh khắc được minh họa, ghi rõ người đang nói (hoặc nói ngoài khung); nếu không có thoại thì ghi rõ không có nhân vật đang nói. Không chèn chữ/phụ đề vào ảnh trừ khi được yêu cầu. Với video, dòng `VO` phải gắn đúng lời thoại với đúng người nói hoặc segment ID và phân biệt thoại trong cảnh với voice-over; giữ nguyên văn thoại nguồn khi có audio JSON.

**Bắt buộc lập bản đồ câu chuyện trước khi viết prompt:** Trước khi tạo prompt riêng cho bất kỳ node cảnh nào, lập nội bộ một storyboard/scene map theo thứ tự truyện và timeline. Mỗi beat phải ghi: nguồn thoại/segment và thời gian tương ứng (nếu có), sự kiện trước–sau, nhân vật thực sự có mặt, người đang nói và trạng thái on-screen/off-screen, địa điểm, đạo cụ liên quan, hành động/khoảnh khắc được thể hiện, cùng các continuity cần giữ từ cảnh trước. Chốt character bible, scene/world bible, prop bible và continuity bible từ bản đồ này; chỉ sau đó mới lần lượt viết prompt theo đúng nội dung thoại và bối cảnh tổng thể. Nếu một cảnh chưa xác định được nhân vật, người nói, địa điểm hoặc quan hệ với mạch truyện, phải đối chiếu lại nguồn và scene map trước khi hoàn tất prompt.

### 7.1. Công thức 5 thành phần vàng

Viết theo thứ tự:

`[Camera movement/framing] + [Main subject and specific action] + [Setting/environment] + [Lighting/atmosphere] + [Optical style/lens]`

Thứ tự này dẫn mô hình từ cách nhìn không gian 3D, sang chủ thể và hành động, tương tác với môi trường, điều kiện ánh sáng, rồi tới chất lượng quang học/ống kính. Ví dụ: `Slow cinematic tracking shot following a lone courier across a rain-darkened rooftop; the courier takes three measured steps and steadies a satchel; distant city towers and puddles reflect muted signage; soft amber rim light cuts through cool mist; natural 35mm film grain and shallow depth of field.` Đây là ví dụ về cấu trúc prompt, không phải nội dung mặc định cần áp dụng cho mọi project.

Sau đó xuống dòng và thêm:

- `VO: "..."`
- `SFX: "..."`
- `Continuity: "..."`

### 7.2. Camera và chống morphing

- Góc máy: cinematic wide/drone, low-angle tracking, close-up/medium close-up, over-the-shoulder, extreme wide aerial.
- Chuyển động: slow push-in, orbiting/arc shot, panning, first-person POV walking, subtle handheld tracking, locked-off static tripod.
- Nếu camera di chuyển (`tracking`, `push-in`, `panning`, `drone`, `orbiting`, `handheld`), đặt `generation.camera: "dynamic"`.
- Nếu camera đứng yên hoàn toàn (`locked-off`, `static camera`, `tripod`), đặt `generation.camera: "static"`.
- Không mô tả máy quay vừa locked-off tuyệt đối vừa tracking/panning trong cùng shot trừ khi trình bày rõ chuyển động có chủ ý.

**Từ điển góc máy và chuyển động để chọn chính xác:**

| Cụm từ | Cách dùng hình ảnh |
|---|---|
| `Cinematic wide drone shot` / `extreme wide aerial shot` | Establishing shot, cho thấy quy mô địa hình, thành phố hoặc môi trường rộng. |
| `Low-angle tracking shot` | Bám theo chủ thể từ góc thấp, tạo cảm giác mạnh mẽ hoặc áp lực. |
| `Close-up` / `medium close-up` | Nhấn vào biểu cảm, phản ứng nhỏ hoặc thao tác với đạo cụ. |
| `Over-the-shoulder (OTS)` | Cho thấy góc nhìn qua vai khi nhân vật quan sát, khám phá hoặc đối thoại. |
| `Slow push-in` / `slow zoom-in` | Tiến gần từ từ để tăng tập trung hoặc căng thẳng. |
| `Orbiting` / `arc shot` | Di chuyển theo cung quanh chủ thể; chỉ dùng nếu không làm hỏng continuity không gian. |
| `Panning left/right` | Quét ngang để mở rộng không gian hoặc theo dõi chủ thể. |
| `First-person POV walking` | Góc nhìn thứ nhất với rung động tự nhiên theo bước chân. |
| `Subtle handheld tracking` | Máy cầm tay bám theo, có rung nhẹ để tạo cảm giác hiện trường. |
| `Locked-off static camera on a tripod` | Máy cố định, không lia, rung, zoom hoặc tracking; dùng `generation.camera: "static"`. |

Chỉ chọn một cấu hình camera có thể thực hiện trong shot; nếu dùng động tác máy, phải ghi rõ hướng/chủ thể được theo dõi và giữ `generation.camera: "dynamic"`.

### 7.3. Chuỗi hành động theo thời gian

- Mô tả hành động có điểm bắt đầu, diễn tiến, tương tác vật lý và phản ứng vi mô.
- Với clip 8 giây, thường chỉ 1–2 hành động liên kết chậm rãi; dùng `Slowly`, `Gently`, `Gradually`, `Deliberately`, `Step-by-step`.
- Tránh cụm mơ hồ như “wonderfully” hoặc “hành động đẹp mắt” mà không nói rõ hành vi.
- Chuỗi hành động nên có thứ tự cơ học rõ ràng, chẳng hạn: nhân vật đặt tay lên chai → nâng chai → uống một ngụm → đặt chai xuống → nhận ra âm thanh → quay đầu nhìn về phía phát ra âm thanh. Mỗi hành động sau phải có thể tiếp nối tự nhiên từ tư thế/hành động trước.
- Tránh mô tả trạng thái tĩnh chung chung như “a person exploring beautifully”. Nêu rõ nhân vật nhìn đâu, tay/chân làm gì, vật nào được chạm và phản ứng nào quan sát được.

### 7.4. Ánh sáng, màu sắc và optics

Có thể chọn các chi tiết quan sát được phù hợp cảnh: golden-hour rim lighting, volumetric rays, moody neon, chiaroscuro/low-key lighting, shallow depth of field, soft bokeh, 35mm anamorphic lens, 50mm prime lens, 85mm portrait lens. Tránh ghép hiệu ứng ánh sáng mâu thuẫn với thời tiết/thời gian trong cảnh.

* **Ánh sáng kịch tính (Dramatic Lighting):**
  * **Golden hour rim lighting:** Viền nắng chiều hoàng hôn ấm áp ôm lấy góc cạnh nhân vật, tách bạch chủ thể khỏi phông nền.
  * **Volumetric god rays:** Các luồng tia sáng thể tích xuyên qua khói, sương mù, tán cây hoặc cửa sổ boong-ke.
  * **Moody neon cyber lighting:** Ánh đèn neon phản chiếu tương phản cao trên bề mặt ướt át.
  * **Chiaroscuro lighting / Low-key cinematic lighting:** Tương phản sáng tối gắt gao, mảng tối sâu dứt khoát tạo chiều sâu tâm lý bí ẩn.
* **Độ sâu trường ảnh & Ống kính quang học (Depth of Field & Lens Optics):**
  * Sử dụng `Shallow depth of field`, `Soft bokeh background` khi muốn làm nổi bật chủ thể và làm mờ phông nền mềm mại nghệ thuật.
  * Khai báo ống kính chuyên nghiệp: `35mm anamorphic lens` (tạo vệt lóa ngang cinematic đặc trưng), `50mm prime lens` (tỉ lệ góc nhìn trung thực mắt người), `85mm portrait lens` (nén hậu cảnh, tôn đường nét chân dung).

### 7.5. Continuity cho nhiều shot

- Gọi đúng handle nhân vật như `@Nam_28t`.
- Giữ nguyên khuôn mặt, tóc, trang phục nhận diện và tone màu nhất quán trong các shot trừ khi kịch bản nêu rõ thay đổi.
- Cảnh trước kết thúc ở tư thế/hành động nào, cảnh sau bắt đầu bằng tư thế/hệ quả vật lý hợp lý.
- Dùng `extend_video` cho cùng cú máy Veo; dùng I2V Last-Frame cho shot mới/chuyển góc/clip Omni; dùng Video Reference chỉ cho motion/style transfer qua Omni theo điều kiện mục 4.5.
- Duy trì một “character bible”, “world bible” và “prop bible”: khóa handle, khuôn mặt, trang phục đặc trưng, palette màu, bố cục bối cảnh và vị trí đạo cụ qua các prompt có liên quan. Chỉ thay đổi các yếu tố này khi truyện hoặc người dùng yêu cầu.
- Dùng match cut/hệ quả cơ học khi thích hợp: cảnh trước kết thúc bằng hành động cụ thể, cảnh sau tiếp tục từ tư thế hoặc kết quả đó. Ví dụ: tàu hạ cánh ở wide shot → cận cảnh chân đáp chạm đất → cửa khoang mở và hơi áp suất thoát ra.
- Thời lượng mỗi clip là lựa chọn kỹ thuật của model: Veo 5/6/8 giây, Omni 4/6/8/10 giây. Đây là whitelist render, không thay thế thời lượng timeline; khi timeline cần đoạn ngắn hơn, dùng trim theo mục 2.2.3.

1. **Khóa Prompt gốc về nhân vật / phong cách (Master Prompt Locking):**
   * Luôn gọi đúng nhãn nhận dạng `@Ten_Nhan_Vat` (ví dụ: `@Nam_28t`).
     > *"...same 28-year-old Vietnamese man (@Nam_28t) in dark grey field jacket over black t-shirt, consistent facial identity, retro sci-fi 70s color palette."*
   * Cảnh 1 kết thúc bằng hành động gì, Cảnh 2 nên bắt đầu bằng góc quay phản hồi hoặc hệ quả cơ học trực tiếp của hành động đó.
   * *Ví dụ chuỗi logic:* Cảnh 1 phi thuyền hạ cánh góc rộng $\rightarrow$ Cảnh 2 cận cảnh chân đáp chạm mặt đất $\rightarrow$ Cảnh 3 cửa khoang bật mở xì hơi áp suất.
### 7.6. Prompt anchors

Nên ưu tiên các từ khóa mô tả quan sát được như `Cinematic motion`, `Photorealistic`, `Film grain`, `Natural physics`, `Dynamic lighting`, `Captured on 35mm film`, `Live-action cinematic footage`, `Subtle movement`. Tránh nhồi quá nhiều hành động/chủ thể tốc độ cao vào một shot hẹp. Không dựa vào các từ sáo rỗng chất lượng như `4K`, `8K`, `masterpiece`, `ultra realistic`, `trending on artstation`; mô tả cụ thể kết quả hình ảnh cần đạt.

| Nên ưu tiên | Hạn chế hoặc tránh |
|---|---|
| `Cinematic motion`, `Photorealistic`, `Film grain`, `Natural physics`, `Dynamic lighting`, `Captured on 35mm film`, `Live-action cinematic footage`, `Subtle movement` | `super fast crazy action`, `explosive rapid movements` và nhiều chủ thể/hành động độc lập trong cùng khung hình hẹp; chúng dễ làm nhòe hoặc mất continuity. |
| Mô tả cụ thể nguồn sáng, bề mặt, ống kính, hành vi và chuyển động quan sát được | Các từ tự khen chất lượng như `masterpiece`, `ultra realistic`, `trending on artstation`; không dùng `4K`/`8K` như cách thay thế cho mô tả hình ảnh cụ thể. |

Không coi các từ khóa trên là bắt buộc phải nhồi vào mọi prompt; chỉ dùng chi tiết hỗ trợ ý đồ cảnh.


| **CẤM DÙNG (Gây nhiễu dữ liệu huấn luyện)** | `"4K"`, `"8K"`, `"masterpiece"`, `"ultra realistic"`, `"trending on artstation"` | Các mô hình thế hệ mới của Google đã được huấn luyện trên nguồn dữ liệu phim ảnh cao cấp. Các từ sáo rỗng này là "nhiễu" (noise) và làm giảm chất lượng render thực tế. *(Lưu ý: Trong ví dụ kinh điển 7.1 có chứa "8k" theo thói quen cũ, nhưng khi viết prompt thực tế cho Veo 3.1, AI nên ưu tiên dùng `Cinematic film, 35mm, photorealistic` thay thế).* |
### 7.7. Kiến trúc prompt theo mode

- **T2V:** đại cảnh, môi trường, thời tiết, quy mô không gian; không mô tả nhận dạng phức tạp cần ảnh tham chiếu.
- **R2V:** gọi handle nhân vật, nhắc trang phục cố định, gắn hành động vật lý với bối cảnh/đạo cụ tham chiếu.
- **Extend:** kế thừa góc máy, bối cảnh, ánh sáng và chuyển động của clip trước; phát triển hành động tiếp theo mà không cắt shot.
- **I2V Last-Frame:** mở đầu từ tư thế/frame cuối nguồn, có thể đổi góc máy theo mục tiêu dựng; giữ danh tính/trang phục.
- **Video Reference:** mô tả giữ motion và camera của video nguồn đồng thời chuyển chủ thể/style theo asset ảnh, chỉ dùng Omni `abra_edit`.

**Khung prompt thao tác theo từng mode** (thay nội dung trong ngoặc vuông; timestamp luôn là thời gian cục bộ của clip render):

1. **T2V, 0 edge:** `[Extreme wide/aerial establishing camera] + [environment or weather changes over time] + [specific terrain, structures, and environmental motion] + [lighting/atmosphere] + [lens/film qualities].` Tránh nhân vật chính cần khóa nhận diện khi không có reference.
2. **R2V, từ 2 edge trở lên:** `[Medium/low-angle/tracking camera] + [@Character, age/appearance and unchanged signature outfit, performs a slow physical action] + [inside/at the exact referenced scene, with concrete props/textures] + [motivated key/rim lighting] + [lens/film qualities].` Gọi đúng asset đã nối và mô tả tương tác vật lý với bối cảnh.
3. **I2V from `character`/`image`, one incoming edge:** `[framing and lens suited to the source image] + [begin from the exact source identity, pose, and outfit] + [one clear physical action developing over the render duration] + [referenced environment and motivated lighting] + [realistic motion and continuity]. Do not invent a conflicting starting pose or identity.
4. **Extend, đúng 1 edge từ video Veo:** `[Continuous same framing/lens and camera motion] + [source subject maintains end pose, then continues the next action] + [same scene, layout, lighting and props] + [seamless physical motion, no cut or sudden change].` Không đổi góc máy, bối cảnh hoặc trang phục đột ngột; prompt tiếp tục hành động của clip nguồn.
5. **I2V Last-Frame, đúng 1 edge từ video:** `[New framing/lens if a deliberate angle change is intended] + [subject begins from the source video's exact last-frame posture, then starts a new action] + [same or intentionally changed scene perspective] + [consistent identity/outfit and motivated light] + [realistic motion].` Đây là shot mới từ frame cuối, không mô tả như một cú máy liên tục nếu đang đổi góc.
6. **Video Reference, Omni `abra_edit`:** `[Camera motion/composition matching source video] + [retarget subject to @Character or referenced appearance] + [preserve requested source motion while describing intended scene/style changes] + [lighting and optical qualities].` Nói rõ yếu tố nào phải giữ từ video và yếu tố nào được thay theo ảnh tham chiếu.

Các khung trên là checklist biên soạn, không phải chuỗi literal để chép nguyên. Ghép chúng với công thức 5 thành phần, timestamp, ràng buộc vật lý và 3 dòng bổ trợ ở các mục 7.1–7.10.

### 7.8. Ba dòng bổ trợ `VO`, `SFX`, `Continuity`

- `VO`: nếu người dùng muốn thoại/voice-over nhưng không có audio script, dùng lời thoại/lời bình ngắn theo yêu cầu (thường 10–25 từ cho clip 8 giây). Nếu có audio JSON, giữ nguyên ngôn ngữ nguồn và trích đúng phần liên quan; không dịch, viết lại hoặc bịa thoại mới, đồng thời có thể chỉ ra `audio_segment_ids`. Nếu người dùng yêu cầu không thoại/không VO, ghi `VO: "None — no dialogue or voice-over; visual storytelling only."`; đây là chỉ dẫn phủ định, không phải lời thoại.
- `SFX`: nêu 2–4 âm thanh hiện trường cụ thể, như gió, bước chân, tiếng radio, va chạm vật lý; tránh tuyên bố một hiệu ứng là lời thoại gốc.
- `Continuity`: nêu rõ node nguồn, nhân vật, bối cảnh, frame cuối hoặc kiểu extension/reference đang dùng; nếu là audio project, nêu các segment liên quan khi hữu ích.

### 7.9. Timestamp, loại trừ và vật lý

- Với video 8 giây, dùng các mốc `00:00–00:04` và `00:04–00:08`; tổng mốc phải bằng `generation.duration_s`. Nếu dùng duration khác, điều chỉnh timestamp cho khớp chính xác.
- Ghi negative constraints khi phù hợp: `No crowds, no modern commercial advertisements, no brand logos, no staged poses, no CGI artifacts, no morphing`.
- Khóa tính chân thực: `Believable physics throughout: natural hands and fingers with correct anatomy, feet planted firmly on the ground, clothing fabric moving naturally with wind and body momentum, handheld objects remain separate entities, background objects stay locked in space, no distorted anatomy, no floating or disappearing objects.`
- Không thêm thuộc tính vật lý mâu thuẫn: chẳng hạn không mô tả quần áo ướt trong cảnh được xác định rõ là khô ráo nếu không có sự kiện làm ướt.
- Thêm chi tiết vi mô không gian khi hữu ích: vết nứt bê tông, bụi trong tia sáng, dây điện, đồ vật cũ, vết xước gỗ, hơi nước trên kính.
- Khi hợp cảnh, mô tả các đặc tính quang học quan sát được thay vì chỉ ghi nhãn thể loại: handheld micro-shake, imperfect framing, occasional gentle autofocus hunting, slight exposure shifts, natural sensor noise hoặc organic motion blur. Chỉ dùng các đặc tính này khi phù hợp với camera và không khí của cảnh.
- Chọn một cảm xúc chủ đạo nhất quán, được thể hiện bằng hình ảnh/ánh sáng/hành động cụ thể; có thể chốt prompt bằng một `Final Feel` ngắn, không mâu thuẫn với kịch bản.
- Có thể thêm chi tiết vi mô để bối cảnh có cảm giác đang được sử dụng và tồn tại độc lập: vết nứt trên bê tông, bụi trong tia sáng, dây điện, đồ vật cũ, vết xước trên gỗ, hơi nước trên kính, chậu cây đặt lệch hoặc xe đạp cũ. Chỉ thêm chi tiết hợp thời đại, địa điểm và trạng thái cảnh.
- Có thể dùng cảm xúc chốt ngắn như `Final Feel: quiet, tense, intimate and observational` nếu nó thống nhất với kịch bản. Đây là tùy chọn định hướng sắc thái, không phải sự kiện mới hay lời thoại.
- Negative constraints phải chọn theo cảnh. Ví dụ có thể dùng `No crowds, no tourists, no modern commercial advertisements, no brand logos, no staged poses, no CGI artifacts, no morphing`; không áp đặt các điều cấm camera (như `no drone`) nếu shot thực sự dùng drone.

**Quy tắc chi tiết để prompt bám sát ý đồ (giữ lại từ bản master cũ):**

1. **Chia hành động theo timestamp cục bộ của clip render.** Với clip 8 giây, có thể dùng `00:00–00:04` để đặt vị trí/tư thế và hành động đầu, `00:04–00:08` để tiếp tục hành động hoặc phản ứng. Với duration khác, điều chỉnh mốc cho kết thúc đúng bằng `generation.duration_s`. Không dùng timestamp tuyệt đối của project/audio trong prompt nội bộ clip.
2. **Mỗi mốc chỉ mô tả hành vi có thể quan sát.** Nêu rõ ai làm gì, nhìn về đâu, dùng tay/chân nào khi cần, vật thể nào được chạm và kết quả vật lý nào xảy ra. Bảo đảm hành động sau bắt đầu từ tư thế/hệ quả của hành động trước; không nhồi nhiều hành động độc lập hoặc chủ thể cùng lúc.
3. **Đặt ràng buộc phủ định theo cảnh, không chép máy móc.** Có thể loại trừ người thừa, chữ/logo, quảng cáo hiện đại, pose dàn dựng, biến dạng hoặc vật thể không mong muốn. Không dùng phủ định mâu thuẫn với chủ ý cảnh (ví dụ cấm drone trong shot drone, cấm người trong shot có nhân vật chính).
4. **Khóa vật lý và liên tục không gian.** Khi phù hợp, yêu cầu bàn tay/ngón tay tự nhiên, chân bám mặt đất, vải phản ứng với gió và quán tính, đạo cụ không nhập/tách khỏi bàn tay, vật thể nền giữ vị trí, không biến dạng giải phẫu. Loại bỏ chi tiết mâu thuẫn với thời tiết, ánh sáng, trạng thái vật thể hoặc hành động đã nêu.
5. **Dùng chi tiết vi mô và quang học có chọn lọc.** Bụi trong tia sáng, vết xước, hơi nước trên kính, nhiễu cảm biến tự nhiên, handheld micro-shake hoặc autofocus hunting chỉ được thêm khi hợp địa điểm, thời đại, loại ống kính và phong cách; không biến chúng thành yêu cầu bắt buộc cho mọi cảnh.
6. **Chốt một cảm xúc thị giác thống nhất.** Nếu cần, thêm một câu `Final Feel` ngắn để liên kết nhịp, ánh sáng và biểu cảm. Không đưa sự kiện mới, cảm xúc trái kịch bản hoặc lời thoại vào dòng này.

### 7.9.1. Cấu trúc prompt thao tác theo từng video mode

Các khung sau là chỉ dẫn soạn prompt, không phải văn bản literal. Thay nội dung trong ngoặc vuông bằng thông tin đúng từ kịch bản, asset và shot hiện tại; luôn thêm timestamp cục bộ khi cần và ba dòng `VO`, `SFX`, `Continuity`.

| Mode | Nội dung cần khóa trong prompt | Tránh |
|---|---|---|
| `t2v` | Đại cảnh/establishing; môi trường, địa hình, kiến trúc, thời tiết và biến chuyển không gian; ánh sáng và quang học. | Nhân vật chính có nhận diện phức tạp khi không có ảnh tham chiếu. |
| `r2v` | Handle nhân vật, tuổi/ngoại hình cần thiết, signature outfit; hành động vật lý chậm; địa điểm/đạo cụ khớp các ảnh tham chiếu. | Đổi khuôn mặt/trang phục hoặc mô tả bối cảnh không khớp reference nodes. |
| `extend_video` | Cùng framing, lens, góc máy, bố cục, bối cảnh, ánh sáng và đạo cụ clip Veo trước; bắt đầu từ pose cuối rồi phát triển hành động liên tục. | Cắt shot, đổi góc máy, nhảy bối cảnh hoặc đổi trang phục đột ngột. |
| `i2v` từ video/frame cuối | Mở từ chính tư thế/frame cuối nguồn; nếu đổi góc máy thì nói rõ góc mới; giữ identity, outfit và quan hệ không gian. | Mô tả tư thế mở đầu mâu thuẫn với frame cuối nguồn. |
| `video_reference` | Nêu rõ motion/composition nào của video nguồn cần giữ và những gì ảnh tham chiếu được phép thay đổi (nhân vật, outfit, style, atmosphere); dùng Omni `abra_edit`. | Yêu cầu vừa giữ nguyên vừa thay đổi cùng một đặc tính; dùng nhiều video source khi mode chỉ nhận một nguồn video. |

### 7.9.2. Lựa chọn prompt anchors

- Ưu tiên mô tả cụ thể, quan sát được về camera, hành động, nguồn sáng, bề mặt, vật lý và ống kính; các cụm như `Cinematic motion`, `Natural physics`, `Subtle movement` chỉ dùng khi thực sự hữu ích.
- Hạn chế `super fast crazy action`, `explosive rapid movements` và nhiều chủ thể/hành động độc lập trong cùng một shot hẹp vì làm mất khả năng theo dõi chủ thể và tăng nguy cơ nhòe/biến dạng.
- Tránh dựa vào từ tự khen chất lượng như `masterpiece`, `ultra realistic`, `trending on artstation`; không dùng `4K`/`8K` thay cho mô tả ánh sáng, chất liệu, chuyển động và optics cụ thể.
- Prompt bối cảnh gốc dùng làm reference vẫn phải hoàn toàn không có người theo mục 2.2.2; quy tắc này không cấm nhân vật xuất hiện trong prompt/node video khi có edge reference nhân vật phù hợp.

### 7.10. Checklist prompt cho từng video

Trước khi xuất từng node video, tự rà soát đủ các tiêu chí dưới đây. Các quy tắc về reference chỉ áp dụng cho node ảnh bối cảnh; nhân vật chính vẫn được phép xuất hiện trong prompt video khi có edge reference character. Áp dụng yêu cầu chi tiết tương ứng cho mọi node ảnh theo phần **Yêu cầu bắt buộc về độ chi tiết của prompt ảnh và video**.

| STT | Tiêu chí | Câu hỏi kiểm tra |
|---:|---|---|
| 1 | Character Bible | Gọi đúng handle; khuôn mặt, tóc, signature outfit và phụ kiện có nhất quán với node gốc không? |
| 2 | World Bible | Bối cảnh khớp node image, có layout/chi tiết môi trường hữu ích và node ảnh reference hoàn toàn không có người không? |
| 3 | Sequential Action | Hành động có điểm bắt đầu, diễn tiến, tương tác vật lý và phản ứng quan sát được theo thứ tự không? |
| 4 | Timestamp | Mốc trong prompt dùng thời gian cục bộ clip và kết thúc đúng `generation.duration_s` không? Với audio, timeline tuyệt đối bên ngoài prompt vẫn khớp segment không? |
| 5 | Camera | Góc máy, framing, hướng chuyển động và `generation.camera` (`dynamic`/`static`) có thống nhất không? |
| 6 | Negative Constraints | Đã loại trừ đúng yếu tố không mong muốn của cảnh mà không phủ định nhầm chủ ý (ví dụ cấm người trong shot có nhân vật chính) chưa? |
| 7 | Physical Realism | Tay chân, tiếp xúc đạo cụ, trọng lực, quán tính, vật liệu, thời tiết và ánh sáng có hợp lý, không mâu thuẫn hoặc làm vật thể biến mất không? |
| 8 | Scene Specificity | Bối cảnh có địa điểm, bố cục và chi tiết môi trường cụ thể thay vì mô tả chung chung không? |
| 9 | Visible Emotion | Cảm xúc được thể hiện bằng ánh mắt, nét mặt, tư thế hoặc cử chỉ quan sát được thay vì chỉ gắn nhãn cảm xúc không? |
| 10 | Concrete Action | Hành động nói rõ nhân vật làm gì, tương tác với vật nào/môi trường nào và diễn tiến ra sao trong thời lượng clip không? |
| 11 | VO/SFX/Continuity | Có đủ ba dòng; VO giữ nguyên lời thoại audio nếu có hoặc đúng lựa chọn thoại của người dùng; SFX là âm thanh môi trường cụ thể; Continuity nêu đúng source/asset/segment cần nối không? |

Với từng node `image`, kiểm tra riêng: prompt mô tả một khoảnh khắc tĩnh rõ ràng, bối cảnh cụ thể, pose/hành động, biểu cảm nhìn thấy được nếu có nhân vật, ánh sáng/bố cục; không sao chép prompt của node khác rồi chỉ thay tên nhân vật hoặc địa điểm.
---

### 8.3. Node video — giữ generation hiện có và thêm video_file

```json
{
  "id": "node-003",
  "title": "Shot 01: Dò radio trong boong-ke",
  "type": "video",
  "prompt": "[00:00–00:04 — ACTION START] Medium close-up, 50mm lens. The 28-year-old Vietnamese man (@Nam_28t), wearing his signature dark grey field jacket over a black t-shirt, slowly extends his right hand toward the brass dial of a vintage military radio on the worn wooden desk. [00:04–00:08 — ACTION PROGRESSION] He gently turns the dial, then freezes and listens as faint Morse code crackles through static. Underground bunker atmosphere, cold teal radar glow and warm practical rim light, shallow depth of field. Subtle handheld tracking with natural micro-shake. Believable physics: natural fingers remain in contact with the dial, radio stays anchored, no floating objects, no distorted anatomy, no crowds, no modern logos, no CGI artifacts. Cinematic film, 35mm lens, photorealistic.\nVO: \"Mọi đường dây liên lạc đã đứt, chỉ còn tiếng rè của màn đêm.\"\nSFX: \"Tiếng rè tĩnh điện radio, tiếng xoay núm kim loại, hơi thở nặng nề.\"\nContinuity: \"Giữ diện mạo @Nam_28t từ node-001 và bối cảnh boong-ke từ node-002.\"",
  "generation": {
    "backend": "flow",
    "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
    "model": { "family": "veo", "quality": "lite", "id": "veo_3_1_r2v_lite" },
    "resolution": "720p",
    "duration_s": 8,
    "camera": "dynamic",
    "video_mode": "r2v",
    "connected_video_mode": "r2v",
    "operation": "gen_video",
    "variants": 1
  },
  "properties": {
    "start_time": 5.0,
    "end_time": 13.0,
    "duration": 8.0,
    "video_file": "videos/video_001.mp4",
    "charVibe": "cinematic",
    "action": "@Nam_28t thận trọng dò tần số đài radio",
    "cameraDetail": "Medium close-up, 50mm lens, subtle handheld tracking"
  },
  "status": "idle"
}
```

