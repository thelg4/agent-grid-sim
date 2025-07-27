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
    // Scout specific fields
    cells_visited?: number;
    exploration_percentage?: number;
    visited_cells_list?: number[][];
    // Builder specific fields
    buildings_completed?: number;
    last_built_location?: [number, number];
    processed_messages_count?: number;
    current_target?: [number, number];
    movement_steps_remaining?: number;
    // Strategist specific fields
    scout_reports_received?: number;
    build_orders_issued?: number;
    analysis_cycles?: number;
    building_target?: number;
    buildings_completed?: number;
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
    // Remove redundant agent ID from memory entries
    const cleaned = entry.replace(`Agent ${agentId}`, '').trim();
    // Truncate very long entries
    if (cleaned.length > 60) {
      return cleaned.substring(0, 57) + "...";
    }
    return cleaned || entry; // fallback to original if cleaning resulted in empty string
  };

  // Get status indicator based on agent activity
  const getStatusColor = (status: string) => {
    if (status.includes("Moved") || status.includes("Built") || status.includes("SUCCESS") || status.includes("COMPLETE")) {
      return "bg-green-100 text-green-800";
    } else if (status.includes("failed") || status.includes("Failed") || status.includes("ERROR")) {
      return "bg-red-100 text-red-800";
    } else if (status.includes("Moving") || status.includes("progress")) {
      return "bg-blue-100 text-blue-800";
    } else if (status.includes("Awaiting") || status.includes("Idle") || status.includes("standing by")) {
      return "bg-gray-100 text-gray-800";
    } else if (status.includes("Initializing") || status.includes("Ready")) {
      return "bg-blue-100 text-blue-800";
    }
    return "bg-blue-100 text-blue-800";
  };

  // Get recent meaningful activity from memory
  const getRecentActivity = () => {
    if (!agentData?.memory || agentData.memory.length === 0) {
      return "No recent activity";
    }
    
    // Get the most recent meaningful activities (skip generic status updates)
    const meaningfulActivities = agentData.memory
      .filter(mem => 
        !mem.includes("initialized successfully") && 
        !mem.includes("LLM decision") &&
        mem.trim().length > 0
      )
      .slice(-3); // Get last 3 meaningful activities
    
    return meaningfulActivities.length > 0 ? meaningfulActivities : agentData.memory.slice(-2);
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
        {agentId === "scout" && (
          <div className="text-xs text-muted-foreground bg-blue-50 p-2 rounded">
            <div><strong>Exploration:</strong> {agentData?.cells_visited || 0} cells visited</div>
            {agentData?.exploration_percentage !== undefined && (
              <div><strong>Progress:</strong> {agentData.exploration_percentage.toFixed(1)}% explored</div>
            )}
            {agentData?.visited_cells_list && agentData.visited_cells_list.length > 0 && (
              <div><strong>Recent:</strong> {agentData.visited_cells_list.slice(-3).map(pos => `(${pos[0]},${pos[1]})`).join(', ')}</div>
            )}
          </div>
        )}

        {agentId === "builder" && (
          <div className="text-xs text-muted-foreground bg-yellow-50 p-2 rounded">
            <div><strong>Buildings:</strong> {agentData?.buildings_completed || 0} completed</div>
            {agentData?.last_built_location && (
              <div><strong>Last Built:</strong> ({agentData.last_built_location[0]}, {agentData.last_built_location[1]})</div>
            )}
            {agentData?.current_target && (
              <div><strong>Target:</strong> ({agentData.current_target[0]}, {agentData.current_target[1]})</div>
            )}
            {agentData?.movement_steps_remaining !== undefined && agentData.movement_steps_remaining > 0 && (
              <div><strong>Movement:</strong> {agentData.movement_steps_remaining} steps remaining</div>
            )}
            {agentData?.processed_messages_count !== undefined && (
              <div><strong>Orders Processed:</strong> {agentData.processed_messages_count}</div>
            )}
          </div>
        )}

        {agentId === "strategist" && (
          <div className="text-xs text-muted-foreground bg-green-50 p-2 rounded">
            <div><strong>Intel:</strong> {agentData?.scout_reports_received || 0} scout reports</div>
            <div><strong>Orders:</strong> {agentData?.build_orders_issued || 0} issued</div>
            {agentData?.analysis_cycles !== undefined && (
              <div><strong>Analysis Cycles:</strong> {agentData.analysis_cycles}</div>
            )}
            {agentData?.building_target && (
              <div><strong>Target:</strong> {agentData?.buildings_completed || 0}/{agentData.building_target} buildings</div>
            )}
          </div>
        )}
        
        <div>
          <strong>Recent Activity:</strong>
          <div className="mt-1 space-y-1 max-h-24 overflow-y-auto">
            {(() => {
              const activities = getRecentActivity();
              if (typeof activities === 'string') {
                return <div className="text-xs bg-muted p-2 rounded text-muted-foreground italic">{activities}</div>;
              }
              return activities.map((mem: string, idx: number) => (
                <div key={idx} className="text-xs bg-muted p-2 rounded text-muted-foreground">
                  {formatMemoryEntry(mem)}
                </div>
              ));
            })()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}