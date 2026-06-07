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

async function downloadSingleVideoSubtitles(bvid, partIndex, partTitle, cid, folderPath, aid, extraId = '') {
  const attempts = 3;
  let subtitles = [];
  let selected = null;
  
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      if (attempt > 1) {
        console.log(`[P${partIndex}] Empty subtitle URL or request failed. Retrying (attempt ${attempt}/${attempts}) after 5s delay...`);
        await sleep(5000);
      } else {
        console.log(`[P${partIndex}] Fetching subtitles list for ${bvid} (CID: ${cid})...`);
      }
      
      subtitles = await fetchSubtitleList(bvid, cid, cookie, aid);
      if (!subtitles || subtitles.length === 0) {
        console.log(`[P${partIndex}] No CC/AI subtitles found for CID: ${cid}.`);
        return false;
      }
      
      selected = subtitles.find(s => s.lan === 'zh-CN') ||
                 subtitles.find(s => s.lan.startsWith('zh')) ||
                 subtitles[0];
                 
      if (selected && selected.subtitle_url) {
        break; // Found valid URL
      }
    } catch (err) {
      if (attempt === attempts) {
        console.error(`[P${partIndex}] Error downloading CID ${cid}:`, err.message);
        return false;
      }
      console.log(`[P${partIndex}] Attempt ${attempt} failed: ${err.message}. Retrying...`);
      await sleep(5000);
    }
  }

  if (!selected || !selected.subtitle_url) {
    console.error(`[P${partIndex}] Error downloading CID ${cid}: Subtitle URL is empty (possibly rate-limited by Bilibili).`);
    return false;
  }

  try {
    console.log(`[P${partIndex}] Found subtitle: ${selected.lan_doc} (${selected.lan})`);
    
    // Download the raw BCC json
    const bccJson = await downloadBccJson(selected.subtitle_url);
    
    // Format names
    const paddedIndex = String(partIndex).padStart(3, '0');
    const safeTitle = cleanFilename(partTitle);
    const idSuffix = extraId ? ` - [ID_${extraId}]` : ` - [CID_${cid}]`;
    const baseName = `${paddedIndex}${idSuffix} - ${safeTitle}`;
    
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
    console.error(`[P${partIndex}] Error saving files for CID ${cid}:`, err.message);
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
            aid: episode.aid,
            id: episode.id || episode.ep_id || ''
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
            const ok = await downloadSingleVideoSubtitles(item.bvid, partIndex, partTitle, page.cid, folderPath, epData.aid, item.id);
            if (ok) successCount++;
            await sleep(delayMs);
          }
        } catch (epErr) {
          console.error(`Failed to fetch episode ${item.bvid} data:`, epErr.message);
        }
      } else {
        const ok = await downloadSingleVideoSubtitles(item.bvid, partIndex, item.title, item.cid, folderPath, videoData.aid);
        if (ok) successCount++;
        if (i < videosToDownload.length - 1) {
          await sleep(delayMs);
        }
      }
    }
    
    console.log(`\nFinished! Successfully downloaded ${successCount} subtitle file sets.`);
    
    // 3. Post-download verification / spot-check
    if (successCount > 0) {
      console.log('\n======================================');
      console.log('      POST-DOWNLOAD SPOT-CHECK        ');
      console.log('======================================');
      try {
        const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.srt'));
        if (files.length > 0) {
          // Select up to 3 files to spot-check (first, middle, last)
          const indices = new Set([0, Math.floor(files.length / 2), files.length - 1]);
          const selectedFiles = Array.from(indices).map(idx => files[idx]).filter(Boolean);
          
          for (const file of selectedFiles) {
            const filePath = path.join(folderPath, file);
            const content = fs.readFileSync(filePath, 'utf8');
            // Parse first subtitle line
            const lines = content.split('\n').map(l => l.trim()).filter(Boolean);
            let firstSubText = '(Empty subtitle)';
            for (let j = 0; j < lines.length; j++) {
              if (lines[j].includes('-->')) {
                if (lines[j + 1]) {
                  firstSubText = lines[j + 1];
                  break;
                }
              }
            }
            console.log(`[Spot-Check] File: ${file}`);
            console.log(`             First Line: "${firstSubText}"`);
            console.log('--------------------------------------');
          }
          console.log('Please verify if the subtitle content matches the episodes above.');
        }
      } catch (checkErr) {
        console.error('Failed to run spot-check:', checkErr.message);
      }
    }
  } catch (err) {
    console.error('Execution failed:', err.message);
    process.exit(1);
  }
}

main();
