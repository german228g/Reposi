"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

interface LazyMountProps {
  children: ReactNode;
  className?: string;
  /** Distance before entering the viewport at which mounting occurs. */
  rootMargin?: string;
  fallback?: ReactNode;
}

/**
 * Defers mounting expensive children (e.g. a WebGL canvas) until the
 * container is about to enter the viewport, so off-screen sections never
 * pay their render/GPU cost on initial page load.
 */
export function LazyMount({
  children,
  className,
  rootMargin = "600px 0px",
  fallback = null,
}: LazyMountProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || visible) return;

    if (typeof IntersectionObserver === "undefined") {
      // No IntersectionObserver support: fail open and show content immediately.
      const id = window.setTimeout(() => setVisible(true), 0);
      return () => window.clearTimeout(id);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin, visible]);

  return (
    <div ref={ref} className={className}>
      {visible ? children : fallback}
    </div>
  );
}
