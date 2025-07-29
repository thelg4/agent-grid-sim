// apps/frontend/src/components/AgentCard.tsx
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
    last_activity?: string;
    coordination_status?: string;
    mission_phase?: string;
    
    // Enhanced memory and performance data
    memory_summary?: Record<string, string[]>;
    performance_metrics?: Record<string, number>;
    current_plan?: Array<{action: string; priority: number}>;
    learning_summary?: {
      successful_strategies_count: number;
      failed_strategies_count: number;
    };
    
    // Scout specific fields
    cells_visited?: number;
    exploration_percentage?: number;
    exploration_target?: number;
    visited_cells_list?: number[][];
    
    // Builder specific fields
    buildings_completed?: number;
    last_built_location?: [number, number];
    processed_messages_count?: number;
    current_target?: [number, number];
    movement_steps_remaining?: number;
    construction_target?: number;
    
    // Strategist specific fields
    scout_reports_received?: number;
    build_orders_issued?: number;
    analysis_cycles?: number;
    building_target?: number;
    buildings_completed_strategist?: number;
    strategic_plan_ready?: boolean;
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

const roleDescriptions: Record<string, string> = {
  scout: "Explorer & Intelligence Gatherer",
  builder: "Construction & Infrastructure",
  strategist: "Tactical Coordinator & Planner",
};

export function AgentCard({ agentId, agentData }: AgentCardProps) {
  const color = colorMap[agentId] ?? "bg-gray-400";
  const icon = iconMap[agentId] ?? "🤖";
  const roleDescription = roleDescriptions[agentId] ?? agentData?.mission_role ?? agentData?.role ?? agentId;

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

  // Get status indicator based on agent activity and status
  const getStatusColor = (status: string, activity?: string) => {
    // Check activity first for more specific coloring
    if (activity) {
      switch (activity) {
        case 'exploration':
          return "bg-yellow-100 text-yellow-800 border-yellow-200";
        case 'analysis':
          return "bg-purple-100 text-purple-800 border-purple-200";
        case 'construction':
          return "bg-green-100 text-green-800 border-green-200";
        case 'coordination':
          return "bg-blue-100 text-blue-800 border-blue-200";
        case 'emergency':
          return "bg-red-100 text-red-800 border-red-200";
        case 'parallel_execution':
          return "bg-indigo-100 text-indigo-800 border-indigo-200";
        case 'optimization':
          return "bg-orange-100 text-orange-800 border-orange-200";
        case 'completed':
          return "bg-emerald-100 text-emerald-800 border-emerald-200";
      }
    }
    
    // Fallback to status-based coloring
    if (status?.includes("Moved") || status?.includes("Built") || status?.includes("SUCCESS") || status?.includes("COMPLETE")) {
      return "bg-green-100 text-green-800 border-green-200";
    } else if (status?.includes("failed") || status?.includes("Failed") || status?.includes("ERROR")) {
      return "bg-red-100 text-red-800 border-red-200";
    } else if (status?.includes("Moving") || status?.includes("progress")) {
      return "bg-blue-100 text-blue-800 border-blue-200";
    } else if (status?.includes("Awaiting") || status?.includes("Idle") || status?.includes("standing by")) {
      return "bg-gray-100 text-gray-800 border-gray-200";
    } else if (status?.includes("Initializing") || status?.includes("Ready")) {
      return "bg-blue-100 text-blue-800 border-blue-200";
    }
    return "bg-blue-100 text-blue-800 border-blue-200";
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

  // Get enhanced memory summary if available
  const getMemorySummary = () => {
    if (agentData?.memory_summary) {
      return Object.entries(agentData.memory_summary).map(([type, entries]) => ({
        type,
        entries: entries.slice(-2) // Latest 2 entries per type
      }));
    }
    return null;
  };

  // Get performance metrics display
  const getPerformanceDisplay = () => {
    if (!agentData?.performance_metrics) return null;
    
    const metrics = agentData.performance_metrics;
    return {
      actions: metrics.actions_taken || 0,
      success_rate: metrics.successful_actions && metrics.actions_taken 
        ? ((metrics.successful_actions / metrics.actions_taken) * 100).toFixed(1)
        : "0",
      messages: metrics.messages_sent || 0,
      avg_response_time: metrics.average_response_time 
        ? (metrics.average_response_time * 1000).toFixed(0) + "ms"
        : "N/A"
    };
  };

  const statusColorClass = getStatusColor(agentData?.status || "Idle", agentData?.last_activity);
  const memorySummary = getMemorySummary();
  const performanceDisplay = getPerformanceDisplay();

  return (
    <Card className="mb-4 hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="capitalize flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <div className="flex flex-col">
            <span>{agentId} Agent</span>
            <span className="text-xs font-normal text-muted-foreground">
              {roleDescription}
            </span>
          </div>
          <span className={`w-2 h-2 rounded-full ${color}`} />
        </CardTitle>
        
        {/* Mission Phase Indicator */}
        {agentData?.mission_phase && (
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded border">
            {agentData.mission_phase}
          </span>
        )}
      </CardHeader>
      
      <CardContent className="text-sm space-y-3 pt-0">
        <div>
          <strong>Status:</strong>
          <span className={`ml-2 px-2 py-1 rounded text-xs border ${statusColorClass}`}>
            {agentData?.status || "Idle"}
          </span>
          {agentData?.last_activity && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({agentData.last_activity})
            </span>
          )}
        </div>
        
        {agentData?.position && (
          <div>
            <strong>Position:</strong> ({agentData.position[0]}, {agentData.position[1]})
            {agentData?.coordination_status && (
              <span className="ml-2 text-xs text-blue-600">
                {agentData.coordination_status}
              </span>
            )}
          </div>
        )}
        