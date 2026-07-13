export class Vec2 {
  constructor(x = 0, y = 0) {
    this.x = x;
    this.y = y;
  }

  clone() {
    return new Vec2(this.x, this.y);
  }

  set(x, y) {
    this.x = x;
    this.y = y;
    return this;
  }

  add(v) {
    this.x += v.x;
    this.y += v.y;
    return this;
  }

  sub(v) {
    this.x -= v.x;
    this.y -= v.y;
    return this;
  }

  scale(s) {
    this.x *= s;
    this.y *= s;
    return this;
  }

  length() {
    return Math.hypot(this.x, this.y);
  }

  normalize() {
    const len = this.length();
    if (len > 0) {
      this.x /= len;
      this.y /= len;
    }
    return this;
  }

  dot(v) {
    return this.x * v.x + this.y * v.y;
  }

  static sub(a, b) {
    return new Vec2(a.x - b.x, a.y - b.y);
  }

  static add(a, b) {
    return new Vec2(a.x + b.x, a.y + b.y);
  }

  static scale(v, s) {
    return new Vec2(v.x * s, v.y * s);
  }

  static dist(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
}

export function resolveBallCollision(a, b, restitution = 0.95) {
  const delta = Vec2.sub(b.pos, a.pos);
  const dist = delta.length();
  const minDist = a.radius + b.radius;

  if (dist === 0 || dist >= minDist) return false;

  const normal = delta.clone().normalize();
  const overlap = minDist - dist;

  const totalMass = a.mass + b.mass;
  a.pos.sub(Vec2.scale(normal, overlap * (b.mass / totalMass)));
  b.pos.add(Vec2.scale(normal, overlap * (a.mass / totalMass)));

  const relVel = Vec2.sub(b.vel, a.vel);
  const velAlongNormal = relVel.dot(normal);

  if (velAlongNormal > 0) return true;

  const impulse = (-(1 + restitution) * velAlongNormal) / (1 / a.mass + 1 / b.mass);
  const impulseVec = Vec2.scale(normal, impulse);

  a.vel.sub(Vec2.scale(impulseVec, 1 / a.mass));
  b.vel.add(Vec2.scale(impulseVec, 1 / b.mass));

  return true;
}

export function reflectOffCushion(pos, vel, normal, restitution = 0.85) {
  const dot = vel.dot(normal);
  vel.x -= 2 * dot * normal.x;
  vel.y -= 2 * dot * normal.y;
  vel.scale(restitution);
}

export function applyFriction(vel, friction, dt) {
  const speed = vel.length();
  if (speed < 0.25) {
    vel.set(0, 0);
    return;
  }
  const drop = friction * dt;
  if (speed <= drop) {
    vel.set(0, 0);
  } else {
    vel.scale((speed - drop) / speed);
  }
}

export function isMoving(balls, threshold = 0.2) {
  return balls.some(b => b.active && !b.pocketed && !b.pocketAnim && b.vel.length() > threshold);
}

/** Примерная дальность проката при линейном трении */
export function rollDistance(initialSpeed, friction) {
  return (initialSpeed * initialSpeed) / (2 * friction);
}
