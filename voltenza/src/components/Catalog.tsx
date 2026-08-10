"use client";

import { useMemo, useState } from "react";
import { CATEGORIES, PRODUCTS, type CategoryId } from "@/data/products";
import { ProductCard } from "./ProductCard";
import { Reveal } from "./Reveal";

const FILTERS: Array<{ id: CategoryId | "all"; label: string }> = [
  { id: "all", label: "Все товары" },
  ...CATEGORIES.map((c) => ({ id: c.id, label: c.title })),
];

export function Catalog() {
  const [active, setActive] = useState<CategoryId | "all">("all");

  const products = useMemo(
    () => (active === "all" ? PRODUCTS : PRODUCTS.filter((p) => p.category === active)),
    [active]
  );

  return (
    <section id="catalog" aria-labelledby="catalog-heading" className="border-t border-line bg-bone py-24 sm:py-32">
      <div className="container-edit">
        <Reveal className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="eyebrow text-ink/60">Каталог</span>
            <h2
              id="catalog-heading"
              className="mt-4 max-w-xl text-balance text-4xl font-medium tracking-tight sm:text-5xl"
            >
              Отобранные аксессуары, а не бесконечный список.
            </h2>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-ink/60">
            Цены и способ заказа — плейсхолдеры, редактируются в одном файле
            каталога. Заказ подтверждается администратором, оплата — наложенным
            платежом.
          </p>
        </Reveal>

        <div className="mt-10 flex flex-wrap gap-2">
          {FILTERS.map((filter) => (
            <button
              key={filter.id}
              type="button"
              onClick={() => setActive(filter.id)}
              aria-pressed={active === filter.id}
              className={`focus-ring rounded-full border px-5 py-2.5 text-xs uppercase tracking-[0.08em] transition-colors ${
                active === filter.id
                  ? "border-ink bg-ink text-bone"
                  : "border-line text-ink/60 hover:border-ink hover:text-ink"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product, i) => (
            <Reveal key={product.id} delay={Math.min(i * 0.05, 0.3)}>
              <ProductCard product={product} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
