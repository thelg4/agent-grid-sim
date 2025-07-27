import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";

interface AgentCardProps {
  agentId: string;
  agentData?: {
    id: string;
    role: string;
    status: string;
    memory: string[];
    position?: [number, number];
    mission_role?: string;
    // Additional fields for specific agent types
    cells_visited?: number;
    exploration_percentage?: number;
    buildings_completed?: number;
    scout_reports_received?: number;
    build_orders_issued?: number;
  };
}

const colorMap: Record<string, string> = {
  scout: "bg-blue-500",
  builder: "bg-yellow-500",
  strategist: "bg-green-500",
};

const iconMap: Record<string, string> = {
  scout: "👀",
  builder: "🔨", 
  strategist: "🧠",
};

export function AgentCard({ agentId, agentData }: AgentCardProps) {
  const color = colorMap[agentId] ?? "bg-gray-400";
  const icon = iconMap[agentId] ?? "🤖";

  // Function to format memory entries for better display
  const formatMemoryEntry = (entry: string) => {
    // Truncate very long entries
    if (entry.length > 60) {
      return entry.substring(0, 57) + "...";
    }
    return entry;
  };

  // Get status indicator based on agent activity
  const getStatusColor = (status: string) => {
    if (status.includes("Moved") || status.includes("Built") || status.includes("Suggested")) {
      return "bg-green-100 text-green-800";
    } else if (status.includes("failed") || status.includes("Failed")) {
      return "bg-red-100 text-red-800";
    } else if (status.includes("Awaiting") || status.includes("Idle")) {
      return "bg-gray-100 text-gray-800";
    }
    return "bg-blue-100 text-blue-800";
  };

  return (
    <Card className="mb-4">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="capitalize flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          {agentId} Agent
          <span className={`w-2 h-2 rounded-full ${color}`} />
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-3 pt-0">
        <div>
          <strong>Role:</strong> {agentData?.mission_role || agentData?.role || agentId}
        </div>
        
        <div>
          <strong>Status:</strong>
          <span className={`ml-2 px-2 py-1 rounded text-xs ${getStatusColor(agentData?.status || "Idle")}`}>
            {agentData?.status || "Idle"}
          </span>
        </div>
        
        {agentData?.position && (
          <div>
            <strong>Position:</strong> ({agentData.position[0]}, {agentData.position[1]})
          </div>
        )}

        {/* Agent-specific metrics */}
        {agentId === "scout" && agentData?.cells_visited && (
          <div className="text-xs text-muted-foreground">
            <strong>Exploration:</strong> {agentData.cells_visited} cells visited 
            {agentData.exploration_percentage && (
              <span> ({agentData.exploration_percentage.toFixed(1)}%)</span>
            )}
          </div>
        )}

        {agentId === "builder" && agentData?.buildings_completed !== undefined && (
          <div className="text-xs text-muted-foreground">
            <strong>Completed:</strong> {agentData.buildings_completed} buildings
          </div>
        )}

        {agentId === "strategist" && agentData?.scout_reports_received && (
          <div className="text-xs text-muted-foreground">
            <strong>Intel:</strong> {agentData.scout_reports_received} scout reports, {agentData.build_orders_issued || 0} orders issued
          </div>
        )}
        
        <div>
          <strong>Recent Activity:</strong>
          {agentData?.memory && agentData.memory.length > 0 ? (
            <div className="mt-1 space-y-1 max-h-24 overflow-y-auto">
              {agentData.memory.slice(-3).map((mem, idx) => (
                <div key={idx} className="text-xs bg-muted p-2 rounded text-muted-foreground">
                  {formatMemoryEntry(mem)}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-xs mt-1 italic">No recent activity</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}