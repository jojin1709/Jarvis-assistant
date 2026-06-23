export function SkeletonCard({ lines = 3, className = "" }) {
  return (
    <div className={`animate-pulse rounded-2xl border border-line p-4 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className={`mt-2 h-3 rounded bg-white/5 ${index === 0 ? "w-3/4" : index % 2 === 0 ? "w-1/2" : "w-full"}`} />
      ))}
    </div>
  );
}
