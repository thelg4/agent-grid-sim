import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AgentCardProps {
  agentId: string;
}

export function AgentCard({ agentId }: AgentCardProps) {
  return (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle className="capitalize">{agentId} Agent</CardTitle>
      </CardHeader>
      <CardContent className="text-sm">
        <p><strong>Role:</strong> {agentId}</p>
        <p><strong>Status:</strong> Idle</p>
        <p><strong>Memory:</strong> Empty</p>
      </CardContent>
    </Card>
  );
}
