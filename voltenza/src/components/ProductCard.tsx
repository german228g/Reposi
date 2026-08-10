"use client";

import { useState } from "react";
import type { Product } from "@/data/products";
import { ProductImage } from "./ProductImage";
import { useOrderModal } from "@/context/OrderModalContext";

const BADGE_STYLES: Record<Product["badge"], string> = {
  "НОВИНКА": "bg-ink text-bone",
  "В НАЛИЧИИ": "bg-bone text-ink border border-ink/25",
  "ХИТ": "bg-ink text-bone",
  "ПОД ЗАКАЗ": "bg-bone text-ink/60 border border-ink/20",
};

export function ProductCard({ product }: { product: Product }) {
  const { openOrder } = useOrderModal();
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <article className="group flex h-full flex-col border border-line bg-paper transition-transform duration-300 hover:-translate-y-1">
      <div className="relative aspect-square overflow-hidden border-b border-line">
        <div className="h-full w-full transition-transform duration-500 group-hover:scale-[1.04]">
          <ProductImage
            image={product.image}
            name={product.name}
            category={product.category}
            className="h-full w-full"
          />
        </div>
        <span
          className={`absolute left-3 top-3 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-[0.1em] ${BADGE_STYLES[product.badge]}`}
        >
          {product.badge}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-6">
        <h3 className="text-lg font-medium tracking-tight">{product.name}</h3>
        <p className="line-clamp-3 text-sm leading-relaxed text-ink/60">
          {product.description}
        </p>

        <div className="mt-auto flex items-center justify-between pt-4">
          <span className="text-lg font-medium">{product.price}</span>
          <span
            className={`text-xs uppercase tracking-[0.06em] ${
              product.inStock ? "text-ink/60" : "text-ink/60"
            }`}
          >
            {product.inStock ? "В наличии" : "Под заказ"}
          </span>
        </div>

        <div className="mt-2 flex items-center gap-3">
          <button
            type="button"
            onClick={() => openOrder(product.name)}
            className="focus-ring flex-1 rounded-full bg-ink px-5 py-3 text-xs font-medium uppercase tracking-[0.08em] text-bone transition-opacity hover:opacity-85"
          >
            Заказать
          </button>
          <button
            type="button"
            onClick={() => setDetailsOpen((v) => !v)}
            aria-expanded={detailsOpen}
            className="focus-ring rounded-full border border-line px-5 py-3 text-xs font-medium uppercase tracking-[0.08em] text-ink/70 transition-colors hover:border-ink hover:text-ink"
          >
            Подробнее
          </button>
        </div>

        {detailsOpen && (
          <dl className="mt-4 grid grid-cols-1 gap-2 border-t border-line pt-4 text-xs">
            {product.specs.map((spec) => (
              <div key={spec.label} className="flex justify-between gap-3">
                <dt className="text-ink/60">{spec.label}</dt>
                <dd className="text-right text-ink/75">{spec.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </article>
  );
}
