"use client";

import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

const INK = "#0a0a0a";
const BONE = "#f3f1ec";
const METAL = "#333333";
const METAL_LIGHT = "#4a4a4a";

interface MagneticHolderProps {
  /** Mutable ref (0 → assembled, 1 → fully exploded) updated externally per-frame. */
  explodeRef?: React.MutableRefObject<number>;
  autoRotateSpeed?: number;
  interactive?: boolean;
  scale?: number;
}

/**
 * Stylised, procedurally-built magnetic vent-mount holder (disc + ball
 * joint + clip fins) rendered with primitive geometry only — no external
 * model assets to download, keeping the hero fast and dependency-free.
 */
export function MagneticHolder({
  explodeRef,
  autoRotateSpeed = 0.18,
  interactive = true,
  scale = 1,
}: MagneticHolderProps) {
  const group = useRef<THREE.Group>(null);
  const plate = useRef<THREE.Group>(null);
  const clipBase = useRef<THREE.Group>(null);
  const fins = useRef<Array<THREE.Group | null>>([]);
  const finCount = 5;

  useFrame((state, delta) => {
    const g = group.current;
    if (!g) return;

    g.rotation.y += delta * (autoRotateSpeed + (explodeRef?.current ?? 0) * 0.25);

    if (interactive) {
      const targetX = state.pointer.y * 0.22;
      const targetZ = -state.pointer.x * 0.22;
      g.rotation.x = THREE.MathUtils.damp(g.rotation.x, targetX, 4, delta);
      g.rotation.z = THREE.MathUtils.damp(g.rotation.z, targetZ, 4, delta);
    }

    const explode = explodeRef?.current ?? 0;

    if (plate.current) {
      plate.current.position.y = THREE.MathUtils.damp(
        plate.current.position.y,
        0.65 * explode,
        6,
        delta
      );
      plate.current.rotation.z = THREE.MathUtils.damp(
        plate.current.rotation.z,
        explode * 0.35,
        6,
        delta
      );
    }

    if (clipBase.current) {
      clipBase.current.position.y = THREE.MathUtils.damp(
        clipBase.current.position.y,
        -0.62 - 0.55 * explode,
        6,
        delta
      );
    }

    fins.current.forEach((fin, i) => {
      if (!fin) return;
      const angle = (i / finCount) * Math.PI * 2;
      const dist = 0.85 * explode;
      const targetX = Math.cos(angle) * dist;
      const targetZ = Math.sin(angle) * dist;
      const targetY = -0.95 - 0.35 * explode;
      fin.position.x = THREE.MathUtils.damp(fin.position.x, targetX, 6, delta);
      fin.position.z = THREE.MathUtils.damp(fin.position.z, targetZ, 6, delta);
      fin.position.y = THREE.MathUtils.damp(fin.position.y, targetY, 6, delta);
      fin.rotation.y = THREE.MathUtils.damp(
        fin.rotation.y,
        angle + explode * 1.4,
        6,
        delta
      );
    });
  });

  return (
    <group ref={group} scale={scale} dispose={null}>
      {/* Magnetic disc */}
      <group ref={plate} position={[0, 0, 0]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[1.05, 1.05, 0.16, 32]} />
          <meshStandardMaterial color={INK} metalness={0.75} roughness={0.28} />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.081, 0]}>
          <ringGeometry args={[0.68, 0.86, 32]} />
          <meshStandardMaterial
            color={BONE}
            metalness={0.15}
            roughness={0.55}
            side={THREE.DoubleSide}
          />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.09, 0]}>
          <circleGeometry args={[0.5, 28]} />
          <meshStandardMaterial color={METAL} metalness={0.85} roughness={0.22} />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.095, 0]}>
          <circleGeometry args={[0.09, 16]} />
          <meshStandardMaterial color={BONE} metalness={0.1} roughness={0.6} />
        </mesh>
      </group>

      {/* Ball joint + neck */}
      <group position={[0, -0.34, 0]}>
        <mesh>
          <sphereGeometry args={[0.24, 16, 16]} />
          <meshStandardMaterial color={METAL_LIGHT} metalness={0.8} roughness={0.25} />
        </mesh>
        <mesh position={[0, -0.24, 0]}>
          <cylinderGeometry args={[0.09, 0.15, 0.3, 16]} />
          <meshStandardMaterial color={INK} metalness={0.65} roughness={0.35} />
        </mesh>
      </group>

      {/* Vent-clip base */}
      <group ref={clipBase} position={[0, -0.62, 0]}>
        <mesh>
          <cylinderGeometry args={[0.17, 0.22, 0.16, 20]} />
          <meshStandardMaterial color={INK} metalness={0.6} roughness={0.4} />
        </mesh>
      </group>

      {/* Clip fins that separate on scroll */}
      {Array.from({ length: finCount }).map((_, i) => (
        <group
          key={i}
          ref={(el) => {
            fins.current[i] = el;
          }}
          position={[0, -0.95, 0]}
          rotation={[0, (i / finCount) * Math.PI * 2, 0]}
        >
          <mesh position={[0.3, 0, 0]}>
            <boxGeometry args={[0.52, 0.055, 0.17]} />
            <meshStandardMaterial color={METAL_LIGHT} metalness={0.7} roughness={0.32} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
