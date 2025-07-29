const API_BASE = "http://localhost:8000/api";

async function apiCall(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  console.log(`🌐 API Call: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    console.log(`📡 Response: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ API Error: ${response.status} - ${errorText}`);
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`📦 Response data:`, data);
    
    return data;
  } catch (error) {
    console.error(`❌ API Call Failed:`, error);
    throw error;
  }
}

// Basic simulation endpoints
export async function fetchGrid() {
  return apiCall('/grid');
}

export async function fetchLogs() {
  return apiCall('/logs');
}

export async function fetchAgents() {
  return apiCall('/agents');
}

export async function stepSimulation() {
  return apiCall('/step', {
    method: 'POST'
  });
}

// Enhanced conditional flow endpoints
export async function fetchConditionalMetrics() {
  return apiCall('/conditional-metrics');
}

export async function fetchPhaseInfo() {
  return apiCall('/phase-info');
}

// Testing endpoints for conditional flows
export async function triggerEmergency() {
  return apiCall('/trigger-emergency', {
    method: 'POST'
  });
}

export async function forceCoordination() {
  return apiCall('/force-coordination', {
    method: 'POST'
  });
}

// Debug and monitoring endpoints
export async function fetchDebugInfo() {
  return apiCall('/debug');
}

export async function fetchGridRaw() {
  return apiCall('/grid-raw');
}

export async function resetSimulation() {
  return apiCall('/reset', {
    method: 'POST'
  });
}

// Health check function
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE.replace('/api', '')}/api/health`);
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
}

// Additional utility functions for the enhanced backend
export async function fetchServerStatus() {
  try {
    const response = await fetch(`${API_BASE.replace('/api', '')}/`);
    return await response.json();
  } catch (error) {
    console.error('Server status check failed:', error);
    throw error;
  }
}

// Types for the enhanced backend responses
export interface ConditionalMetrics {
  mission_phase: string;
  phase_transitions: number;
  coordination_events: number;
  emergency_activations: number;
  last_activity: Record<string, string>;
  coordination_needed: boolean;
  strategic_plan_ready: boolean;
  active_threats: number;
  resource_constraints: boolean;
}

export interface PhaseInfo {
  current_phase: string;
  step_count: number;
  current_objectives: string[];
  exploration_progress: number;
  buildings_built: number;
  coordination_needed: boolean;
  emergency_mode: boolean;
  strategic_plan_ready: boolean;
  phase_transitions: Array<{
    step: number;
    from: string;
    to: string;
  }>;
  coordination_events: Array<{
    step: number;
    type: string;
  }>;
  targets: {
    exploration_target: number;
    building_target: number;
    max_steps: number;
  };
}

export interface HealthStatus {
  status: string;
  simulation: string;
  agents: number;
  grid_size: string;
  mission_phase: string;
  coordination_active: boolean;
  emergency_mode: boolean;
  openai_configured: boolean;
  conditional_flows: string;
}

export interface ServerInfo {
  message: string;
  version: string;
  status: string;
  simulation_initialized: boolean;
  features: string[];
  endpoints: string[];
}