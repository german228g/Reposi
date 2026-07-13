import { Vec2 } from './physics.js';

export class InputController {
  constructor(canvas, table, cue, game, onPowerChange) {
    this.canvas = canvas;
    this.table = table;
    this.cue = cue;
    this.game = game;
    this.onPowerChange = onPowerChange;
    this.active = false;
    this.pointerId = null;
    this.lastPos = new Vec2(0, 0);

    canvas.style.touchAction = 'none';
    canvas.addEventListener('pointerdown', (e) => this.onDown(e));
    canvas.addEventListener('pointermove', (e) => this.onMove(e));
    canvas.addEventListener('pointerup', (e) => this.onUp(e));
    canvas.addEventListener('pointercancel', (e) => this.onUp(e));
  }

  getPos(e) {
    const t = e.touches?.[0] || e.changedTouches?.[0];
    const x = t ? t.clientX : e.clientX;
    const y = t ? t.clientY : e.clientY;
    const pos = this.table.screenToWorld(x, y);
    this.lastPos.set(pos.x, pos.y);
    return pos;
  }

  onDown(e) {
    if (this.game.canPlaceCueBall()) {
      e.preventDefault();
      const pos = this.getPos(e);
      this.game.placeCueBall(pos.x, pos.y);
      return;
    }

    if (!this.game.canShoot()) return;

    e.preventDefault();
    this.active = true;
    this.pointerId = e.pointerId;
    this.canvas.setPointerCapture(e.pointerId);
    this.cue.startShot();
    this.updateAimPower(this.getPos(e));
  }

  onMove(e) {
    if (!this.active || e.pointerId !== this.pointerId) return;
    e.preventDefault();
    this.updateAimPower(this.getPos(e));
  }

  onUp(e) {
    if (!this.active || e.pointerId !== this.pointerId) return;
    e.preventDefault();
    this.active = false;

    try {
      this.canvas.releasePointerCapture(e.pointerId);
    } catch (_) { /* ignore */ }

    const shot = this.cue.release();
    if (shot) {
      this.game.shoot(shot.vx, shot.vy);
    } else {
      this.cue.cancelPull();
    }
    this.onPowerChange?.(0);
  }

  updateAimPower(pos) {
    const cueBall = this.game.getCueBall();
    if (!cueBall) return;

    this.cue.setAimFromPoint(pos, cueBall.pos);
    this.cue.updatePowerFromFinger(pos, cueBall.pos);
    this.onPowerChange?.(this.cue.getPowerPercent());
  }
}
