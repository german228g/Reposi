import { Table } from './table.js';
import { Cue } from './cue.js';
import { Game } from './game.js';

const canvas = document.getElementById('table-canvas');
const powerFill = document.getElementById('power-fill');
const turnIndicator = document.getElementById('turn-indicator');
const groupIndicator = document.getElementById('group-indicator');
const messageEl = document.getElementById('message');
const btnReset = document.getElementById('btn-reset');
const btnAimLine = document.getElementById('btn-aim-line');

const table = new Table(canvas);
const cue = new Cue();
const game = new Game(table);

let lastTime = 0;
let isDragging = false;

function updateHUD() {
  turnIndicator.textContent = game.state === 'game_over'
    ? (game.winner === 1 ? 'Победа!' : 'Поражение')
    : `Игрок ${game.currentPlayer}`;
  groupIndicator.textContent = `Группа: ${game.getGroupLabel()}`;
  messageEl.textContent = game.message;
  powerFill.style.width = `${cue.getPowerPercent()}%`;
}

game.onUpdate = updateHUD;

function getEventPos(e) {
  const x = e.touches ? e.touches[0].clientX : e.clientX;
  const y = e.touches ? e.touches[0].clientY : e.clientY;
  return table.screenToWorld(x, y);
}

function onPointerDown(e) {
  e.preventDefault();
  const pos = getEventPos(e);

  if (game.canPlaceCueBall()) {
    game.placeCueBall(pos.x, pos.y);
    return;
  }

  if (!game.canShoot()) return;

  const cueBall = game.getCueBall();
  cue.startAim(pos, cueBall.pos);
  isDragging = true;
}

function onPointerMove(e) {
  if (!isDragging) return;
  e.preventDefault();
  const pos = getEventPos(e);
  const cueBall = game.getCueBall();

  if (!cue.pulling) {
    cue.updateAim(pos, cueBall.pos);
    const distToCue = Math.hypot(pos.x - cueBall.pos.x, pos.y - cueBall.pos.y);
    if (distToCue < 80) {
      cue.startPull();
    }
  } else {
    cue.updatePull(pos, cueBall.pos);
    powerFill.style.width = `${cue.getPowerPercent()}%`;
  }
}

function onPointerUp(e) {
  if (!isDragging) return;
  e.preventDefault();
  isDragging = false;

  if (cue.pulling) {
    const shot = cue.release();
    if (shot) {
      game.shoot(shot.vx, shot.vy);
    } else {
      cue.cancel();
    }
    powerFill.style.width = '0%';
  } else {
    cue.cancel();
  }
}

canvas.addEventListener('mousedown', onPointerDown);
canvas.addEventListener('mousemove', onPointerMove);
canvas.addEventListener('mouseup', onPointerUp);
canvas.addEventListener('mouseleave', onPointerUp);

canvas.addEventListener('touchstart', onPointerDown, { passive: false });
canvas.addEventListener('touchmove', onPointerMove, { passive: false });
canvas.addEventListener('touchend', onPointerUp);

btnReset.addEventListener('click', () => {
  game.reset();
  cue.cancel();
  powerFill.style.width = '0%';
});

btnAimLine.addEventListener('click', () => {
  cue.showAimLine = !cue.showAimLine;
  btnAimLine.textContent = cue.showAimLine ? 'Линия прицела' : 'Линия: выкл';
});

function render() {
  table.draw();

  for (const ball of game.balls) {
    ball.draw(table.ctx);
  }

  if (game.canPlaceCueBall()) {
    const ctx = table.ctx;
    const b = table.bounds;
    ctx.save();
    ctx.strokeStyle = 'rgba(240, 192, 64, 0.5)';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 8]);
    ctx.strokeRect(b.left, b.top, b.right - b.left, b.bottom - b.top);
    ctx.fillStyle = 'rgba(240, 192, 64, 0.85)';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Кликните, чтобы поставить биток', table.width / 2, b.top + 30);
    ctx.restore();
  }

  if (game.canShoot()) {
    cue.draw(table.ctx, game.getCueBall(), game.balls);
  }
}

function loop(timestamp) {
  const dt = Math.min((timestamp - lastTime) / 1000, 0.033);
  lastTime = timestamp;

  game.update(dt);
  render();
  requestAnimationFrame(loop);
}

game.reset();
requestAnimationFrame(loop);
