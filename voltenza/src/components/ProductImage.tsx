"use client";

import { useState } from "react";
import type { CategoryId } from "@/data/products";

interface ProductImageProps {
  image: string;
  name: string;
  category: CategoryId;
  className?: string;
}

/**
 * Editorial placeholder artwork used until the owner drops a real product
 * photo at the referenced `image` path (see /public/products/README).
 * Rendered as inline SVG: zero network requests, instant paint, and it
 * keeps the monochrome art direction consistent across the whole catalog.
 */
function CategoryGlyph({ category }: { category: CategoryId }) {
  switch (category) {
    case "magnetic-power":
      return (
        <g stroke="#0a0a0a" strokeWidth="1.2" fill="none">
          <circle cx="60" cy="60" r="34" />
          <circle cx="60" cy="60" r="22" />
          <circle cx="60" cy="60" r="3.5" fill="#0a0a0a" />
        </g>
      );
    case "mobile-mounts":
      return (
        <g stroke="#0a0a0a" strokeWidth="1.2" fill="none">
          <rect x="42" y="30" width="36" height="56" rx="8" />
          <circle cx="60" cy="20" r="7" />
          <line x1="60" y1="27" x2="60" y2="30" />
        </g>
      );
    case "everyday-carry":
      return (
        <g stroke="#0a0a0a" strokeWidth="1.2" fill="none">
          <path d="M30 45 C30 30, 90 30, 90 45 S30 75, 30 90 S90 105, 90 90" />
        </g>
      );
    case "travel-essentials":
    default:
      return (
        <g stroke="#0a0a0a" strokeWidth="1.2" fill="none">
          <rect x="34" y="38" width="52" height="44" rx="10" />
          <path d="M46 38 V30 a8 8 0 0 1 8 -8 h12 a8 8 0 0 1 8 8 v8" />
        </g>
      );
  }
}

export function ProductImage({ image, name, category, className = "" }: ProductImageProps) {
  const [loadFailed, setLoadFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  return (
    <div
      className={`relative overflow-hidden bg-bone ${className}`}
      role="img"
      aria-label={`Фото товара: ${name}`}
    >
      {/* Illustrated placeholder is always in the DOM as the base layer, so
          a missing photo never flashes the browser's broken-image icon —
          the real photo (once the owner adds one) simply fades in above it. */}
      <svg
        viewBox="0 0 120 120"
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <rect x="0" y="0" width="120" height="120" fill="#f3f1ec" />
        <g opacity="0.35">
          <line x1="0" y1="60" x2="120" y2="60" stroke="#0a0a0a" strokeWidth="0.4" />
          <line x1="60" y1="0" x2="60" y2="120" stroke="#0a0a0a" strokeWidth="0.4" />
        </g>
        <CategoryGlyph category={category} />
      </svg>

      {loadFailed && (
        <span className="pointer-events-none absolute bottom-2 left-2 right-2 truncate text-[9px] uppercase tracking-[0.14em] text-ink/60">
          {image}
        </span>
      )}

      {!loadFailed && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={image}
          alt={name}
          loading="lazy"
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => setLoadFailed(true)}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
}
