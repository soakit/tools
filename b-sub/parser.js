const { getHeaders, formatSrtTime } = require('./utils.js');

function bccToSrt(bccJson) {
  if (!bccJson || !Array.isArray(bccJson.body)) {
    return '';
  }
  return bccJson.body.map((item, index) => {
    const seq = index + 1;
    const timeRange = `${formatSrtTime(item.from)} --> ${formatSrtTime(item.to)}`;
    return `${seq}\r\n${timeRange}\r\n${item.content}\r\n`;
  }).join('\r\n');
}

async function fetchVideoInfo(bvid, cookie) {
  const url = `https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`;
  const res = await fetch(url, { headers: getHeaders(cookie) });
  if (!res.ok) {
    throw new Error(`Failed to fetch video info, HTTP status: ${res.status}`);
  }
  const data = await res.json();
  if (data.code !== 0) {
    throw new Error(`Bilibili API Error: ${data.message} (code: ${data.code})`);
  }
  return data.data;
}

async function fetchSubtitleList(bvid, cid, cookie, aid = '') {
  let url = `https://api.bilibili.com/x/player/wbi/v2?bvid=${bvid}&cid=${cid}`;
  if (aid) {
    url += `&aid=${aid}`;
  }
  const res = await fetch(url, { headers: getHeaders(cookie) });
  if (!res.ok) {
    throw new Error(`Failed to fetch player info, HTTP status: ${res.status}`);
  }
  const data = await res.json();
  if (data.code !== 0) {
    throw new Error(`Bilibili Player API Error: ${data.message} (code: ${data.code})`);
  }
  return data.data.subtitle ? data.data.subtitle.subtitles : [];
}

async function downloadBccJson(url) {
  if (!url) {
    throw new Error('Subtitle URL is empty');
  }
  const fullUrl = url.startsWith('http') ? url : `https:${url}`;
  const res = await fetch(fullUrl);
  if (!res.ok) {
    throw new Error(`Failed to download subtitle content, HTTP status: ${res.status}`);
  }
  return res.json();
}

module.exports = {
  bccToSrt,
  fetchVideoInfo,
  fetchSubtitleList,
  downloadBccJson
};
