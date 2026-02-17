/**
 * Skeleton shimmer effect for loading states.
 * Usage: <Skeleton width="100%" height={20} />
 *        <Skeleton variant="circle" width={40} height={40} />
 *        <Skeleton variant="card" />
 */
export default function Skeleton({ width = "100%", height = 16, variant = "text", count = 1, style = {} }) {
  const baseStyle = {
    background: "var(--bg-input, #e0e0e0)",
    borderRadius: variant === "circle" ? "50%" : variant === "card" ? 12 : 4,
    width: variant === "card" ? "100%" : width,
    height: variant === "card" ? 120 : height,
    animation: "skeleton-shimmer 1.5s ease-in-out infinite",
    ...style,
  };

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ ...baseStyle, marginBottom: count > 1 ? 8 : 0 }} aria-hidden="true" />
      ))}
      <style>{`
        @keyframes skeleton-shimmer {
          0% { opacity: 0.6; }
          50% { opacity: 0.3; }
          100% { opacity: 0.6; }
        }
      `}</style>
    </>
  );
}

/** Pre-built skeleton layouts */
export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }} role="status" aria-label="Cargando datos">
      <div style={{ display: "flex", gap: 16 }}>
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} height={14} width={`${100 / cols}%`} style={{ opacity: 0.5 }} />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} style={{ display: "flex", gap: 16 }}>
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} height={18} width={`${100 / cols}%`} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonCards({ count = 4 }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16 }} role="status" aria-label="Cargando tarjetas">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ background: "var(--bg-card, #fff)", borderRadius: 12, padding: 20, border: "1px solid var(--border-color, #e0e0e0)" }}>
          <Skeleton height={18} width="60%" style={{ marginBottom: 12 }} />
          <Skeleton height={12} count={3} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonKPI({ count = 4 }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }} role="status" aria-label="Cargando métricas">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ background: "var(--bg-card, #fff)", borderRadius: 12, padding: 20, textAlign: "center", border: "1px solid var(--border-color, #e0e0e0)" }}>
          <Skeleton height={32} width="50%" style={{ margin: "0 auto 8px" }} />
          <Skeleton height={12} width="70%" style={{ margin: "0 auto" }} />
        </div>
      ))}
    </div>
  );
}
