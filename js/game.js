import { Vec2, resolveBallCollision, isMoving } from './physics.js';
import { PHYSICS, applyFriction } from './physicsConfig.js';
import { createRack, getBallGroup } from './balls.js';
import { findBestShot } from './cue.js';

export const GameState = {
  AIMING: 'aiming',
  SHOOTING: 'shooting',
  BALL_IN_HAND: 'ball_in_hand',
  AI_THINKING: 'ai_thinking',
  GAME_OVER: 'game_over',
};

export class Game {
  constructor(table) {
    this.table = table;
    this.balls = [];
    this.state = GameState.AIMING;
    this.currentPlayer = 1;
    this.players = {
      1: { name: 'Вы', isHuman: true, group: null },
      2: { name: 'Соперник', isHuman: false, group: null },
    };
    this.message = 'Потяните кий назад и отпустите';
    this.winner = null;
    this.firstShot = true;
    this.shotInProgress = false;
    this.pocketedThisShot = [];
    this.firstHitBall = null;
    this.cushionBeforeHit = false;
    this.foul = false;
    this.foulReason = '';
    this.friction = 0.72;
    this.onUpdate = null;
    this.aiTimer = 0;
    this.aiShot = null;
    this.ballInHandPlayer = null;
    this.tableOpen = true;
  }

  reset() {
    this.balls = createRack(this.table.bounds, this.table.ballRadius);
    this.state = GameState.AIMING;
    this.currentPlayer = 1;
    this.players[1].group = null;
    this.players[2].group = null;
    this.message = 'Ведите палец от битка — чем дальше, тем сильнее удар';
    this.winner = null;
    this.firstShot = true;
    this.tableOpen = true;
    this.shotInProgress = false;
    this.pocketedThisShot = [];
    this.firstHitBall = null;
    this.cushionBeforeHit = false;
    this.foul = false;
    this.aiTimer = 0;
    this.aiShot = null;
    this.ballInHandPlayer = null;
    this.notify();
  }

  isHumanTurn() {
    return this.players[this.currentPlayer].isHuman;
  }

  getCurrentPlayer() {
    return this.players[this.currentPlayer];
  }

  getPlayerGroup(playerId) {
    return this.players[playerId].group;
  }

  getCueBall() {
    return this.balls.find(b => b.id === 0);
  }

  getActiveBalls() {
    return this.balls.filter(b => b.active && !b.pocketed && !b.pocketAnim);
  }

  hasAnimations() {
    return this.balls.some(b => b.pocketAnim);
  }

  canShoot() {
    return this.state === GameState.AIMING
      && !isMoving(this.balls)
      && !this.hasAnimations()
      && this.isHumanTurn();
  }

  canPlaceCueBall() {
    return this.state === GameState.BALL_IN_HAND
      && this.ballInHandPlayer === this.currentPlayer
      && this.isHumanTurn();
  }

  getLegalTargets() {
    const player = this.getCurrentPlayer();
    if (this.tableOpen || !player.group) {
      return this.balls.filter(b => b.active && !b.pocketed && !b.isCue && !b.isEight && !b.pocketAnim);
    }
    if (this.isGroupCleared(player.group)) {
      return this.balls.filter(b => b.active && !b.pocketed && b.isEight && !b.pocketAnim);
    }
    return this.balls.filter(b => b.active && !b.pocketed && getBallGroup(b) === player.group && !b.pocketAnim);
  }

  shoot(vx, vy) {
    if (this.state !== GameState.AIMING && this.state !== GameState.AI_THINKING) return false;
    if (isMoving(this.balls) || this.hasAnimations()) return false;

    const cue = this.getCueBall();
    if (!cue) return false;

    cue.vel.set(vx, vy);
    this.state = GameState.SHOOTING;
    this.shotInProgress = true;
    this.pocketedThisShot = [];
    this.firstHitBall = null;
    this.cushionBeforeHit = false;
    this.foul = false;
    this.foulReason = '';
    this.aiShot = null;
    this.message = this.isHumanTurn() ? '' : 'Соперник бьёт...';
    this.notify();
    return true;
  }

  placeCueBall(x, y) {
    if (!this.canPlaceCueBall()) return false;

    const b = this.table.bounds;
    const r = this.table.ballRadius;
    const cue = this.getCueBall();

    x = Math.max(b.left + r, Math.min(b.right - r, x));
    y = Math.max(b.top + r, Math.min(b.bottom - r, y));

    for (const ball of this.balls) {
      if (ball.id === 0 || !ball.active || ball.pocketed) continue;
      if (Vec2.dist({ x, y }, ball.pos) < r * 2.05) {
        this.message = 'Слишком близко к другому шару';
        this.notify();
        return false;
      }
    }

    cue.reset(x, y);
    this.ballInHandPlayer = null;
    this.state = GameState.AIMING;
    this.message = 'Ваш удар';
    this.notify();
    return true;
  }

  update(dt) {
    if (this.state === GameState.GAME_OVER) return;

    for (const ball of this.balls) {
      if (ball.pocketAnim) {
        ball.updatePocketAnim(dt);
        continue;
      }
    }

    if (this.state === GameState.AI_THINKING) {
      this.aiTimer -= dt;
      if (this.aiTimer <= 0 && this.aiShot) {
        const { angle, power } = this.aiShot;
        this.shoot(Math.cos(angle) * power, Math.sin(angle) * power);
      }
      return;
    }

    if (this.state !== GameState.SHOOTING) {
      if (this.state === GameState.AIMING && !this.isHumanTurn() && !isMoving(this.balls) && !this.hasAnimations()) {
        this.startAI();
      }
      if (this.state === GameState.BALL_IN_HAND && !this.isHumanTurn() && !isMoving(this.balls)) {
        this.aiPlaceCueBall();
      }
      return;
    }

    const activeBalls = this.getActiveBalls();
    const steps = PHYSICS.substeps;
    const subDt = dt / steps;
    let anyMoving = false;

    for (let step = 0; step < steps; step++) {
      for (const ball of activeBalls) {
        ball.pos.add(Vec2.scale(ball.vel, subDt));
        applyFriction(ball.vel, subDt);
        if (ball.vel.length() > PHYSICS.stopSpeed) anyMoving = true;

        if (this.table.constrainBall(ball, PHYSICS.cushionRestitution)) {
          if (!this.firstHitBall) this.cushionBeforeHit = true;
        }

        const pocket = this.table.checkPocket(ball);
        if (pocket) {
          this.onBallPocketed(ball, pocket);
        }
      }

      for (let i = 0; i < activeBalls.length; i++) {
        for (let j = i + 1; j < activeBalls.length; j++) {
          if (resolveBallCollision(activeBalls[i], activeBalls[j], PHYSICS.restitution)) {
            this.registerHit(activeBalls[i], activeBalls[j]);
          }
        }
      }
    }

    const stillMoving = anyMoving || isMoving(this.balls, PHYSICS.stopSpeed);
    const animating = this.hasAnimations();

    if (this.shotInProgress && !stillMoving && !animating) {
      this.endShot();
    }
  }

  registerHit(a, b) {
    if (!this.firstHitBall) {
      if (a.id === 0) this.firstHitBall = b;
      else if (b.id === 0) this.firstHitBall = a;
    }
  }

  onBallPocketed(ball, pocket) {
    if (ball.pocketAnim) return;
    ball.startPocketAnim(pocket);
    this.pocketedThisShot.push(ball);

    if (ball.id === 0) {
      this.foul = true;
      this.foulReason = 'Биток в лузу';
    }
  }

  startAI() {
    this.state = GameState.AI_THINKING;
    this.aiTimer = 1.2 + Math.random() * 0.8;
    const shot = findBestShot(this);
    if (shot) {
      const err = (Math.random() - 0.5) * 0.04;
      const pErr = (Math.random() - 0.5) * 1.5;
      this.aiShot = { angle: shot.angle + err, power: Math.max(PHYSICS.minSpeed(this.table), shot.power + pErr) };
    } else {
      const cue = this.getCueBall();
      const maxSpd = PHYSICS.maxSpeed(this.table);
      this.aiShot = { angle: 0, power: maxSpd * 0.5 };
      if (cue) {
        const targets = this.getLegalTargets();
        if (targets.length) {
          const t = targets[Math.floor(Math.random() * targets.length)];
          const dir = Vec2.sub(t.pos, cue.pos);
          this.aiShot.angle = Math.atan2(dir.y, dir.x) + (Math.random() - 0.5) * 0.2;
        }
      }
    }
    this.message = 'Соперник прицеливается...';
    this.notify();
  }

  aiPlaceCueBall() {
    const b = this.table.bounds;
    const r = this.table.ballRadius;
    const cue = this.getCueBall();
    let best = { x: b.cueX, y: b.cueY, score: 0 };

    for (let i = 0; i < 40; i++) {
      const x = b.left + r + Math.random() * (b.right - b.left - r * 2);
      const y = b.top + r + Math.random() * (b.bottom - b.top - r * 2);
      let ok = true;
      for (const ball of this.balls) {
        if (ball.id === 0 || !ball.active || ball.pocketed) continue;
        if (Vec2.dist({ x, y }, ball.pos) < r * 2.1) { ok = false; break; }
      }
      if (!ok) continue;
      cue.reset(x, y);
      const shot = findBestShot(this);
      const score = shot ? shot.score : Math.random() * 0.01;
      if (score > best.score) best = { x, y, score };
    }

    cue.reset(best.x, best.y);
    this.ballInHandPlayer = null;
    this.state = GameState.AIMING;
    this.message = 'Соперник бьёт...';
    this.notify();
  }

  endShot() {
    this.shotInProgress = false;

    if (this.firstShot) {
      this.resolveBreak();
      return;
    }
    this.resolveNormalShot();
  }

  resolveBreak() {
    this.firstShot = false;
    const cuePocketed = this.pocketedThisShot.some(b => b.id === 0);
    const objectBalls = this.pocketedThisShot.filter(b => b.id !== 0);

    if (cuePocketed) {
      this.handleFoul('Биток в лузу при разбое');
      return;
    }

    if (!this.firstHitBall) {
      this.handleFoul('Не попали ни в один шар');
      return;
    }

    if (objectBalls.length === 0) {
      this.continueTurn('Разбой! Ещё один удар.');
      return;
    }

    this.assignGroupsFromPocket(objectBalls);
    this.tableOpen = false;
    this.continueTurn(this.getTurnMessage(true));
  }

  assignGroupsFromPocket(pocketed) {
    const solids = pocketed.filter(b => b.isSolid);
    const stripes = pocketed.filter(b => b.isStripe);

    if (solids.length && !stripes.length) {
      this.players[this.currentPlayer].group = 'solid';
      this.players[this.otherPlayer()].group = 'stripe';
    } else if (stripes.length && !solids.length) {
      this.players[this.currentPlayer].group = 'stripe';
      this.players[this.otherPlayer()].group = 'solid';
    }
  }

  resolveNormalShot() {
    const shooter = this.currentPlayer;
    const cuePocketed = this.pocketedThisShot.some(b => b.id === 0);
    const eightPocketed = this.pocketedThisShot.some(b => b.id === 8);
    const objectPocketed = this.pocketedThisShot.filter(b => b.id !== 0 && b.id !== 8);

    if (cuePocketed) {
      if (eightPocketed) {
        this.endGame(this.otherPlayer(), 'Восьмёрка с битком — поражение!');
        return;
      }
      this.handleFoul('Биток в лузу');
      return;
    }

    if (!this.firstHitBall) {
      this.handleFoul('Не попали ни в один шар');
      return;
    }

    if (!this.tableOpen && this.players[shooter].group) {
      const legalFirst = this.isLegalFirstHit(this.firstHitBall, shooter);
      if (!legalFirst) {
        this.handleFoul('Первый контакт с чужим шаром');
        return;
      }
    }

    if (!this.players[shooter].group && objectPocketed.length) {
      this.assignGroupsFromPocket(objectPocketed);
      this.tableOpen = false;
    }

    if (eightPocketed) {
      const group = this.players[shooter].group;
      if (group && this.isGroupCleared(group)) {
        this.endGame(shooter, `${this.players[shooter].name} победил!`);
      } else {
        this.endGame(this.otherPlayer(), 'Восьмёрка забита рано — поражение!');
      }
      return;
    }

    let pocketedWrong = false;
    for (const ball of objectPocketed) {
      const g = getBallGroup(ball);
      const pg = this.players[shooter].group;
      if (pg && g && g !== pg) pocketedWrong = true;
    }

    if (pocketedWrong) {
      this.handleFoul('Забит чужой шар');
      return;
    }

    const pocketedOwn = objectPocketed.some(b => getBallGroup(b) === this.players[shooter].group);

    if (pocketedOwn) {
      this.continueTurn(this.getTurnMessage(true));
    } else {
      this.switchTurn();
      this.state = GameState.AIMING;
      this.message = `${this.players[this.currentPlayer].name} — ход`;
      this.notify();
    }
  }

  isLegalFirstHit(ball, shooter) {
    if (!ball || ball.id === 0) return false;
    const group = this.players[shooter].group;
    if (!group) return !ball.isEight;
    if (this.isGroupCleared(group)) return ball.isEight;
    return getBallGroup(ball) === group;
  }

  handleFoul(reason) {
    this.foul = true;
    this.foulReason = reason;
    this.switchTurn();
    const cue = this.getCueBall();
    if (cue) {
      cue.reset(this.table.bounds.cueX, this.table.bounds.cueY);
    }
    this.ballInHandPlayer = this.currentPlayer;
    this.state = GameState.BALL_IN_HAND;
    const p = this.players[this.currentPlayer];
    this.message = `Фол: ${reason}. ${p.name} — свободный биток.`;
    this.notify();
  }

  continueTurn(msg) {
    this.state = GameState.AIMING;
    this.message = msg;
    this.notify();
  }

  getTurnMessage(continued) {
    const p = this.players[this.currentPlayer];
    if (!p.group) return continued ? 'Хороший удар! Ещё раз.' : `${p.name} — ход`;
    const g = p.group === 'solid' ? 'цельные' : 'полосатые';
    return continued ? `Отлично! Забивайте ${g}.` : `${p.name} — ваши ${g}`;
  }

  switchTurn() {
    this.currentPlayer = this.otherPlayer();
  }

  otherPlayer() {
    return this.currentPlayer === 1 ? 2 : 1;
  }

  isGroupCleared(group) {
    if (!group) return false;
    return !this.balls.some(b => b.active && !b.pocketed && getBallGroup(b) === group);
  }

  endGame(winnerId, msg) {
    this.winner = winnerId;
    this.state = GameState.GAME_OVER;
    this.message = msg;
    this.notify();
  }

  notify() {
    if (this.onUpdate) this.onUpdate(this);
  }

  getGroupLabel() {
    const g = this.players[1].group;
    if (!g) return '—';
    return g === 'solid' ? 'Цельные (1–7)' : 'Полосатые (9–15)';
  }

  getOpponentGroupLabel() {
    const g = this.players[2].group;
    if (!g) return '—';
    return g === 'solid' ? 'Цельные' : 'Полосатые';
  }
}
