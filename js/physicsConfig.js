/**
 * Физика v5 — скорости подобраны так, чтобы биток
 * пересекал стол (~1600px) за доли секунды.
 */
export const PHYSICS = {
  version: '5.1',

  /** px/сек при powerLevel=1. Полный стол ≈ 0.35 сек */
  maxSpeed(table) {
    return table.width * 2.8;
  },

  minSpeed(table) {
    return table.width * 0.18;
  },

  powerReach(table) {
    return table.width * 0.28;
  },

  /** Трение сукна (1/сек). rollDistance ≈ v0 / frictionK */
  frictionK: 2.1,

  restitution: 0.97,
  cushionRestitution: 0.92,
  stopSpeed: 12,
  substeps: 8,
};

export function applyFriction(vel, dt) {
  const speed = vel.length();
  if (speed < PHYSICS.stopSpeed) {
    vel.set(0, 0);
    return;
  }
  vel.scale(Math.exp(-PHYSICS.frictionK * dt));
}

export function rollDistance(initialSpeed) {
  return initialSpeed / PHYSICS.frictionK;
}
