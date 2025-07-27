export function GridMap() {
  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm mb-6">
      <h2 className="text-xl font-semibold mb-4">Grid Map</h2>
      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: 25 }, (_, i) => (
          <div
            key={i}
            className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs text-muted-foreground border transition hover:scale-105 hover:border-foreground"
          >
            ⬜
          </div>
        ))}
      </div>
    </div>
  );
}
