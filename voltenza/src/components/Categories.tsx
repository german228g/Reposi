"use client";

import { useRef, type MouseEvent } from "react";
import { motion } from "framer-motion";
import { CATEGORIES } from "@/data/products";
import { Reveal } from "./Reveal";

function CategoryCard({
  index,
  title,
  subtitle,
  description,
}: {
  index: number;
  title: string;
  subtitle: string;
  description: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function handleMouseMove(event: MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    el.style.setProperty("--px", `${px * 100}%`);
    el.style.setProperty("--py", `${py * 100}%`);
    el.style.setProperty("--rx", `${(py - 0.5) * -6}deg`);
    el.style.setProperty("--ry", `${(px - 0.5) * 6}deg`);
  }

  function handleMouseLeave() {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--rx", "0deg");
    el.style.setProperty("--ry", "0deg");
  }

  return (
    <Reveal delay={index * 0.06} className="h-full">
      <div
        ref={ref}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          transform:
            "perspective(900px) rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg))",
          transition: "transform 0.3s ease-out",
        }}
        className="group relative flex h-full min-h-[280px] flex-col justify-between overflow-hidden border border-line bg-paper p-8 will-change-transform"
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{
            background:
              "radial-gradient(280px circle at var(--px, 50%) var(--py, 50%), rgba(10,10,10,0.06), transparent 70%)",
          }}
        />
        <div className="relative">
          <span className="eyebrow text-ink/60">0{index + 1}</span>
          <h3 className="mt-6 text-3xl font-medium tracking-tight sm:text-4xl">
            {title}
          </h3>
          <p className="mt-2 text-sm uppercase tracking-[0.08em] text-ink/60">
            {subtitle}
          </p>
        </div>
        <p className="relative mt-8 max-w-sm text-sm leading-relaxed text-ink/65">
          {description}
        </p>
      </div>
    </Reveal>
  );
}

export function Categories() {
  return (
    <section id="about" aria-labelledby="categories-heading" className="border-t border-line bg-bone py-24 sm:py-32">
      <div className="container-edit">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <Reveal>
            <span className="eyebrow text-ink/60">Категории</span>
            <h2
              id="categories-heading"
              className="mt-4 max-w-xl text-balance text-4xl font-medium tracking-tight sm:text-5xl"
            >
              Четыре направления, одна философия притяжения.
            </h2>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="max-w-sm text-sm leading-relaxed text-ink/60">
              Каждая категория VOLTENZA решает одну задачу без компромиссов —
              от магнитной энергии до дорожных мелочей.
            </p>
          </Reveal>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden bg-line sm:grid-cols-2 lg:grid-cols-4">
          {CATEGORIES.map((category, index) => (
            <motion.div key={category.id} className="bg-bone">
              <CategoryCard
                index={index}
                title={category.title}
                subtitle={category.subtitle}
                description={category.description}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
