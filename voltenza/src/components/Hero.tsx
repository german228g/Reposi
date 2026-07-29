"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { MagneticButton } from "./MagneticButton";
import { DeferredMount } from "./DeferredMount";
import { HeroSceneLite } from "./HeroSceneLite";
import { useIsMobile } from "@/hooks/useIsMobile";

const HeroScene = dynamic(
  () => import("./three/HeroScene").then((mod) => mod.HeroScene),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center">
        <div className="h-56 w-56 animate-pulse rounded-full border border-ink/15 sm:h-72 sm:w-72" />
      </div>
    ),
  }
);

export function Hero() {
  const isMobile = useIsMobile();

  return (
    <section
      id="hero"
      aria-label="VOLTENZA — Энергия. Притяжение. Движение."
      className="relative flex min-h-[100svh] w-full flex-col justify-between overflow-hidden bg-bone"
    >
      <div className="container-edit relative z-10 flex flex-1 flex-col justify-center pt-28 pb-10 sm:pt-32">
        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-7">
            {/* Critical above-the-fold text renders at full opacity immediately
                (no entrance animation) so it never delays Largest Contentful
                Paint — only non-LCP elements below get a light rise-in. */}
            <p className="eyebrow mb-6 text-ink/60">
              VOLTENZA — Mobile Accessories
            </p>

            <h1 className="text-balance font-display text-[13vw] font-medium leading-[0.95] tracking-tight text-ink sm:text-[8vw] lg:text-[5.4vw]">
              <span className="block">Энергия.</span>
              <span className="block">Притяжение.</span>
              <span className="block text-ink/60">Движение.</span>
            </h1>

            <p className="mt-8 max-w-md text-balance text-base leading-relaxed text-ink/65 sm:text-lg">
              Тщательно отобранные аксессуары для энергии, крепления и
              повседневного использования смартфона — магнитная физика,
              промышленная точность, минимум лишнего.
            </p>

            <div
              className="hero-rise mt-10 flex flex-wrap items-center gap-4"
              style={{ animationDelay: "0.15s" }}
            >
              <MagneticButton
                className="focus-ring group relative overflow-hidden rounded-full bg-ink px-8 py-4 text-sm font-medium uppercase tracking-[0.08em] text-bone transition-colors"
                onClick={() => {
                  document
                    .getElementById("catalog")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                Смотреть каталог
              </MagneticButton>
              <MagneticButton
                className="focus-ring rounded-full border border-ink/25 px-8 py-4 text-sm font-medium uppercase tracking-[0.08em] text-ink transition-colors hover:border-ink"
                onClick={() => {
                  document
                    .getElementById("how-to-order")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                Как заказать
              </MagneticButton>
            </div>
          </div>

          <div className="relative lg:col-span-5">
            <div className="relative mx-auto aspect-square w-full max-w-[420px]">
              {isMobile ? (
                <HeroSceneLite />
              ) : (
                <DeferredMount
                  fallback={
                    <div className="flex h-full w-full items-center justify-center">
                      <div className="h-56 w-56 animate-pulse rounded-full border border-ink/15 sm:h-72 sm:w-72" />
                    </div>
                  }
                >
                  <HeroScene />
                </DeferredMount>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container-edit relative z-10 flex items-center justify-between border-t border-line py-5 text-xs uppercase tracking-[0.14em] text-ink/60">
        <span>Varna, Bulgaria</span>
        <span className="hidden sm:inline">Magnetic Power / Mobile Mounts / Everyday Carry</span>
        <span aria-hidden className="inline-flex items-center gap-1">
          <span className="hidden sm:inline">Scroll</span>
          <motion.span
            animate={{ y: [0, 6, 0] }}
            transition={{ repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
          >
            ↓
          </motion.span>
        </span>
      </div>
    </section>
  );
}
