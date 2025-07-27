const API_BASE = "http://localhost:8000/api"; // adjust if needed

export async function fetchGrid() {
  const res = await fetch(`${API_BASE}/grid`);
  return res.json();
}

export async function fetchLogs() {
  const res = await fetch(`${API_BASE}/logs`);
  return res.json();
}

export async function fetchAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  return res.json();
}

export async function stepSimulation() {
  const res = await fetch(`${API_BASE}/step`, {
    method: "POST"
  });
  return res.json();
}
