import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  fetchGrid,
  fetchLogs,
  fetchAgents,
  stepSimulation,
} from "../lib/api";

interface SimulationContextType {
  grid: any;
  logs: string[];
  agents: any;
  step: () => Promise<void>;
  loading: boolean;
  error: string | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

const SimulationContext = createContext<SimulationContextType | null>(null);

export function useSimulation() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
}

interface SimulationProviderProps {
  children: ReactNode;
}

export function SimulationProvider({ children }: SimulationProviderProps) {
  const [grid, setGrid] = useState(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [agents, setAgents] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      setConnectionStatus('connecting');
      
      console.log('🔄 Attempting to load simulation data...');
      
      const [g, l, a] = await Promise.all([
        fetchGrid(),
        fetchLogs(),
        fetchAgents(),
      ]);
      
      console.log('📊 Raw API responses:', {
        grid: g,
        logs: l,
        agents: a
      });
      
      setGrid(g);
      setLogs(l.logs || []);
      setAgents(a);
      setConnectionStatus('connected');
      setError(null);
      
      console.log('✅ Simulation data loaded successfully:', { 
        gridSize: g ? `${g.width}x${g.height}` : 'null',
        logsCount: l.logs?.length || 0, 
        agentsCount: Object.keys(a).length,
        agentIds: Object.keys(a)
      });
      
      // Log detailed agent data for debugging
      Object.entries(a).forEach(([id, data]: [string, any]) => {
        console.log(`🤖 Agent ${id}:`, {
          role: data.role,
          status: data.status,
          position: data.position,
          memoryCount: data.memory?.length || 0,
          lastMemory: data.memory?.[data.memory.length - 1]
        });
      });
      
    } catch (err) {
      console.error('❌ Failed to load simulation data:', err);
      setError(`Failed to connect to backend: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
      
      // Set fallback data
      setGrid(null);
      setLogs(['❌ Failed to connect to backend. Please ensure the backend server is running on http://localhost:8000']);
      setAgents({});
    } finally {
      setLoading(false);
    }
  }

  async function step() {
    try {
      setError(null);
      console.log('⏩ Executing simulation step...');
      
      const result = await stepSimulation();
      
      console.log('📈 Step result received:', {
        gridSize: result.grid ? `${result.grid.width}x${result.grid.height}` : 'null',
        logsCount: result.logs?.length || 0,
        agentsCount: Object.keys(result.agents || {}).length,
        stepCount: result.step_count,
        status: result.status
      });
      
      // Log what changed in this step
      const newLogs = result.logs?.slice(logs.length) || [];
      if (newLogs.length > 0) {
        console.log('📝 New logs from this step:', newLogs);
      }
      
      // Log agent changes
      Object.entries(result.agents || {}).forEach(([id, newData]: [string, any]) => {
        const oldData = agents[id];
        if (oldData && newData) {
          const changes = [];
          if (oldData.status !== newData.status) {
            changes.push(`status: ${oldData.status} → ${newData.status}`);
          }
          if (JSON.stringify(oldData.position) !== JSON.stringify(newData.position)) {
            changes.push(`position: ${JSON.stringify(oldData.position)} → ${JSON.stringify(newData.position)}`);
          }
          if (oldData.memory?.length !== newData.memory?.length) {
            changes.push(`memory: ${oldData.memory?.length || 0} → ${newData.memory?.length || 0} entries`);
          }
          
          if (changes.length > 0) {
            console.log(`🔄 Agent ${id} changes:`, changes.join(', '));
          }
        }
      });
      
      setGrid(result.grid);
      setLogs(result.logs || []);
      setAgents(result.agents || {});
      setConnectionStatus('connected');
      
      console.log('✅ Simulation step completed successfully');
      
    } catch (err) {
      console.error('❌ Failed to step simulation:', err);
      setError(`Failed to step simulation: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
    }
  }

  useEffect(() => {
    console.log('🚀 SimulationProvider initializing...');
    loadData();
    
    // Set up periodic health check
    const healthCheck = setInterval(async () => {
      if (connectionStatus === 'disconnected') {
        console.log('🔍 Health check: Attempting to reconnect...');
        try {
          await fetchGrid();
          console.log('✅ Health check: Reconnected!');
          setConnectionStatus('connected');
          setError(null);
        } catch {
          console.log('❌ Health check: Still disconnected');
        }
      }
    }, 5000);

    return () => {
      console.log('🛑 SimulationProvider cleanup');
      clearInterval(healthCheck);
    };
  }, []);

  // Log state changes for debugging
  useEffect(() => {
    console.log('📊 State updated:', {
      connectionStatus,
      agentsCount: Object.keys(agents).length,
      logsCount: logs.length,
      hasGrid: !!grid,
      loading,
      error: error ? error.substring(0, 100) : null
    });
  }, [connectionStatus, agents, logs, grid, loading, error]);

  return (
    <SimulationContext.Provider
      value={{ 
        grid, 
        logs, 
        agents, 
        step, 
        loading, 
        error, 
        connectionStatus 
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}