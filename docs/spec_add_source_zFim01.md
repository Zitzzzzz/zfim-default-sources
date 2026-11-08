# 📋 ĐẶC TẢ ĐIỀU CHỈNH MÃ NGUỒN APP zFim TỐI ƯU HÓA CHO CÁC NGUỒN KHO zFim01
> **Mã đặc tả:** `ZFIM-SPEC-ENGINE-ADAPTATION-V1`  
> **Dành cho:** AI Agent / Kỹ sư phụ trách mã nguồn Flutter của dự án zFim (`zfim_flutter/`)  
> **Kho nguồn tương ứng:** `zFim01.json` (Phiên bản kho hiện hành: **v1.5.2**)  
> **Ngày cập nhật:** 2026-11-08  

---

## 📌 MỤC ĐÍCH TÀI LIỆU
Tài liệu này tổng hợp toàn bộ các phát hiện kỹ thuật, hiện trạng không tương thích và đặc tả chi tiết các đoạn mã cần điều chỉnh trong ứng dụng Flutter `zfim_flutter/` để giúp app khai thác tối đa sức mạnh của các nguồn phim mới được bổ sung vào kho `zFim01`.

Các kỹ sư/AI Agent phụ trách app Flutter chỉ cần đọc tài liệu này và thực hiện cập nhật mã nguồn theo đúng các mục dưới đây.

---

## 📑 MỤC LỤC
1. [Nguồn 1: VieFlix (`vieflix`) - Đặc Tả Nâng Cấp Engine](#1-nguồn-1-vieflix-vieflix---đặc-tả-nâng-cấp-engine)
2. [Nguồn 2: XiaoPhim (`xiaofilm`) - Đặc Tả Nâng Cấp Engine](#2-nguồn-2-xiaophim-xiaofilm---đặc-tả-nâng-cấp-engine)
3. [Bảng Kiểm Thử Đối Soát (Verification Matrix)](#3-bảng-kiểm-thử-đối-soát-verification-matrix)

---

## 1. Nguồn 1: VieFlix (`vieflix`) - Đặc Tả Nâng Cấp Engine

### 1.1. Tổng quan nguồn
* **ID Addon:** `vieflix`
* **Loại nguồn:** REST API JSON (`json`)
* **Tên miền hoạt động:** `https://vieflix.buzz`
* **Tên miền động gốc (Landing Page):** `https://www.vieflix.com/` (cấu hình tại `https://www.vieflix.com/constant.js`)
* **Quy mô:** Hơn 30.470 phim, tích hợp 5 Server phát lớn (`KKPhim`, `NguonC`, `OnFlix`, `ViCDN`, `VSPhim`), poster dọc 2:3 chuẩn điện ảnh sắc nét (`posterUrl`).

### 1.2. Vấn đề kỹ thuật trong Engine hiện tại
1. **Lỗi phân giải tập phim đa server lồng nhau:**
   * Trong file `zfim_flutter/lib/addons/json/json_rest_addon.dart` (hàm `parseMetaJson`, dòng 533-575):
   * Engine hiện tại giả định mảng tập phim nằm trực tiếp trong `epGroup['server_data']` hoặc `epGroup['items']` (chuẩn KKPhim / NguonC).
   * Tuy nhiên, API chi tiết `/api/movies/{slug}` của VieFlix có cấu trúc lồng 2 cấp:
     ```json
     "sources": [
       {
         "serverName": "KKPhim",
         "serverKey": "kkphim",
         "languages": [
           {
             "name": "Vietsub",
             "slug": "vietsub",
             "episodes": [
               {
                 "name": "Tập 1",
                 "slug": "tap-1",
                 "linkM3u8": "https://v7.kkphimplayer7.com/20260819/UXIzsB0W/index.m3u8",
                 "linkEmbed": "https://player.phimapi.com/player/?url=..."
               }
             ]
           }
         ]
       }
     ]
     ```
   * Do `epGroup['server_data']` và `items` đều trả về `null`, engine hiện tại bỏ qua mảng tập thật và chỉ sinh 1 tập giả rỗng.
2. **Thiếu hỗ trợ Dynamic Domain trong `JsonRestAddon`:**
   * `JsonRestAddon` chưa có hàm `_initDynamicDomain()` và `_refreshDynamicDomain()`.
   * Thêm vào đó, trang `https://www.vieflix.com/` trả về HTTP 200 kèm file Javascript `constant.js` (`TARGET_DOMAIN: "https://vieflix.buzz"`), không dùng mã chuyển hướng HTTP 301/302. Cơ chế dò redirect của engine cần mở rộng thêm khả năng bóc tách regex.

### 1.3. Hướng dẫn sửa code chi tiết cho `json_rest_addon.dart`

**File:** `zfim_flutter/lib/addons/json/json_rest_addon.dart`

#### Bước 1: Bổ sung nhánh bóc tách đa server (`languages -> episodes`)
Tại hàm `parseMetaJson`, tìm khối vòng lặp `for (final epGroup in rawEpisodes)`:

```dart
// [THÊM VÀO ĐẦU VÒNG LẶP for (final epGroup in rawEpisodes)]
if (epGroup is Map<String, dynamic>) {
  final languages = epGroup['languages'] as List<dynamic>?;
  if (languages != null && languages.isNotEmpty) {
    final sName = (epGroup['serverName'] ?? epGroup['server_name'] ?? 'Server').toString().trim();
    for (final lang in languages) {
      if (lang is! Map<String, dynamic>) continue;
      final langName = (lang['name'] ?? '').toString().trim();
      final fullServerName = langName.isNotEmpty ? '$sName ($langName)' : sName;
      final eps = lang['episodes'] as List<dynamic>?;
      if (eps != null) {
        for (final item in eps) {
          if (item is Map<String, dynamic>) {
            final epName = (item['name'] ?? '$epCounter').toString();
            final epSlug = (item['slug'] ?? 'tap-$epCounter').toString();
            final linkM3u8 = (item['linkM3u8'] ?? item['link_m3u8'] ?? item['m3u8'] ?? '').toString();
            final linkEmbed = (item['linkEmbed'] ?? item['link_embed'] ?? item['embed'] ?? '').toString();
            final playId = linkM3u8.isNotEmpty
                ? linkM3u8
                : (linkEmbed.isNotEmpty ? linkEmbed : '$id/$epSlug');

            final cleanEp = epName.replaceAll(RegExp(r'^(?:tập\s*)+', caseSensitive: false), '').trim();
            videos.add(MetaVideo(
              id: playId,
              title: cleanEp.isNotEmpty ? 'Tập $cleanEp' : 'Tập $epName',
              episode: int.tryParse(epName.replaceAll(RegExp(r'[^0-9]'), '')) ?? epCounter,
              season: 1,
              server: fullServerName,
              serverId: fullServerName,
            ));
            epCounter++;
          }
        }
      }
    }
    continue;
  }
}
```

#### Bước 2: Bổ sung Dynamic Domain Resolution cho `JsonRestAddon`
Kế thừa cơ chế `_initDynamicDomain()` và `_refreshDynamicDomain()` từ `JsonScrapeAddon`, đồng thời hỗ trợ đọc biến `TARGET_DOMAIN` trong file JS / HTML landing page:

```dart
// Khi response.statusCode == 200, kiểm tra chuỗi regex:
final body = fullRes.body;
final jsMatch = RegExp(r'''TARGET_DOMAIN\s*:\s*["\'](https?://[^"\']+)["\']''').firstMatch(body) ??
                RegExp(r'''id=["\']domainInput["\'][^>]*value=["\'](https?://[^"\']+)["\']''').firstMatch(body);
if (jsMatch != null) {
  targetDomain = jsMatch.group(1);
}
```

---

## 2. Nguồn 2: XiaoPhim (`xiaofilm`) - Đặc Tả Nâng Cấp Engine

### 2.1. Tổng quan nguồn
* **ID Addon:** `xiaofilm`
* **Loại nguồn:** Web Scraping HTML (`scrape`)
* **Tên miền hoạt động:** `https://xiaofilm.online`
* **Tên miền động qua Cloudflare Worker:** `https://api1.xiaofilm.workers.dev/config.json`
* **Quy mô:** Tuyển tập hơn 10.000+ phim bộ, 10.000+ phim lẻ chiếu rạp, chuyên mục 4K Ultra HD, Anime Vietsub, Vũ trụ Marvel, Phim Châu Tinh Trì, Top TMDB.
* **Đặc tính luồng phát:** Luồng HLS Master Playlist `.m3u8` trực tiếp tốc độ cao trên CDN `v8.streamvsmov.com`, hỗ trợ đầy đủ CORS (`access-control-allow-origin: *`).

### 2.2. Vấn đề kỹ thuật trong Engine hiện tại
1. **Dữ liệu tập phim & Stream nhúng trong React Server Component (Next.js RSC):**
   * Trong file `zfim_flutter/lib/addons/json/json_scrape_addon.dart`:
   * Khi người dùng xem một phim (ví dụ `/phim/36-ke-doat-mang`), nút xem phim trỏ sang `/xem-phim/36-ke-doat-mang`.
   * Tuy nhiên, trang `/xem-phim/{slug}` không render danh sách tập bằng thẻ HTML truyền thống (`<a>` hay `<button>`) mà truyền toàn bộ dữ liệu qua script payload Next.js:
     ```javascript
     self.__next_f.push([1, "...\"servers\":[{\"server_name\":\"Vietsub_1\",\"source\":\"vsmov\",\"episodes\":[{\"ep_name\":\"1\",\"ep_slug\":\"tap-1\",\"link_m3u8\":\"https://v8.streamvsmov.com/video/.../master.m3u8\"}]}]..."])
     ```
   * Engine hiện tại do không tìm thấy thẻ DOM chứa link video nên rơi vào fallback WebView `Trình phát VIP Web`.
2. **Cơ chế phân giải tên miền từ Cloudflare Worker:**
   * URL `https://api1.xiaofilm.workers.dev/config.json` trả về JSON:
     ```json
     {
       "version": 1,
       "server_origin": "https://xiaofilm.online",
       "refresh_seconds": 21600
     }
     ```
   * Engine cần hỗ trợ đọc trực tiếp trường `server_origin` này khi cập nhật domain động.

### 2.3. Hướng dẫn sửa code chi tiết cho `json_scrape_addon.dart`

**File:** `zfim_flutter/lib/addons/json/json_scrape_addon.dart`

#### Bước 1: Trích xuất tập phim từ Next.js RSC Payload trong `getMeta`
Tại hàm `getMeta` (sau khi tải HTML trang chi tiết hoặc trang xem phim), nếu `detail.videos.length <= 1`:

```dart
// [HỖ TRỢ NEXT.JS RSC EPISODES CHO XIAOPHIM]
if (html.contains('__next_f') && (html.contains('"servers"') || html.contains('"episodes"'))) {
  try {
    // Trích xuất toàn bộ chuỗi RSC được đẩy vào self.__next_f
    final rscMatches = RegExp(r'self\.__next_f\.push\(\[1,\s*"([\s\S]*?)"\]\)').allMatches(html);
    final buffer = StringBuffer();
    for (final m in rscMatches) {
      final chunk = m.group(1) ?? '';
      buffer.write(chunk.replaceAll(r'\"', '"').replaceAll(r'\\', r'\'));
    }
    final rscPayload = buffer.toString();

    // Tìm block "servers":[...]
    final serversRegex = RegExp(r'"servers"\s*:\s*(\[\{[\s\S]*?\}\])\s*(?:,\s*"|[}\]])');
    final sMatch = serversRegex.firstMatch(rscPayload);
    if (sMatch != null) {
      final serversList = json.decode(sMatch.group(1)!) as List<dynamic>;
      final rscVideos = <MetaVideo>[];
      int epCounter = 1;
      for (final s in serversList) {
        if (s is! Map<String, dynamic>) continue;
        final sName = (s['server_name'] ?? 'Server VIP').toString();
        final eps = s['episodes'] as List<dynamic>?;
        if (eps != null) {
          for (final ep in eps) {
            if (ep is Map<String, dynamic>) {
              final epName = (ep['ep_name'] ?? '$epCounter').toString();
              final linkM3u8 = (ep['link_m3u8'] ?? '').toString();
              final linkEmbed = (ep['link_embed'] ?? '').toString();
              final playUrl = linkM3u8.isNotEmpty ? linkM3u8 : linkEmbed;
              if (playUrl.isNotEmpty) {
                rscVideos.add(MetaVideo(
                  id: playUrl,
                  title: epName.startsWith('Tập') ? epName : 'Tập $epName',
                  episode: int.tryParse(epName.replaceAll(RegExp(r'[^0-9]'), '')) ?? epCounter,
                  season: 1,
                  server: sName,
                  serverId: sName,
                ));
                epCounter++;
              }
            }
          }
        }
      }
      if (rscVideos.isNotEmpty) {
        return detail.copyWith(videos: rscVideos);
      }
    }
  } catch (e) {
    DebugLogger.instance.warning('JsonScrape', 'Error parsing Next.js RSC episodes: $e');
  }
}
```

#### Bước 2: Trích xuất trực tiếp link `.m3u8` từ trang xem trong `getStreams`
Tại hàm `getStreams`, trước khi rơi vào fallback WebView dòng 823:

```dart
// [HỖ TRỢ QUÉT STREAM DIRECT M3U8 TỪ TRANG XEM XIAOPHIM]
if (candidates.isEmpty && html.contains('link_m3u8')) {
  final m3u8Matches = RegExp(r'"link_m3u8"\s*:\s*"([^"]+\.m3u8[^"]*)"').allMatches(html);
  for (final m in m3u8Matches) {
    final directM3u8 = m.group(1)?.replaceAll(r'\/', '/');
    if (directM3u8 != null && directM3u8.isNotEmpty) {
      candidates.add(
        StreamItem(
          name: spec.name,
          title: 'Direct HLS Fast',
          url: directM3u8,
          behaviorHints: {
            'headers': {
              'Referer': 'https://xiaofilm.online/',
              'User-Agent': spec.headers['User-Agent'] ?? AppConstants.DEFAULT_USER_AGENT,
            },
          },
        ),
      );
    }
  }
}
```

#### Bước 3: Hỗ trợ đọc `server_origin` trong `_refreshDynamicDomain`
Nếu response từ `dynamicDomainUrl` là file JSON (như worker `api1.xiaofilm.workers.dev`):
```dart
try {
  final jsonBody = json.decode(fullRes.body);
  if (jsonBody is Map<String, dynamic> && jsonBody['server_origin'] != null) {
    targetDomain = jsonBody['server_origin'].toString();
  }
} catch (_) {}
```

---

## 3. Bảng Kiểm Thử Đối Soát (Verification Matrix)

Sau khi điều chỉnh mã nguồn app zFim, Agent kiểm thử theo danh sách URL thực tế dưới đây:

| Nguồn | Kịch bản kiểm thử | URL mục tiêu | Kết quả kỳ vọng sau tối ưu |
| :--- | :--- | :--- | :--- |
| **VieFlix** | Danh sách Mới cập nhật | `https://vieflix.buzz/api/movies?page=1` | Hiển thị 24 thẻ phim kèm poster 2:3 sắc nét, không méo |
| **VieFlix** | Phim Bộ có nhiều Server | `https://vieflix.buzz/api/movies/su-huynh-qua-can-trong` | Trích xuất đủ 5 Server (`KKPhim`, `NguonC`, `OnFlix`, `ViCDN`, `VSPhim`), đủ 30 tập |
| **VieFlix** | Luồng phát HLS | `https://v7.kkphimplayer7.com/20260819/UXIzsB0W/index.m3u8` | Phát video native qua `media_kit` không giật lag |
| **XiaoPhim** | Danh sách Phim Bộ | `https://xiaofilm.online/phim-bo?page=1` | Hiển thị 24 phim, huy hiệu số tập màu cam rõ ràng |
| **XiaoPhim** | Danh mục Phim 4K | `https://xiaofilm.online/c/4k.4k?page=1` | Tải trang mượt mà, phân trang `page=2` chính xác |
| **XiaoPhim** | Xem tập phim HLS | `https://xiaofilm.online/xem-phim/36-ke-doat-mang` | Nhận diện mảng tập từ RSC, phát trực tiếp link `master.m3u8` native thay vì qua WebView |
| **XiaoPhim** | Kiểm tra Domain Worker | `https://api1.xiaofilm.workers.dev/config.json` | Tự động đọc `server_origin: https://xiaofilm.online` |

---
*Tài liệu được sinh tự động bởi Antigravity Engine - Quản lý Kho nguồn zFim.*
