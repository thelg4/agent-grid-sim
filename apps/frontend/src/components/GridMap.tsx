export function GridMap() {
  // Placeholder grid
  return (
    <div className="border rounded-md p-4 bg-background mb-4">
      <h2 className="font-semibold text-lg mb-2">Grid Map</h2>
      <div className="grid grid-cols-5 gap-1">
        {Array.from({ length: 25 }, (_, i) => (
          <div
            key={i}
            className="w-8 h-8 bg-muted rounded-sm flex items-center justify-center text-xs"
          >
            ⬜
          </div>
        ))}
      </div>
    </div>
  );
}
