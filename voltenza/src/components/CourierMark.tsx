interface CourierMarkProps {
  id: "speedy" | "econt";
  active?: boolean;
  className?: string;
}

/**
 * Minimal monochrome monogram badges standing in for the Speedy / Econt
 * wordmarks. Replace with the couriers' official logo assets if licensed
 * for use — kept as simple typographic marks to avoid using third-party
 * brand artwork without permission.
 */
export function CourierMark({ id, active = false, className = "" }: CourierMarkProps) {
  const color = active ? "#f3f1ec" : "#0a0a0a";
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      aria-hidden="true"
      className={className}
    >
      <rect
        x="0.5"
        y="0.5"
        width="17"
        height="17"
        rx="4"
        stroke={color}
        strokeWidth="1"
        fill="none"
      />
      <text
        x="9"
        y="12.5"
        textAnchor="middle"
        fontSize="9"
        fontWeight="700"
        fill={color}
        fontFamily="var(--font-inter-tight), sans-serif"
      >
        {id === "speedy" ? "S" : "E"}
      </text>
    </svg>
  );
}
