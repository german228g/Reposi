"use client";

import {
  motion,
  useMotionValue,
  useSpring,
  type HTMLMotionProps,
} from "framer-motion";
import { useRef, type ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface MagneticButtonProps extends HTMLMotionProps<"button"> {
  children: ReactNode;
  strength?: number;
  className?: string;
}

/**
 * Buttons that subtly attract toward the cursor within their bounds,
 * evoking the brand's magnetic-attraction concept. Disabled entirely
 * when the user prefers reduced motion.
 */
export function MagneticButton({
  children,
  strength = 0.35,
  className = "",
  ...props
}: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);
  const reducedMotion = useReducedMotion();

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 200, damping: 15, mass: 0.4 });
  const springY = useSpring(y, { stiffness: 200, damping: 15, mass: 0.4 });

  function handleMouseMove(event: React.MouseEvent<HTMLButtonElement>) {
    if (reducedMotion || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const relX = event.clientX - (rect.left + rect.width / 2);
    const relY = event.clientY - (rect.top + rect.height / 2);
    x.set(relX * strength);
    y.set(relY * strength);
  }

  function handleMouseLeave() {
    x.set(0);
    y.set(0);
  }

  return (
    <motion.button
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={reducedMotion ? undefined : { x: springX, y: springY }}
      className={className}
      {...props}
    >
      {children}
    </motion.button>
  );
}
