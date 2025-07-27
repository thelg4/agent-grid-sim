import { useSimulation } from "@/context/SimulationContext";

export function GridMap() {
  const { grid } = useSimulation();

  if (!grid) {
    return (
      <div className="rounded-xl border bg-background p-6 shadow-sm mb-6">
        <h2 className="text-xl font-semibold mb-4">Grid Map</h2>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm mb-6">
      <h2 className="text-xl font-semibold mb-4">Grid Map</h2>
      <div
        className={`grid gap-2`}
        style={{ gridTemplateColumns: `repeat(${grid.width}, 2.5rem)` }}
      >
        {Array.from({ length: grid.width * grid.height }, (_, i) => {
          const x = i % grid.width;
          const y = Math.floor(i / grid.width);
          const cellKey = `${x},${y}`;
          const cell = grid.cells[cellKey];

          return (
            <div
              key={cellKey}
              className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs text-muted-foreground border transition hover:scale-105 hover:border-foreground"
            >
              {renderCell(cell)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function renderCell(cell: any) {
  if (cell.occupied_by) {
    switch (cell.occupied_by) {
      case "builder":
        return "🔨";
      case "scout":
        return "👀";
      case "strategist":
        return "🧠";
      default:
        return "🤖";
    }
  }

  if (cell.structure === "building") {
    return "🏠";
  }

  return "⬜";
}
