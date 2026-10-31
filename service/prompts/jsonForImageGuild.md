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

#### 2.2.3. Quy tắc bắt buộc tạo ảnh truyện đúng nội dung và giữ continuity giữa các node

Trước khi viết prompt cho bất kỳ ảnh truyện nào, đọc toàn bộ cốt truyện/audio script và dựng một mạch hình ảnh thống nhất từ đầu đến cuối. Không tạo prompt từng node một cách rời rạc. Dùng storyboard/scene map và continuity bible làm chuẩn xuyên suốt project; đây là tài liệu lập kế hoạch nội bộ, không tự thêm các trường JSON ngoài schema chỉ để lưu chúng.

**Giới hạn độ dài và mức độ chi tiết bắt buộc cho mọi prompt ảnh**

- Mọi `prompt` dùng để tạo ảnh phải tự mô tả đầy đủ hình ảnh cần tạo, cụ thể và bám sát đúng chức năng node: ảnh nhân vật, ảnh tham chiếu bối cảnh/đạo cụ hoặc ảnh truyện trên timeline. Không viết prompt sơ sài/chung chung, không chỉ ghi tên nhân vật/địa điểm, và không trông chờ model tự đọc cốt truyện hay tự suy ra các chi tiết quan trọng từ node khác.
- Tùy loại ảnh, prompt phải nêu đủ các chi tiết áp dụng: chủ thể và nhận diện nhân vật; số người/vai trò/vị trí trong khung; hành động hoặc khoảnh khắc tĩnh; nét mặt/tư thế; bối cảnh và bố cục không gian; đạo cụ và trạng thái; cỡ cảnh/góc nhìn/bố cục; ánh sáng, thời gian/thời tiết, màu sắc và không khí; phong cách hình ảnh; ràng buộc cần giữ và chi tiết cần tránh. Với ảnh bối cảnh `reference_only`, mô tả đầy đủ kiến trúc/bố trí/ánh sáng nhưng tuyệt đối không có người. Với ảnh timeline có thoại, áp dụng thêm quy tắc khớp speaker ở mục B.
- Prompt timeline sau vẫn phải mô tả đủ nội dung của ảnh hiện tại; ảnh reference/edge trước đó chỉ bổ sung continuity, không thay thế mô tả về nhân vật, blocking, quần chúng, đạo cụ, hành động và khung hình cần tạo.
- **Giới hạn cứng:** giá trị văn bản của từng trường `node.prompt` tạo ảnh phải có ít hơn 10.000 ký tự (tối đa 9.999 ký tự sau khi JSON được parse). Tính từng prompt riêng, không tính toàn bộ JSON. Không được cắt prompt giữa câu hoặc bỏ yêu cầu cốt truyện/continuity để đạt giới hạn; hãy bỏ phần lặp, tính từ thừa và diễn giải trùng trước, nhưng giữ đủ thông tin hình ảnh thiết yếu.
- Trước khi xuất JSON, đếm/ước lượng có kiểm soát độ dài từng prompt ảnh và xác nhận mọi prompt đều không vượt 9.999 ký tự. Nếu một prompt vượt giới hạn, viết gọn lại rồi rà soát lại độ đầy đủ và đếm lại; không để prompt nào vượt giới hạn.

**A. Khóa Character Bible và Scene Bible trước khi tạo ảnh**

- Với mỗi nhân vật, xác định một handle và một node `character` duy nhất. Ghi rõ các đặc điểm nhận diện ổn định có căn cứ trong truyện: khuôn mặt, tóc, tuổi/diện mạo, vóc dáng, trang phục, phụ kiện và đạo cụ riêng. Mọi ảnh có nhân vật đó phải dùng đúng node tham chiếu và giữ nguyên các đặc điểm này; chỉ thay đổi khi truyện nói rõ nhân vật đã thay đồ, bị thương, già đi hoặc có thay đổi ngoại hình.
- Với mỗi địa điểm, lập một hồ sơ bối cảnh nhất quán: sơ đồ không gian và hướng nhìn, cửa ra vào/cửa sổ, vị trí bàn ghế và vật thể lớn, hướng ánh sáng, thời điểm, thời tiết, bảng màu cùng các chi tiết nhận diện. Dùng đúng một ảnh tham chiếu gốc cho cùng một địa điểm và tái sử dụng nó ở tất cả ảnh thuộc địa điểm đó. Ảnh tham chiếu bối cảnh vẫn phải trống người theo quy tắc `reference_only`.
- Với mỗi cảnh liên tục, ghi rõ nhân vật hiện diện, vị trí tương đối của từng người, hướng ngồi/đứng và hướng nhìn, đạo cụ/vật thể đang ở đâu và trạng thái của chúng, cùng những nhân vật phụ/quần chúng đã được xác lập. Ví dụ: nếu một cuộc họp có A ngồi bên trái bàn, B ngồi bên phải và 10 nhân viên ở các hàng ghế phía sau, hãy giữ đúng bố cục và sự hiện diện của nhóm nhân viên trong mọi ảnh tiếp theo của cùng cảnh, trừ khi diễn biến cho thấy họ rời đi hoặc vị trí thay đổi.
- Không tự thêm nhân vật, quần chúng, đạo cụ hoặc chi tiết cốt truyện. Tuy nhiên, cũng không được làm biến mất người/đạo cụ đã hiện diện và vẫn cần tiếp tục có mặt theo scene map chỉ vì prompt mới không nhắc lại. Phân biệt nhân vật có tên với quần chúng nền; quần chúng không trở thành character node trừ khi họ có vai trò nhân vật theo workflow chung.

**B. Mỗi prompt ảnh phải mô tả chính xác beat và đúng người đang nói**

- Với mỗi node `timeline_visual`, viết prompt riêng, mô tả cụ thể một khoảnh khắc tĩnh đúng với beat mà ảnh minh họa: ai xuất hiện, vị trí của từng người trong khung hình, hành động, nét mặt/tư thế, địa điểm, đạo cụ, bố cục/cỡ cảnh và trạng thái nối tiếp từ ảnh trước. Prompt phải khớp cốt truyện và thời điểm tương ứng; không dùng prompt chung chung kiểu chỉ nhắc tên địa điểm hoặc cảm xúc.
- Nếu có audio JSON, đối chiếu trực tiếp `speaker_id`, `voices` và `audio_segment_ids`. Khi ảnh thể hiện người đang nói, người đó phải đúng là speaker của câu/đoạn được gán cho ảnh; mô tả rõ họ đang nói và không gán lời/khẩu hình nói cho nhân vật khác. Những nhân vật khác trong ảnh phải ở trạng thái phù hợp (đang nghe, phản ứng, im lặng...).
- Nếu ảnh là reaction shot/cảnh minh họa người nghe trong khi lời thoại vẫn tiếp tục, ghi rõ speaker là người ngoài khung/voice-over và nhân vật đang thấy trong ảnh chỉ đang nghe hoặc phản ứng, không phải người nói. Nếu truyện không xác định ai đang nói hoặc không có lời thoại tại beat đó, không tự bịa speaker hay miệng đang nói.
- Chỉ nối edge từ các node `character` của nhân vật thực sự có mặt trong ảnh; không nối character của speaker nếu người đó chỉ là voice-over/ngoài khung và không xuất hiện. Đồng thời nối đúng node ảnh tham chiếu của địa điểm và đạo cụ nhận diện thực sự có trong ảnh. Nội dung prompt, danh sách nhân vật, `speaker_id`/segment và edges phải khớp nhau.

**C. Continuity bắt buộc giữa các ảnh liên tiếp trong cùng một cảnh**

- Phân biệt *đổi shot* với *đổi cảnh*: nhiều node ảnh có thể là các góc/cỡ cảnh khác nhau nhưng vẫn thuộc cùng một cảnh liên tục. Trước khi soạn prompt, nhóm beat theo scene/location và xác định trạng thái đầu vào của từng beat từ ảnh timeline ngay trước đó.
- Với node ảnh tiếp theo trong cùng một cảnh liên tục, bắt buộc dùng ảnh timeline gần nhất trước đó của chính cảnh đó làm ảnh tham chiếu continuity, bên cạnh các node `character` và ảnh bối cảnh/đạo cụ gốc cần thiết. Tạo edge từ ảnh timeline trước đó đến node ảnh hiện tại để truyền bố cục/trạng thái đã thiết lập; đồng thời giữ edges tới đúng character và scene reference. Các edge này biểu thị dependency tham chiếu, không thay đổi thứ tự hoặc thời gian timeline. Đảm bảo graph vẫn là DAG.
- Không chỉ dựa vào chân dung character và ảnh bối cảnh trống: chúng không thể thể hiện vị trí ghế, số lượng/vị trí quần chúng, blocking của nhóm, trạng thái đạo cụ hoặc bố cục cụ thể đã xuất hiện ở ảnh trước. Prompt node sau phải nêu rõ các yếu tố nào được kế thừa từ ảnh trước và chỉ ra phần nào thay đổi trong beat hiện tại.
- Giữ nguyên trục không gian, hướng trái/phải, vị trí tương đối của nhân vật, số lượng và phân bố quần chúng, vị trí đồ nội thất/đạo cụ, nguồn sáng, thời gian và thời tiết qua các ảnh của cùng cảnh. Góc máy/cỡ cảnh có thể thay đổi theo storyboard, nhưng không được làm căn phòng, vị trí nhân vật hoặc nhóm người tự thay đổi. Chỉ thay đổi yếu tố nào khi câu chuyện/beat thể hiện rõ hành động làm thay đổi nó; cập nhật continuity bible sau thay đổi để các ảnh sau kế thừa trạng thái mới.
- Khi chuyển sang địa điểm hoặc cảnh mới, không nối ảnh trước như thể đó là cùng không gian; dùng đúng scene reference của cảnh mới và chỉ giữ những trạng thái nhân vật/đạo cụ thực sự đi theo cốt truyện. Establishing/re-establishing shot chỉ được bỏ hoặc thay đổi nhân vật/quần chúng nếu lựa chọn khung hình đó hợp lý và không tạo mâu thuẫn với beat liên tục.
- Nếu workflow/backend hiện hành không nhận edge ảnh timeline → ảnh timeline làm nguồn tham chiếu, không xuất edge không hợp lệ. Trong trường hợp đó, prompt node hiện tại bắt buộc phải chép lại đầy đủ các chi tiết continuity đã xác lập từ ảnh trước vào chính prompt (blocking, người/quần chúng, đồ vật, trục không gian, ánh sáng và trạng thái); không được lặng lẽ bỏ continuity. Nhưng nếu edge loại này được hỗ trợ, phải nối ảnh trước theo quy tắc trên.

**D. Rà soát trước khi xuất JSON ảnh**

- Duyệt các ảnh timeline theo thứ tự: kiểm tra prompt từng ảnh với đúng beat/câu thoại, người đang nói, người thực sự có mặt, edges và scene bible. Không chấp nhận trường hợp A là speaker nhưng prompt/khẩu hình lại mô tả B đang nói, hoặc nhân vật không có trong beat tự xuất hiện.
- Với mỗi chuỗi ảnh cùng cảnh, so ảnh liền trước và liền sau: địa điểm, camera axis, blocking, chỗ ngồi, số lượng/vị trí nhân vật phụ, đạo cụ, thời gian và ánh sáng phải nhất quán; mọi thay đổi phải có nguyên nhân trong truyện và được ghi rõ trong prompt.
- Kiểm tra riêng độ dài từng `prompt` tạo ảnh sau khi parse JSON: tất cả phải dưới 10.000 ký tự và vẫn mô tả đầy đủ các chi tiết hình ảnh cần thiết. Rút gọn phần lặp nếu cần, không bỏ mất nội dung quan trọng.
- Nếu phát hiện thiếu người đã được xác lập, đổi chỗ nhân vật vô cớ, đạo cụ biến mất, nhầm speaker hoặc reference edge sai/thiếu, sửa prompt/edges và kiểm tra lại toàn bộ chuỗi cảnh liên quan trước khi xuất.

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

