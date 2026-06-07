function cleanFilename(name) {
  // Replace invalid Windows filename chars: \ / : * ? " < > | with _
  return name.replace(/[\\/:*?"<>|]/g, '_');
}

function getHeaders(cookie = '') {
  return {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Cookie': cookie
  };
}

function formatSrtTime(seconds) {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  
  const pad = (num, len = 2) => String(num).padStart(len, '0');
  return `${pad(hrs)}:${pad(mins)}:${pad(secs)},${pad(ms, 3)}`;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  cleanFilename,
  getHeaders,
  formatSrtTime,
  sleep
};
