"use client";

import { useSyncExternalStore } from "react";

/**
 * Simple viewport-width based mobile detector used to scale back decorative
 * animation and 3D effort on smaller / touch-first devices.
 */
export function useIsMobile(breakpoint = 768): boolean {
  const query = `(max-width: ${breakpoint}px)`;

  return useSyncExternalStore(
    (callback) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", callback);
      return () => mql.removeEventListener("change", callback);
    },
    () => window.matchMedia(query).matches,
    () => false
  );
}
