import { useSimulation } from "../context/SimulationContext";
import { AgentCard } from "../components/AgentCard";
import { GridMap } from "../components/GridMap";
import { MessageLog } from "../components/MessageLog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

export function SimulationPage() {
  const { agents, step, logs, loading, error, connectionStatus, grid } = useSimulation();
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState<any>(null);

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
              {connectionStatus === 'disconnected' && (
                <div className="mt-2 text-xs text-muted-foreground">
                  <p>Make sure the backend is running:</p>
                  <code className="bg-gray-200 px-2 py-1 rounded">
                    cd apps/backend && uvicorn app.main:app --reload
                  </code>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <GridMap />
        
        <MessageLog logs={logs} />
        
        <div className="flex gap-4">
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
        </div>

        {/* Enhanced Debug Info */}
        {showDebug && debugData && (
          <Card className="bg-muted/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm">Debug Information</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowDebug(false)}
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="text-xs space-y-3 max-h-96 overflow-y-auto">
              
              {/* Simulation State */}
              <div>
                <strong className="text-blue-600">Simulation State:</strong>
                <div className="bg-blue-50 p-2 rounded mt-1">
                  <div>Step: {debugData.simulation?.step_count}</div>
                  <div>Status: {debugData.simulation?.mission_status}</div>
                  <div>Exploration: {debugData.simulation?.exploration_progress?.toFixed(1)}%</div>
                  <div>Buildings: {debugData.simulation?.buildings_built}</div>
                  <div>Visited Cells: {debugData.simulation?.visited_cells_count}</div>
                </div>
              </div>

              {/* Grid State */}
              <div>
                <strong className="text-green-600">Grid State:</strong>
                <div className="bg-green-50 p-2 rounded mt-1">
                  <div>Dimensions: {debugData.grid?.dimensions}</div>
                  <div>Total Cells: {debugData.grid?.total_cells}</div>
                  <div>Structures: {debugData.grid?.cells_with_structures?.length || 0}</div>
                  <div>Agent Positions: {JSON.stringify(debugData.grid?.agent_positions)}</div>
                </div>
              </div>

              {/* Agent Details */}
              <div>
                <strong className="text-purple-600">Agent Details:</strong>
                {debugData.agents && Object.entries(debugData.agents).map(([agentId, agentData]: [string, any]) => (
                  <div key={agentId} className="bg-purple-50 p-2 rounded mt-1">
                    <div className="font-semibold">{agentId}:</div>
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

              {/* Recent Logs */}
              <div>
                <strong className="text-orange-600">Recent Backend Logs:</strong>
                <div className="bg-orange-50 p-2 rounded mt-1 font-mono">
                  {debugData.simulation?.recent_logs?.map((log: string, idx: number) => (
                    <div key={idx} className="text-xs">{log}</div>
                  ))}
                </div>
              </div>

              {/* Raw JSON for Deep Debugging */}
              <details className="text-xs">
                <summary className="cursor-pointer font-semibold">Raw Debug Data</summary>
                <pre className="bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                  {JSON.stringify(debugData, null, 2)}
                </pre>
              </details>
            </CardContent>
          </Card>
        )}

        {/* Basic Debug Info (always visible in development) */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="bg-muted/50">
            <CardHeader>
              <CardTitle className="text-sm">Quick Debug Info</CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-1">
              <p><strong>Connection:</strong> {connectionStatus}</p>
              <p><strong>Agents Count:</strong> {Object.keys(agents).length}</p>
              <p><strong>Logs Count:</strong> {logs.length}</p>
              <p><strong>Grid Size:</strong> {grid ? `${grid.width}×${grid.height}` : 'Unknown'}</p>
              <p><strong>Error:</strong> {error || 'None'}</p>
              
              {/* Agent positions */}
              {Object.keys(agents).length > 0 && (
                <div>
                  <strong>Agent Positions:</strong>
                  {Object.entries(agents).map(([id, data]: [string, any]) => (
                    <div key={id} className="ml-2">
                      {id}: {data.position ? `(${data.position[0]}, ${data.position[1]})` : 'Unknown'}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Buildings count */}
              {grid && (
                <p><strong>Buildings:</strong> {
                  Object.values(grid.cells).filter((cell: any) => cell.structure === 'building').length
                }</p>
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