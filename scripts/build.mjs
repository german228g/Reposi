import { readFileSync, writeFileSync, mkdirSync, cpSync } from 'fs';
import { execSync } from 'child_process';

mkdirSync('dist', { recursive: true });

execSync('npx esbuild js/main.js --bundle --format=esm --outfile=dist/bundle.js', { stdio: 'inherit' });

const css = readFileSync('css/style.css', 'utf8') + '\n' + readFileSync('css/launch.css', 'utf8');
const js = readFileSync('dist/bundle.js', 'utf8');
const icon = readFileSync('icons/icon-180.png').toString('base64');

const body = readFileSync('index.html', 'utf8')
  .replace(/<link rel="stylesheet" href="css\/style\.css">\s*/, '')
  .replace(/<link rel="stylesheet" href="css\/launch\.css">\s*/, '')
  .replace(/<link rel="manifest"[^>]*>\s*/, '')
  .replace('src="icons/icon-180.png"', `src="data:image/png;base64,${icon}"`)
  .replace(/<link rel="apple-touch-icon"[^>]*>\s*/, '')
  .replace(/<link rel="icon"[^>]*>\s*/, '')
  .replace('<script type="module" src="js/main.js"></script>', '');

const standalone = body.replace(
  '</head>',
  `<style>${css}</style>\n</head>`
).replace(
  '</body>',
  `<script type="module">${js}</script>\n</body>`
);

writeFileSync('play.html', standalone);
writeFileSync('pool-v5.html', standalone);
writeFileSync('pool-v51.html', standalone);

cpSync('icons', 'dist/icons', { recursive: true });
writeFileSync('dist/styles.css', css);
writeFileSync('dist/index.html', readFileSync('index.html', 'utf8')
  .replace('css/style.css', 'styles.css')
  .replace('css/launch.css', '')
  .replace('js/main.js', 'bundle.js')
  .replace('<link rel="stylesheet" href="">\n', ''));

console.log('Built play.html (standalone) and dist/');
