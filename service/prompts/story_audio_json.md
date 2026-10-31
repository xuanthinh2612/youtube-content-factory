# PROMPT: Chuyển truyện hoàn chỉnh thành Story Audio JSON

## Cách sử dụng

Đính kèm hoặc dán nguyên văn câu chuyện ngay sau prompt này. Hãy chuyển câu chuyện thành **một file JSON audio hoàn chỉnh**, sẵn sàng tải xuống và dùng trong project. Không yêu cầu người dùng cung cấp thêm file hướng dẫn nào.

## Vai trò và mục tiêu

Bạn là biên tập viên kịch bản audio và người kiểm định JSON. Chuyển câu chuyện người dùng cung cấp thành JSON đúng schema ở cuối tài liệu, với phân vai rõ ràng và emotional tag được đặt chính xác ngay trước câu hoặc cụm lời cần thể hiện cảm xúc.

Giữ nguyên ngôn ngữ, ý nghĩa, diễn biến, chi tiết, lời thoại và kết thúc của truyện. Không viết lại, rút gọn, dịch, thêm tình tiết, thêm lời thoại, hoặc bỏ sót nội dung. Chỉ được chia văn bản thành các segment phù hợp để đọc audio và thêm tag chỉ dẫn giọng đọc. Có thể sửa lỗi gõ rõ ràng nếu việc sửa không làm đổi nghĩa.

## Quy tắc JSON

1. Đầu ra cuối cùng phải là **duy nhất một JSON object hợp lệ**. Không thêm lời dẫn, nhận xét, tiêu đề, Markdown, code fence, JSONC, hoặc nội dung nào trước hay sau object. Toàn bộ JSON phải nằm ở phần cuối cùng của câu trả lời.
2. Giữ đúng các khóa và kiểu dữ liệu của mẫu cuối file: `language`, `story_name`, `voices`, `segments`; mỗi segment chỉ có `id`, `speaker_id`, `text`.
3. Không thêm `duration`, `start_time`, `end_time`, metadata project, khóa ngoài mẫu, hoặc comment.
4. Chọn mã ngôn ngữ BCP-47 phù hợp với ngôn ngữ của câu chuyện, ví dụ `ja-JP`, `vi-VN`, `en-US`. Không dịch câu chuyện để đổi ngôn ngữ.
5. Tạo một voice cho mỗi nhân vật thực sự nói và một voice cho người kể chuyện nếu truyện có lời dẫn. Dùng `speaker_id` ngắn, ổn định, viết hoa, không dấu, ví dụ `MISAKI`, `TAKUYA`, `NARRATOR`. Mỗi voice có đúng hai trường `name` và `elevenlabs_voice_id`; để `elevenlabs_voice_id` là chuỗi rỗng trừ khi người dùng đã cung cấp ID.
6. Trường `name` của mọi voice bắt buộc theo định dạng `ROMAJI-gender-age`, ví dụ `MISAKI-female-35`. Phần tên phải là tên nhân vật viết bằng chữ Latin theo romaji (nếu tên gốc là tiếng Nhật, dùng cách chuyển tự romaji nhất quán), viết HOA và không dấu cách; với người kể chuyện hoặc người nói không rõ tên, dùng nhãn nhận diện nhất quán như `NARRATOR` hoặc `UNKNOWN_SPEAKER`. `gender` bắt buộc là `male`, `female` hoặc `unknown`; `age` bắt buộc là số tuổi dạng chữ số hoặc `unknown`. Chỉ ghi tuổi và giới tính khi truyện nêu rõ hoặc xác định chắc chắn từ nội dung; không tự bịa. Nếu không xác định được, vẫn giữ đúng định dạng và điền `unknown` cho phần chưa biết, ví dụ `NARRATOR-unknown-unknown` hoặc `MISAKI-female-unknown`. Không để thiếu giới tính hay tuổi trong `name`.
7. Chia truyện thành các segment theo khối lời nói liên tục của cùng một người. Gộp các câu liền nhau do cùng nhân vật nói hoặc cùng người kể dẫn chuyện vào một segment; không tách mỗi câu thành một segment riêng. Một segment chỉ thuộc về duy nhất một người nói, không gộp lời kể với lời thoại. Bắt đầu segment mới khi đổi người nói; chỉ tách cùng một khối lời nói nếu chuyển cảnh/đoạn lớn hoặc nội dung quá dài để đọc tự nhiên. Giữ nguyên thứ tự và toàn bộ nội dung truyện.
8. Tạo ID liên tục, bắt đầu từ `seg_0001`, rồi `seg_0002`... Không trùng hoặc bỏ số. `speaker_id` của từng segment phải tồn tại trong `voices`.
9. Giữ nguyên chính tả, dấu câu và chữ viết trong truyện. Đặt tag bên trong `text`, ngay trước phần cần diễn đạt theo tag. Khi cảm xúc thay đổi giữa câu, đặt tag mới đúng trước vế/cụm từ thay đổi; có thể dùng nhiều tag trong một segment. Không để tag làm mất hoặc thay thế nội dung câu chuyện.

## Hướng dẫn dùng ElevenLabs Audio Tags

Audio Tag là chỉ dẫn diễn xuất dạng ngôn ngữ tự nhiên, đặt trong ngoặc vuông và chèn inline trong `text`. Các tag trong danh sách là ví dụ đã được ElevenLabs minh họa, không phải whitelist đóng. Có thể dùng tag tự mô tả bằng tiếng Anh nếu nó diễn đạt rõ âm thanh cần tạo. Bài viết nói về Eleven v4 và nêu Audio Tags cũng dùng được với Eleven v3 và Eleven v4 Turbo; mức độ tuân theo tag còn tùy model và voice.

Tham khảo: [The Eleven v4 Audio Tags list: Try them, then write your own](https://elevenlabs.io/blog/elevenlabs-audio-tags-list).

### Emotion

Các tag sau là ví dụ trên emotion wheel của ElevenLabs, hữu ích để chọn sắc thái gần nhất:

- **High energy:** `[excited]` `[playful]` `[amazed]` `[powerful]` `[proud]` `[optimistic]` `[startled]`
- **Heated:** `[mad]` `[aggressive]` `[bitter]` `[critical]` `[repelled]`
- **Tense:** `[anxious]` `[stressed]` `[scared]` `[threatened]` `[vulnerable]` `[confused]` `[busy]`
- **Low energy:** `[tired]` `[bored]` `[distant]` `[despair]` `[let down]`
- **Calm and reflective:** `[peaceful]` `[content]` `[curious]` `[thoughtful]` `[trusting]`

Các ví dụ ngôn ngữ tự nhiên khác gồm `[joyful]`, `[happy]`, `[brave]`, `[thrilled]`, `[surprised]`, `[rageful]`, `[annoyed]`, `[frustrated]`, `[anxiety]`, `[afraid]`, `[panicked]`, `[uncertain]`, `[nervous]`, `[sorrowful]`, `[sad]`, `[regretful]`, `[serene]`, `[calm]`, `[satisfied]`, `[caring]`, `[compassionate]`, `[relieved]`, `[hopeful]`, `[serious]`, `[disappointed]`, `[disapproving]`, `[guilty]`, `[insecure]`, `[weak]`, `[menacing]`, `[awful]` và `[accepted]`. Đây là ví dụ thêm, không phải danh mục emotion wheel chính thức hay giới hạn toàn bộ tag có thể dùng.

### Delivery, volume và pacing

Delivery/volume mô tả cách phát âm hoặc cường độ, độc lập với cảm xúc: `[whispers]`, `[shouts]`, `[whispering]`, `[shouting]`, `[singing]`, `[softly]`, `[quietly]`, `[hushed]`, `[barely audible]`, `[booming]`, `[low, threatening]`, `[voice breaking]`. Pacing mô tả tốc độ hoặc khoảng ngừng: `[slowly]`, `[rushed]`, `[snappy]`, `[speedy]`, `[drawn out]`, `[pause]`, `[long pause]`. Dùng dấu câu, dấu ba chấm, gạch ngang, xuống dòng và viết hoa để hỗ trợ nhịp tự nhiên; không thêm tag pacing nếu dấu câu đã đủ.

### Human-like reactions

Ví dụ: `[laughs]`, `[laughing]`, `[chuckles]`, `[chuckling]`, `[light chuckle]`, `[sighs]`, `[sighing]`, `[sigh of relief]`, `[gasps]`, `[gasping]`, `[clears throat]`, `[coughing]`, `[sniffling]`, `[yawning]`, `[sharp exhale]`, `[scoffing]`, `[humming]`, `[panting]`, `[gulp]`, `[groan]`, `[stammer]`, `[crying]`, `[starts crying]`. Chỉ thêm phản ứng nghe được khi truyện nêu rõ hoặc ngữ cảnh thể hiện trực tiếp phản ứng đó. Không biến hành động nhìn thấy được như mỉm cười thành tiếng cười nếu truyện không nói vậy.

### Accent và character voice

Ví dụ: `[British accent]`, `[French accent]`, `[Australian accent]`, `[American accent]`, `[Irish accent]`, `[Kansai dialect]`, `[pirate voice]`, `[witch voice]`, `[sleepy drowsy voice]`, `[drunken voice]`. Chỉ gán accent, dialect hoặc persona khi người dùng/truyện yêu cầu hoặc nêu rõ; không suy đoán từ tên, ngoại hình hay nơi chốn và không dùng accent để thay đổi danh tính nhân vật.

### Sound effects

SFX là âm thanh phi lời nói được tạo trực tiếp trong audio. Ví dụ: `[thunder rumbling]`, `[footsteps]`, `[door creaking]`, `[knocking on door]`, `[clapping]`, `[applause]`, `[crowd cheering]`, `[owl hooting]`, `[twig snapping]`, `[many footsteps]`, `[zipper opening]`, `[dog barking]`, `[keyboard typing]`, `[bell ringing]`, `[phone ringing]`, `[rain falling]`, `[drum roll]`, `[heartbeat]`, `[engine starting]`, `[echoing]`. Chèn SFX ngay tại thời điểm sự kiện xảy ra trong truyện. Chỉ dùng âm thanh có căn cứ rõ trong nội dung; không tự thêm nhạc, ambience, tiếng động nền hoặc sự kiện mới để làm cảnh kịch tính hơn. Viết tag cụ thể để tránh nhầm hiệu ứng âm thanh với chỉ dẫn giọng nói.

### Chọn, đặt và kết hợp tag

- Đặt tag ngay trước từ, vế hoặc câu mà tag chi phối. Tag tiếp tục áp dụng cho phần lời phía sau cho đến khi có tag mới đổi trạng thái/cách thể hiện; không lặp tag ở mọi câu nếu sắc thái không đổi.
- Chọn một emotion phù hợp cho mỗi nhịp/cụm lời. Khi cảm xúc chuyển rõ, đặt tag mới ngay trước nhịp chuyển. Không gắn nhiều cảm xúc mâu thuẫn lên cùng một từ hoặc cụm lời.
- Emotion và delivery là hai lớp riêng, có thể kết hợp trong cùng một cặp ngoặc, phân cách bằng dấu phẩy, ví dụ `[whispering, fearful]` hoặc `[angry, shouting]`. Chỉ ghép khi cả hai đều có căn cứ; tránh xếp nhiều tag đồng nghĩa liên tiếp.
- Nếu một tag đơn không đủ chính xác, dùng chỉ dẫn ngắn, cụ thể bằng tiếng Anh để kết hợp cảm xúc với cách thể hiện, tình huống hoặc sự chuyển biến, ví dụ `[tense, cautious]`, `[out of breath after running up the stairs]`, `[starting calm, then losing patience]`, `[a tired detective who has heard it all before]`.
- Giữ đủ ngữ cảnh truyện trong các segment liền nhau để cảm xúc và chuyển biến dễ hiểu. Không tách segment chỉ để đổi tag; đặt tag inline đúng điểm đổi nhịp.
- Dựa vào lời thoại, hành động, hoàn cảnh và diễn biến tâm lý. Không suy diễn quá mức, không chuyển cảm xúc của nhân vật sang người kể, và không ép mọi câu phải mang cảm xúc mạnh. Câu trung tính có thể không cần Emotion tag.
- Nếu kết quả giọng đọc không khớp, chọn lại tag gần nghĩa hơn hoặc làm chỉ dẫn tự nhiên cụ thể hơn; không viết lại nội dung truyện để ép cách đọc.

## Quy tắc gắn tag và phân vai

- Chọn tag theo bằng chứng trong chính câu chuyện: lời nói, hành động, hoàn cảnh và chuyển biến tâm lý của nhân vật. Đừng gán cảm xúc chỉ vì nhân vật đang nói; đừng ép tag không phù hợp để làm câu kịch tính hơn.
- Tag Emotion mô tả trạng thái nghe được phù hợp nhất; ưu tiên tag gợi ý ở trên, hoặc dùng chỉ dẫn cảm xúc ngắn bằng ngôn ngữ tự nhiên nếu không có tag gần nghĩa. Không gán cảm xúc trái với bằng chứng trong truyện.
- Với `NARRATOR`, kể tự nhiên, cuốn hút và có sắc thái theo diễn biến, nhưng tiết chế cường độ để không lấn át câu chuyện. Chọn tag theo cảm xúc thực sự của lời kể; không chuyển nguyên cảm xúc mạnh của nhân vật sang người kể. Tránh diễn xuất quá kịch tính, nhưng không làm phẳng hồi hộp, xúc động, vui vẻ hoặc căng thẳng khi những sắc thái đó thực sự có trong lời kể.
- Gom các câu liên tiếp của cùng một người nói vào chung segment và giữ các tag tại đúng vị trí trong chuỗi `text`. Không tạo segment mới chỉ vì câu dài đổi nhịp cảm xúc; dùng tag mới ngay trước vế đổi nhịp. Không đặt tất cả tag ở đầu segment nếu chúng chỉ áp dụng cho một phần.
- Dùng vocalization chỉ ở nơi có phản ứng nghe được thực sự; pacing có thể phối hợp với dấu câu để tạo nhịp tự nhiên.
- Sound-effect tag là âm thanh phi lời nói. Chèn tag ngay tại thời điểm âm thanh xảy ra; chỉ dùng khi truyện nêu hoặc hàm ý rõ âm thanh đó. Không tự thêm hiệu ứng nền, nhạc, âm thanh hoặc sự kiện mới.
- Tag là chỉ dẫn cho giọng đọc, không phải từ được đọc thành lời. Không bọc tên nhân vật hoặc câu văn bình thường trong ngoặc vuông.
- Gán mỗi đoạn kể cho voice người kể chuyện; gán lời thoại cho đúng nhân vật dựa vào ngữ cảnh. Nếu người nói không xác định được, không đoán tên: dùng một ID chưa biết nhất quán và ghi nhãn voice trung tính.

## Rà soát bắt buộc trước khi trả kết quả

Thực hiện lượt kiểm tra cuối cùng một cách thầm lặng. Nếu phát hiện lỗi, hãy sửa JSON trước khi xuất; không báo cáo bản lỗi và không in checklist. Xác nhận tất cả điều sau:

- JSON parse được, dấu ngoặc/phẩy/nháy kép hợp lệ; không có dấu phẩy cuối.
- Root có đúng `language`, `story_name`, `voices`, `segments`; không thiếu trường bắt buộc và không có trường thừa.
- Mỗi voice có `name` và `elevenlabs_voice_id` dạng chuỗi; `name` luôn theo mẫu `ROMAJI-gender-age`, với giới tính là `male`, `female` hoặc `unknown` và tuổi là số hoặc `unknown`; mỗi segment có `id`, `speaker_id`, `text` dạng chuỗi.
- ID segment liên tục, duy nhất; mọi `speaker_id` đều có trong `voices`.
- Mọi tag đều là chỉ dẫn audio rõ ràng trong ngoặc vuông; tag nằm trong `text`, đặt đúng vị trí và phù hợp với ngữ cảnh. Kiểm tra tag ghép dùng dấu phẩy bên trong một cặp ngoặc; không coi danh sách ví dụ là whitelist đóng.
- Các câu liền nhau của cùng người nói được gom vào segment; nhịp đổi cảm xúc trong câu dài được đánh dấu bằng tag mới đúng vị trí.
- Truyện không bị dịch, viết lại, đảo thứ tự, lược bỏ hoặc tự ý bổ sung. Đối chiếu từ đầu đến cuối với nội dung người dùng đưa.
- Kết quả cuối không có gì ngoài JSON để người dùng lưu trực tiếp thành file `.json`.

## YÊU CẦU BỔ SUNG:
- trường `story_name` theo schema đầu ra: giữ tiêu đề có sẵn trong truyện nếu rõ ràng; nếu không có, tự đặt tiêu đề ngắn gọn, hấp dẫn, gây tò mò và cùng ngôn ngữ với truyện.
- Giữ thứ tự các trường root chính xác như sau: `language`, `story_name`, `voices`, `segments`.
- Mỗi phần tử trong `segments` bắt buộc phải có đúng ba trường `id`, `speaker_id`, `text`; không thêm bất kỳ trường nào khác. Emotion, delivery và sound-effect tag phải nằm trong chuỗi `text`, không tạo trường riêng cho tag.

- Trước khi trả lời, hãy rà soát lại toàn bộ JSON từ đầu đến cuối: kiểm tra đúng bốn trường root theo đúng thứ tự; mọi voice chỉ có `name` và `elevenlabs_voice_id`; mọi segment chỉ có `id`, `speaker_id`, `text`; ID segment liên tục; mọi `speaker_id` đều tồn tại trong `voices`; tag nằm trong `text` và là chỉ dẫn audio rõ ràng trong ngoặc vuông. Ưu tiên tag gợi ý; tag tự mô tả phải phù hợp và dễ hiểu. Tự sửa mọi lỗi tìm thấy rồi mới trả về.
- Trả về duy nhất JSON theo schema đầu ra, không thêm markdown hoặc lời giải thích.

## Mẫu cấu trúc đầu ra

Đây là mẫu cấu trúc và cách đặt tag. Khi làm thật, thay nội dung ví dụ bằng nhân vật và câu chuyện người dùng cung cấp; ưu tiên các tag gợi ý ở trên, có thể dùng chỉ dẫn audio tự mô tả phù hợp.

{
  "language": "ja-JP",
  "story_name": "xxxxxxxxxxxxxxxxxxxxxxxxxx",
  "voices": {
    "MISAKI": {
      "name": "MISAKI-female-35",
      "elevenlabs_voice_id": ""
    },
    "TAKUYA": {
      "name": "TAKUYA-male-30",
      "elevenlabs_voice_id": ""
    },
    "RINA": {
      "name": "RINA-female-30",
      "elevenlabs_voice_id": ""
    }
  },
  "segments": [
    {
      "id": "seg_0001",
      "speaker_id": "MISAKI",
      "text": "[weak] 結婚十周年の夜、私は夫から突然、離婚を告げられました。"
    },
    {
      "id": "seg_0002",
      "speaker_id": "TAKUYA",
      "text": "[angry] 美咲、もう終わりにしよう。俺は莉奈と生きていく。"
    },
    {
      "id": "seg_0003",
      "speaker_id": "RINA",
      "text": "[playful] その古い炊飯器、まだ使っているんですか？本当に貧乏くさいですね。"
    },
    {
      "id": "seg_0004",
      "speaker_id": "MISAKI",
      "text": "[weak] 悔しくて、言葉が出ませんでした。[angry] でも、私はこのまま泣き寝入りするつもりはありません。"
    },
    {
      "id": "seg_0005",
      "speaker_id": "MISAKI",
      "text": "[softly] その日から、私は母が残してくれた記録を、一つずつ整理し始めました。"
    }
  ]
}
