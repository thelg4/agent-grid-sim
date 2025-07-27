import { createContext, useContext, useEffect, useState } from "react";
import {
  fetchGrid,
  fetchLogs,
  fetchAgents,
  stepSimulation,
} from "../lib/api";

const SimulationContext = createContext(null);

export function useSimulation() {
  return useContext(SimulationContext);
}

export function SimulationProvider({ children }) {
  const [grid, setGrid] = useState(null);
  const [logs, setLogs] = useState([]);
  const [agents, setAgents] = useState({});

  async function loadData() {
    const [g, l, a] = await Promise.all([
      fetchGrid(),
      fetchLogs(),
      fetchAgents(),
    ]);
    setGrid(g);
    setLogs(l.logs);
    setAgents(a);
  }

  async function step() {
    const result = await stepSimulation();
    setGrid(result.grid);
    setLogs(result.logs);
    setAgents(result.agents);
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <SimulationContext.Provider
      value={{ grid, logs, agents, step }}
    >
      {children}
    </SimulationContext.Provider>
  );
}
