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
      
      console.log('Attempting to load simulation data...');
      
      const [g, l, a] = await Promise.all([
        fetchGrid(),
        fetchLogs(),
        fetchAgents(),
      ]);
      
      setGrid(g);
      setLogs(l.logs || []);
      setAgents(a);
      setConnectionStatus('connected');
      setError(null);
      
      console.log('Simulation data loaded successfully:', { grid: g, logs: l.logs, agents: a });
      
    } catch (err) {
      console.error('Failed to load simulation data:', err);
      setError(`Failed to connect to backend: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
      
      // Set fallback data
      setGrid(null);
      setLogs(['Failed to connect to backend. Please ensure the backend server is running on http://localhost:8000']);
      setAgents({});
    } finally {
      setLoading(false);
    }
  }

  async function step() {
    try {
      setError(null);
      console.log('Executing simulation step...');
      
      const result = await stepSimulation();
      setGrid(result.grid);
      setLogs(result.logs || []);
      setAgents(result.agents);
      setConnectionStatus('connected');
      
      console.log('Simulation step completed:', result);
      
    } catch (err) {
      console.error('Failed to step simulation:', err);
      setError(`Failed to step simulation: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
    }
  }

  useEffect(() => {
    loadData();
    
    // Set up periodic health check
    const healthCheck = setInterval(async () => {
      if (connectionStatus === 'disconnected') {
        try {
          await fetchGrid();
          setConnectionStatus('connected');
          setError(null);
        } catch {
          // Still disconnected
        }
      }
    }, 5000);

    return () => clearInterval(healthCheck);
  }, []);

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