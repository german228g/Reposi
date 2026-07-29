"use client";

import { useThree } from "@react-three/fiber";
import { useEffect } from "react";

interface FrameThrottleProps {
  fps?: number;
  active?: boolean;
}

/**
 * Drives a capped-fps render loop for a `frameloop="demand"` canvas so the
 * continuous rotation/parallax animation stays visually smooth while never
 * saturating the main thread with an uncapped 60fps WebGL loop — this keeps
 * lab performance metrics (e.g. Lighthouse TBT) low without hurting the
 * perceived motion of a slow, ambient rotation.
 */
export function FrameThrottle({ fps = 30, active = true }: FrameThrottleProps) {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    if (!active) return;

    let frameId: number;
    let last = 0;
    const interval = 1000 / fps;

    function loop(time: number) {
      if (time - last >= interval) {
        last = time;
        invalidate();
      }
      frameId = requestAnimationFrame(loop);
    }

    function handleVisibility() {
      if (document.hidden) {
        cancelAnimationFrame(frameId);
      } else {
        frameId = requestAnimationFrame(loop);
      }
    }

    frameId = requestAnimationFrame(loop);
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      cancelAnimationFrame(frameId);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [fps, active, invalidate]);

  return null;
}
