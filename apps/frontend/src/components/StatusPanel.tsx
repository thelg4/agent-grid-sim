// apps/frontend/src/components/StatusPanel.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSimulation } from "@/context/SimulationContext";

export function StatusPanel() {
  const { 
    conditionalMetrics, 
    phaseInfo, 
    healthStatus, 
    connectionStatus,
    lastUpdated,
    triggerEmergencyMode,
    forceCoordinationMode
  } = useSimulation();

  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500 animate-pulse';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'initialization': return 'default';
      case 'exploration': return 'secondary';
      case 'analysis': return 'outline';
      case 'construction': return 'default';
      case 'optimization': return 'secondary';
      case 'completion': return 'default';
      default: return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${getConnectionColor()}`} />
            System Status
          </span>
          {conditionalMetrics && (
            <Badge variant={getPhaseColor(conditionalMetrics.mission_phase)}>
              {conditionalMetrics.mission_phase?.toUpperCase()}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Connection Info */}
        <div className="flex justify-between items-center text-sm">
          <span>Connection:</span>
          <span className="capitalize font-medium">{connectionStatus}</span>
        </div>
        
        {healthStatus && (
          <>
            <div className="flex justify-between items-center text-sm">
              <span>Backend:</span>
              <Badge variant={healthStatus.status === 'healthy' ? 'default' : 'destructive'}>
                {healthStatus.status}
              </Badge>
            </div>
            
            <div className="flex justify-between items-center text-sm">
              <span>Agents:</span>
              <span className="font-mono">{healthStatus.agents}</span>
            </div>
            
            <div className="flex justify-between items-center text-sm">
              <span>Grid:</span>
              <span className="font-mono">{healthStatus.grid_size}</span>
            </div>
          </>
        )}

        {conditionalMetrics && (
          <>
            <div className="border-t pt-4">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>Phase Transitions: <span className="font-mono">{conditionalMetrics.phase_transitions}</span></div>
                <div>Coordination Events: <span className="font-mono">{conditionalMetrics.coordination_events}</span></div>
                <div>Emergency Responses: <span className="font-mono">{conditionalMetrics.emergency_activations}</span></div>
                <div>Active Threats: <span className="font-mono">{conditionalMetrics.active_threats}</span></div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge variant={conditionalMetrics.coordination_needed ? 'default' : 'outline'}>
                Coordination {conditionalMetrics.coordination_needed ? 'Active' : 'Idle'}
              </Badge>
              <Badge variant={conditionalMetrics.strategic_plan_ready ? 'default' : 'outline'}>
                Strategy {conditionalMetrics.strategic_plan_ready ? 'Ready' : 'Planning'}
              </Badge>
              <Badge variant={conditionalMetrics.active_threats > 0 ? 'destructive' : 'outline'}>
                Emergency {conditionalMetrics.active_threats > 0 ? 'Active' : 'Idle'}
              </Badge>
            </div>
          </>
        )}

        {phaseInfo && (
          <div className="border-t pt-4 space-y-2">
            <div className="text-sm font-medium">Mission Progress</div>
            
            {/* Exploration Progress */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span>Exploration</span>
                <span>{(phaseInfo.exploration_progress * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(phaseInfo.exploration_progress * 100, 100)}%` }}
                />
              </div>
            </div>

            {/* Construction Progress */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span>Construction</span>
                <span>{phaseInfo.buildings_built} / {phaseInfo.targets?.building_target}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${Math.min((phaseInfo.buildings_built / (phaseInfo.targets?.building_target || 1)) * 100, 100)}%` 
                  }}
                />
              </div>
            </div>

            {/* Mission Progress */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span>Mission</span>
                <span>{phaseInfo.step_count} / {phaseInfo.targets?.max_steps}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-purple-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${Math.min((phaseInfo.step_count / (phaseInfo.targets?.max_steps || 1)) * 100, 100)}%` 
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Testing Controls */}
        <div className="border-t pt-4 space-y-2">
          <div className="text-sm font-medium">Flow Testing</div>
          <div className="flex gap-2">
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={triggerEmergencyMode}
              className="flex-1"
            >
              🚨 Emergency
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={forceCoordinationMode}
              className="flex-1"
            >
              🤝 Coordinate
            </Button>
          </div>
        </div>

        {lastUpdated && (
          <div className="text-xs text-muted-foreground text-center border-t pt-2">
            Updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}