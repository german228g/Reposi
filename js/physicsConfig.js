/** Физика под размер стола (1600×880) */
export const PHYSICS = {
  version: '4.0',

  /** Скорость удара: v = powerLevel * maxSpeed */
  maxSpeed(table) {
    return table.width * 0.28;
  },

  minSpeed(table) {
    return table.width * 0.02;
  },

  /** Расстояние пальца от битка → полная сила */
  powerReach(table) {
    return table.width * 0.32;
  },

  /** Экспоненциальное трение сукна (1/сек) */
  frictionK: 0.55,

  restitution: 0.96,
  cushionRestitution: 0.9,
  stopSpeed: 4,
  substeps: 6,
};

export function applyFriction(vel, dt) {
  const speed = vel.length();
  if (speed < PHYSICS.stopSpeed) {
    vel.set(0, 0);
    return;
  }
  const factor = Math.exp(-PHYSICS.frictionK * dt);
  vel.scale(factor);
}

export function rollDistance(initialSpeed) {
  return initialSpeed / PHYSICS.frictionK;
}
