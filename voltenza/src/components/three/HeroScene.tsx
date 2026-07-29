"use client";

import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import { MagneticHolder } from "./MagneticHolder";
import { FrameThrottle } from "./FrameThrottle";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useIsMobile } from "@/hooks/useIsMobile";

/**
 * Hero canvas: a single continuously-rotating, cursor-reactive model.
 * Rendering effort is scaled down on mobile (lower DPR, no shadows) and
 * rotation freezes entirely under prefers-reduced-motion.
 */
export function HeroScene() {
  const reducedMotion = useReducedMotion();
  const isMobile = useIsMobile();

  return (
    <Canvas
      frameloop="demand"
      shadows={false}
      dpr={isMobile ? 0.85 : [1, 1.25]}
      camera={{ position: [0.6, 0.5, 4.4], fov: 32 }}
      gl={{ antialias: false, alpha: false, powerPreference: "low-power" }}
      onCreated={({ gl }) => gl.setClearColor("#f3f1ec", 1)}
      className="!touch-none"
    >
      <ambientLight intensity={0.65} />
      <directionalLight position={[3, 4, 3]} intensity={1.4} />
      <directionalLight position={[-3, -1, -2]} intensity={0.35} />
      <directionalLight position={[0, -3, 2]} intensity={0.25} />
      <FrameThrottle fps={reducedMotion ? 1 : isMobile ? 12 : 18} />
      <Suspense fallback={null}>
        <MagneticHolder
          autoRotateSpeed={reducedMotion ? 0 : isMobile ? 0.12 : 0.18}
          interactive={!reducedMotion}
          scale={1.35}
        />
      </Suspense>
    </Canvas>
  );
}
