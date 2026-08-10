"use client";

import { Canvas } from "@react-three/fiber";
import { Suspense, type MutableRefObject } from "react";
import { MagneticHolder } from "./MagneticHolder";
import { FrameThrottle } from "./FrameThrottle";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useIsMobile } from "@/hooks/useIsMobile";

interface StorySceneProps {
  explodeRef: MutableRefObject<number>;
}

export function StoryScene({ explodeRef }: StorySceneProps) {
  const reducedMotion = useReducedMotion();
  const isMobile = useIsMobile();

  return (
    <Canvas
      frameloop="demand"
      shadows={false}
      dpr={isMobile ? 0.85 : [1, 1.25]}
      camera={{ position: [0.8, 0.6, 4.6], fov: 30 }}
      gl={{ antialias: false, alpha: false, powerPreference: "low-power" }}
      onCreated={({ gl }) => gl.setClearColor("#0a0a0a", 1)}
    >
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 4, 3]} intensity={1.5} />
      <directionalLight position={[-3, -1, -2]} intensity={0.4} />
      <directionalLight position={[0, -3, 2]} intensity={0.3} />
      <FrameThrottle fps={reducedMotion ? 1 : isMobile ? 12 : 18} />
      <Suspense fallback={null}>
        <MagneticHolder
          explodeRef={explodeRef}
          autoRotateSpeed={reducedMotion ? 0.02 : 0.1}
          interactive={!reducedMotion}
          scale={1.5}
        />
      </Suspense>
    </Canvas>
  );
}
