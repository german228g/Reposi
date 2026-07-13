import { Vec2 } from './physics.js';

const RACK_LAYOUT = [
  [1],
  [9, 2],
  [3, 8, 10],
  [11, 4, 12, 5],
  [13, 6, 14, 7, 15],
];

export class Ball {
  constructor(id, x, y, radius = 14) {
    this.id = id;
    this.pos = new Vec2(x, y);
    this.vel = new Vec2(0, 0);
    this.radius = radius;
    this.mass = 1;
    this.active = true;
    this.pocketed = false;
    this.isCue = id === 0;
    this.isEight = id === 8;
    this.isSolid = id >= 1 && id <= 7;
    this.isStripe = id >= 9 && id <= 15;
    this.pocketAnim = null;
    this.pocketTarget = null;
    this.spin = 0;
  }

  startPocketAnim(pocket) {
    this.pocketAnim = { t: 0, duration: 0.28 };
    this.pocketTarget = pocket;
    this.vel.set(0, 0);
  }

  updatePocketAnim(dt) {
    if (!this.pocketAnim || !this.pocketTarget) return false;

    this.pocketAnim.t += dt / this.pocketAnim.duration;

    const t = Math.min(1, this.pocketAnim.t);
    const target = this.pocketTarget;
    this.pos.x += (target.x - this.pos.x) * 0.18;
    this.pos.y += (target.y - this.pos.y) * 0.18;

    if (this.pocketAnim.t >= 1) {
      this.pocketed = true;
      this.active = false;
      this.pocketAnim = null;
      return true;
    }
    return false;
  }

  getPocketT() {
    return this.pocketAnim ? Math.min(1, this.pocketAnim.t) : 0;
  }

  pocket() {
    this.pocketed = true;
    this.active = false;
    this.vel.set(0, 0);
    this.pocketAnim = null;
  }

  reset(x, y) {
    this.pos.set(x, y);
    this.vel.set(0, 0);
    this.active = true;
    this.pocketed = false;
    this.pocketAnim = null;
    this.pocketTarget = null;
  }
}

export function createRack(tableBounds, ballRadius) {
  const balls = [new Ball(0, tableBounds.cueX, tableBounds.cueY, ballRadius)];

  const d = ballRadius * 2;
  const rowStep = d * (Math.sqrt(3) / 2);
  const apexX = tableBounds.rackX - rowStep * 4;
  const apexY = tableBounds.rackY;

  for (let row = 0; row < RACK_LAYOUT.length; row++) {
    const ids = RACK_LAYOUT[row];
    const x = apexX + row * rowStep;
    const rowWidth = (ids.length - 1) * d;
    const startY = apexY - rowWidth / 2;

    for (let col = 0; col < ids.length; col++) {
      const y = startY + col * d;
      balls.push(new Ball(ids[col], x, y, ballRadius));
    }
  }

  return balls;
}

export function getBallGroup(ball) {
  if (ball.isSolid) return 'solid';
  if (ball.isStripe) return 'stripe';
  return null;
}

export function getBallsByGroup(balls, group) {
  return balls.filter(b => b.active && !b.pocketed && getBallGroup(b) === group);
}
