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

    canvas.style.touchAction = 'none';
    canvas.addEventListener('pointerdown', (e) => this.onDown(e), { passive: false });
    canvas.addEventListener('pointermove', (e) => this.onMove(e), { passive: false });
    canvas.addEventListener('pointerup', (e) => this.onUp(e), { passive: false });
    canvas.addEventListener('pointercancel', (e) => this.onUp(e), { passive: false });
  }

  getPos(e) {
    const t = e.touches?.[0] || e.changedTouches?.[0];
    const x = t ? t.clientX : e.clientX;
    const y = t ? t.clientY : e.clientY;
    return this.table.screenToWorld(x, y);
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
    try { this.canvas.setPointerCapture(e.pointerId); } catch (_) {}

    this.cue.beginAim();
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
    try { this.canvas.releasePointerCapture(e.pointerId); } catch (_) {}

    this.fire();
  }

  updateAimPower(pos) {
    const cueBall = this.game.getCueBall();
    if (!cueBall) return;
    this.cue.setAimFromPoint(pos, cueBall.pos);
    this.cue.setPowerFromFinger(pos, cueBall.pos);
    this.onPowerChange?.(this.cue.getPowerPercent());
  }

  fire(forceFull = false) {
    const shot = this.cue.fireShot(forceFull);
    if (shot) {
      this.game.shoot(shot.vx, shot.vy);
      if (navigator.vibrate) navigator.vibrate(15);
    } else {
      this.cue.cancelAim();
    }
    this.onPowerChange?.(this.cue.getPowerPercent());
  }
}
