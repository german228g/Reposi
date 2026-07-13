const BALL_DEFS = {
  0: { base: '#f8f8f2', dark: '#d8d8d0', label: '' },
  1: { base: '#ffd700', dark: '#c9a000', label: '1' },
  2: { base: '#1e6fd9', dark: '#0d4080', label: '2' },
  3: { base: '#e5252a', dark: '#8b1010', label: '3' },
  4: { base: '#7b2cbf', dark: '#3d1260', label: '4' },
  5: { base: '#ff6b1a', dark: '#a04000', label: '5' },
  6: { base: '#1aad5c', dark: '#0a6030', label: '6' },
  7: { base: '#7b1818', dark: '#3d0a0a', label: '7' },
  8: { base: '#111111', dark: '#000000', label: '8' },
  9: { base: '#ffd700', dark: '#c9a000', label: '9', stripe: true },
  10: { base: '#1e6fd9', dark: '#0d4080', label: '10', stripe: true },
  11: { base: '#e5252a', dark: '#8b1010', label: '11', stripe: true },
  12: { base: '#7b2cbf', dark: '#3d1260', label: '12', stripe: true },
  13: { base: '#ff6b1a', dark: '#a04000', label: '13', stripe: true },
  14: { base: '#1aad5c', dark: '#0a6030', label: '14', stripe: true },
  15: { base: '#7b1818', dark: '#3d0a0a', label: '15', stripe: true },
};

export class Renderer {
  constructor(table) {
    this.table = table;
    this.feltPattern = this.createFeltPattern();
    this.woodPattern = this.createWoodPattern();
    this.lightPos = { x: 0.5, y: 0.35 };
  }

  createFeltPattern() {
    const size = 64;
    const c = document.createElement('canvas');
    c.width = c.height = size;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#1a7a42';
    ctx.fillRect(0, 0, size, size);
    for (let i = 0; i < 400; i++) {
      const x = Math.random() * size;
      const y = Math.random() * size;
      const a = 0.03 + Math.random() * 0.05;
      ctx.fillStyle = Math.random() > 0.5
        ? `rgba(255,255,255,${a})`
        : `rgba(0,0,0,${a})`;
      ctx.fillRect(x, y, 1, 1);
    }
    return ctx.createPattern(c, 'repeat');
  }

  createWoodPattern() {
    const w = 256, h = 64;
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, '#a0714f');
    grad.addColorStop(0.5, '#7a5235');
    grad.addColorStop(1, '#5c3a22');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < 30; i++) {
      ctx.strokeStyle = `rgba(0,0,0,${0.05 + Math.random() * 0.08})`;
      ctx.lineWidth = 0.5 + Math.random();
      ctx.beginPath();
      const y = Math.random() * h;
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(w * 0.3, y + Math.random() * 4 - 2, w * 0.7, y + Math.random() * 4 - 2, w, y);
      ctx.stroke();
    }
    return ctx.createPattern(c, 'repeat');
  }

  drawTable(ctx) {
    const { width: w, height: h, railWidth: r, pockets } = this.table;

    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, w, h);

    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.6)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 12;
    this.drawRails(ctx, w, h, r);
    ctx.restore();

    const fx = r + 6, fy = r + 6, fw = w - (r + 6) * 2, fh = h - (r + 6) * 2;

    ctx.save();
    ctx.beginPath();
    ctx.rect(fx, fy, fw, fh);
    ctx.clip();

    ctx.fillStyle = this.feltPattern;
    ctx.fillRect(fx, fy, fw, fh);

    const vignette = ctx.createRadialGradient(w / 2, h / 2, 80, w / 2, h / 2, w * 0.65);
    vignette.addColorStop(0, 'rgba(255,255,255,0.08)');
    vignette.addColorStop(0.6, 'rgba(0,0,0,0)');
    vignette.addColorStop(1, 'rgba(0,0,0,0.35)');
    ctx.fillStyle = vignette;
    ctx.fillRect(fx, fy, fw, fh);

    const lamp = ctx.createRadialGradient(
      w * this.lightPos.x, h * this.lightPos.y, 20,
      w * this.lightPos.x, h * this.lightPos.y, w * 0.55
    );
    lamp.addColorStop(0, 'rgba(255,255,220,0.12)');
    lamp.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = lamp;
    ctx.fillRect(fx, fy, fw, fh);

    this.drawSpots(ctx);
    ctx.restore();

    for (const pocket of pockets) {
      this.drawPocket(ctx, pocket);
    }

    this.drawCushions(ctx, w, h, r);
  }

  drawRails(ctx, w, h, r) {
    ctx.fillStyle = this.woodPattern;
    ctx.fillRect(0, 0, w, h);

    const inner = ctx.createLinearGradient(0, 0, w, h);
    inner.addColorStop(0, 'rgba(255,255,255,0.12)');
    inner.addColorStop(1, 'rgba(0,0,0,0.2)');
    ctx.fillStyle = inner;
    ctx.fillRect(r * 0.3, r * 0.3, w - r * 0.6, h - r * 0.6);
  }

  drawCushions(ctx, w, h, r) {
    ctx.strokeStyle = '#1a6b35';
    ctx.lineWidth = 5;
    ctx.strokeRect(r + 3, r + 3, w - (r + 3) * 2, h - (r + 3) * 2);

    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    ctx.strokeRect(r + 8, r + 8, w - (r + 8) * 2, h - (r + 8) * 2);
  }

  drawSpots(ctx) {
    const { bounds } = this.table;
    for (const spot of [{ x: bounds.cueX, y: bounds.cueY }, { x: bounds.rackX, y: bounds.rackY }]) {
      ctx.beginPath();
      ctx.arc(spot.x, spot.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.25)';
      ctx.fill();
    }
  }

  drawPocket(ctx, pocket) {
    const pr = this.table.pocketRadius;

    ctx.save();
    ctx.beginPath();
    ctx.arc(pocket.x, pocket.y, pr + 6, 0, Math.PI * 2);
    const apron = ctx.createRadialGradient(pocket.x, pocket.y, pr * 0.5, pocket.x, pocket.y, pr + 6);
    apron.addColorStop(0, '#1a0e08');
    apron.addColorStop(1, '#3d2518');
    ctx.fillStyle = apron;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pocket.x, pocket.y, pr, 0, Math.PI * 2);
    const hole = ctx.createRadialGradient(
      pocket.x - pr * 0.2, pocket.y - pr * 0.2, 0,
      pocket.x, pocket.y, pr
    );
    hole.addColorStop(0, '#1a1a1a');
    hole.addColorStop(0.7, '#050505');
    hole.addColorStop(1, '#000000');
    ctx.fillStyle = hole;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pocket.x - pr * 0.25, pocket.y - pr * 0.25, pr * 0.15, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.04)';
    ctx.fill();
    ctx.restore();
  }

  drawBallShadow(ctx, ball, alpha = 0.45) {
    if (!ball.active || ball.pocketed) return;
    const { x, y } = ball.pos;
    const r = ball.radius;
    const speed = ball.vel.length();
    const stretch = Math.min(speed * 0.02, 0.3);

    ctx.save();
    ctx.translate(x, y + r * 0.55);
    ctx.scale(1 + stretch, 0.45 - stretch * 0.1);
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.95, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(0,0,0,${alpha})`;
    ctx.filter = 'blur(3px)';
    ctx.fill();
    ctx.restore();
  }

  drawBall(ctx, ball, pocketT = 0) {
    if (!ball.active) return;

    const { x, y } = ball.pos;
    const r = ball.radius;
    const def = BALL_DEFS[ball.id] || BALL_DEFS[1];

    let scale = 1;
    let drawX = x, drawY = y;
    if (pocketT > 0) {
      scale = 1 - pocketT * 0.85;
      drawX = x + (ball.pocketTarget?.x - x) * pocketT * 0.5;
      drawY = y + (ball.pocketTarget?.y - y) * pocketT * 0.5;
    }

    const drawR = r * scale;
    if (drawR < 0.5) return;

    ctx.save();
    ctx.translate(drawX, drawY);

    const lightX = -drawR * 0.38;
    const lightY = -drawR * 0.42;

    const bodyGrad = ctx.createRadialGradient(lightX, lightY, drawR * 0.05, 0, 0, drawR);
    bodyGrad.addColorStop(0, this.lighten(def.base, 50));
    bodyGrad.addColorStop(0.45, def.base);
    bodyGrad.addColorStop(0.85, def.dark);
    bodyGrad.addColorStop(1, this.darken(def.dark, 30));

    ctx.beginPath();
    ctx.arc(0, 0, drawR, 0, Math.PI * 2);
    ctx.fillStyle = bodyGrad;
    ctx.fill();

    if (def.stripe) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(0, 0, drawR, 0, Math.PI * 2);
      ctx.clip();
      ctx.fillStyle = '#f5f5ee';
      ctx.fillRect(-drawR, -drawR * 0.3, drawR * 2, drawR * 0.6);
      ctx.restore();
    }

    if (def.label) {
      const cr = drawR * 0.4;
      ctx.beginPath();
      ctx.arc(0, 0, cr, 0, Math.PI * 2);
      const circleGrad = ctx.createRadialGradient(-cr * 0.2, -cr * 0.2, 0, 0, 0, cr);
      circleGrad.addColorStop(0, '#ffffff');
      circleGrad.addColorStop(1, ball.id === 8 ? '#e8e8e8' : '#f0f0f0');
      ctx.fillStyle = circleGrad;
      ctx.fill();

      ctx.fillStyle = ball.id === 8 ? '#111' : '#222';
      ctx.font = `bold ${drawR * 0.62}px 'Segoe UI', sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(def.label, 0, 1);
    }

    ctx.beginPath();
    ctx.arc(lightX, lightY, drawR * 0.22, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.75)';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(lightX * 0.5, lightY * 0.5, drawR * 0.1, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fill();

    const rimGrad = ctx.createRadialGradient(0, 0, drawR * 0.7, 0, 0, drawR);
    rimGrad.addColorStop(0, 'rgba(0,0,0,0)');
    rimGrad.addColorStop(1, 'rgba(0,0,0,0.45)');
    ctx.beginPath();
    ctx.arc(0, 0, drawR, 0, Math.PI * 2);
    ctx.fillStyle = rimGrad;
    ctx.fill();

    ctx.restore();
  }

  lighten(hex, amount) {
    const n = parseInt(hex.slice(1), 16);
    const r = Math.min(255, (n >> 16) + amount);
    const g = Math.min(255, ((n >> 8) & 0xff) + amount);
    const b = Math.min(255, (n & 0xff) + amount);
    return `rgb(${r},${g},${b})`;
  }

  darken(hex, amount) {
    const n = parseInt(hex.slice(1), 16);
    const r = Math.max(0, (n >> 16) - amount);
    const g = Math.max(0, ((n >> 8) & 0xff) - amount);
    const b = Math.max(0, (n & 0xff) - amount);
    return `rgb(${r},${g},${b})`;
  }
}
