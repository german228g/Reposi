import { Vec2 } from './physics.js';

const BALL_COLORS = {
  0: { fill: '#f5f5f0', stroke: '#ccc', label: '' },
  1: { fill: '#f4d03f', stroke: '#c9a227', label: '1', stripe: false },
  2: { fill: '#2e86c1', stroke: '#1a5276', label: '2', stripe: false },
  3: { fill: '#e74c3c', stroke: '#922b21', label: '3', stripe: false },
  4: { fill: '#8e44ad', stroke: '#5b2c6f', label: '4', stripe: false },
  5: { fill: '#e67e22', stroke: '#a04000', label: '5', stripe: false },
  6: { fill: '#27ae60', stroke: '#1e8449', label: '6', stripe: false },
  7: { fill: '#7b241c', stroke: '#4a1510', label: '7', stripe: false },
  8: { fill: '#1a1a1a', stroke: '#000', label: '8', stripe: false },
  9: { fill: '#f4d03f', stroke: '#c9a227', label: '9', stripe: true },
  10: { fill: '#2e86c1', stroke: '#1a5276', label: '10', stripe: true },
  11: { fill: '#e74c3c', stroke: '#922b21', label: '11', stripe: true },
  12: { fill: '#8e44ad', stroke: '#5b2c6f', label: '12', stripe: true },
  13: { fill: '#e67e22', stroke: '#a04000', label: '13', stripe: true },
  14: { fill: '#27ae60', stroke: '#1e8449', label: '14', stripe: true },
  15: { fill: '#7b241c', stroke: '#4a1510', label: '15', stripe: true },
};

export class Ball {
  constructor(id, x, y, radius = 12) {
    this.id = id;
    this.pos = new Vec2(x, y);
    this.vel = new Vec2(0, 0);
    this.radius = radius;
    this.mass = 1;
    this.active = true;
    this.pocketed = false;
    this.color = BALL_COLORS[id] || BALL_COLORS[1];
    this.isCue = id === 0;
    this.isEight = id === 8;
    this.isSolid = id >= 1 && id <= 7;
    this.isStripe = id >= 9 && id <= 15;
  }

  draw(ctx) {
    if (!this.active || this.pocketed) return;

    const { x, y } = this.pos;
    const r = this.radius;
    const c = this.color;

    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = c.fill;
    ctx.fill();
    ctx.strokeStyle = c.stroke;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    if (c.stripe) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.clip();
      ctx.fillStyle = '#f5f5f0';
      ctx.fillRect(x - r, y - r * 0.32, r * 2, r * 0.64);
      ctx.restore();
    }

    if (c.label) {
      const circleR = r * 0.42;
      ctx.beginPath();
      ctx.arc(x, y, circleR, 0, Math.PI * 2);
      ctx.fillStyle = this.isEight ? '#f5f5f0' : '#fff';
      ctx.fill();

      ctx.fillStyle = this.isEight ? '#1a1a1a' : '#222';
      ctx.font = `bold ${r * 0.65}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(c.label, x, y + 1);
    }

    const highlightX = x - r * 0.35;
    const highlightY = y - r * 0.35;
    ctx.beginPath();
    ctx.arc(highlightX, highlightY, r * 0.18, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.fill();

    ctx.restore();
  }

  pocket() {
    this.pocketed = true;
    this.active = false;
    this.vel.set(0, 0);
  }

  reset(x, y) {
    this.pos.set(x, y);
    this.vel.set(0, 0);
    this.active = true;
    this.pocketed = false;
  }
}

export function createRack(tableBounds, ballRadius) {
  const balls = [new Ball(0, tableBounds.cueX, tableBounds.cueY, ballRadius)];

  const rackX = tableBounds.rackX;
  const rackY = tableBounds.rackY;
  const spacing = ballRadius * 2.05;

  const order = [1, 9, 2, 10, 8, 3, 11, 4, 12, 5, 13, 6, 14, 7, 15];

  let idx = 0;
  for (let row = 0; row < 5; row++) {
    const rowY = rackY + row * spacing * Math.sin(Math.PI / 3);
    const rowCount = row + 1;
    const rowWidth = (rowCount - 1) * spacing;
    const startX = rackX - rowWidth / 2;

    for (let col = 0; col < rowCount; col++) {
      const x = startX + col * spacing;
      const y = rowY;
      const id = order[idx++];
      balls.push(new Ball(id, x, y, ballRadius));
    }
  }

  return balls;
}

export function getBallGroup(ball) {
  if (ball.isSolid) return 'solid';
  if (ball.isStripe) return 'stripe';
  return null;
}
