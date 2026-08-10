"use client";

import { KITS } from "@/data/products";
import { Reveal } from "./Reveal";
import { ProductImage } from "./ProductImage";
import { useOrderModal } from "@/context/OrderModalContext";

export function Kits() {
  const { openOrder } = useOrderModal();

  return (
    <section id="kits" aria-labelledby="kits-heading" className="border-t border-line bg-paper py-24 sm:py-32">
      <div className="container-edit">
        <Reveal>
          <span className="eyebrow text-ink/60">Наборы</span>
          <h2 id="kits-heading" className="mt-4 max-w-xl text-balance text-4xl font-medium tracking-tight sm:text-5xl">
            Собранные комплекты под сценарий использования.
          </h2>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {KITS.map((kit, i) => (
            <Reveal key={kit.id} delay={i * 0.08}>
              <article className="flex h-full flex-col border border-line bg-bone">
                <div className="aspect-[4/3] border-b border-line">
                  <ProductImage
                    image={kit.image}
                    name={kit.title}
                    category="mobile-mounts"
                    className="h-full w-full"
                  />
                </div>
                <div className="flex flex-1 flex-col gap-4 p-7">
                  <div>
                    <span className="eyebrow text-ink/60">{kit.tagline}</span>
                    <h3 className="mt-2 text-2xl font-medium tracking-tight">{kit.title}</h3>
                  </div>
                  <p className="text-sm leading-relaxed text-ink/60">{kit.description}</p>
                  <ul className="flex flex-col gap-1.5 border-t border-line pt-4 text-sm text-ink/70">
                    {kit.items.map((item) => (
                      <li key={item} className="flex items-center gap-2">
                        <span className="h-1 w-1 rounded-full bg-ink/50" aria-hidden />
                        {item}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-auto flex items-center justify-between pt-4">
                    <span className="text-lg font-medium">{kit.price}</span>
                    <button
                      type="button"
                      onClick={() => openOrder(kit.title)}
                      className="focus-ring rounded-full bg-ink px-6 py-3 text-xs font-medium uppercase tracking-[0.08em] text-bone transition-opacity hover:opacity-85"
                    >
                      Заказать набор
                    </button>
                  </div>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
