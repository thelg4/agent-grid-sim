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

export async function fetchDebugInfo() {
  return apiCall('/debug');
}

export async function fetchGridRaw() {
  return apiCall('/grid-raw');
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