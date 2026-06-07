# Bilibili Subtitle Downloader Design Document

This document defines the design and specifications for a command-line tool written in Node.js to download Bilibili video subtitles (both standard CC and AI-generated subtitles) for video playlists, multi-part (分P) videos, and UGC collections.

## 1. Goal

The objective is to create a robust, lightweight, and easy-to-use Node.js CLI script that downloads Bilibili subtitles for a given video URL or BV number, handles multi-part videos or collection playlists, and outputs subtitles in both the original BCC (JSON) format and converted SRT format.

## 2. Requirements

- **Runtime**: Node.js (version 18+ for native fetch support).
- **Authentication**: Ability to read Bilibili login cookies from a `.env` file to support accessing AI-generated subtitles and member-only videos.
- **Input**: A Bilibili URL or BV ID (e.g., `https://www.bilibili.com/video/BV1SJ411H7MB` or `BV1SJ411H7MB`).
- **Modes Supported**:
  - **Single Multi-part Video (多分P)**: Downloads subtitles for all P's (cids) of the BV ID.
  - **UGC Collection/Season (合集)**: Detects if the video belongs to a UGC collection/season, and downloads subtitles for all videos in that collection.
- **Output Formats**:
  - Original `.json` (BCC format).
  - Converted `.srt` (SubRip Subtitle format).
- **Output Naming**: Files saved in a subfolder under `./downloads` (or custom directory), named sequentially (e.g., `001 - 第1集.srt`, `001 - 第1集.json`).
- **Robustness**: Rate limiting/delay between API calls to prevent anti-bot blocking (Status 412). Clean file naming to avoid issues with special characters in Windows.

## 3. Directory Structure

```text
b-sub/
├── .env                  # Configuration (BILI_COOKIE, DELAY_MS, etc.)
├── package.json          # Node dependencies and scripts
├── index.js              # Command line entry point and flow control
├── parser.js             # API request module and JSON to SRT parser
├── utils.js              # Utility functions (headers, clean filename, sleep)
└── README.md             # Documentation on how to get cookies and run the tool
```

## 4. API Specification

### 4.1 Video Metadata
- **Endpoint**: `GET https://api.bilibili.com/x/web-interface/view?bvid={bvid}`
- **Headers**:
  - `User-Agent`: Desktop browser agent.
  - `Referer`: `https://www.bilibili.com/`
  - `Cookie`: (configured in `.env`)
- **Key Fields**:
  - `data.title`: Video main title.
  - `data.pages`: List of parts containing `cid` and `part` (part title).
  - `data.ugc_season`: If present, contains `sections[].episodes` listing all videos (`bvid` and `title`) in the collection.

### 4.2 Subtitle Metadata
- **Endpoint**: `GET https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}`
- **Headers**: Same as above.
- **Key Fields**:
  - `data.subtitle.subtitles`: List of subtitle tracks containing `lan` (e.g., `zh-CN`, `ai-zh`) and `subtitle_url`.

### 4.3 Subtitle Content Download
- **Endpoint**: `GET https:{subtitle_url}`
- **Response**: BCC JSON structure:
  ```json
  {
    "body": [
      {
        "from": 1.5,
        "to": 3.8,
        "content": "Subtitle content"
      }
    ]
  }
  ```

## 5. Subtitle Conversion (BCC to SRT)

The converter transforms seconds into `HH:MM:SS,mmm` format:
- Hour: `Math.floor(seconds / 3600)` -> pad to 2 digits.
- Minute: `Math.floor((seconds % 3600) / 60)` -> pad to 2 digits.
- Second: `Math.floor(seconds % 60)` -> pad to 2 digits.
- Milliseconds: `Math.round((seconds % 1) * 1000)` -> pad to 3 digits.

## 6. Rate Limiting and Safety

- Configurable delay (default `1000ms`) between fetching subtitle info or subtitle contents.
- Handling empty subtitle tracks gracefully by logging warning and skipping.
- Basic error handling for fetch failures, invalid JSON responses, and API status blocks.
