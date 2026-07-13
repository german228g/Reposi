import { Vec2 } from './physics.js';
import { PHYSICS } from './physicsConfig.js';
import { getBallGroup } from './balls.js';

export class Cue {
  constructor(table) {
    this.table = table;
    this.aimAngle = 0;
    this.powerLevel = 0;
    this.showAimLine = true;
    this.mousePos = new Vec2(0, 0);
    this.aiming = false;
    this.visible = false;
    this.strikeAnim = 0;
  }

  get maxSpeed() {
    return PHYSICS.maxSpeed(this.table);
  }

  get minSpeed() {
    return PHYSICS.minSpeed(this.table);
  }

  get powerReach() {
    return PHYSICS.powerReach(this.table);
  }

  beginAim() {
    this.aiming = true;
    this.visible = true;
  }

  setAimFromPoint(point, cueBallPos) {
    if (!cueBallPos) return;
    const px = point.x ?? point[0];
    const py = point.y ?? point[1];
    this.mousePos.set(px, py);
    const dx = px - cueBallPos.x;
    const dy = py - cueBallPos.y;
    if (Math.hypot(dx, dy) > 5) {
      this.aimAngle = Math.atan2(dy, dx);
      this.visible = true;
    }
  }

  /** Сила = расстояние пальца от битка (просто и понятно) */
  setPowerFromFinger(fingerPos, cueBallPos) {
    if (!cueBallPos) return;
    const dist = Vec2.dist(fingerPos, cueBallPos);
    const t = (dist - 25) / this.powerReach;
    this.powerLevel = Math.max(0, Math.min(1, t));
  }

  getPowerPercent() {
    return this.powerLevel * 100;
  }

  /** Выстрел с текущим прицелом и силой */
  fireShot() {
    const speed = this.powerLevel * this.maxSpeed;
    if (speed < this.minSpeed) return null;

    this.aiming = false;
    this.strikeAnim = 1;
  const angle = this.aimAngle;
    const shot = {
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      power: speed,
    };
    this.powerLevel = 0;
    return shot;
  }

  cancelAim() {
    this.aiming = false;
    this.powerLevel = 0;
  }

  update(dt) {
    if (this.strikeAnim > 0) {
      this.strikeAnim = Math.max(0, this.strikeAnim - dt * 8);
    }
  }

  draw(ctx, cueBall, balls, tableBounds) {
    if (!cueBall || !cueBall.active || cueBall.pocketed || !this.visible) return;

    const { x, y } = cueBall.pos;
    const angle = this.aimAngle;
    const pull = this.powerLevel * this.powerReach * 0.35 + this.strikeAnim * 40;
    const r = cueBall.radius;

    if (this.showAimLine) {
      this.drawAimGuide(ctx, cueBall, balls, tableBounds, angle);
    }

    if (this.powerLevel > 0.02) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r + 10 + this.powerLevel * 40, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(240, 192, 64, ${0.3 + this.powerLevel * 0.5})`;
      ctx.lineWidth = 3 + this.powerLevel * 4;
      ctx.stroke();
      ctx.restore();
    }

    const cueLength = 400;
    const tipOffset = r + 8 + pull;
    const buttX = x - Math.cos(angle) * (tipOffset + cueLength);
    const buttY = y - Math.sin(angle) * (tipOffset + cueLength);
    const tipX = x - Math.cos(angle) * tipOffset;
    const tipY = y - Math.sin(angle) * tipOffset;

    ctx.save();
    ctx.lineCap = 'round';
    const grad = ctx.createLinearGradient(buttX, buttY, tipX, tipY);
    grad.addColorStop(0, '#3d2518');
    grad.addColorStop(0.4, '#c4a574');
    grad.addColorStop(0.9, '#f0e8d8');
    grad.addColorStop(1, '#2980b9');

    ctx.beginPath();
    ctx.moveTo(buttX, buttY);
    ctx.lineTo(tipX, tipY);
    ctx.strokeStyle = grad;
    ctx.lineWidth = 10;
    ctx.stroke();
    ctx.restore();
  }

  drawAimGuide(ctx, cueBall, balls, bounds, angle) {
    const dir = new Vec2(Math.cos(angle), Math.sin(angle));
    let start = cueBall.pos.clone();
    let remaining = 1000;
    const activeBalls = balls.filter(b => b.active && !b.pocketed && b.id !== 0 && !b.pocketAnim);

    ctx.save();
    for (let bounce = 0; bounce < 3 && remaining > 0; bounce++) {
      let hitDist = remaining;
      let hitBall = null;

      for (const ball of activeBalls) {
        const toBall = Vec2.sub(ball.pos, start);
        const proj = toBall.dot(dir);
        if (proj <= 0) continue;
        const perp = Math.abs(toBall.x * dir.y - toBall.y * dir.x);
        const combined = cueBall.radius + ball.radius;
        if (perp > combined) continue;
        const along = Math.sqrt(Math.max(0, combined * combined - perp * perp));
        const dist = proj - along;
        if (dist > 0 && dist < hitDist) {
          hitDist = dist;
          hitBall = ball;
        }
      }

      if (!hitBall) {
        const wall = this.rayWall(start, dir, bounds, hitDist);
        if (wall) hitDist = wall.dist;
      }

      const endX = start.x + dir.x * hitDist;
      const endY = start.y + dir.y * hitDist;

      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = bounce === 0 ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.3)';
      ctx.lineWidth = bounce === 0 ? 3 : 1.5;
      ctx.setLineDash(bounce === 0 ? [] : [6, 6]);
      ctx.stroke();

      if (hitBall) break;
      remaining -= hitDist;
      start.set(endX, endY);
      dir.x *= -1;
      dir.y *= -1;
    }
    ctx.restore();
  }

  rayWall(start, dir, bounds, maxDist) {
    let best = null;
    const walls = [
      { axis: 'x', value: bounds.left, normal: new Vec2(1, 0) },
      { axis: 'x', value: bounds.right, normal: new Vec2(-1, 0) },
      { axis: 'y', value: bounds.top, normal: new Vec2(0, 1) },
      { axis: 'y', value: bounds.bottom, normal: new Vec2(0, -1) },
    ];
    for (const wall of walls) {
      const d = wall.axis === 'x'
        ? (wall.value - start.x) / dir.x
        : (wall.value - start.y) / dir.y;
      if (d > 0 && d < maxDist && (!best || d < best.dist)) {
        best = { dist: d };
      }
    }
    return best;
  }
}

export function findBestShot(game) {
  const cue = game.getCueBall();
  if (!cue) return null;
  const maxSpd = PHYSICS.maxSpeed(game.table);
  const targets = game.getLegalTargets();
  const pockets = game.table.pockets;
  const r = game.table.ballRadius;
  let best = null;

  for (const target of targets) {
    for (const pocket of pockets) {
      const toPocket = Vec2.sub(pocket, target.pos).normalize();
      const ghostX = target.pos.x - toPocket.x * r * 2;
      const ghostY = target.pos.y - toPocket.y * r * 2;
      const toGhost = Vec2.sub({ x: ghostX, y: ghostY }, cue.pos);
      const dist = toGhost.length();
      if (dist < 20) continue;
      const angle = Math.atan2(toGhost.y, toGhost.x);
      if (!isPathClear(cue.pos, { x: ghostX, y: ghostY }, game.balls, cue.radius, [0, target.id])) continue;
      if (!isPathClear(target.pos, pocket, game.balls, r, [0, target.id])) continue;
      const score = 1 / (dist * 0.008 + 1);
      if (!best || score > best.score) {
        const t = Math.min(1, (dist + 200) / (game.table.width * 0.55));
        best = { angle, power: maxSpd * t, score };
      }
    }
  }

  if (!best && game.firstShot) {
    const rack = { x: game.table.bounds.rackX - 60, y: game.table.bounds.rackY };
    const dir = Vec2.sub(rack, cue.pos);
    return { angle: Math.atan2(dir.y, dir.x), power: maxSpd * 0.92 };
  }

  if (!best && targets.length) {
    const t = targets[0];
    const dir = Vec2.sub(t.pos, cue.pos);
    return { angle: Math.atan2(dir.y, dir.x), power: maxSpd * 0.55 };
  }

  return best;
}

function isPathClear(from, to, balls, radius, ignoreIds) {
  const dir = Vec2.sub(to, from);
  const len = dir.length();
  if (len < 1) return true;
  dir.normalize();
  for (const ball of balls) {
    if (!ball.active || ball.pocketed || ball.pocketAnim) continue;
    if (ignoreIds.includes(ball.id)) continue;
    const toBall = Vec2.sub(ball.pos, from);
    const proj = toBall.dot(dir);
    if (proj < 0 || proj > len) continue;
    const perp = Math.abs(toBall.x * dir.y - toBall.y * dir.x);
    if (perp < radius + ball.radius) return false;
  }
  return true;
}
