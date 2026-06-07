# Bilibili Subtitle Downloader

A lightweight Node.js script to download Bilibili CC and AI subtitles in both original JSON format and converted SRT format.

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure Cookies**:
   Copy `.env.example` to `.env` and fill in your Bilibili cookie.
   To obtain the cookie:
   - Log in to [Bilibili](https://www.bilibili.com).
   - Press `F12` to open Developer Tools, go to the **Application** or **Storage** tab -> **Cookies** -> `https://www.bilibili.com`.
   - Copy the values for `SESSDATA`, `bili_jct`, and `buvid3`.
   - Put them in the `BILI_COOKIE` field in `.env` as: `SESSDATA=xxx; bili_jct=yyy; buvid3=zzz`

## Usage

Run the script by providing a Bilibili video URL or BV ID:

```bash
node index.js <Bilibili URL or BV ID> [Output Directory]
```

### Examples

Download a multi-part video's subtitles:
```bash
node index.js https://www.bilibili.com/video/BV1SJ411H7MB
```

Specify a custom output directory:
```bash
node index.js BV1SJ411H7MB ./my_subtitles
```
