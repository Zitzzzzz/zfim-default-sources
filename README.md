# 🎬 Kho Nguồn Phim Mặc Định cho zFim (zFim Official Sources Repository)

Kho nguồn cấu hình Addon chuẩn định dạng **zFim Addon JSON v1** dành cho ứng dụng xem phim đa nền tảng **zFim**. Được nghiên cứu, bóc tách và kiểm thử kỹ lưỡng trên môi trường Android Emulator thực tế.

---

## 🚀 Hướng Dẫn Thêm Vào App zFim

### Cách 1: Thêm Toàn Bộ Kho Nguồn (Khuyến Nghị - 1 Click)

1. Mở ứng dụng **zFim** trên thiết bị của bạn.
2. Điều hướng tới mục **Quản lý Nguồn** (Nút icon `+` hoặc `Kho Nguồn` trên thanh công cụ / Cài đặt).
3. Chọn **Thêm Kho Nguồn (Add Repository)**.
4. Dán đường link sau và bấm **Lưu / Đồng bộ**:
   ```text
   https://raw.githubusercontent.com/magicxlll/zfim-default-sources/main/repo.json
   ```
5. Tất cả các nguồn phim sẵn sàng sẽ xuất hiện trong danh sách. Bấm **Cài đặt** vào nguồn bạn muốn xem!

---

### Cách 2: Thêm Từng Nguồn Độc Lập (Single Addon Import)

Bạn cũng có thể copy và dán trực tiếp đường link Raw JSON của từng nguồn độc lập:

| Nguồn Phim | Link Raw JSON Nhập Vào zFim |
|---|---|
| **YanHH3D 4K** | `https://raw.githubusercontent.com/magicxlll/zfim-default-sources/main/addons/yanhh3d.json` |
| **KKPhim (Mọi thiết bị)** | `https://raw.githubusercontent.com/magicxlll/zfim-default-sources/main/addons/kkphim.json` |
| **HH3D.com** | `https://raw.githubusercontent.com/magicxlll/zfim-default-sources/main/addons/hh3d.json` |

---

## 📊 Bảng Tổng Hợp Kiểm Thử & Trạng Thái 8 Nguồn

Toàn bộ 8 nguồn được yêu cầu đã được kiểm thử trực tiếp trên ứng dụng **zFim** chạy trên Android Emulator (`emulator-5554`, Android SDK 35):

| # | Nguồn | Domain Gốc | Thể Loại | Trạng Thái | Cơ Chế Kỹ Thuật | Ghi Chú Kiểm Thử Thực Tế |
|:---:|---|---|:---:|:---:|:---:|---|
| **1** | **YanHH3D 4K** | `yanhh3d.plus` | Hoạt hình 3D | ✅ **Hoạt động tốt** | HTML Scraper (`scrape`) | 5 catalog, bóc tách đầy đủ tập, stream HLS M3U8 phát mượt mà qua media_kit. |
| **2** | **HoatHinh3D** | `hoathinh3d.pw` | Hoạt hình 3D | ⚠️ `needs-js` | Halim Encrypted Stream | Mã hóa AES-GCM với khóa phiên động tại `/wp-json/halim/v1/player-key`. Yêu cầu JS runtime để giải mã. |
| **3** | **HH3D.com** | `hh3d.com` | Hoạt hình 3D | ✅ **Hoạt động tốt** | HTML Scraper + Unwrapper | StreamUnwrapper bóc tách thành công stream plain M3U8 từ khối `data-obf` của server streaming. |
| **4** | **HHHTQ.Team** | `hhhtq.team` | Hoạt hình 3D | ⚠️ `needs-js` | Third-party Embeds | Nhúng qua iframe Dailymotion (`geo.dailymotion.com`), AbyssPlayer (`player.abyssplayer.com`), Rumble. Cần webview/JS. |
| **5** | **KKPhim** | `phimapi.com` | Phim lẻ & Bộ | ✅ **Hoạt động tốt** | REST API (`json`) | REST API v1 chuẩn JSON, trích xuất HLS Full HD 1080p siêu tốc độ, tải danh mục tức thì. |
| **6** | **VSMOV** | `vsmov.com` | Phim lẻ & Bộ | ⚠️ `needs-js` | Client JS Concatenation | Video player ghép nối link stream động trong iframe (`baseUrl + '/stream/' + hash + '/master.m3u8'`). |
| **7** | **PHIMMOI** | `phimmoic.bz` | Phim lẻ & Bộ | ⚠️ `needs-js` | Next.js Hydration | Player container render tĩnh trả về `BAILOUT_TO_CLIENT_SIDE_RENDERING`. Chỉ nạp video khi chạy React client. |
| **8** | **Motchill** | `motchilln.fm` | Phim lẻ & Bộ | ⚠️ `needs-js` | Next.js Hydration | Cấu trúc Next.js SPA tương tự PHIMMOI, không chứa stream URL tĩnh trong payload HTML. |

---

## 🔬 Chi Tiết Bóc Tách & Cơ Chế Hoạt Động Của Từng Nguồn

### 1. YanHH3D 4K (`addons/yanhh3d.json`)
- **Loại hình:** HTML Scraping tĩnh kết hợp bộ lọc stream.
- **Danh mục:** Mới Cập Nhật, Hoạt Hình 3D, Đang Chiếu, Hoàn Thành, Phim Lẻ.
- **Bóc tách danh sách:**
  - Item selector: `.flw-item`
  - Tên phim: `h3.film-name a @text`
  - Poster: `img.film-poster-img @data-src`
  - Chi tiết: `a.film-poster-ahref @href`
- **Stream:** Trích xuất candidate qua `a.btn3dsv, a.btn-play, iframe, video, source` với thuộc tính `data-src`, đi qua bộ lọc tên miền rác (`streamFilters.blocklistHosts`) và trả về trực tiếp luồng phát M3U8.

### 2. KKPhim (`addons/kkphim.json`)
- **Loại hình:** REST API JSON thuần (`json`).
- **Endpoint:**
  - Danh sách phim: `https://phimapi.com/danh-sach/phim-moi-cap-nhat?page={page}` (Map trường `items -> slug, name, poster_url`).
  - Chi tiết & Tập phim: `https://phimapi.com/phim/{slug}` (Map `movie.name`, `movie.poster_url`, `movie.content`, `episodes`).
- **Stream:** Sử dụng regex trích xuất luồng phát HLS trực tiếp:
  - Regex: `https?://[^\"'\\s]+\\.m3u8`
  - Stream được trả về dưới định dạng `direct-m3u8` Full HD (1920x1080) chất lượng cao.

### 3. HH3D.com (`addons/hh3d.json`)
- **Loại hình:** HTML Scraper + Trình bóc tách nâng cao (`streamUnwrapping: ["data-obf", "direct-m3u8"]`).
- **Danh mục:** Tiên Hiệp, Huyền Huyễn, Phiêu Lưu, Phim Lẻ.
- **Cơ chế bóc tách:**
  - Server streaming được định danh qua: `span.streaming-server, .streaming-server` với thuộc tính `data-link`.
  - Candidate HTML chứa container player bị làm mờ: `<div id="player" data-obf="...">`.
  - Bộ giải mã `StreamUnwrapper` của zFim tự động bóc tách chuỗi base64/obfuscated để tìm URL luồng HLS trực tiếp dạng plain stream (`https://cdn.donghua3d.top/.../stream-plain?t=...`).

---

## 🛡️ Tuân Thủ Tiêu Chuẩn Minh Bạch (Transparency Standard)

Theo nguyên tắc bóc tách dữ liệu của tài liệu `PROMPT-ADDON-JSON.md` (Quy tắc 2):
> *"Nếu trang web sử dụng cơ chế bảo vệ Cloudflare Turnstile/Bot Protection, mã hóa phức tạp không thể giải mã tĩnh, hoặc yêu cầu trình duyệt thực thi JavaScript nặng (SPA), Agent PHẢI trả về JSON với trường `unsupported: "needs-js"` (hoặc `needs-cloudflare`) kèm theo lý do cụ thể ở trường `reason`. Tuyệt đối không bịa CSS selector hoặc tạo JSON giả vờ chạy được."*

Vì vậy, 5 nguồn phụ thuộc hoàn toàn vào trình thực thi JavaScript trong trình duyệt (`hoathinh3d`, `hhhtq`, `vsmov`, `phimmoi`, `motchill`) đã được phân loại chính xác, trung thực kèm nguyên nhân kỹ thuật chi tiết trong thư mục `addons/`.

---

## 📁 Cấu Trúc Kho Nguồn

```text
zfim-default-sources/
├── README.md               # Tài liệu hướng dẫn sử dụng & báo cáo kỹ thuật
├── repo.json               # File Kho Nguồn tổng hợp (Collection v1)
└── addons/                 # Danh sách chi tiết từng Addon
    ├── yanhh3d.json        # [OK] YanHH3D 4K (HTML Scraper)
    ├── kkphim.json         # [OK] KKPhim (REST API JSON)
    ├── hh3d.json           # [OK] HH3D.com (HTML Scraper + Deobfuscator)
    ├── hoathinh3d.json     # [Unsupported] HoatHinh3D (Needs JS: Halim AES-GCM)
    ├── hhhtq.json          # [Unsupported] HHHTQ.Team (Needs JS: 3rd-party Embeds)
    ├── vsmov.json          # [Unsupported] VSMOV (Needs JS: Dynamic URL concatenation)
    ├── phimmoi.json        # [Unsupported] PHIMMOI (Needs JS: Next.js Client Hydration)
    └── motchill.json       # [Unsupported] Motchill (Needs JS: Next.js Client Hydration)
```

---

## ⚖️ Bản Quyền & Miễn Trừ Trách Nhiệm

Kho nguồn này được thiết kế và lưu trữ dưới dạng cấu hình quy tắc bóc tách dữ liệu công khai (metadata/scraper rule specifications). zFim và kho nguồn này không lưu trữ, sở hữu hay trực tiếp truyền tải bất kỳ tệp tin video hoặc nội dung có bản quyền nào. Toàn bộ nội dung thuộc quyền sở hữu của các nhà cung cấp nguồn tương ứng.
