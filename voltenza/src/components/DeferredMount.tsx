"use client";

import { useEffect, useState, type ReactNode } from "react";

interface DeferredMountProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Mounts expensive children (the WebGL canvas) only after the browser has
 * already completed loading and painted at least one frame. Waiting for
 * `load` + a double requestAnimationFrame guarantees critical content (the
 * hero copy — our Largest Contentful Paint candidate) is fully composited
 * before any heavy Three.js work ever touches the main thread.
 */
export function DeferredMount({ children, fallback = null }: DeferredMountProps) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let raf1 = 0;
    let raf2 = 0;
    let timer = 0;

    function schedule() {
      // A short fixed delay on top of the load event keeps the heavy
      // WebGL bundle from ever competing with the critical text paint,
      // even on a page that finishes loading almost instantly.
      timer = window.setTimeout(() => {
        raf1 = requestAnimationFrame(() => {
          raf2 = requestAnimationFrame(() => setReady(true));
        });
      }, 400);
    }

    if (document.readyState === "complete") {
      schedule();
    } else {
      window.addEventListener("load", schedule, { once: true });
    }

    return () => {
      window.removeEventListener("load", schedule);
      window.clearTimeout(timer);
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, []);

  return <>{ready ? children : fallback}</>;
}
