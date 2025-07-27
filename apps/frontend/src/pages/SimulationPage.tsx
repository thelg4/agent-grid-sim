// import { GridMap } from "@/components/GridMap";
// import { MessageLog } from "@/components/MessageLog";
// import { AgentCard } from "@/components/AgentCard";

// export function SimulationPage() {
//   return (
//     <div className="min-h-screen p-4 grid grid-cols-1 md:grid-cols-3 gap-6">
//       <div className="flex flex-col gap-4 h-full">
//         <AgentCard agentId="scout" />
//         <AgentCard agentId="builder" />
//         <AgentCard agentId="strategist" />
//       </div>
//       <div className="md:col-span-2 flex flex-col gap-4">
//         <GridMap />
//         <MessageLog />
//       </div>
//     </div>
//   );
// }

import { useSimulation } from "../context/SimulationContext";
import { AgentCard } from "../components/AgentCard";
import { GridMap } from "../components/GridMap";
import { MessageLog } from "../components/MessageLog";
import { Button } from "@/components/ui/button";

export function SimulationPage() {
  const { agents, step, logs } = useSimulation();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 min-h-screen">
      <div className="md:col-span-2 space-y-4">
        <GridMap />
        <MessageLog logs={logs} />
        <Button onClick={step}>Step Simulation</Button>
      </div>
      <div className="flex flex-col space-y-4">
        {Object.keys(agents).map((agentId) => (
          <AgentCard key={agentId} agentId={agentId} />
        ))}
      </div>
    </div>
  );
}
