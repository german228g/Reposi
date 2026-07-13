import { Vec2 } from './physics.js';

export class Cue {
  constructor() {
    this.aiming = false;
    this.pulling = false;
    this.aimAngle = 0;
    this.pullDistance = 0;
    this.maxPull = 120;
    this.maxPower = 18;
    this.showAimLine = true;
    this.mousePos = new Vec2(0, 0);
  }

  startAim(mousePos, cueBallPos) {
    if (!cueBallPos) return;
    this.aiming = true;
    this.mousePos = mousePos.clone();
    this.updateAngle(cueBallPos);
  }

  updateAim(mousePos, cueBallPos) {
    if (!this.aiming || !cueBallPos) return;
    this.mousePos = mousePos.clone();
    this.updateAngle(cueBallPos);
  }

  updateAngle(cueBallPos) {
    const dir = Vec2.sub(this.mousePos, cueBallPos);
    this.aimAngle = Math.atan2(dir.y, dir.x);
  }

  startPull() {
    if (!this.aiming) return;
    this.pulling = true;
    this.pullDistance = 0;
  }

  updatePull(mousePos, cueBallPos) {
    if (!this.pulling || !cueBallPos) return;

    const aimDir = new Vec2(Math.cos(this.aimAngle), Math.sin(this.aimAngle));
    const toMouse = Vec2.sub(mousePos, cueBallPos);
    const pull = -toMouse.dot(aimDir);
    this.pullDistance = Math.max(0, Math.min(pull, this.maxPull));
  }

  release() {
    if (!this.pulling) return null;

    const power = (this.pullDistance / this.maxPull) * this.maxPower;
    const angle = this.aimAngle;

    this.pulling = false;
    this.aiming = false;
    this.pullDistance = 0;

    if (power < 0.3) return null;

    return {
      vx: Math.cos(angle) * power,
      vy: Math.sin(angle) * power,
      power,
    };
  }

  cancel() {
    this.aiming = false;
    this.pulling = false;
    this.pullDistance = 0;
  }

  getPowerPercent() {
    return (this.pullDistance / this.maxPull) * 100;
  }

  draw(ctx, cueBall, balls) {
    if (!cueBall || !cueBall.active || cueBall.pocketed) return;
    if (!this.aiming && !this.pulling) return;

    const { x, y } = cueBall.pos;
    const angle = this.aimAngle;
    const pull = this.pullDistance;

    if (this.showAimLine) {
      this.drawAimLine(ctx, cueBall, balls, angle);
    }

    const cueLength = 280;
    const tipOffset = cueBall.radius + 4 + pull;
    const buttX = x - Math.cos(angle) * (tipOffset + cueLength);
    const buttY = y - Math.sin(angle) * (tipOffset + cueLength);
    const tipX = x - Math.cos(angle) * tipOffset;
    const tipY = y - Math.sin(angle) * tipOffset;

    ctx.save();
    ctx.lineCap = 'round';

    const grad = ctx.createLinearGradient(buttX, buttY, tipX, tipY);
    grad.addColorStop(0, '#5c3d2e');
    grad.addColorStop(0.3, '#c4a574');
    grad.addColorStop(0.85, '#e8dcc8');
    grad.addColorStop(1, '#3d8ec9');

    ctx.beginPath();
    ctx.moveTo(buttX, buttY);
    ctx.lineTo(tipX, tipY);
    ctx.strokeStyle = grad;
    ctx.lineWidth = 6;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(tipX, tipY, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#2a6a9a';
    ctx.fill();

    ctx.restore();
  }

  drawAimLine(ctx, cueBall, balls, angle) {
    const dir = new Vec2(Math.cos(angle), Math.sin(angle));
    let start = cueBall.pos.clone();
    let remaining = 600;

    ctx.save();
    ctx.setLineDash([6, 6]);
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';

    const activeBalls = balls.filter(b => b.active && !b.pocketed && b.id !== 0);

    for (let bounce = 0; bounce < 3 && remaining > 0; bounce++) {
      let hitDist = remaining;
      let hitBall = null;

      for (const ball of activeBalls) {
        const toBall = Vec2.sub(ball.pos, start);
        const proj = toBall.dot(dir);
        if (proj <= 0) continue;

        const perpDist = Math.abs(toBall.x * dir.y - toBall.y * dir.x);
        const combinedR = cueBall.radius + ball.radius;
        if (perpDist > combinedR) continue;

        const alongDist = Math.sqrt(combinedR * combinedR - perpDist * perpDist);
        const dist = proj - alongDist;
        if (dist > 0 && dist < hitDist) {
          hitDist = dist;
          hitBall = ball;
        }
      }

      const endX = start.x + dir.x * hitDist;
      const endY = start.y + dir.y * hitDist;

      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(endX, endY);
      ctx.stroke();

      if (hitBall) {
        const ghostR = cueBall.radius;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.arc(endX + dir.x * ghostR, endY + dir.y * ghostR, ghostR, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.25)';
        ctx.stroke();
        break;
      }

      remaining -= hitDist;
      start.set(endX, endY);
      dir.x = -dir.x;
      dir.y = -dir.y;
    }

    ctx.restore();
  }
}
