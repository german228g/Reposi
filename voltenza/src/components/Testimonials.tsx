"use client";

import { TESTIMONIALS } from "@/data/products";
import { Reveal } from "./Reveal";

export function Testimonials() {
  const track = [...TESTIMONIALS, ...TESTIMONIALS];

  return (
    <section
      id="testimonials"
      aria-labelledby="testimonials-heading"
      className="border-t border-line bg-paper py-24 sm:py-32"
    >
      <div className="container-edit">
        <Reveal className="max-w-xl">
          <span className="eyebrow text-ink/60">Отзывы</span>
          <h2
            id="testimonials-heading"
            className="mt-4 text-balance text-4xl font-medium tracking-tight sm:text-5xl"
          >
            Здесь появятся голоса первых клиентов VOLTENZA.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-ink/60">
            Раздел подготовлен под реальные отзывы — сейчас показаны только
            плейсхолдеры, без вымышленных цитат.
          </p>
        </Reveal>
      </div>

      <div className="relative mt-14 overflow-hidden">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-paper to-transparent sm:w-32" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-paper to-transparent sm:w-32" />
        <div className="marquee-track flex w-max gap-6 py-2">
          {track.map((item, i) => (
            <figure
              key={`${item.id}-${i}`}
              className="flex w-[300px] shrink-0 flex-col justify-between gap-6 border border-line bg-bone p-7 sm:w-[360px]"
            >
              <blockquote className="text-balance text-lg font-medium leading-snug tracking-tight text-ink/80">
                &ldquo;{item.quote}&rdquo;
              </blockquote>
              <figcaption className="text-xs uppercase tracking-[0.08em] text-ink/60">
                {item.meta}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
