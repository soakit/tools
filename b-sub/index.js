#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const { cleanFilename, sleep } = require('./utils.js');
const {
  bccToSrt,
  fetchVideoInfo,
  fetchSubtitleList,
  downloadBccJson
} = require('./parser.js');

const cookie = process.env.BILI_COOKIE || '';
const delayMs = parseInt(process.env.DELAY_MS || '1000', 10);
const outputBaseDir = process.env.OUTPUT_DIR || './downloads';

function parseBvid(input) {
  // Matches BVxxxxxxxxxx
  const match = input.match(/BV[a-zA-Z0-9]{10}/);
  return match ? match[0] : null;
}

async function downloadSingleVideoSubtitles(bvid, partIndex, partTitle, cid, folderPath) {
  try {
    console.log(`[P${partIndex}] Fetching subtitles list for ${bvid} (CID: ${cid})...`);
    const subtitles = await fetchSubtitleList(bvid, cid, cookie);
    if (!subtitles || subtitles.length === 0) {
      console.log(`[P${partIndex}] No CC/AI subtitles found for CID: ${cid}.`);
      return false;
    }
    
    // Choose the first subtitle track (prefer zh-CN, then zh, then any)
    let selected = subtitles.find(s => s.lan === 'zh-CN') ||
                   subtitles.find(s => s.lan.startsWith('zh')) ||
                   subtitles[0];
                   
    console.log(`[P${partIndex}] Found subtitle: ${selected.lan_doc} (${selected.lan})`);
    
    // Download the raw BCC json
    const bccJson = await downloadBccJson(selected.subtitle_url);
    
    // Format names
    const paddedIndex = String(partIndex).padStart(3, '0');
    const safeTitle = cleanFilename(partTitle);
    const baseName = `${paddedIndex} - ${safeTitle}`;
    
    // Save original BCC
    const jsonPath = path.join(folderPath, `${baseName}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(bccJson, null, 2), 'utf8');
    
    // Save converted SRT
    const srtContent = bccToSrt(bccJson);
    const srtPath = path.join(folderPath, `${baseName}.srt`);
    fs.writeFileSync(srtPath, srtContent, 'utf8');
    
    console.log(`[P${partIndex}] Downloaded and converted: ${baseName}`);
    return true;
  } catch (err) {
    console.error(`[P${partIndex}] Error downloading CID ${cid}:`, err.message);
    return false;
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: node index.js <Bilibili URL or BV ID> [Output Directory]');
    process.exit(1);
  }
  
  const input = args[0];
  const bvid = parseBvid(input);
  if (!bvid) {
    console.error('Invalid Bilibili URL or BV ID.');
    process.exit(1);
  }
  
  const customOutDir = args[1] || outputBaseDir;
  
  try {
    console.log(`Fetching metadata for BV ID: ${bvid}...`);
    const videoData = await fetchVideoInfo(bvid, cookie);
    const videoTitle = cleanFilename(videoData.title);
    
    // 1. Determine download target list (episodes/videos)
    let videosToDownload = [];
    let isCollection = false;
    
    if (videoData.ugc_season) {
      console.log(`Detected UGC Season/Collection: "${videoData.ugc_season.title}"`);
      isCollection = true;
      const episodes = [];
      videoData.ugc_season.sections.forEach(section => {
        section.episodes.forEach(episode => {
          episodes.push({
            bvid: episode.bvid,
            title: episode.title,
            cid: episode.cid,
            aid: episode.aid
          });
        });
      });
      videosToDownload = episodes;
    } else {
      console.log(`Detected Single Video: "${videoData.title}" with ${videoData.pages.length} part(s).`);
      videosToDownload = videoData.pages.map(page => ({
        bvid: bvid,
        title: page.part,
        cid: page.cid,
        index: page.page
      }));
    }
    
    // Create folders
    const targetFolderName = isCollection ? videoData.ugc_season.title : videoTitle;
    const folderPath = path.resolve(customOutDir, cleanFilename(targetFolderName));
    fs.mkdirSync(folderPath, { recursive: true });
    console.log(`Saving files into folder: ${folderPath}`);
    
    // 2. Loop downloads
    let successCount = 0;
    for (let i = 0; i < videosToDownload.length; i++) {
      const item = videosToDownload[i];
      const partIndex = isCollection ? (i + 1) : item.index;
      
      // If collection, we first need to fetch this episode's detailed pages, because sometimes a collection episode itself has multiple parts!
      // But typically collection episodes are single-part. To be robust, if it's a collection, we fetch its page details.
      if (isCollection) {
        console.log(`[Episode ${partIndex}/${videosToDownload.length}] Fetching parts for episode "${item.title}" (${item.bvid})...`);
        try {
          const epData = await fetchVideoInfo(item.bvid, cookie);
          for (let p = 0; p < epData.pages.length; p++) {
            const page = epData.pages[p];
            const partTitle = epData.pages.length > 1 ? `${item.title} - ${page.part}` : item.title;
            const ok = await downloadSingleVideoSubtitles(item.bvid, partIndex, partTitle, page.cid, folderPath);
            if (ok) successCount++;
            await sleep(delayMs);
          }
        } catch (epErr) {
          console.error(`Failed to fetch episode ${item.bvid} data:`, epErr.message);
        }
      } else {
        const ok = await downloadSingleVideoSubtitles(item.bvid, partIndex, item.title, item.cid, folderPath);
        if (ok) successCount++;
        if (i < videosToDownload.length - 1) {
          await sleep(delayMs);
        }
      }
    }
    
    console.log(`\nFinished! Successfully downloaded ${successCount} subtitle file sets.`);
  } catch (err) {
    console.error('Execution failed:', err.message);
    process.exit(1);
  }
}

main();
