# 📋 ĐẶC TẢ ĐIỀU CHỈNH MÃ NGUỒN APP zFim TỐI ƯU HÓA CHO CÁC NGUỒN KHO zFim01
> **Mã đặc tả:** `ZFIM-SPEC-ENGINE-ADAPTATION-V1`  
> **Dành cho:** AI Agent / Kỹ sư phụ trách mã nguồn Flutter của dự án zFim (`zfim_flutter/`)  
> **Kho nguồn tương ứng:** `zFim01.json` (Phiên bản kho hiện hành: **v1.5.4**)  
> **Ngày cập nhật:** 2026-11-08  

---

## 📌 MỤC ĐÍCH TÀI LIỆU
Tài liệu này tổng hợp toàn bộ các phát hiện kỹ thuật, hiện trạng không tương thích và đặc tả chi tiết các đoạn mã cần điều chỉnh trong ứng dụng Flutter `zfim_flutter/` để giúp app khai thác tối đa sức mạnh của các nguồn phim mới được bổ sung vào kho `zFim01`.

Các kỹ sư/AI Agent phụ trách app Flutter chỉ cần đọc tài liệu này và thực hiện cập nhật mã nguồn theo đúng các mục dưới đây.

---

## 📑 MỤC LỤC
1. [Nguồn 1: VieFlix (`vieflix`) - Đặc Tả Nâng Cấp Engine](#1-nguồn-1-vieflix-vieflix---đặc-tả-nâng-cấp-engine)
2. [Nguồn 2: XiaoPhim (`xiaofilm`) - Đặc Tả Nâng Cấp Engine](#2-nguồn-2-xiaophim-xiaofilm---đặc-tả-nâng-cấp-engine)
3. [Nguồn 3: 500Phim 4K (`500phim`) - Đặc Tả Nâng Cấp Engine & Trình Phát Phụ Đề Song Ngữ](#3-nguồn-3-500phim-4k-500phim---đặc-tả-nâng-cấp-engine--trình-phát-phụ-đề-song-ngữ)
4. [Nguồn 4: Film4k (`film4k`) - Đặc Tả Nâng Cấp Engine Đa Ngôn Ngữ & Luồng 4K Dolby EAC3](#4-nguồn-4-film4k-film4k---đặc-tả-nâng-cấp-engine-đa-ngôn-ngữ--luồng-4k-dolby-eac3)
5. [Bảng Kiểm Thử Đối Soát (Verification Matrix)](#5-bảng-kiểm-thử-đối-soát-verification-matrix)

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

## 3. Nguồn 3: 500Phim 4K (`500phim`) - Đặc Tả Nâng Cấp Engine & Trình Phát Phụ Đề Song Ngữ

### 3.1. Tổng quan nguồn
* **ID Addon:** `500phim`
* **Loại nguồn:** Web Scraping HTML (`scrape`)
* **Tên miền hoạt động:** `https://www.500phim.net`
* **Quy mô:** Hơn 22 chuyên mục tuyển chọn, dẫn đầu về **Kho Phim 4K Ultra HD** (`/c/phim-4k`), **Phim Phụ Đề Song Ngữ** (`/tag/song-ngu`), Phim Chiếu Rạp, Phim AI, Thuyết Minh, Lồng Tiếng cực mạnh.
* **Đặc tính luồng phát:** 
  * Trang xem `/xem-phim/{slug}.{id}` nhúng iframe player `/embed/{id}?v=5`.
  * Luồng stream được bảo vệ bằng chuỗi mã hóa XOR Hex (`encrypted_url`) giải mã bằng secret key `"mySecretKey2024"`.
  * Sau khi giải mã, trả về trực tiếp luồng `.m3u8` chất lượng gốc 4K/Full HD từ CDN 500Phim / Chợ Phim (`https://chophim.app/public/m3u8/...`), KKPhim (`kvp`), StreamVsMov (`v8.streamvsmov.com`), hoặc PlayEmbed (`playembed.vip`).
  * Cung cấp đồng thời file phụ đề Tiếng Việt và Tiếng Anh định dạng WebVTT (`.vtt`) trong biến `CONFIG.subtitles`.

### 3.2. Vấn đề kỹ thuật trong Engine hiện tại & Giải pháp

#### Vấn đề 1: Trích xuất và Giải mã Luồng 4K XOR Hex (`encrypted_url`)
* Trong file `zfim_flutter/lib/addons/json/json_scrape_addon.dart` (dòng 982-999), hàm `_resolveCandidate` đã có bước bóc tách `encrypted_url`:
  ```dart
  final encMatch = RegExp(r'''"encrypted_url"\s*:\s*"([a-f0-9]+)"''', caseSensitive: false).firstMatch(body);
  if (encMatch != null) {
    final decrypted = StreamUnwrapper.hexXorDecrypt(encMatch.group(1)!, 'mySecretKey2024');
    ...
    behaviorHints: {
      'headers': {
        'Referer': 'https://cobephim.fun/', // <-- CẦN SỬA THÀNH DYNAMIC BASE HOẶC 500PHIM!
      }
    }
  }
  ```
* Sửa Referer thành `spec.base` (hoặc `https://www.500phim.net/`).

#### Vấn đề 2: Kích hoạt DNS-over-HTTPS (DoH) cho host `chophim.app`
* Domain `chophim.app` bị một số nhà mạng/thiết bị phân giải sinkhole về `127.0.0.1`.
* Kích hoạt `DohClient` (`doh_client.dart`) phân giải qua Cloudflare DoH (`https://1.1.1.1/dns-query`) khi stream từ domain `chophim.app`.

#### Vấn đề 3: ĐẶC TẢ NÂNG CẤP TRÌNH PHÁT PHỤ ĐỀ SONG NGỮ (DUAL / BILINGUAL SUBTITLES)
1. **Trích xuất Subtitles từ `CONFIG`:**
   ```dart
   final subList = <SubtitleTrack>[];
   final configSubMatch = RegExp(r'"subtitles"\s*:\s*(\[\{[\s\S]*?\}\])').firstMatch(body);
   if (configSubMatch != null) {
     final rawSubs = json.decode(configSubMatch.group(1)!) as List<dynamic>;
     for (final s in rawSubs) {
       final rawFile = s['file']?.toString() ?? '';
       final fullUrl = rawFile.startsWith('http') ? rawFile : '${spec.base}$rawFile';
       subList.add(SubtitleTrack(label: s['label'], language: s['language'], url: fullUrl));
     }
   }
   ```
2. **Nâng cấp `subtitle_service.dart` & `player_screen.dart`:**
   * Nạp song song 2 track: Primary (Tiếng Việt) và Secondary (Tiếng Anh).
   * Render dòng Tiếng Anh phía trên (font 15sp, màu trắng xám `Colors.white70`), dòng Tiếng Việt phía dưới (font 19sp, màu vàng sáng `#FFEB3B`, đổ bóng đậm).

---

## 4. Nguồn 4: Film4k (`film4k`) - Đặc Tả Nâng Cấp Engine Đa Ngôn Ngữ & Luồng 4K Dolby EAC3

### 4.1. Tổng quan nguồn
* **ID Addon:** `film4k`
* **Loại nguồn:** REST API JSON (`json`)
* **Tên miền hoạt động:** `https://film4k.pl`
* **Quy mô:** Hơn 3.690+ phim điện ảnh và series đỉnh cao, chất lượng **4K Ultra HD gốc (3832x1600 HEVC / H.265, bitrate ~24 Mbps)**.
* **Đặc tính âm thanh & phụ đề:**
  * **Âm thanh vòm Dolby Digital Plus (EAC3 5.1 / 6 channels)** cho cả thuyết minh Tiếng Việt (`VIE (6ch EAC3)`) và âm thanh gốc Tiếng Anh (`ENG (6ch EAC3)`).
  * Đi kèm thuyết minh Tiếng Việt chuẩn Stereo (`VIE (Stereo)`) và Tiếng Anh Stereo (`ENG (Stereo)`).
  * Tích hợp sẵn 4 track phụ đề trong HLS (`VIE`, `ENG`, `SDH`, `British`).
* **Đặc tính luồng phát:** 
  * Master Playlist `.m3u8` trực tiếp tốc độ cực cao từ Cloudflare Worker CDN (`https://film4knet.ngaodacopho.workers.dev/tt/...`), đạt trạng thái `cf-cache-status: HIT`, hỗ trợ CORS đầy đủ (`access-control-allow-origin: *`).

---

### 4.2. Vấn đề kỹ thuật trong Engine hiện tại & Hướng dẫn sửa code

#### Vấn đề 1: Xử lý trường đa ngôn ngữ dạng Map (`title`, `poster`, `overview`) trong `parseCatalogListJson`

1. **Hiện trạng:**
   * Trong API `/api/home` của `film4k.pl`, các trường dữ liệu được lưu dưới dạng Map đa ngôn ngữ:
     ```json
     {
       "slug": "spider-man-brand-new-day",
       "title": { "vi": "Người Nhện: Khởi Đầu Mới", "en": "Spider-Man: Brand New Day" },
       "poster": { "vi": "https://image.tmdb.org/t/p/w500/...", "en": "https://image.tmdb.org/t/p/w500/..." },
       "backdrop": "https://image.tmdb.org/t/p/w1280/...",
       "overview": { "vi": "...", "en": "..." },
       "year": 2026,
       "maxRes": "4K",
       "mediaType": "movie"
     }
     ```
   * Trong file `zfim_flutter/lib/addons/json/json_rest_addon.dart` (hàm `parseCatalogListJson`, dòng 134-143):
     ```dart
     final itemId = (item[idKey] ?? item['slug'] ?? '').toString();
     final itemName = (item[nameKey] ?? item['title'] ?? '').toString();
     ```
   * **Hậu quả:** 
     - Do `item['title']` là một `Map<String, dynamic>`, lệnh `item['title'].toString()` biến tên phim thành chuỗi JSON thô: `{en: Spider-Man, vi: Người Nhện}` hiển thị xấu trên thẻ card.
     - Tương tự, nếu `item['poster']` là Map, chuỗi poster trở thành chuỗi không hợp lệ, làm vỡ hình ảnh đại diện.

2. **Hướng dẫn sửa code:**
   Thêm helper method giải nén chuỗi đa ngôn ngữ thông minh:
   ```dart
   String _extractLocalized(dynamic val, [String preferred = 'vi']) {
     if (val == null) return '';
     if (val is Map) {
       return (val[preferred] ?? val['en'] ?? (val.values.isNotEmpty ? val.values.first : '')).toString().trim();
     }
     return val.toString().trim();
   }
   ```
   Sau đó tại `parseCatalogListJson`:
   ```dart
   final rawName = _extractJsonValue(item, nameKey) ?? item['title'] ?? item['name'];
   final itemName = _extractLocalized(rawName);

   final rawPoster = _extractJsonValue(item, posterKey) ?? item['poster'] ?? item['thumb_url'];
   String itemPoster = _extractLocalized(rawPoster);
   ```

---

#### Vấn đề 2: Bóc tách đường dẫn phát cho Phim Lẻ (`movie.hlsUrl`) và Phim Bộ (`episodes.sources`) trong `parseMetaJson`

1. **Hiện trạng:**
   * Khi gọi chi tiết phim `/api/title/{slug}`:
     * **Với phim lẻ (`mediaType == 'movie'`):** Mảng `data['episodes']` trả về rỗng `[]`. Link stream master playlist 4K nằm trực tiếp trong:
       `data['movie']['hlsUrl']` = `"/api/hls/b0AQBRsfpaTBSJv.../master.m3u8"`
     * **Với phim bộ (`mediaType == 'tv'`):** Mảng `data['episodes']` chứa danh sách tập:
       ```json
       [
         {
           "season": 1,
           "episode": 1,
           "sources": [
             {
               "kind": "other",
               "url": "/api/hls/vXwveakBRwNWbew.../master.m3u8",
               "label": "Server 1"
             }
           ]
         }
       ]
       ```
   * Engine hiện tại (`json_rest_addon.dart`, dòng 544-600) chỉ kiểm tra `epGroup['server_data']` hoặc `epGroup['items']`. Do đó:
     - Phim lẻ bị rỗng tập -> sinh tập giả với ID là slug -> không lấy được link stream 4K.
     - Phim bộ không tìm thấy `server_data` -> không lấy được `sources[0]['url']`.

2. **Hướng dẫn sửa code trong `parseMetaJson`:**
   ```dart
   // [THÊM VÀO ĐẦU VÒNG LẶP for (final epGroup in rawEpisodes)]
   if (epGroup is Map<String, dynamic>) {
     // Hỗ trợ Film4k episodes with sources
     final sources = epGroup['sources'] as List<dynamic>?;
     if (sources != null && sources.isNotEmpty) {
       final epNum = epGroup['episode']?.toString() ?? '$epCounter';
       final seasonNum = epGroup['season'] is int ? epGroup['season'] as int : 1;
       final s = sources.first;
       final streamUrl = (s is Map ? s['url'] : '').toString();
       if (streamUrl.isNotEmpty) {
         final fullPlayUrl = streamUrl.startsWith('/') ? '${spec.base}$streamUrl' : streamUrl;
         videos.add(MetaVideo(
           id: fullPlayUrl,
           title: 'Tập $epNum',
           episode: int.tryParse(epNum) ?? epCounter,
           season: seasonNum,
           server: 'Film4k Server',
           serverId: 'film4k_server',
         ));
         epCounter++;
         continue;
       }
     }
   }

   // [XỬ LÝ PHIM LẺ FILM4K KHI rawEpisodes RỖNG]
   if (videos.isEmpty) {
     final hlsUrl = (movieObj?['hlsUrl'] ?? _extractJsonValue(data, 'movie.hlsUrl'))?.toString();
     if (hlsUrl != null && hlsUrl.isNotEmpty) {
       final fullPlayUrl = hlsUrl.startsWith('/') ? '${spec.base}$hlsUrl' : hlsUrl;
       videos.add(MetaVideo(
         id: fullPlayUrl,
         title: 'Bản 4K Ultra HD',
         episode: 1,
         season: 1,
         server: 'Film4k 4K HEVC',
         serverId: 'film4k_direct',
       ));
     }
   }
   ```

---

#### Vấn đề 3: Tự động ưu tiên Audio Track Tiếng Việt (Dolby EAC3 / Stereo) trong Trình phát

1. Master playlist của Film4k khai báo:
   ```
   #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud-ec3",NAME="VIE (6ch EAC3)",LANGUAGE="vie"...
   #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="VIE (Stereo)",LANGUAGE="vie"...
   ```
2. Trong `player_screen.dart` (hoặc cấu hình player `media_kit`):
   Khi nạp luồng phát từ nguồn `film4k`, đặt thiết lập:
   ```dart
   // Tự động chọn audio track có language code == 'vie'
   final audioTracks = player.state.tracks.audio;
   final viTrack = audioTracks.firstWhere(
     (t) => (t.language?.toLowerCase() == 'vie' || t.title?.toLowerCase().contains('vie') == true),
     orElse: () => AudioTrack.auto(),
   );
   if (viTrack != AudioTrack.auto()) {
     player.setAudioTrack(viTrack);
   }
   ```
   Điều này giúp người dùng vào phim là có ngay thuyết minh tiếng Việt chất lượng Dolby 5.1 sống động mà không cần bấm đổi track thủ công!

---

## 5. Bảng Kiểm Thử Đối Soát (Verification Matrix)

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
| **500Phim** | Danh mục Phim 4K Ultra HD | `https://www.500phim.net/c/phim-4k?page=1` | Hiển thị 32 phim, poster TMDB 2:3 sắc nét, huy hiệu 4K vàng nổi bật |
| **500Phim** | Danh mục Phụ đề Song ngữ | `https://www.500phim.net/tag/song-ngu?page=1` | Hiển thị các phim hỗ trợ phụ đề song ngữ Việt - Anh |
| **500Phim** | Chi tiết & Danh sách tập | `https://www.500phim.net/phim/vung-dat-quy-du-2026` | Trích xuất đủ các server `500TT (Song Ngữ)`, `500 (Vietsub)`, `c500 (QC)` |
| **500Phim** | Giải mã Luồng phát 4K | `https://www.500phim.net/embed/1523590?v=5` | Giải mã XOR `mySecretKey2024` thành link `.m3u8` trực tiếp không cần WebView |
| **500Phim** | Trình phát Phụ đề Song ngữ | `https://www.500phim.net/phim/vung-dat-quy-du-2026` | Tải đồng thời 2 file `.vtt`, render song song phụ đề Tiếng Anh (trên) và Tiếng Việt (dưới) |
| **Film4k** | Danh sách Mới cập nhật | `https://film4k.pl/api/home?page=1` | Hiển thị 24 phim, tên phim và poster Tiếng Việt hiển thị đúng, không bị chuỗi Object `{vi: ...}` |
| **Film4k** | Phim Bộ 4K | `https://film4k.pl/api/home?type=tv&page=1` | Lọc chính xác 100% phim series 4K |
| **Film4k** | Phim Lẻ 4K | `https://film4k.pl/api/home?type=movie&page=1` | Lọc chính xác 100% phim lẻ 4K |
| **Film4k** | Xem Phim Lẻ 4K | `https://film4k.pl/api/title/spider-man-brand-new-day` | Trích xuất trực tiếp `movie.hlsUrl`, phát luồng 4K HEVC 3832x1600 mượt mà |
| **Film4k** | Thuyết minh Dolby EAC3 | `https://film4k.pl/api/title/spider-man-brand-new-day` | Tự động chọn track `VIE (6ch EAC3)` hoặc `VIE (Stereo)`, âm thanh vòm sống động |
| **Film4k** | Tìm kiếm Gợi ý | `https://film4k.pl/api/search/suggest?q=spider` | Trả về danh sách kết quả phim kèm năm và ảnh poster chuẩn |

---
*Tài liệu được sinh tự động bởi Antigravity Engine - Quản lý Kho nguồn zFim.*
