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
  const recentActivity = getRecentActivity();

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

        {/* Agent-specific Information */}
        {agentId === "scout" && agentData && (
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <div className="font-medium text-blue-700 mb-2">Scout Metrics</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Cells Visited: <span className="font-mono">{agentData.cells_visited || 0}</span></div>
              <div>Exploration: <span className="font-mono">{agentData.exploration_percentage?.toFixed(1) || 0}%</span></div>
              <div>Target: <span className="font-mono">{agentData.exploration_target || 80}%</span></div>
              <div>Efficiency: <span className="font-mono">
                {agentData.exploration_percentage && agentData.exploration_target 
                  ? ((agentData.exploration_percentage / agentData.exploration_target) * 100).toFixed(0)
                  : 0}%
              </span></div>
            </div>
            {agentData.visited_cells_list && agentData.visited_cells_list.length > 0 && (
              <div className="mt-2 text-xs text-blue-600">
                Recent: {agentData.visited_cells_list.slice(-3).map(pos => `(${pos[0]},${pos[1]})`).join(", ")}
              </div>
            )}
          </div>
        )}

        {agentId === "builder" && agentData && (
          <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
            <div className="font-medium text-yellow-700 mb-2">Builder Metrics</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Buildings: <span className="font-mono">{agentData.buildings_completed || 0}</span></div>
              <div>Target: <span className="font-mono">{agentData.construction_target || 5}</span></div>
              <div>Messages: <span className="font-mono">{agentData.processed_messages_count || 0}</span></div>
              <div>Progress: <span className="font-mono">
                {agentData.buildings_completed && agentData.construction_target
                  ? ((agentData.buildings_completed / agentData.construction_target) * 100).toFixed(0)
                  : 0}%
              </span></div>
            </div>
            {agentData.current_target && (
              <div className="mt-2 text-xs text-yellow-600">
                Target: ({agentData.current_target[0]}, {agentData.current_target[1]})
                {agentData.movement_steps_remaining !== undefined && (
                  <span className="ml-2">({agentData.movement_steps_remaining} steps)</span>
                )}
              </div>
            )}
            {agentData.last_built_location && (
              <div className="mt-1 text-xs text-yellow-600">
                Last Built: ({agentData.last_built_location[0]}, {agentData.last_built_location[1]})
              </div>
            )}
          </div>
        )}

        {agentId === "strategist" && agentData && (
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <div className="font-medium text-green-700 mb-2">Strategist Metrics</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Build Orders: <span className="font-mono">{agentData.build_orders_issued || 0}</span></div>
              <div>Reports: <span className="font-mono">{agentData.scout_reports_received || 0}</span></div>
              <div>Analysis: <span className="font-mono">{agentData.analysis_cycles || 0}</span></div>
              <div>Buildings: <span className="font-mono">{agentData.buildings_completed_strategist || agentData.buildings_completed || 0}</span></div>
            </div>
            <div className="mt-2 text-xs">
              <span className={`px-2 py-1 rounded ${
                agentData.strategic_plan_ready 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                Plan: {agentData.strategic_plan_ready ? 'Ready' : 'Planning'}
              </span>
              {agentData.building_target && (
                <span className="ml-2 text-green-600">
                  Target: {agentData.building_target}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {performanceDisplay && (
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="font-medium text-slate-700 mb-2">Performance</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Actions: <span className="font-mono">{performanceDisplay.actions}</span></div>
              <div>Success Rate: <span className="font-mono">{performanceDisplay.success_rate}%</span></div>
              <div>Messages: <span className="font-mono">{performanceDisplay.messages}</span></div>
              <div>Avg Response: <span className="font-mono">{performanceDisplay.avg_response_time}</span></div>
            </div>
          </div>
        )}

        {/* Current Plan */}
        {agentData?.current_plan && agentData.current_plan.length > 0 && (
          <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200">
            <div className="font-medium text-indigo-700 mb-2">Current Plan</div>
            <div className="space-y-1">
              {agentData.current_plan.slice(0, 3).map((step, idx) => (
                <div key={idx} className="text-xs flex justify-between">
                  <span>{step.action}</span>
                  <span className="text-indigo-600 font-mono">P{step.priority}</span>
                </div>
              ))}
              {agentData.current_plan.length > 3 && (
                <div className="text-xs text-indigo-500">
                  +{agentData.current_plan.length - 3} more steps...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Enhanced Memory Display */}
        {memorySummary ? (
          <div>
            <strong>Enhanced Memory:</strong>
            <div className="mt-2 space-y-2">
              {memorySummary.map(({ type, entries }) => (
                <div key={type} className="bg-gray-50 p-2 rounded border">
                  <div className="text-xs font-medium text-gray-700 mb-1 capitalize">
                    {type.replace('_', ' ')}:
                  </div>
                  {entries.map((entry, idx) => (
                    <div key={idx} className="text-xs text-gray-600 truncate">
                      • {formatMemoryEntry(entry)}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        ) : (
          // Standard Memory Display
          <div>
            <strong>Recent Activity:</strong>
            <div className="mt-2 space-y-1">
              {Array.isArray(recentActivity) ? recentActivity.map((activity, idx) => (
                <div key={idx} className="text-xs text-muted-foreground bg-gray-50 p-2 rounded border">
                  {formatMemoryEntry(activity)}
                </div>
              )) : (
                <div className="text-xs text-muted-foreground italic">
                  {recentActivity}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Learning Summary */}
        {agentData?.learning_summary && (
          <div className="text-xs text-muted-foreground">
            <strong>Learning:</strong> {agentData.learning_summary.successful_strategies_count} successes, {agentData.learning_summary.failed_strategies_count} failures
          </div>
        )}
      </CardContent>
    </Card>
  );
}