import { useSimulation } from "../context/SimulationContext";
import { AgentCard } from "../components/AgentCard";
import { GridMap } from "../components/GridMap";
import { MessageLog } from "../components/MessageLog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SimulationPage() {
  const { agents, step, logs, loading, error, connectionStatus } = useSimulation();

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
        </div>

        {/* Debug Info (remove in production) */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="bg-muted/50">
            <CardHeader>
              <CardTitle className="text-sm">Debug Info</CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-1">
              <p><strong>Connection:</strong> {connectionStatus}</p>
              <p><strong>Agents Count:</strong> {Object.keys(agents).length}</p>
              <p><strong>Logs Count:</strong> {logs.length}</p>
              <p><strong>Error:</strong> {error || 'None'}</p>
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