import { Vec2, reflectOffCushion } from './physics.js';

export class Table {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);

    this.railWidth = 42;
    this.ballRadius = 14;
    this.pocketRadius = 32;

    this.logicalWidth = 1600;
    this.logicalHeight = 880;

    this.resize();
    this.bounds = this.computeBounds();
    this.pockets = this.computePockets();

    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const w = this.logicalWidth;
    const h = this.logicalHeight;
    this.canvas.width = w * this.dpr;
    this.canvas.height = h * this.dpr;
    this.canvas.style.width = '100%';
    this.canvas.style.aspectRatio = `${w} / ${h}`;
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    this.width = w;
    this.height = h;
    this.bounds = this.computeBounds();
    this.pockets = this.computePockets();
  }

  computeBounds() {
    const r = this.railWidth;
    const br = this.ballRadius;
    return {
      left: r + br + 4,
      right: this.width - r - br - 4,
      top: r + br + 4,
      bottom: this.height - r - br - 4,
      cueX: this.width * 0.26,
      cueY: this.height / 2,
      rackX: this.width * 0.74,
      rackY: this.height / 2,
    };
  }

  computePockets() {
    const inset = this.railWidth * 0.42;
    const w = this.width;
    const h = this.height;
    return [
      { x: inset, y: inset },
      { x: w / 2, y: inset * 0.75 },
      { x: w - inset, y: inset },
      { x: inset, y: h - inset },
      { x: w / 2, y: h - inset * 0.75 },
      { x: w - inset, y: h - inset },
    ];
  }

  constrainBall(ball, restitution = 0.88) {
    const b = this.bounds;
    const r = ball.radius;
    let hit = false;

    if (ball.pos.x - r < b.left) {
      ball.pos.x = b.left + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(1, 0), restitution);
      hit = true;
    }
    if (ball.pos.x + r > b.right) {
      ball.pos.x = b.right - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(-1, 0), restitution);
      hit = true;
    }
    if (ball.pos.y - r < b.top) {
      ball.pos.y = b.top + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, 1), restitution);
      hit = true;
    }
    if (ball.pos.y + r > b.bottom) {
      ball.pos.y = b.bottom - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, -1), restitution);
      hit = true;
    }

    return hit;
  }

  checkPocket(ball) {
    if (ball.pocketAnim) return null;
    for (const pocket of this.pockets) {
      const dist = Vec2.dist(ball.pos, pocket);
      const capture = this.pocketRadius - ball.radius * 0.15;
      if (dist < capture) return pocket;
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

  getBoundsForAim() {
    return this.bounds;
  }
}
