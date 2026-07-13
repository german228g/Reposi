import { Vec2 } from './physics.js';
import { getBallGroup } from './balls.js';

export class Cue {
  constructor() {
    this.aimAngle = 0;
    this.pullDistance = 0;
    this.maxPull = 200;
    this.maxPower = 28;
    this.minPower = 0.15;
    this.showAimLine = true;
    this.mousePos = new Vec2(0, 0);
    this.pulling = false;
    this.visible = false;
    this.strikeAnim = 0;
  }

  startShot() {
    this.pulling = true;
    this.pullDistance = 0;
    this.visible = true;
  }

  setAimFromPoint(point, cueBallPos) {
    if (!cueBallPos) return;
    const px = point.x ?? point[0];
    const py = point.y ?? point[1];
    this.mousePos.set(px, py);
    const dx = px - cueBallPos.x;
    const dy = py - cueBallPos.y;
    if (Math.hypot(dx, dy) > 8) {
      this.aimAngle = Math.atan2(dy, dx);
      this.visible = true;
    }
  }

  updatePowerFromFinger(fingerPos, cueBallPos) {
    if (!this.pulling || !cueBallPos) return;

    const toFinger = Vec2.sub(fingerPos, cueBallPos);
    const dist = toFinger.length();
    if (dist < 15) {
      this.pullDistance = 0;
      return;
    }

    const aimDir = new Vec2(Math.cos(this.aimAngle), Math.sin(this.aimAngle));
    const pullBack = -toFinger.dot(aimDir);

    let power = 0;
    if (pullBack > 8) {
      power = pullBack;
    } else {
      power = Math.max(0, (dist - 50) * 0.55);
    }

    this.pullDistance = Math.max(0, Math.min(power, this.maxPull));
  }

  release() {
    if (!this.pulling) return null;

    const power = (this.pullDistance / this.maxPull) * this.maxPower;
    const angle = this.aimAngle;

    this.pulling = false;
    this.strikeAnim = 1;

    if (power < this.minPower) {
      this.pullDistance = 0;
      return null;
    }

    this.pullDistance = 0;
    return {
      vx: Math.cos(angle) * power,
      vy: Math.sin(angle) * power,
      power,
    };
  }

  cancelPull() {
    this.pulling = false;
    this.pullDistance = 0;
  }

  getPowerPercent() {
    return (this.pullDistance / this.maxPull) * 100;
  }

  update(dt) {
    if (this.strikeAnim > 0) {
      this.strikeAnim = Math.max(0, this.strikeAnim - dt * 6);
    }
  }

  draw(ctx, cueBall, balls, tableBounds) {
    if (!cueBall || !cueBall.active || cueBall.pocketed || !this.visible) return;

    const { x, y } = cueBall.pos;
    const angle = this.aimAngle;
    const pull = this.pullDistance + this.strikeAnim * 30;
    const r = cueBall.radius;

    if (this.showAimLine) {
      this.drawAimGuide(ctx, cueBall, balls, tableBounds, angle);
    }

    if (this.pulling && this.pullDistance > 2) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r + 8 + this.pullDistance * 0.15, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(240, 192, 64, ${0.25 + this.getPowerPercent() * 0.005})`;
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.restore();
    }

    const cueLength = 420;
    const tipOffset = r + 6 + pull;
    const buttX = x - Math.cos(angle) * (tipOffset + cueLength);
    const buttY = y - Math.sin(angle) * (tipOffset + cueLength);
    const tipX = x - Math.cos(angle) * tipOffset;
    const tipY = y - Math.sin(angle) * tipOffset;

    ctx.save();
    ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(0,0,0,0.4)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 3;

    const grad = ctx.createLinearGradient(buttX, buttY, tipX, tipY);
    grad.addColorStop(0, '#3d2518');
    grad.addColorStop(0.15, '#8b6340');
    grad.addColorStop(0.5, '#d4b896');
    grad.addColorStop(0.85, '#f0e8d8');
    grad.addColorStop(1, '#2980b9');

    ctx.beginPath();
    ctx.moveTo(buttX, buttY);
    ctx.lineTo(tipX, tipY);
    ctx.strokeStyle = grad;
    ctx.lineWidth = 9;
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.beginPath();
    ctx.arc(tipX, tipY, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#1a5a80';
    ctx.fill();
    ctx.restore();
  }

  drawAimGuide(ctx, cueBall, balls, bounds, angle) {
    const dir = new Vec2(Math.cos(angle), Math.sin(angle));
    let start = cueBall.pos.clone();
    let remaining = 900;
    const activeBalls = balls.filter(b => b.active && !b.pocketed && b.id !== 0 && !b.pocketAnim);

    ctx.save();

    for (let bounce = 0; bounce < 4 && remaining > 0; bounce++) {
      let hitDist = remaining;
      let hitBall = null;
      let hitWall = false;
      let wallNormal = null;

      for (const ball of activeBalls) {
        const toBall = Vec2.sub(ball.pos, start);
        const proj = toBall.dot(dir);
        if (proj <= 0.5) continue;
        const perp = Math.abs(toBall.x * dir.y - toBall.y * dir.x);
        const combined = cueBall.radius + ball.radius;
        if (perp > combined) continue;
        const along = Math.sqrt(Math.max(0, combined * combined - perp * perp));
        const dist = proj - along;
        if (dist > 0 && dist < hitDist) {
          hitDist = dist;
          hitBall = ball;
          hitWall = false;
        }
      }

      if (!hitBall) {
        const wallHit = this.rayWall(start, dir, bounds, hitDist);
        if (wallHit) {
          hitDist = wallHit.dist;
          wallNormal = wallHit.normal;
          hitWall = true;
        }
      }

      const endX = start.x + dir.x * hitDist;
      const endY = start.y + dir.y * hitDist;

      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = bounce === 0 ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.35)';
      ctx.lineWidth = bounce === 0 ? 2.5 : 1.2;
      ctx.setLineDash(bounce === 0 ? [] : [5, 5]);
      ctx.stroke();

      if (hitBall) {
        const gx = endX + dir.x * cueBall.radius;
        const gy = endY + dir.y * cueBall.radius;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.arc(gx, gy, cueBall.radius, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.35)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        const targetDir = Vec2.sub(hitBall.pos, new Vec2(gx, gy)).normalize();
        ctx.beginPath();
        ctx.moveTo(hitBall.pos.x, hitBall.pos.y);
        ctx.lineTo(hitBall.pos.x + targetDir.x * 80, hitBall.pos.y + targetDir.y * 80);
        ctx.strokeStyle = 'rgba(255,220,80,0.55)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        break;
      }

      if (hitWall && wallNormal) {
        remaining -= hitDist;
        start.set(endX, endY);
        const dot = dir.dot(wallNormal);
        dir.x -= 2 * dot * wallNormal.x;
        dir.y -= 2 * dot * wallNormal.y;
      } else {
        break;
      }
    }

    ctx.restore();
  }

  rayWall(start, dir, bounds, maxDist) {
    let best = null;
    const checks = [
      { axis: 'x', value: bounds.left, normal: new Vec2(1, 0) },
      { axis: 'x', value: bounds.right, normal: new Vec2(-1, 0) },
      { axis: 'y', value: bounds.top, normal: new Vec2(0, 1) },
      { axis: 'y', value: bounds.bottom, normal: new Vec2(0, -1) },
    ];

    for (const wall of checks) {
      const d = wall.axis === 'x'
        ? (wall.value - start.x) / dir.x
        : (wall.value - start.y) / dir.y;
      if (d > 0 && d < maxDist && (!best || d < best.dist)) {
        best = { dist: d, normal: wall.normal };
      }
    }
    return best;
  }
}

export function findBestShot(game) {
  const cue = game.getCueBall();
  if (!cue) return null;

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
      if (dist < 30) continue;

      const angle = Math.atan2(toGhost.y, toGhost.x);

      if (!isPathClear(cue.pos, { x: ghostX, y: ghostY }, game.balls, cue.radius, [0, target.id])) continue;
      if (!isPathClear(target.pos, pocket, game.balls, r, [0, target.id])) continue;

      const distScore = 1 / (dist * 0.01 + 1);
      const pocketDist = Vec2.dist(target.pos, pocket);
      const score = distScore + 1 / (pocketDist * 0.005 + 1);

      if (!best || score > best.score) {
        const power = Math.min(game.table.width * 0.012, 8 + dist * 0.018);
        best = { angle, power: Math.min(24, power), score, target };
      }
    }
  }

  if (!best && game.firstShot) {
    const rackCenter = { x: game.table.bounds.rackX - 80, y: game.table.bounds.rackY };
    const toRack = Vec2.sub(rackCenter, cue.pos);
    return { angle: Math.atan2(toRack.y, toRack.x), power: 22, score: 0.1 };
  }

  if (!best) {
    for (const target of targets) {
      const toTarget = Vec2.sub(target.pos, cue.pos);
      const angle = Math.atan2(toTarget.y, toTarget.x);
      if (isPathClear(cue.pos, target.pos, game.balls, cue.radius, [0, target.id])) {
        return { angle, power: 12, score: 0.05 };
      }
    }
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
