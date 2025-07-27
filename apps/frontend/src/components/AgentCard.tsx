import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";

interface AgentCardProps {
  agentId: string;
}

const colorMap: Record<string, string> = {
  scout: "bg-blue-500",
  builder: "bg-yellow-500",
  strategist: "bg-green-500",
};

export function AgentCard({ agentId }: AgentCardProps) {
  const color = colorMap[agentId] ?? "bg-gray-400";

  return (
    <Card className="mb-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="capitalize flex items-center justify-between gap-2">
          {agentId} Agent
          <span className={`w-2 h-2 rounded-full ${color}`} />
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-1">
        <p>
          <strong>Role:</strong> {agentId}
        </p>
        <p>
          <strong>Status:</strong> Idle
        </p>
        <p>
          <strong>Memory:</strong> Empty
        </p>
      </CardContent>
    </Card>
  );
}
