# HƯỚNG DẪN DÀNH CHO AI AGENT TRONG DỰ ÁN zFim

## ⚠️ QUY TẮC CỨNG: CẬP NHẬT / TẠO NGUỒN PHIM MỚI VÀO KHO ZFIM01 (TRIGGER RULE)

### 1. CỜ KÍCH HOẠT (TRIGGER PHRASES):
Bất cứ khi nào User yêu cầu các tác vụ liên quan đến nguồn phim:
- *"Cập nhật nguồn [tên nguồn] vào kho phim"*
- *"Thêm nguồn [tên nguồn] vào kho"*
- *"Tạo nguồn [tên nguồn] cho kho zFim"*
- *"Sửa lỗi nguồn [tên nguồn]"*

### 2. ĐIỀU CẤM KỴ TUYỆT ĐỐI:
- **TUYỆT ĐỐI KHÔNG SINH HOẶC SỬA CODE CHO FLUTTER APP (`zfim_flutter/`)!**
- App zFim vận hành theo kiến trúc "Clean Platform" (hoàn toàn trắng nguồn mặc định). Không thêm code scraping hardcode vào app.
- **CHỈ TẠO/SỬA NGUỒN VÀO KHO GIT NGUỒN PHIM ZFIM:** Thao tác trực tiếp trên repo:
  `https://github.com/magicxlll/zfim-default-sources.git` (thư mục local: `/Volumes/ZMac1TB/Workspace/StudioProjects/zfim-default-sources`).

### 3. QUY TRÌNH THỰC HIỆN BẮT BUỘC (7 BƯỚC):
1. **Đọc Spec chuẩn:** Đọc tài liệu đặc tả kỹ thuật `docs/SOURCE_CREATION_SPEC.md` tại repo `zfim-default-sources`.
2. **Khảo sát & Bóc tách:** Phân loại nguồn (`json`, `scrape`, `m3u`) và áp dụng các case đặc biệt (JWPlayer `data-obf`, mã hóa XOR, `dynamicDomainUrl`, Referer anti-hotlink, M3U IPTV/sports).
3. **Tạo/sửa file nguồn con:** `addons/<id>.json` trong repo `zfim-default-sources`.
4. **ĐÁNH DẤU PHIÊN BẢN RÕ RÀNG:**
   - **Nguồn con:** Tăng `version` (ví dụ `1.0.0` -> `1.0.1` hoặc mới thì `1.0.0`).
   - **Kho tổng `zFim01.json`:** **BẮT BUỘC TĂNG `version` CỦA COLLECTION** (ví dụ `1.4.1` -> `1.4.2`). Thêm/cập nhật nguồn vào mảng `addons`.
5. **Đồng bộ song song:**
   - Copy `zFim01.json` sang `/Volumes/ZMac1TB/Workspace/StudioProjects/zApp-dist/zFim01.json`.
   - Copy `zFim01.json` sang `/Volumes/ZMac1TB/Workspace/StudioProjects/zFim/zfim_flutter/assets/addons/zFim01.json`.
6. **Commit, Push & Purge CDN:**
   - Commit & Push lên nhánh `main` của cả `zfim-default-sources` và `zApp-dist`.
   - Purge CDN cache jsDelivr:
     ```sh
     curl -s https://purge.jsdelivr.net/gh/magicxlll/zfim-default-sources@main/zFim01.json
     curl -s https://purge.jsdelivr.net/gh/magicxlll/zApp-dist@main/zFim01.json
     ```
7. **Bàn giao kết quả:** Thông báo cho User biết phiên bản kho mới đã được phát hành. Người dùng chỉ cần mở app và bấm "Đồng bộ" / "Cập nhật kho nguồn" (hoặc mở lại app để Auto-Sync ngầm kích hoạt) là có thể sử dụng ngay nguồn phim mới mà không cần cài lại app hay update APK!
