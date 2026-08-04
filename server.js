import http from 'http';
import { readFileSync, existsSync, statSync } from 'fs';
import { extname, join, normalize } from 'path';
import { fileURLToPath } from 'url';
import { createGzip } from 'zlib';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const ROOT = join(__dirname, 'public');
const PORT = process.env.PORT || 3000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.geojson': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/') urlPath = '/index.html';
  const filePath = normalize(join(ROOT, urlPath));
  if (!filePath.startsWith(ROOT) || !existsSync(filePath) || !statSync(filePath).isFile()) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  const ext = extname(filePath).toLowerCase();
  const body = readFileSync(filePath);
  const headers = { 'Content-Type': MIME[ext] || 'application/octet-stream', 'Cache-Control': 'no-cache' };
  const acceptGzip = (req.headers['accept-encoding'] || '').includes('gzip');
  if (acceptGzip && (ext === '.json' || ext === '.geojson' || ext === '.html' || ext === '.js' || ext === '.css') && body.length > 1024) {
    const gz = createGzip();
    res.writeHead(200, { ...headers, 'Content-Encoding': 'gzip' });
    gz.end(body);
    gz.pipe(res);
  } else {
    res.writeHead(200, headers);
    res.end(body);
  }
});

server.listen(PORT, () => console.log(`Карта України: http://localhost:${PORT}`));
