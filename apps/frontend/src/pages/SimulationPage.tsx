// apps/frontend/src/pages/SimulationPage.tsx
import { useSimulation } from "../context/SimulationContext";
import { AgentCard } from "../components/AgentCard";
import { GridMap } from "../components/GridMap";
import { MessageLog } from "../components/MessageLog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { fetchDebugInfo, fetchGridRaw } from "../lib/api";

export function SimulationPage() {
  const { 
    agents, 
    step, 
    reset,
    refresh,
    triggerEmergencyMode,
    forceCoordinationMode,
    logs, 
    loading, 
    stepping,
    error, 
    connectionStatus, 
    grid,
    conditionalMetrics,
    phaseInfo,
    healthStatus,
    lastUpdated
  } = useSimulation();
  
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState<any>(null);
  const [showRawGrid, setShowRawGrid] = useState(false);
  const [rawGridData, setRawGridData] = useState<any>(null);

  const fetchDebugInfo = async () => {
    try {
      const data = await fetchDebugInfo();
      setDebugData(data);
      setShowDebug(true);
    } catch (err) {
      console.error("Failed to fetch debug info:", err);
    }
  };

  const fetchRawGrid = async () => {
    try {
      const data = await fetchGridRaw();
      setRawGridData(data);
      setShowRawGrid(true);
    } catch (err) {
      console.error("Failed to fetch raw grid:", err);
    }
  };

  const getMissionPhaseColor = (phase: string) => {
    switch (phase) {
      case 'initialization': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'exploration': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'analysis': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'construction': return 'bg-green-100 text-green-800 border-green-200';
      case 'optimization': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'completion': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getActivityColor = (activity: string) => {
    switch (activity) {
      case 'exploration': return 'text-yellow-600 bg-yellow-50';
      case 'analysis': return 'text-purple-600 bg-purple-50';
      case 'construction': return 'text-green-600 bg-green-50';
      case 'coordination': return 'text-blue-600 bg-blue-50';
      case 'emergency': return 'text-red-600 bg-red-50';
      case 'parallel_execution': return 'text-indigo-600 bg-indigo-50';
      case 'optimization': return 'text-orange-600 bg-orange-50';
      case 'completed': return 'text-emerald-600 bg-emerald-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500 animate-pulse';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-4 min-h-screen">
      <div className="lg:col-span-2 space-y-4">
        {/* Enhanced Connection Status Banner */}
        {(connectionStatus !== 'connected' || error) && (
          <Card className={`border-l-4 ${
            connectionStatus === 'connecting' ? 'border-yellow-500 bg-yellow-50' : 'border-red-500 bg-red-50'
          }`}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`} />
                  <p className="text-sm font-medium">
                    {connectionStatus === 'connecting' ? 'Connecting to backend...' : 
                     connectionStatus === 'disconnected' ? 'Backend disconnected' : 'Connection issue'}
                  </p>
                  {healthStatus && (
                    <span className="text-xs text-muted-foreground">
                      Health: {healthStatus.status}
                    </span>
                  )}
                </div>
                <Button size="sm" variant="outline" onClick={refresh} disabled={loading}>
                  Retry
                </Button>
              </div>
              {error && (
                <p className="text-xs text-muted-foreground mt-1">{error}</p>
              )}
              {lastUpdated && (
                <p className="text-xs text-muted-foreground mt-1">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Enhanced Mission Control Panel */}
        {conditionalMetrics && (
          <Card className="bg-gradient-to-r from-blue-50 via-purple-50 to-green-50 border-2">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-lg">
                <span className="flex items-center gap-2">
                  🎯 Mission Control Center
                  {healthStatus?.conditional_flows && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {healthStatus.conditional_flows}
                    </span>
                  )}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getMissionPhaseColor(conditionalMetrics.mission_phase)}`}>
                  {conditionalMetrics.mission_phase?.toUpperCase()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Phase Transitions</div>
                  <div className="text-xl font-bold text-blue-600">{conditionalMetrics.phase_transitions}</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Coordination Events</div>
                  <div className="text-xl font-bold text-purple-600">{conditionalMetrics.coordination_events}</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Emergency Responses</div>
                  <div className="text-xl font-bold text-red-600">{conditionalMetrics.emergency_activations}</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Strategic Plan</div>
                  <div className={`text-xl font-bold ${conditionalMetrics.strategic_plan_ready ? 'text-green-600' : 'text-gray-400'}`}>
                    {conditionalMetrics.strategic_plan_ready ? '✓ Ready' : '○ Planning'}
                  </div>
                </div>
              </div>
              
              {/* Agent Activity Status */}
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Agent Activities:</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(conditionalMetrics.last_activity).map(([agent, activity]: [string, any]) => (
                    <span key={agent} className={`px-3 py-1 rounded-full text-xs font-medium border ${getActivityColor(activity)}`}>
                      {agent}: {activity}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* System Status Indicators */}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${conditionalMetrics.coordination_needed ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.coordination_needed ? 'bg-blue-500' : 'bg-gray-300'}`} />
                  Coordination {conditionalMetrics.coordination_needed ? 'Active' : 'Idle'}
                </div>
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${conditionalMetrics.active_threats > 0 ? 'bg-red-50 text-red-700 border-red-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.active_threats > 0 ? 'bg-red-500' : 'bg-gray-300'}`} />
                  Emergency {conditionalMetrics.active_threats > 0 ? 'Active' : 'Idle'}
                </div>
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${conditionalMetrics.resource_constraints ? 'bg-orange-50 text-orange-700 border-orange-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                  <span className={`w-2 h-2 rounded-full ${conditionalMetrics.resource_constraints ? 'bg-orange-500' : 'bg-gray-300'}`} />
                  Resources {conditionalMetrics.resource_constraints ? 'Constrained' : 'Available'}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Enhanced Phase Information Panel */}
        {phaseInfo && (
          <Card className="bg-gradient-to-r from-green-50 via-blue-50 to-purple-50 border-2">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>📋 Mission Phase: {phaseInfo.current_phase?.toUpperCase()}</span>
                <span className="text-sm text-muted-foreground">
                  Step {phaseInfo.step_count} / {phaseInfo.targets?.max_steps}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current Objectives */}
              <div>
                <strong className="text-sm">Current Objectives:</strong>
                <div className="mt-2 space-y-1">
                  {phaseInfo.current_objectives?.map((objective: string, idx: number) => (
                    <div key={idx} className="text-sm pl-3 py-1 border-l-2 border-blue-200 bg-blue-50 rounded-r">
                      {objective}
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Progress Metrics */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Exploration</div>
                  <div className="text-lg font-bold text-blue-600">
                    {(phaseInfo.exploration_progress * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    / {(phaseInfo.targets?.exploration_target * 100)}%
                  </div>
                </div>
                <div className="p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Buildings</div>
                  <div className="text-lg font-bold text-green-600">
                    {phaseInfo.buildings_built}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    / {phaseInfo.targets?.building_target}
                  </div>
                </div>
                <div className="p-3 bg-white rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Progress</div>
                  <div className="text-lg font-bold text-purple-600">
                    {((phaseInfo.step_count / phaseInfo.targets?.max_steps) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Complete</div>
                </div>
              </div>
              
              {/* Progress Bars */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Exploration Progress</span>
                    <span>{(phaseInfo.exploration_progress * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(phaseInfo.exploration_progress * 100, 100)}%` }}
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
                      className="bg-green-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min((phaseInfo.buildings_built / phaseInfo.targets?.building_target) * 100, 100)}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Mission Progress</span>
                    <span>{Math.round((phaseInfo.step_count / phaseInfo.targets?.max_steps) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min((phaseInfo.step_count / phaseInfo.targets?.max_steps) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
              
              {/* Recent Events */}
              {(phaseInfo.phase_transitions?.length > 0 || phaseInfo.coordination_events?.length > 0) && (
                <div>
                  <strong className="text-sm">Recent Events:</strong>
                  <div className="mt-2 space-y-1 max-h-20 overflow-y-auto">
                    {phaseInfo.phase_transitions?.slice(-3).map((transition, idx) => (
                      <div key={idx} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        Step {transition.step}: Phase {transition.from} → {transition.to}
                      </div>
                    ))}
                    {phaseInfo.coordination_events?.slice(-3).map((event, idx) => (
                      <div key={idx} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        Step {event.step}: Coordination {event.type}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <GridMap />
        
        <MessageLog logs={logs} />
        
        {/* Enhanced Control Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">🎮 Simulation Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Primary Controls */}
            <div className="flex gap-2 flex-wrap">
              <Button 
                onClick={step} 
                disabled={loading || stepping || connectionStatus !== 'connected'}
                className="flex-1 min-w-32"
                size="lg"
              >
                {stepping ? 'Processing...' : '▶️ Step Simulation'}
              </Button>
              
              <Button 
                variant="outline" 
                onClick={refresh}
                disabled={loading || stepping}
              >
                🔄 Refresh
              </Button>

              <Button 
                variant="destructive" 
                onClick={reset}
                disabled={loading || stepping || connectionStatus !== 'connected'}
              >
                🔄 Reset
              </Button>
            </div>

            {/* Advanced Controls */}
            <div className="grid grid-cols-2 gap-2">
              <Button 
                variant="secondary" 
                onClick={fetchDebugInfo}
                disabled={loading || connectionStatus !== 'connected'}
                size="sm"
              >
                🔍 Debug Info
              </Button>
              
              <Button 
                variant="secondary" 
                onClick={fetchRawGrid}
                disabled={loading || connectionStatus !== 'connected'}
                size="sm"
              >
                📊 Raw Grid
              </Button>
            </div>
            
            {/* Conditional Flow Test Controls */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">Conditional Flow Testing:</div>
              <div className="flex gap-2">
                <Button 
                  variant="destructive" 
                  onClick={triggerEmergencyMode}
                  disabled={loading || stepping || connectionStatus !== 'connected'}
                  size="sm"
                  className="flex-1"
                >
                  🚨 Trigger Emergency
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={forceCoordinationMode}
                  disabled={loading || stepping || connectionStatus !== 'connected'}
                  size="sm"
                  className="flex-1"
                >
                  🤝 Force Coordination
                </Button>
              </div>
            </div>

            {/* System Status */}
            <div className="pt-2 border-t">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>System Status:</span>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`} />
                  <span className="capitalize">{connectionStatus}</span>
                  {healthStatus && (
                    <span className="ml-2">({healthStatus.status})</span>
                  )}
                </div>
              </div>
              {lastUpdated && (
                <div className="text-xs text-muted-foreground mt-1">
                  Last updated: {lastUpdated.toLocaleString()}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Debug Info Modal */}
        {showDebug && debugData && (
          <Card className="bg-muted/50 border-2 border-blue-200">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">🔍 Comprehensive Debug Information</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowDebug(false)}
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="text-sm space-y-4 max-h-96 overflow-y-auto">
              
              {/* Enhanced Conditional Flow State */}
              <div>
                <strong className="text-indigo-600">🔄 Conditional Flow State:</strong>
                <div className="bg-indigo-50 p-3 rounded-lg mt-2 border border-indigo-200">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>Mission Phase: <span className="font-mono">{debugData.conditional_metrics?.mission_phase}</span></div>
                    <div>Coordination: <span className={debugData.conditional_metrics?.coordination_needed ? 'text-blue-600 font-bold' : 'text-gray-500'}>{debugData.conditional_metrics?.coordination_needed ? 'Active' : 'Idle'}</span></div>
                    <div>Strategic Plan: <span className={debugData.conditional_metrics?.strategic_plan_ready ? 'text-green-600 font-bold' : 'text-gray-500'}>{debugData.conditional_metrics?.strategic_plan_ready ? 'Ready' : 'Planning'}</span></div>
                    <div>Threats: <span className={debugData.conditional_metrics?.active_threats > 0 ? 'text-red-600 font-bold' : 'text-gray-500'}>{debugData.conditional_metrics?.active_threats || 0}</span></div>
                    <div>Resources: <span className={debugData.conditional_metrics?.resource_constraints ? 'text-orange-600 font-bold' : 'text-gray-500'}>{debugData.conditional_metrics?.resource_constraints ? 'Constrained' : 'Available'}</span></div>
                  </div>
                </div>
              </div>

              {/* Flow Events History */}
              <div>
                <strong className="text-purple-600">📈 Flow Events History:</strong>
                <div className="bg-purple-50 p-3 rounded-lg mt-2 border border-purple-200">
                  <div className="text-xs space-y-1">
                    <div>Phase Transitions: {debugData.simulation?.phase_transitions?.length || 0}</div>
                    <div>Coordination Events: {debugData.simulation?.coordination_events?.length || 0}</div>
                    {debugData.simulation?.phase_transitions?.slice(-3).map((transition: any, idx: number) => (
                      <div key={idx} className="text-xs text-purple-700 bg-white px-2 py-1 rounded">
                        Step {transition.step}: {transition.from} → {transition.to}
                      </div>
                    ))}
                    {debugData.simulation?.coordination_events?.slice(-3).map((event: any, idx: number) => (
                      <div key={idx} className="text-xs text-blue-700 bg-white px-2 py-1 rounded">
                        Step {event.step}: Coordination {event.type}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Detailed Simulation State */}
              <div>
                <strong className="text-blue-600">🎯 Simulation State:</strong>
                <div className="bg-blue-50 p-3 rounded-lg mt-2 border border-blue-200">
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>Step: <span className="font-mono">{debugData.simulation?.step_count}</span></div>
                    <div>Status: <span className="font-mono">{debugData.simulation?.mission_status}</span></div>
                    <div>Phase: <span className="font-mono">{debugData.simulation?.mission_phase}</span></div>
                    <div>Exploration: <span className="font-mono">{debugData.simulation?.exploration_progress?.toFixed(3)}</span></div>
                    <div>Buildings: <span className="font-mono">{debugData.simulation?.buildings_built}</span></div>
                    <div>Visited: <span className="font-mono">{debugData.simulation?.visited_cells_count}</span></div>
                  </div>
                </div>
              </div>

              {/* Enhanced Agent Details */}
              <div>
                <strong className="text-green-600">🤖 Agent Details:</strong>
                {debugData.agents && Object.entries(debugData.agents).map(([agentId, agentData]: [string, any]) => (
                  <div key={agentId} className="bg-green-50 p-3 rounded-lg mt-2 border border-green-200">
                    <div className="font-semibold flex justify-between items-center mb-2">
                      <span className="flex items-center gap-2">
                        {agentId === 'scout' && '👀'} 
                        {agentId === 'builder' && '🔨'}
                        {agentId === 'strategist' && '🧠'}
                        {agentId}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getActivityColor(agentData.last_activity)}`}>
                        {agentData.last_activity}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>Position: <span className="font-mono">{JSON.stringify(agentData.position)}</span></div>
                      <div>Memory: <span className="font-mono">{agentData.memory_count} entries</span></div>
                      <div>Status: <span className="font-mono">{agentData.basic_status?.status}</span></div>
                      <div>Class: <span className="font-mono">{agentData.agent_class}</span></div>
                    </div>
                    
                    {/* Agent-specific enhanced debug info */}
                    {agentId === 'scout' && (
                      <div className="mt-2 p-2 bg-blue-100 rounded text-xs">
                        <div className="font-medium text-blue-700 mb-1">Scout Metrics:</div>
                        <div>Cells Visited: {agentData.cells_visited}</div>
                        <div>Exploration %: {agentData.exploration_percentage?.toFixed(1)}%</div>
                        <div>Recent: {JSON.stringify(agentData.visited_cells_list?.slice(-3))}</div>
                      </div>
                    )}
                    
                    {agentId === 'builder' && (
                      <div className="mt-2 p-2 bg-yellow-100 rounded text-xs">
                        <div className="font-medium text-yellow-700 mb-1">Builder Metrics:</div>
                        <div>Buildings: {agentData.buildings_completed}</div>
                        <div>Last Built: {JSON.stringify(agentData.last_built_location)}</div>
                        <div>Orders Processed: {agentData.processed_messages}</div>
                        <div>Target: {JSON.stringify(agentData.current_target)}</div>
                        <div>Steps Remaining: {agentData.movement_steps_remaining}</div>
                      </div>
                    )}
                    
                    {agentId === 'strategist' && (
                      <div className="mt-2 p-2 bg-green-100 rounded text-xs">
                        <div className="font-medium text-green-700 mb-1">Strategist Metrics:</div>
                        <div>Build Orders: {agentData.build_orders_issued}</div>
                        <div>Scout Reports: {agentData.scout_reports}</div>
                        <div>Analysis Cycles: {agentData.analysis_cycles}</div>
                        <div>Building Target: {agentData.building_target}</div>
                        <div>Suggested Locations: {JSON.stringify(agentData.suggested_locations)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Grid Debug Info */}
              <div>
                <strong className="text-orange-600">🗺️ Grid Debug:</strong>
                <div className="bg-orange-50 p-3 rounded-lg mt-2 border border-orange-200">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>Dimensions: <span className="font-mono">{debugData.grid?.dimensions}</span></div>
                    <div>Total Cells: <span className="font-mono">{debugData.grid?.total_cells}</span></div>
                    <div>With Structures: <span className="font-mono">{debugData.grid?.cells_with_structures?.length || 0}</span></div>
                    <div>With Agents: <span className="font-mono">{debugData.grid?.cells_with_agents?.length || 0}</span></div>
                  </div>
                  {debugData.grid?.cells_with_structures?.length > 0 && (
                    <div className="mt-2">
                      <div className="font-medium text-orange-700 mb-1">Structures:</div>
                      {debugData.grid.cells_with_structures.map((cell: any, idx: number) => (
                        <div key={idx} className="text-xs">
                          {JSON.stringify(cell.position)}: {cell.structure}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Raw Data Section */}
              <details className="text-xs">
                <summary className="cursor-pointer font-semibold text-gray-600 hover:text-gray-800">🔍 Raw Debug Data</summary>
                <pre className="bg-gray-100 p-3 rounded-lg mt-2 overflow-x-auto text-[10px] border">
                  {JSON.stringify(debugData, null, 2)}
                </pre>
              </details>
            </CardContent>
          </Card>
        )}

        {/* Raw Grid Data Modal */}
        {showRawGrid && rawGridData && (
          <Card className="bg-muted/50 border-2 border-green-200">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">📊 Raw Grid Data</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowRawGrid(false)}
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="text-sm space-y-4 max-h-96 overflow-y-auto">
              <div>
                <strong>Grid Bounds:</strong>
                <div className="bg-green-50 p-2 rounded mt-1 text-xs">
                  <div>Width: {rawGridData.width} (0 to {rawGridData.width - 1})</div>
                  <div>Height: {rawGridData.height} (0 to {rawGridData.height - 1})</div>
                  <div>Total Cells: {Object.keys(rawGridData.raw_cells || {}).length}</div>
                </div>
              </div>
              
              <div>
                <strong>Agent Positions:</strong>
                <div className="bg-blue-50 p-2 rounded mt-1 text-xs">
                  {Object.entries(rawGridData.agent_positions || {}).map(([agent, pos]: [string, any]) => (
                    <div key={agent}>{agent}: {JSON.stringify(pos)}</div>
                  ))}
                </div>
              </div>

              <details className="text-xs">
                <summary className="cursor-pointer font-semibold">Raw Cell Data</summary>
                <pre className="bg-gray-100 p-2 rounded mt-1 overflow-x-auto text-[10px]">
                  {JSON.stringify(rawGridData.raw_cells, null, 2)}
                </pre>
              </details>
            </CardContent>
          </Card>
        )}
      </div>
      
      {/* Enhanced Agent Panel */}
      <div className="flex flex-col space-y-4">
        <div className="sticky top-4">
          {/* System Status Header */}
          <Card className="mb-4">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`} />
                  <span className="font-medium capitalize">{connectionStatus}</span>
                  {conditionalMetrics && (
                    <span className={`text-xs px-2 py-1 rounded-full border ${getMissionPhaseColor(conditionalMetrics.mission_phase)}`}>
                      {conditionalMetrics.mission_phase}
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {Object.keys(agents).length} agents
                </div>
              </div>
              
              {healthStatus && (
                <div className="mt-2 text-xs text-muted-foreground">
                  <div>Backend: {healthStatus.status}</div>
                  <div>Agents: {healthStatus.agents}</div>
                  <div>Grid: {healthStatus.grid_size}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Agent Cards */}
        {Object.keys(agents).length > 0 ? (
          Object.entries(agents).map(([agentId, agentData]: [string, any]) => (
            <AgentCard key={agentId} agentId={agentId} agentData={agentData} />
          ))
        ) : (
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-muted-foreground">
                {loading ? 'Loading agents...' : 'No agents available'}
              </p>
              {connectionStatus === 'disconnected' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={refresh} 
                  className="mt-2"
                >
                  Retry Connection
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}