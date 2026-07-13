import { Vec2, reflectOffCushion } from './physics.js';

export class Table {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.railWidth = 28;
    this.ballRadius = 12;
    this.pocketRadius = 22;

    this.width = 900;
    this.height = 500;
    canvas.width = this.width;
    canvas.height = this.height;

    this.bounds = this.computeBounds();
    this.pockets = this.computePockets();
  }

  computeBounds() {
    const r = this.railWidth;
    const br = this.ballRadius;
    return {
      left: r + br,
      right: this.width - r - br,
      top: r + br,
      bottom: this.height - r - br,
      cueX: this.width * 0.25,
      cueY: this.height / 2,
      rackX: this.width * 0.72,
      rackY: this.height / 2,
    };
  }

  computePockets() {
    const r = this.railWidth * 0.55;
    const w = this.width;
    const h = this.height;
    const midX = w / 2;
    const midY = h / 2;

    return [
      { x: r, y: r },
      { x: midX, y: r * 0.85 },
      { x: w - r, y: r },
      { x: r, y: h - r },
      { x: midX, y: h - r * 0.85 },
      { x: w - r, y: h - r },
    ];
  }

  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const r = this.railWidth;

    ctx.clearRect(0, 0, w, h);

    const railGrad = ctx.createLinearGradient(0, 0, w, h);
    railGrad.addColorStop(0, '#6b4423');
    railGrad.addColorStop(0.5, '#8b5a2b');
    railGrad.addColorStop(1, '#5c3a1e');
    ctx.fillStyle = railGrad;
    ctx.fillRect(0, 0, w, h);

    const feltGrad = ctx.createRadialGradient(w / 2, h / 2, 50, w / 2, h / 2, w * 0.6);
    feltGrad.addColorStop(0, '#1f7a45');
    feltGrad.addColorStop(1, '#145a32');
    ctx.fillStyle = feltGrad;
    ctx.fillRect(r, r, w - r * 2, h - r * 2);

    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    ctx.strokeRect(r + 2, r + 2, w - r * 2 - 4, h - r * 2 - 4);

    this.drawHeadSpot();
    this.drawFootSpot();

    for (const pocket of this.pockets) {
      this.drawPocket(pocket);
    }

    ctx.strokeStyle = 'rgba(0,0,0,0.15)';
    ctx.lineWidth = 2;
    ctx.strokeRect(r, r, w - r * 2, h - r * 2);
  }

  drawHeadSpot() {
    const ctx = this.ctx;
    const { cueX, cueY } = this.bounds;
    ctx.beginPath();
    ctx.arc(cueX, cueY, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fill();
  }

  drawFootSpot() {
    const ctx = this.ctx;
    const { rackX, rackY } = this.bounds;
    ctx.beginPath();
    ctx.arc(rackX, rackY, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fill();
  }

  drawPocket(pocket) {
    const ctx = this.ctx;
    const pr = this.pocketRadius;

    ctx.beginPath();
    ctx.arc(pocket.x, pocket.y, pr, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(
      pocket.x, pocket.y, pr * 0.2,
      pocket.x, pocket.y, pr
    );
    grad.addColorStop(0, '#0a0a0a');
    grad.addColorStop(1, '#1a1a1a');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = '#2a2a2a';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  constrainBall(ball) {
    const b = this.bounds;
    const r = ball.radius;
    let hit = false;

    if (ball.pos.x - r < b.left) {
      ball.pos.x = b.left + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(1, 0));
      hit = true;
    }
    if (ball.pos.x + r > b.right) {
      ball.pos.x = b.right - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(-1, 0));
      hit = true;
    }
    if (ball.pos.y - r < b.top) {
      ball.pos.y = b.top + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, 1));
      hit = true;
    }
    if (ball.pos.y + r > b.bottom) {
      ball.pos.y = b.bottom - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, -1));
      hit = true;
    }

    return hit;
  }

  checkPocket(ball) {
    for (const pocket of this.pockets) {
      const dist = Vec2.dist(ball.pos, pocket);
      const captureDist = this.pocketRadius - ball.radius * 0.3;
      if (dist < captureDist) {
        return pocket;
      }
    }
    return null;
  }

  screenToWorld(screenX, screenY) {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.width / rect.width;
    const scaleY = this.height / rect.height;
    return new Vec2(
      (screenX - rect.left) * scaleX,
      (screenY - rect.top) * scaleY
    );
  }
}
