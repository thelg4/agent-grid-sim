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

  // Count structures for debug info
  const structureCount = Object.values(grid.cells).filter((cell: any) => 
    cell.structure === "building"
  ).length;

  const agentCount = Object.values(grid.cells).filter((cell: any) => 
    cell.occupied_by
  ).length;

  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Grid Map</h2>
        <div className="text-sm text-muted-foreground">
          {grid.width}×{grid.height} | {structureCount} buildings | {agentCount} agents
        </div>
      </div>
      
      {/* Grid coordinate labels */}
      <div className="mb-2">
        <div className="flex gap-2 ml-8">
          {Array.from({ length: grid.width }, (_, i) => (
            <div key={i} className="w-10 text-center text-xs text-muted-foreground font-mono">
              {i}
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex">
        {/* Y-axis labels */}
        <div className="flex flex-col gap-2 mr-2 pt-1">
          {Array.from({ length: grid.height }, (_, i) => (
            <div key={i} className="h-10 flex items-center justify-center text-xs text-muted-foreground font-mono w-6">
              {i}
            </div>
          ))}
        </div>
        
        {/* Grid */}
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
                className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs text-muted-foreground border transition hover:scale-105 hover:border-foreground relative group"
                title={`(${x}, ${y}) - ${renderCellDescription(cell)}`}
              >
                {renderCell(cell)}
                
                {/* Tooltip on hover */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                  ({x}, {y}) - {renderCellDescription(cell)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <span>👀</span> Scout
        </div>
        <div className="flex items-center gap-1">
          <span>🔨</span> Builder
        </div>
        <div className="flex items-center gap-1">
          <span>🧠</span> Strategist
        </div>
        <div className="flex items-center gap-1">
          <span>🏠</span> Building
        </div>
        <div className="flex items-center gap-1">
          <span>⬜</span> Empty
        </div>
      </div>
    </div>
  );
}

function renderCell(cell: any) {
  if (cell?.occupied_by) {
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

  if (cell?.structure === "building") {
    return "🏠";
  }

  return "⬜";
}

function renderCellDescription(cell: any): string {
  if (cell?.occupied_by && cell?.structure) {
    return `${cell.occupied_by} + ${cell.structure}`;
  } else if (cell?.occupied_by) {
    return cell.occupied_by;
  } else if (cell?.structure) {
    return cell.structure;
  } else {
    return "empty";
  }
}