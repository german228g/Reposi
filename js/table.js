import { Vec2, reflectOffCushion } from './physics.js';

export class Table {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);

    this.railWidth = 42;
    this.ballRadius = 14;
    this.pocketRadius = 40;

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

  /** Лузы на углах и серединах бортов — там, куда реально доезжают шары */
  computePockets() {
    const b = this.bounds;
    const w = this.width;
    return [
      { x: b.left, y: b.top, type: 'corner' },
      { x: w / 2, y: b.top, type: 'side' },
      { x: b.right, y: b.top, type: 'corner' },
      { x: b.left, y: b.bottom, type: 'corner' },
      { x: w / 2, y: b.bottom, type: 'side' },
      { x: b.right, y: b.bottom, type: 'corner' },
    ];
  }

  distToPocket(ball, pocket) {
    return Vec2.dist(ball.pos, pocket);
  }

  /** Зона лузы — в ней борт не отбивает шар */
  isInPocketZone(ball, pocket) {
    const d = this.distToPocket(ball, pocket);
    const jaw = this.pocketRadius + ball.radius * 1.8;
    if (pocket.type === 'corner') return d < jaw;
    const along = pocket.type === 'side' && pocket.y < this.height / 2
      ? Math.abs(ball.pos.x - pocket.x) < jaw * 0.85
      : Math.abs(ball.pos.x - pocket.x) < jaw * 0.85;
    return d < jaw && along;
  }

  isNearAnyPocket(ball) {
    return this.pockets.some(p => this.isInPocketZone(ball, p));
  }

  /** Борт с вырезами под лузы */
  constrainBall(ball, restitution = 0.92) {
    const b = this.bounds;
    const r = ball.radius;
    let hit = false;

    const skipLeft = this.pockets.some(p =>
      (p.type === 'corner' && p.x <= b.left && this.isInPocketZone(ball, p))
    );
    const skipRight = this.pockets.some(p =>
      (p.type === 'corner' && p.x >= b.right && this.isInPocketZone(ball, p))
    );
    const skipTop = this.pockets.some(p =>
      (p.y <= b.top) && this.isInPocketZone(ball, p)
    );
    const skipBottom = this.pockets.some(p =>
      (p.y >= b.bottom) && this.isInPocketZone(ball, p)
    );

    if (!skipLeft && ball.pos.x - r < b.left) {
      ball.pos.x = b.left + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(1, 0), restitution);
      hit = true;
    }
    if (!skipRight && ball.pos.x + r > b.right) {
      ball.pos.x = b.right - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(-1, 0), restitution);
      hit = true;
    }
    if (!skipTop && ball.pos.y - r < b.top) {
      ball.pos.y = b.top + r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, 1), restitution);
      hit = true;
    }
    if (!skipBottom && ball.pos.y + r > b.bottom) {
      ball.pos.y = b.bottom - r;
      reflectOffCushion(ball.pos, ball.vel, new Vec2(0, -1), restitution);
      hit = true;
    }

    return hit;
  }

  checkPocket(ball) {
    if (ball.pocketAnim) return null;

    for (const pocket of this.pockets) {
      const dist = this.distToPocket(ball, pocket);
      const capture = this.pocketRadius + ball.radius * 0.55;

      if (dist < capture) return pocket;

      const jaw = this.pocketRadius + ball.radius * 2.2;
      if (dist < jaw) {
        const toPocket = Vec2.sub(pocket, ball.pos);
        const speed = ball.vel.length();
        if (speed > 8) {
          toPocket.normalize();
          const approach = ball.vel.dot(toPocket);
          if (approach > speed * 0.25) return pocket;
        }
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
