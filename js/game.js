import { Vec2, resolveBallCollision, applyFriction, isMoving } from './physics.js';
import { createRack, getBallGroup } from './balls.js';

export const GameState = {
  AIMING: 'aiming',
  SHOOTING: 'shooting',
  BALL_IN_HAND: 'ball_in_hand',
  GAME_OVER: 'game_over',
};

export class Game {
  constructor(table) {
    this.table = table;
    this.balls = [];
    this.state = GameState.AIMING;
    this.playerGroup = null;
    this.opponentGroup = null;
    this.currentPlayer = 1;
    this.message = 'Потяните кий назад и отпустите';
    this.winner = null;
    this.firstShot = true;
    this.shotInProgress = false;
    this.pocketedThisShot = [];
    this.hitBallThisShot = false;
    this.cushionHitThisShot = false;
    this.foul = false;
    this.foulReason = '';
    this.ballInHandPos = null;
    this.friction = 2.8;
    this.onUpdate = null;
  }

  reset() {
    this.balls = createRack(this.table.bounds, this.table.ballRadius);
    this.state = GameState.AIMING;
    this.playerGroup = null;
    this.opponentGroup = null;
    this.currentPlayer = 1;
    this.message = 'Разбейте пирамиду! Попадите в любой шар.';
    this.winner = null;
    this.firstShot = true;
    this.shotInProgress = false;
    this.pocketedThisShot = [];
    this.hitBallThisShot = false;
    this.cushionHitThisShot = false;
    this.foul = false;
    this.foulReason = '';
    this.ballInHandPos = null;
    this.notify();
  }

  getCueBall() {
    return this.balls.find(b => b.id === 0);
  }

  getActiveBalls() {
    return this.balls.filter(b => b.active && !b.pocketed);
  }

  canShoot() {
    return this.state === GameState.AIMING && !isMoving(this.balls);
  }

  canPlaceCueBall() {
    return this.state === GameState.BALL_IN_HAND;
  }

  shoot(vx, vy) {
    if (!this.canShoot()) return false;

    const cue = this.getCueBall();
    if (!cue) return false;

    cue.vel.set(vx, vy);
    this.state = GameState.SHOOTING;
    this.shotInProgress = true;
    this.pocketedThisShot = [];
    this.hitBallThisShot = false;
    this.cushionHitThisShot = false;
    this.foul = false;
    this.foulReason = '';
    this.message = '';
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
      if (Vec2.dist({ x, y }, ball.pos) < r * 2.2) {
        this.message = 'Слишком близко к другому шару';
        this.notify();
        return false;
      }
    }

    cue.reset(x, y);
    this.ballInHandPos = null;
    this.state = GameState.AIMING;
    this.message = 'Ваш удар';
    this.notify();
    return true;
  }

  update(dt) {
    if (this.state === GameState.GAME_OVER) return;

    const activeBalls = this.getActiveBalls();
    let anyMoving = false;

    for (const ball of activeBalls) {
      ball.pos.add(Vec2.scale(ball.vel, dt));
      applyFriction(ball.vel, this.friction, dt);

      if (ball.vel.length() > 0.05) anyMoving = true;

      if (this.table.constrainBall(ball)) {
        this.cushionHitThisShot = true;
      }

      const pocket = this.table.checkPocket(ball);
      if (pocket) {
        this.onBallPocketed(ball);
      }
    }

    for (let i = 0; i < activeBalls.length; i++) {
      for (let j = i + 1; j < activeBalls.length; j++) {
        if (resolveBallCollision(activeBalls[i], activeBalls[j])) {
          if (activeBalls[i].id === 0 || activeBalls[j].id === 0) {
            this.hitBallThisShot = true;
          }
        }
      }
    }

    if (this.shotInProgress && !anyMoving && !isMoving(this.balls)) {
      this.endShot();
    }
  }

  onBallPocketed(ball) {
    ball.pocket();
    this.pocketedThisShot.push(ball);

    if (ball.id === 0) {
      this.foul = true;
      this.foulReason = 'Биток в лузу';
    }
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

    if (!this.hitBallThisShot) {
      this.handleFoul('Не попали ни в один шар');
      return;
    }

    if (objectBalls.length === 0) {
      this.message = 'Разбой засчитан. Ещё один удар.';
      this.state = GameState.AIMING;
      this.notify();
      return;
    }

    this.assignGroups(objectBalls);
    this.state = GameState.AIMING;
    this.notify();
  }

  assignGroups(pocketed) {
    const hasSolid = pocketed.some(b => b.isSolid);
    const hasStripe = pocketed.some(b => b.isStripe);

    if (hasSolid && !hasStripe) {
      this.playerGroup = 'solid';
      this.opponentGroup = 'stripe';
      this.message = 'Ваши шары: цельные (1–7). Забейте восьмёрку в конце.';
    } else if (hasStripe && !hasSolid) {
      this.playerGroup = 'stripe';
      this.opponentGroup = 'solid';
      this.message = 'Ваши шары: полосатые (9–15). Забейте восьмёрку в конце.';
    } else {
      this.playerGroup = null;
      this.message = 'Забито обе группы — выберите свою первым забитым шаром.';
    }
  }

  resolveNormalShot() {
    const cuePocketed = this.pocketedThisShot.some(b => b.id === 0);
    const eightPocketed = this.pocketedThisShot.some(b => b.id === 8);
    const objectPocketed = this.pocketedThisShot.filter(b => b.id !== 0 && b.id !== 8);

    if (cuePocketed) {
      this.handleFoul('Биток в лузу');
      if (eightPocketed) {
        this.endGame(false, 'Восьмёрка забита вместе с битком — вы проиграли');
      }
      return;
    }

    if (!this.hitBallThisShot) {
      this.handleFoul('Не попали ни в один шар');
      return;
    }

    if (this.playerGroup === null && objectPocketed.length > 0) {
      const first = objectPocketed[0];
      const group = getBallGroup(first);
      if (group === 'solid') {
        this.playerGroup = 'solid';
        this.opponentGroup = 'stripe';
        this.message = 'Ваши шары: цельные (1–7)';
      } else if (group === 'stripe') {
        this.playerGroup = 'stripe';
        this.opponentGroup = 'solid';
        this.message = 'Ваши шары: полосатые (9–15)';
      }
    }

    if (eightPocketed) {
      const myGroupCleared = this.isGroupCleared(this.playerGroup);
      if (myGroupCleared) {
        this.endGame(true, 'Восьмёрка забита — вы победили!');
      } else {
        this.endGame(false, 'Восьмёрка забита рано — вы проиграли');
      }
      return;
    }

    let pocketedWrong = false;
    for (const ball of objectPocketed) {
      const group = getBallGroup(ball);
      if (this.playerGroup && group && group !== this.playerGroup) {
        pocketedWrong = true;
      }
    }

    if (this.foul || pocketedWrong) {
      const reason = pocketedWrong ? 'Забит чужой шар' : this.foulReason;
      this.handleFoul(reason);
      return;
    }

    const pocketedOwn = objectPocketed.some(b => getBallGroup(b) === this.playerGroup);

    if (pocketedOwn) {
      this.message = 'Отличный удар! Ещё раз.';
    } else {
      this.switchPlayer();
      this.message = 'Переход хода';
    }

    this.state = GameState.AIMING;
    this.notify();
  }

  isGroupCleared(group) {
    if (!group) return false;
    return !this.balls.some(b => {
      if (!b.active || b.pocketed) return false;
      return getBallGroup(b) === group;
    });
  }

  handleFoul(reason) {
    this.foul = true;
    this.foulReason = reason;
    this.switchPlayer();
    this.respotCueBall();
    this.message = `Фол: ${reason}. Свободный биток у соперника.`;
    this.state = GameState.BALL_IN_HAND;
    this.notify();
  }

  respotCueBall() {
    const cue = this.getCueBall();
    cue.reset(this.table.bounds.cueX, this.table.bounds.cueY);
    this.ballInHandPos = cue.pos.clone();
  }

  switchPlayer() {
    this.currentPlayer = this.currentPlayer === 1 ? 2 : 1;
    const temp = this.playerGroup;
    this.playerGroup = this.opponentGroup;
    this.opponentGroup = temp;
  }

  endGame(won, msg) {
    this.winner = won ? 1 : 2;
    this.state = GameState.GAME_OVER;
    this.message = msg;
    this.notify();
  }

  notify() {
    if (this.onUpdate) this.onUpdate(this);
  }

  getGroupLabel() {
    if (!this.playerGroup) return '—';
    return this.playerGroup === 'solid' ? 'Цельные (1–7)' : 'Полосатые (9–15)';
  }
}
