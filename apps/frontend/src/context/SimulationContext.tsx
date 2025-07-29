// apps/frontend/src/context/SimulationContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  fetchGrid,
  fetchLogs,
  fetchAgents,
  stepSimulation,
  fetchConditionalMetrics,
  fetchPhaseInfo,
  healthCheck,
  triggerEmergency,
  forceCoordination,
  resetSimulation,
  type ConditionalMetrics,
  type PhaseInfo,
  type HealthStatus,
} from "../lib/api";

interface SimulationContextType {
  // Basic simulation data
  grid: any;
  logs: string[];
  agents: any;
  
  // Enhanced conditional flow data
  conditionalMetrics: ConditionalMetrics | null;
  phaseInfo: PhaseInfo | null;
  healthStatus: HealthStatus | null;
  
  // Actions
  step: () => Promise<void>;
  reset: () => Promise<void>;
  refresh: () => Promise<void>;
  
  // Testing actions for conditional flows
  triggerEmergencyMode: () => Promise<void>;
  forceCoordinationMode: () => Promise<void>;
  
  // State management
  loading: boolean;
  stepping: boolean;
  error: string | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
  lastUpdated: Date | null;
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
  // Basic simulation state
  const [grid, setGrid] = useState(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [agents, setAgents] = useState({});
  
  // Enhanced conditional flow state
  const [conditionalMetrics, setConditionalMetrics] = useState<ConditionalMetrics | null>(null);
  const [phaseInfo, setPhaseInfo] = useState<PhaseInfo | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  
  // Loading and error state
  const [loading, setLoading] = useState(true);
  const [stepping, setStepping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Auto-refresh interval
  const [autoRefresh, setAutoRefresh] = useState<NodeJS.Timeout | null>(null);

  async function loadBasicData() {
    console.log('🔄 Loading basic simulation data...');
    
    const [g, l, a] = await Promise.all([
      fetchGrid(),
      fetchLogs(),
      fetchAgents(),
    ]);
    
    setGrid(g);
    setLogs(l.logs || []);
    setAgents(a);
    
    console.log('✅ Basic data loaded:', { 
      gridSize: g ? `${g.width}x${g.height}` : 'null',
      logsCount: l.logs?.length || 0, 
      agentsCount: Object.keys(a).length,
    });
  }

  async function loadEnhancedData() {
    console.log('🔄 Loading enhanced conditional flow data...');
    
    try {
      const [metrics, phase, health] = await Promise.all([
        fetchConditionalMetrics().catch(e => {
          console.warn('Failed to fetch conditional metrics:', e);
          return null;
        }),
        fetchPhaseInfo().catch(e => {
          console.warn('Failed to fetch phase info:', e);
          return null;
        }),
        healthCheck().catch(e => {
          console.warn('Failed to fetch health status:', e);
          return null;
        }),
      ]);
      
      setConditionalMetrics(metrics);
      setPhaseInfo(phase);
      setHealthStatus(health);
      
      console.log('✅ Enhanced data loaded:', { 
        phase: metrics?.mission_phase,
        coordination: metrics?.coordination_needed,
        emergency: metrics?.active_threats > 0,
        healthStatus: health?.status
      });
      
    } catch (error) {
      console.warn('Failed to load some enhanced data:', error);
    }
  }

  async function loadAllData() {
    try {
      setLoading(true);
      setError(null);
      setConnectionStatus('connecting');
      
      console.log('🔄 Attempting to load all simulation data...');
      
      // Load basic data first
      await loadBasicData();
      
      // Then load enhanced data
      await loadEnhancedData();
      
      setConnectionStatus('connected');
      setError(null);
      setLastUpdated(new Date());
      
      console.log('✅ All simulation data loaded successfully');
      
    } catch (err) {
      console.error('❌ Failed to load simulation data:', err);
      setError(`Failed to connect to backend: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
      
      // Set fallback data
      setGrid(null);
      setLogs(['❌ Failed to connect to backend. Please ensure the backend server is running on http://localhost:8000']);
      setAgents({});
      setConditionalMetrics(null);
      setPhaseInfo(null);
      setHealthStatus(null);
    } finally {
      setLoading(false);
    }
  }

  async function step() {
    try {
      setStepping(true);
      setError(null);
      console.log('⏩ Executing simulation step...');
      
      const result = await stepSimulation();
      
      console.log('📈 Step result received:', {
        stepCount: result.step_count,
        status: result.status,
        phase: result.mission_phase
      });
      
      // Update basic data from step result
      setGrid(result.grid);
      setLogs(result.logs || []);
      setAgents(result.agents || {});
      
      // Load enhanced data after step
      await loadEnhancedData();
      
      setConnectionStatus('connected');
      setLastUpdated(new Date());
      
      console.log('✅ Simulation step completed successfully');
      
    } catch (err) {
      console.error('❌ Failed to step simulation:', err);
      setError(`Failed to step simulation: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setConnectionStatus('disconnected');
    } finally {
      setStepping(false);
    }
  }

  async function reset() {
    try {
      setLoading(true);
      setError(null);
      console.log('🔄 Resetting simulation...');
      
      await resetSimulation();
      
      // Reload all data after reset
      await loadAllData();
      
      console.log('✅ Simulation reset successfully');
      
    } catch (err) {
      console.error('❌ Failed to reset simulation:', err);
      setError(`Failed to reset simulation: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }

  async function refresh() {
    await loadAllData();
  }

  async function triggerEmergencyMode() {
    try {
      console.log('🚨 Triggering emergency mode...');
      await triggerEmergency();
      
      // Refresh enhanced data to see changes
      await loadEnhancedData();
      
      console.log('✅ Emergency mode triggered');
      
    } catch (err) {
      console.error('❌ Failed to trigger emergency:', err);
      setError(`Failed to trigger emergency: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }

  async function forceCoordinationMode() {
    try {
      console.log('🤝 Forcing coordination mode...');
      await forceCoordination();
      
      // Refresh enhanced data to see changes
      await loadEnhancedData();
      
      console.log('✅ Coordination mode forced');
      
    } catch (err) {
      console.error('❌ Failed to force coordination:', err);
      setError(`Failed to force coordination: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }

  useEffect(() => {
    console.log('🚀 SimulationProvider initializing...');
    loadAllData();
    
    // Set up periodic health check and auto-refresh
    const healthCheckInterval = setInterval(async () => {
      if (connectionStatus === 'disconnected') {
        console.log('🔍 Health check: Attempting to reconnect...');
        try {
          const health = await healthCheck();
          if (health) {
            console.log('✅ Health check: Reconnected!');
            setConnectionStatus('connected');
            setError(null);
            await loadAllData();
          }
        } catch {
          console.log('❌ Health check: Still disconnected');
        }
      } else if (connectionStatus === 'connected') {
        // Auto-refresh enhanced data every 30 seconds
        try {
          await loadEnhancedData();
        } catch (error) {
          console.warn('Auto-refresh failed:', error);
        }
      }
    }, 30000); // 30 seconds

    return () => {
      console.log('🛑 SimulationProvider cleanup');
      clearInterval(healthCheckInterval);
      if (autoRefresh) {
        clearInterval(autoRefresh);
      }
    };
  }, []);

  // Log state changes for debugging
  useEffect(() => {
    console.log('📊 State updated:', {
      connectionStatus,
      agentsCount: Object.keys(agents).length,
      logsCount: logs.length,
      hasGrid: !!grid,
      phase: conditionalMetrics?.mission_phase,
      coordination: conditionalMetrics?.coordination_needed,
      emergency: conditionalMetrics?.active_threats > 0,
      loading,
      stepping,
      error: error ? error.substring(0, 100) : null
    });
  }, [connectionStatus, agents, logs, grid, conditionalMetrics, loading, stepping, error]);

  return (
    <SimulationContext.Provider
      value={{ 
        // Basic data
        grid, 
        logs, 
        agents,
        
        // Enhanced data
        conditionalMetrics,
        phaseInfo,
        healthStatus,
        
        // Actions
        step,
        reset,
        refresh,
        triggerEmergencyMode,
        forceCoordinationMode,
        
        // State
        loading,
        stepping,
        error, 
        connectionStatus,
        lastUpdated
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}