// import { useSimulation } from "../context/SimulationContext";
// import { AgentCard } from "../components/AgentCard";
// import { GridMap } from "../components/GridMap";
// import { MessageLog } from "../components/MessageLog";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { useState } from "react";

// export function SimulationPage() {
//   const { agents, step, logs, loading, error, connectionStatus, grid } = useSimulation();
//   const [showDebug, setShowDebug] = useState(false);
//   const [debugData, setDebugData] = useState<any>(null);

//   const fetchDebugInfo = async () => {
//     try {
//       const response = await fetch("http://localhost:8000/api/debug");
//       const data = await response.json();
//       setDebugData(data);
//       setShowDebug(true);
//     } catch (err) {
//       console.error("Failed to fetch debug info:", err);
//     }
//   };

//   return (
//     <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 min-h-screen">
//       <div className="md:col-span-2 space-y-4">
//         {/* Connection Status Banner */}
//         {connectionStatus !== 'connected' && (
//           <Card className={`border-l-4 ${
//             connectionStatus === 'connecting' ? 'border-yellow-500 bg-yellow-50' : 'border-red-500 bg-red-50'
//           }`}>
//             <CardContent className="pt-4">
//               <div className="flex items-center space-x-2">
//                 <div className={`w-2 h-2 rounded-full ${
//                   connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
//                 }`} />
//                 <p className="text-sm font-medium">
//                   {connectionStatus === 'connecting' ? 'Connecting to backend...' : 'Backend disconnected'}
//                 </p>
//               </div>
//               {error && (
//                 <p className="text-xs text-muted-foreground mt-1">{error}</p>
//               )}
//               {connectionStatus === 'disconnected' && (
//                 <div className="mt-2 text-xs text-muted-foreground">
//                   <p>Make sure the backend is running:</p>
//                   <code className="bg-gray-200 px-2 py-1 rounded">
//                     cd apps/backend && uvicorn app.main:app --reload
//                   </code>
//                 </div>
//               )}
//             </CardContent>
//           </Card>
//         )}

//         <GridMap />
        
//         <MessageLog logs={logs} />
        
//         <div className="flex gap-4">
//           <Button 
//             onClick={step} 
//             disabled={loading || connectionStatus !== 'connected'}
//             className="flex-1"
//           >
//             {loading ? 'Processing...' : 'Step Simulation'}
//           </Button>
          
//           <Button 
//             variant="outline" 
//             onClick={() => window.location.reload()}
//             disabled={loading}
//           >
//             Refresh
//           </Button>

//           <Button 
//             variant="secondary" 
//             onClick={fetchDebugInfo}
//             disabled={loading || connectionStatus !== 'connected'}
//             size="sm"
//           >
//             Debug
//           </Button>
//         </div>

//         {/* Enhanced Debug Info */}
//         {showDebug && debugData && (
//           <Card className="bg-muted/50">
//             <CardHeader className="flex flex-row items-center justify-between">
//               <CardTitle className="text-sm">Debug Information</CardTitle>
//               <Button 
//                 variant="ghost" 
//                 size="sm" 
//                 onClick={() => setShowDebug(false)}
//               >
//                 ✕
//               </Button>
//             </CardHeader>
//             <CardContent className="text-xs space-y-3 max-h-96 overflow-y-auto">
              
//               {/* Simulation State */}
//               <div>
//                 <strong className="text-blue-600">Simulation State:</strong>
//                 <div className="bg-blue-50 p-2 rounded mt-1">
//                   <div>Step: {debugData.simulation?.step_count}</div>
//                   <div>Status: {debugData.simulation?.mission_status}</div>
//                   <div>Exploration: {debugData.simulation?.exploration_progress?.toFixed(1)}%</div>
//                   <div>Buildings: {debugData.simulation?.buildings_built}</div>
//                   <div>Visited Cells: {debugData.simulation?.visited_cells_count}</div>
//                 </div>
//               </div>

//               {/* Grid State */}
//               <div>
//                 <strong className="text-green-600">Grid State:</strong>
//                 <div className="bg-green-50 p-2 rounded mt-1">
//                   <div>Dimensions: {debugData.grid?.dimensions}</div>
//                   <div>Total Cells: {debugData.grid?.total_cells}</div>
//                   <div>Structures: {debugData.grid?.cells_with_structures?.length || 0}</div>
//                   <div>Agent Positions: {JSON.stringify(debugData.grid?.agent_positions)}</div>
//                 </div>
//               </div>

//               {/* Agent Details */}
//               <div>
//                 <strong className="text-purple-600">Agent Details:</strong>
//                 {debugData.agents && Object.entries(debugData.agents).map(([agentId, agentData]: [string, any]) => (
//                   <div key={agentId} className="bg-purple-50 p-2 rounded mt-1">
//                     <div className="font-semibold">{agentId}:</div>
//                     <div>Position: {JSON.stringify(agentData.position)}</div>
//                     <div>Memory Count: {agentData.memory_count}</div>
//                     <div>Status: {agentData.basic_status?.status}</div>
                    
//                     {/* Agent-specific debug info */}
//                     {agentId === 'scout' && (
//                       <div className="text-blue-600">
//                         <div>Cells Visited: {agentData.cells_visited}</div>
//                         <div>Recent Visits: {JSON.stringify(agentData.visited_cells_list?.slice(-3))}</div>
//                       </div>
//                     )}
                    
//                     {agentId === 'builder' && (
//                       <div className="text-yellow-600">
//                         <div>Buildings: {agentData.buildings_completed}</div>
//                         <div>Last Built: {JSON.stringify(agentData.last_built_location)}</div>
//                         <div>Messages Processed: {agentData.processed_messages}</div>
//                       </div>
//                     )}
                    
//                     {agentId === 'strategist' && (
//                       <div className="text-green-600">
//                         <div>Build Orders: {agentData.build_orders_issued}</div>
//                         <div>Scout Reports: {agentData.scout_reports}</div>
//                         <div>Suggested Locations: {JSON.stringify(agentData.suggested_locations)}</div>
//                       </div>
//                     )}
//                   </div>
//                 ))}
//               </div>

//               {/* Recent Logs */}
//               <div>
//                 <strong className="text-orange-600">Recent Backend Logs:</strong>
//                 <div className="bg-orange-50 p-2 rounded mt-1 font-mono">
//                   {debugData.simulation?.recent_logs?.map((log: string, idx: number) => (
//                     <div key={idx} className="text-xs">{log}</div>
//                   ))}
//                 </div>
//               </div>

//               {/* Raw JSON for Deep Debugging */}
//               <details className="text-xs">
//                 <summary className="cursor-pointer font-semibold">Raw Debug Data</summary>
//                 <pre className="bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
//                   {JSON.stringify(debugData, null, 2)}
//                 </pre>
//               </details>
//             </CardContent>
//           </Card>
//         )}

//         {/* Basic Debug Info (always visible in development) */}
//         {process.env.NODE_ENV === 'development' && (
//           <Card className="bg-muted/50">
//             <CardHeader>
//               <CardTitle className="text-sm">Quick Debug Info</CardTitle>
//             </CardHeader>
//             <CardContent className="text-xs space-y-1">
//               <p><strong>Connection:</strong> {connectionStatus}</p>
//               <p><strong>Agents Count:</strong> {Object.keys(agents).length}</p>
//               <p><strong>Logs Count:</strong> {logs.length}</p>
//               <p><strong>Grid Size:</strong> {grid ? `${grid.width}×${grid.height}` : 'Unknown'}</p>
//               <p><strong>Error:</strong> {error || 'None'}</p>
              
//               {/* Agent positions */}
//               {Object.keys(agents).length > 0 && (
//                 <div>
//                   <strong>Agent Positions:</strong>
//                   {Object.entries(agents).map(([id, data]: [string, any]) => (
//                     <div key={id} className="ml-2">
//                       {id}: {data.position ? `(${data.position[0]}, ${data.position[1]})` : 'Unknown'}
//                     </div>
//                   ))}
//                 </div>
//               )}
              
//               {/* Buildings count */}
//               {grid && (
//                 <p><strong>Buildings:</strong> {
//                   Object.values(grid.cells).filter((cell: any) => cell.structure === 'building').length
//                 }</p>
//               )}
//             </CardContent>
//           </Card>
//         )}
//       </div>
      
//       <div className="flex flex-col space-y-4">
//         <div className="text-sm text-muted-foreground mb-2">
//           <div className="flex items-center gap-2 mb-1">
//             <span className={`w-2 h-2 rounded-full ${
//               connectionStatus === 'connected' ? 'bg-green-500' : 
//               connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
//             }`} />
//             <span className="capitalize">{connectionStatus}</span>
//           </div>
//         </div>
        
//         {Object.keys(agents).length > 0 ? (
//           Object.entries(agents).map(([agentId, agentData]: [string, any]) => (
//             <AgentCard key={agentId} agentId={agentId} agentData={agentData} />
//           ))
//         ) : (
//           <Card>
//             <CardContent className="pt-6">
//               <p className="text-muted-foreground text-center">
//                 {loading ? 'Loading agents...' : 'No agents available'}
//               </p>
//             </CardContent>
//           </Card>
//         )}
//       </div>
//     </div>
//   );
// }

// apps/frontend/src/pages/SimulationPage.tsx

import { useSimulation } from "../context/SimulationContext";
import { AgentCard } from "../components/AgentCard";
import { GridMap } from "../components/GridMap";
import { MessageLog } from "../components/MessageLog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState, useEffect } from "react";

export function SimulationPage() {
  const { agents, step, logs, loading, error, connectionStatus, grid } = useSimulation();
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState<any>(null);
  const [conditionalMetrics, setConditionalMetrics] = useState<any>(null);
  const [phaseInfo, setPhaseInfo] = useState<any>(null);

  const fetchDebugInfo = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/debug");
      const data = await response.json();
      setDebugData(data);
      setShowDebug(true);
    } catch (err) {
      console.error("Failed to fetch debug info:", err);
    }
  };

  const fetchConditionalMetrics = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/conditional-metrics");
      const data = await response.json();
      setConditionalMetrics(data);
    } catch (err) {
      console.error("Failed to fetch conditional metrics:", err);
    }
  };

  const fetchPhaseInfo = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/phase-info");
      const data = await response.json();
      setPhaseInfo(data);
    } catch (err) {
      console.error("Failed to fetch phase info:", err);
    }
  };

  const triggerEmergency = async () => {
    try {
      await fetch("http://localhost:8000/api/trigger-emergency", { method: 'POST' });
      fetchConditionalMetrics();
    } catch (err) {
      console.error("Failed to trigger emergency:", err);
    }
  };

  const forceCoordination = async () => {
    try {
      await fetch("http://localhost:8000/api/force-coordination", { method: 'POST' });
      fetchConditionalMetrics();
    } catch (err) {
      console.error("Failed to force coordination:", err);
    }
  };

  // Auto-fetch conditional metrics when connection is established
  useEffect(() => {
    if (connectionStatus === 'connected') {
      fetchConditionalMetrics();
      fetchPhaseInfo();
    }
  }, [connectionStatus, logs.length]); // Refresh when logs change

  const getMissionPhaseColor = (phase: string) => {
    switch (phase) {
      case 'initialization': return 'bg-blue-100 text-blue-800';
      case 'exploration': return 'bg-yellow-100 text-yellow-800';
      case 'analysis': return 'bg-purple-100 text-purple-800';
      case 'construction': return 'bg-green-100 text-green-800';
      case 'optimization': return 'bg-orange-100 text-orange-800';
      case 'completion': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActivityColor = (activity: string) => {
    switch (activity) {
      case 'exploration': return 'text-yellow-600';
      case 'analysis': return 'text-purple-600';
      case 'construction': return 'text-green-600';
      case 'coordination': return 'text-blue-600';
      case 'emergency': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 min-h-screen">
      <div className="md:col-span-2 space-y-4">
        {/* Connection Status Banner */}
        {connectionStatus !== 'connected' && (
          <Card className={`border-l-4 ${
            connectionStatus === 'connecting' ? 'border-yellow-500 bg-yellow-50' : 'border-red-500 bg-red-50'
          }`}>
            <CardContent className="pt-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
                }`} />
                <p className="text-sm font-medium">
                  {connectionStatus === 'connecting' ? 'Connecting to backend...' : 'Backend disconnected'}
                </p>
              </div>
              {error && (
                <p className="text-xs text-muted-foreground mt-1">{error}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Enhanced Mission Status */}
        {conditionalMetrics && (
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-sm">
                <span>🎯 Mission Control Center</span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getMissionPhaseColor(conditionalMetrics.mission_phase)}`}>
                  {conditionalMetrics.mission_phase?.toUpperCase()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Phase Transitions</div>
                  <div className="text-lg font-bold text-blue-600">{conditionalMetrics.phase_transitions}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Coordination Events</div>
                  <div className="text-lg font-bold text-purple-600">{conditionalMetrics.coordination_events}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Emergency Responses</div>
                  <div className="text-lg font-bold text-red-600">{conditionalMetrics.emergency_activations}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Strategic Plan</div>
                  <div className={`text-lg font-bold ${conditionalMetrics.strategic_plan_ready ? 'text-green-600' : 'text-gray-400'}`}>
                    {conditionalMetrics.strategic_plan_ready ? '✓' : '○'}
                  </div>
                </div>
              </div>
              
              {/* Agent Activity Status */}
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-2">Agent Activities:</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(conditionalMetrics.last_activity).map(([agent, activity]: [string, any]) => (
                    <span key={agent} className={`px-2 py-1 rounded text-xs ${getActivityColor(activity)} bg-white border`}>
                      {agent}: {activity}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Status Indicators */}
              <div className="flex flex-wrap gap-3 text-xs">
                <div className={`flex items-center gap-1 ${conditionalMetrics.coordination_needed ? 'text-blue-600' : 'text-gray-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.coordination_needed ? 'bg-blue-500' : 'bg-gray-300'}`} />
                  Coordination {conditionalMetrics.coordination_needed ? 'Active' : 'Idle'}
                </div>
                <div className={`flex items-center gap-1 ${conditionalMetrics.active_threats > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.active_threats > 0 ? 'bg-red-500' : 'bg-gray-300'}`} />
                  Emergency {conditionalMetrics.active_threats > 0 ? 'Active' : 'Idle'}
                </div>
                <div className={`flex items-center gap-1 ${conditionalMetrics.resource_constraints ? 'text-orange-600' : 'text-gray-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.resource_constraints ? 'bg-orange-500' : 'bg-gray-300'}`} />
                  Resources {conditionalMetrics.resource_constraints ? 'Constrained' : 'Available'}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Phase Information Panel */}
        {phaseInfo && (
          <Card className="bg-gradient-to-r from-green-50 to-blue-50">
            <CardHeader>
              <CardTitle className="text-sm">📋 Current Phase: {phaseInfo.current_phase?.toUpperCase()}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-3">
              <div>
                <strong>Current Objectives:</strong>
                <ul className="mt-1 space-y-1">
                  {phaseInfo.current_objectives?.map((objective: string, idx: number) => (
                    <li key={idx} className="text-xs pl-2 border-l-2 border-blue-200">{objective}</li>
                  ))}
                </ul>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-xs text-muted-foreground">Exploration</div>
                  <div className="text-sm font-bold">
                    {(phaseInfo.exploration_progress * 100).toFixed(1)}% / {(phaseInfo.targets?.exploration_target * 100)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Buildings</div>
                  <div className="text-sm font-bold">
                    {phaseInfo.buildings_built} / {phaseInfo.targets?.building_target}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Steps</div>
                  <div className="text-sm font-bold">
                    {phaseInfo.step_count} / {phaseInfo.targets?.max_steps}
                  </div>
                </div>
              </div>
              
              {/* Progress Bars */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Exploration Progress</span>
                    <span>{(phaseInfo.exploration_progress * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${phaseInfo.exploration_progress * 100}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Construction Progress</span>
                    <span>{Math.round((phaseInfo.buildings_built / phaseInfo.targets?.building_target) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(phaseInfo.buildings_built / phaseInfo.targets?.building_target) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <GridMap />
        
        <MessageLog logs={logs} />
        
        <div className="flex gap-2 flex-wrap">
          <Button 
            onClick={step} 
            disabled={loading || connectionStatus !== 'connected'}
            className="flex-1"
          >
            {loading ? 'Processing...' : 'Step Simulation'}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={() => window.location.reload()}
            disabled={loading}
          >
            Refresh
          </Button>

          <Button 
            variant="secondary" 
            onClick={fetchDebugInfo}
            disabled={loading || connectionStatus !== 'connected'}
            size="sm"
          >
            Debug
          </Button>
          
          {/* Conditional Flow Test Buttons */}
          <Button 
            variant="destructive" 
            onClick={triggerEmergency}
            disabled={loading || connectionStatus !== 'connected'}
            size="sm"
          >
            🚨 Emergency
          </Button>
          
          <Button 
            variant="secondary" 
            onClick={forceCoordination}
            disabled={loading || connectionStatus !== 'connected'}
            size="sm"
          >
            🤝 Coordinate
          </Button>
        </div>

        {/* Enhanced Debug Info */}
        {showDebug && debugData && (
          <Card className="bg-muted/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm">🔍 Enhanced Debug Information</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowDebug(false)}
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="text-xs space-y-4 max-h-96 overflow-y-auto">
              
              {/* Conditional Flow State */}
              <div>
                <strong className="text-indigo-600">Conditional Flow State:</strong>
                <div className="bg-indigo-50 p-2 rounded mt-1">
                  <div>Mission Phase: {debugData.conditional_metrics?.mission_phase}</div>
                  <div>Coordination Needed: {debugData.conditional_metrics?.coordination_needed ? 'Yes' : 'No'}</div>
                  <div>Strategic Plan Ready: {debugData.conditional_metrics?.strategic_plan_ready ? 'Yes' : 'No'}</div>
                  <div>Active Threats: {debugData.conditional_metrics?.active_threats}</div>
                  <div>Resource Constraints: {debugData.conditional_metrics?.resource_constraints ? 'Yes' : 'No'}</div>
                </div>
              </div>

              {/* Flow Events */}
              <div>
                <strong className="text-purple-600">Flow Events:</strong>
                <div className="bg-purple-50 p-2 rounded mt-1">
                  <div>Phase Transitions: {debugData.simulation?.phase_transitions?.length || 0}</div>
                  <div>Coordination Events: {debugData.simulation?.coordination_events?.length || 0}</div>
                  {debugData.simulation?.phase_transitions?.slice(-3).map((transition: any, idx: number) => (
                    <div key={idx} className="text-xs text-purple-700">
                      Step {transition.step}: {transition.from} → {transition.to}
                    </div>
                  ))}
                </div>
              </div>

              {/* Simulation State */}
              <div>
                <strong className="text-blue-600">Simulation State:</strong>
                <div className="bg-blue-50 p-2 rounded mt-1">
                  <div>Step: {debugData.simulation?.step_count}</div>
                  <div>Status: {debugData.simulation?.mission_status}</div>
                  <div>Phase: {debugData.simulation?.mission_phase}</div>
                  <div>Exploration: {debugData.simulation?.exploration_progress?.toFixed(3)}</div>
                  <div>Buildings: {debugData.simulation?.buildings_built}</div>
                  <div>Visited Cells: {debugData.simulation?.visited_cells_count}</div>
                </div>
              </div>

              {/* Agent Details */}
              <div>
                <strong className="text-purple-600">Agent Details:</strong>
                {debugData.agents && Object.entries(debugData.agents).map(([agentId, agentData]: [string, any]) => (
                  <div key={agentId} className="bg-purple-50 p-2 rounded mt-1">
                    <div className="font-semibold flex justify-between">
                      <span>{agentId}:</span>
                      <span className={`text-xs px-1 rounded ${getActivityColor(agentData.last_activity)}`}>
                        {agentData.last_activity}
                      </span>
                    </div>
                    <div>Position: {JSON.stringify(agentData.position)}</div>
                    <div>Memory Count: {agentData.memory_count}</div>
                    <div>Status: {agentData.basic_status?.status}</div>
                    
                    {/* Agent-specific debug info */}
                    {agentId === 'scout' && (
                      <div className="text-blue-600">
                        <div>Cells Visited: {agentData.cells_visited}</div>
                        <div>Recent Visits: {JSON.stringify(agentData.visited_cells_list?.slice(-3))}</div>
                      </div>
                    )}
                    
                    {agentId === 'builder' && (
                      <div className="text-yellow-600">
                        <div>Buildings: {agentData.buildings_completed}</div>
                        <div>Last Built: {JSON.stringify(agentData.last_built_location)}</div>
                        <div>Messages Processed: {agentData.processed_messages}</div>
                      </div>
                    )}
                    
                    {agentId === 'strategist' && (
                      <div className="text-green-600">
                        <div>Build Orders: {agentData.build_orders_issued}</div>
                        <div>Scout Reports: {agentData.scout_reports}</div>
                        <div>Suggested Locations: {JSON.stringify(agentData.suggested_locations)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Raw JSON for Deep Debugging */}
              <details className="text-xs">
                <summary className="cursor-pointer font-semibold">Raw Conditional Flow Data</summary>
                <pre className="bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                  {JSON.stringify(debugData.conditional_metrics, null, 2)}
                </pre>
              </details>
            </CardContent>
          </Card>
        )}

        {/* Enhanced Quick Debug Info */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="bg-muted/50">
            <CardHeader>
              <CardTitle className="text-sm">⚡ Quick Debug Info</CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-1">
              <p><strong>Connection:</strong> {connectionStatus}</p>
              <p><strong>Mission Phase:</strong> {conditionalMetrics?.mission_phase || 'Unknown'}</p>
              <p><strong>Coordination:</strong> {conditionalMetrics?.coordination_needed ? 'Active' : 'Idle'}</p>
              <p><strong>Agents Count:</strong> {Object.keys(agents).length}</p>
              <p><strong>Logs Count:</strong> {logs.length}</p>
              <p><strong>Grid Size:</strong> {grid ? `${grid.width}×${grid.height}` : 'Unknown'}</p>
              <p><strong>Error:</strong> {error || 'None'}</p>
              
              {/* Agent positions and activities */}
              {Object.keys(agents).length > 0 && (
                <div>
                  <strong>Agent Status:</strong>
                  {Object.entries(agents).map(([id, data]: [string, any]) => (
                    <div key={id} className="ml-2 flex justify-between">
                      <span>{id}: {data.position ? `(${data.position[0]}, ${data.position[1]})` : 'Unknown'}</span>
                      <span className={`text-xs ${getActivityColor(data.last_activity || 'none')}`}>
                        {data.last_activity || 'none'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
      
      <div className="flex flex-col space-y-4">
        <div className="text-sm text-muted-foreground mb-2">
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' : 
              connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
            }`} />
            <span className="capitalize">{connectionStatus}</span>
            {conditionalMetrics && (
              <span className={`text-xs px-2 py-1 rounded ${getMissionPhaseColor(conditionalMetrics.mission_phase)}`}>
                {conditionalMetrics.mission_phase}
              </span>
            )}
          </div>
        </div>
        
        {Object.keys(agents).length > 0 ? (
          Object.entries(agents).map(([agentId, agentData]: [string, any]) => (
            <AgentCard key={agentId} agentId={agentId} agentData={agentData} />
          ))
        ) : (
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center">
                {loading ? 'Loading agents...' : 'No agents available'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}