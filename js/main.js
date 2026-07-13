import { Table } from './table.js';
import { Cue } from './cue.js';
import { Game } from './game.js';
import { Renderer } from './renderer.js';
import { InputController } from './input.js';
import { initPWA, isStandalone } from './pwa.js';

const splash = document.getElementById('splash');
const gameApp = document.getElementById('game-app');
const btnPlay = document.getElementById('btn-play');
const gameUrlEl = document.getElementById('game-url');

initPWA();

if (gameUrlEl) {
  gameUrlEl.textContent = window.location.href;
}

let started = false;
let table, renderer, cue, game, input;
let lastTime = 0;

function startGame() {
  if (started) return;
  started = true;

  splash?.classList.add('hidden');
  gameApp?.removeAttribute('hidden');

  const canvas = document.getElementById('table-canvas');
  const powerFill = document.getElementById('power-fill');
  const turnIndicator = document.getElementById('turn-indicator');
  const groupIndicator = document.getElementById('group-indicator');
  const opponentIndicator = document.getElementById('opponent-indicator');
  const messageEl = document.getElementById('message');
  const btnReset = document.getElementById('btn-reset');
  const btnAimLine = document.getElementById('btn-aim-line');
  const btnShoot = document.getElementById('btn-shoot');
  const playerPanel = document.getElementById('player-panel');
  const opponentPanel = document.getElementById('opponent-panel');

  table = new Table(canvas);
  renderer = new Renderer(table);
  cue = new Cue();
  game = new Game(table);

  function updateHUD() {
    const human = game.players[1];
    const ai = game.players[2];

    if (game.state === 'game_over') {
      turnIndicator.textContent = game.winner === 1 ? 'Победа!' : 'Поражение';
    } else if (game.isHumanTurn()) {
      turnIndicator.textContent = 'Ваш ход';
    } else {
      turnIndicator.textContent = 'Ход соперника';
    }

    groupIndicator.textContent = `Ваши: ${human.group ? (human.group === 'solid' ? 'цельные' : 'полосатые') : '—'}`;
    opponentIndicator.textContent = `Соперник: ${ai.group ? (ai.group === 'solid' ? 'цельные' : 'полосатые') : '—'}`;
    messageEl.textContent = game.message;
    powerFill.style.width = `${cue.getPowerPercent()}%`;

    const canShoot = game.canShoot();
    playerPanel.classList.toggle('active', game.isHumanTurn() && game.state !== 'game_over');
    opponentPanel.classList.toggle('active', !game.isHumanTurn() && game.state !== 'game_over');
    btnShoot.disabled = !canShoot || cue.getPowerPercent() < 8;
  }

  game.onUpdate = updateHUD;

  input = new InputController(canvas, table, cue, game, (pct) => {
    powerFill.style.width = `${pct}%`;
    btnShoot.disabled = !game.canShoot() || pct < 8;
  });

  btnShoot.addEventListener('click', () => {
    if (!game.canShoot()) return;
    const shot = cue.release();
    if (shot) {
      game.shoot(shot.vx, shot.vy);
      powerFill.style.width = '0%';
    }
  });

  btnReset.addEventListener('click', () => {
    game.reset();
    cue.cancelPull();
    powerFill.style.width = '0%';
  });

  btnAimLine.addEventListener('click', () => {
    cue.showAimLine = !cue.showAimLine;
    btnAimLine.textContent = cue.showAimLine ? 'Прицел: вкл' : 'Прицел: выкл';
  });

  function render() {
    const ctx = table.ctx;
    renderer.drawTable(ctx);

    const balls = game.balls.filter(b => b.active && !b.pocketed);
    balls.sort((a, b) => a.pos.y - b.pos.y);

    for (const ball of balls) {
      if (!ball.pocketAnim) renderer.drawBallShadow(ctx, ball);
    }
    for (const ball of balls) {
      renderer.drawBall(ctx, ball, ball.getPocketT());
    }

    if (game.canPlaceCueBall()) {
      const b = table.bounds;
      ctx.save();
      ctx.strokeStyle = 'rgba(240, 192, 64, 0.6)';
      ctx.lineWidth = 3;
      ctx.setLineDash([12, 8]);
      ctx.strokeRect(b.left, b.top, b.right - b.left, b.bottom - b.top);
      ctx.fillStyle = 'rgba(240, 192, 64, 0.9)';
      ctx.font = 'bold 22px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Нажмите, чтобы поставить биток', table.width / 2, b.top + 40);
      ctx.restore();
    }

    if (game.canShoot()) {
      cue.draw(ctx, game.getCueBall(), game.balls, table.bounds);
    } else if (game.state === 'ai_thinking' && game.aiShot) {
      cue.aimAngle = game.aiShot.angle;
      cue.visible = true;
      cue.pullDistance = (game.aiShot.power / cue.maxPower) * cue.maxPull * 0.7;
      cue.draw(ctx, game.getCueBall(), game.balls, table.bounds);
    }
  }

  function loop(timestamp) {
    const dt = Math.min((timestamp - lastTime) / 1000, 0.033);
    lastTime = timestamp;
    game.update(dt);
    cue.update(dt);
    render();
    requestAnimationFrame(loop);
  }

  game.reset();
  cue.visible = true;
  const cueBall = game.getCueBall();
  if (cueBall) cue.setAimFromPoint({ x: cueBall.pos.x + 200, y: cueBall.pos.y }, cueBall.pos);
  requestAnimationFrame(loop);
}

btnPlay?.addEventListener('click', startGame);

if (isStandalone) {
  startGame();
}
