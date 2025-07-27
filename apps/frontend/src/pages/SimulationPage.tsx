import { GridMap } from "@/components/GridMap";
import { MessageLog } from "@/components/MessageLog";
import { AgentCard } from "@/components/AgentCard";

export function SimulationPage() {
  return (
    <div className="min-h-screen p-4 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="flex flex-col gap-4 h-full">
        <AgentCard agentId="scout" />
        <AgentCard agentId="builder" />
        <AgentCard agentId="strategist" />
      </div>
      <div className="md:col-span-2 flex flex-col gap-4">
        <GridMap />
        <MessageLog />
      </div>
    </div>
  );
}
