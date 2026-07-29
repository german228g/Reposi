"use client";

/**
 * Lightweight, WebGL-free stand-in for the 3D hero model on mobile: a
 * pure CSS/SVG rendition of the magnetic disc with a slow, GPU-composited
 * transform rotation. Costs virtually nothing on the main thread, matching
 * the brief's requirement to keep mobile animation lightweight and never
 * trade load speed for decorative effects.
 */
export function HeroSceneLite() {
  return (
    <div className="relative flex h-full w-full items-center justify-center">
      <div
        className="hero-lite-spin relative aspect-square w-[78%] max-w-[280px]"
        aria-hidden="true"
      >
        <svg viewBox="0 0 200 200" className="h-full w-full drop-shadow-xl">
          <circle cx="100" cy="100" r="92" fill="#0a0a0a" />
          <circle
            cx="100"
            cy="100"
            r="70"
            fill="none"
            stroke="#f3f1ec"
            strokeWidth="12"
          />
          <circle cx="100" cy="100" r="46" fill="#2f2f2f" />
          <circle cx="100" cy="100" r="9" fill="#f3f1ec" />
        </svg>
      </div>
      <div className="absolute bottom-2 left-1/2 h-6 w-28 -translate-x-1/2 rounded-full bg-ink/10 blur-md" />
      <p className="sr-only">
        Магнитный держатель VOLTENZA — упрощённая анимация для мобильных
        устройств
      </p>
    </div>
  );
}
