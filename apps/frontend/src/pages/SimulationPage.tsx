import { GridMap } from "@/components/GridMap";
import { MessageLog } from "@/components/MessageLog";
import { AgentCard } from "@/components/AgentCard";

export function SimulationPage() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <GridMap />
        <MessageLog />
      </div>
      <div>
        <AgentCard agentId="scout" />
        <AgentCard agentId="builder" />
        <AgentCard agentId="strategist" />
      </div>
    </div>
  );
}