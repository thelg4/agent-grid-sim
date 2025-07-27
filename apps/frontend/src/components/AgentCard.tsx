// import {
//   Card,
//   CardHeader,
//   CardTitle,
//   CardContent,
// } from "@/components/ui/card";

// interface AgentCardProps {
//   agentId: string;
// }

// const colorMap: Record<string, string> = {
//   scout: "bg-blue-500",
//   builder: "bg-yellow-500",
//   strategist: "bg-green-500",
// };

// export function AgentCard({ agentId }: AgentCardProps) {
//   const color = colorMap[agentId] ?? "bg-gray-400";

//   return (
//     <Card className="mb-4">
//       <CardHeader className="flex flex-row items-center justify-between">
//         <CardTitle className="capitalize flex items-center justify-between gap-2">
//           {agentId} Agent
//           <span className={`w-2 h-2 rounded-full ${color}`} />
//         </CardTitle>
//       </CardHeader>
//       <CardContent className="text-sm space-y-1">
//         <p>
//           <strong>Role:</strong> {agentId}
//         </p>
//         <p>
//           <strong>Status:</strong> Idle
//         </p>
//         <p>
//           <strong>Memory:</strong> Empty
//         </p>
//       </CardContent>
//     </Card>
//   );
// }

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";

interface AgentCardProps {
  agentId: string;
  agentData?: {
    id: string;
    role: string;
    status: string;
    memory: string[];
    position?: [number, number];
  };
}

const colorMap: Record<string, string> = {
  scout: "bg-blue-500",
  builder: "bg-yellow-500",
  strategist: "bg-green-500",
};

const iconMap: Record<string, string> = {
  scout: "👀",
  builder: "🔨", 
  strategist: "🧠",
};

export function AgentCard({ agentId, agentData }: AgentCardProps) {
  const color = colorMap[agentId] ?? "bg-gray-400";
  const icon = iconMap[agentId] ?? "🤖";

  return (
    <Card className="mb-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="capitalize flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          {agentId} Agent
          <span className={`w-2 h-2 rounded-full ${color}`} />
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-2">
        <div>
          <strong>Role:</strong> {agentData?.role || agentId}
        </div>
        <div>
          <strong>Status:</strong> 
          <span className="ml-1 px-2 py-1 rounded text-xs bg-muted">
            {agentData?.status || "Idle"}
          </span>
        </div>
        {agentData?.position && (
          <div>
            <strong>Position:</strong> ({agentData.position[0]}, {agentData.position[1]})
          </div>
        )}
        <div>
          <strong>Recent Memory:</strong>
          {agentData?.memory && agentData.memory.length > 0 ? (
            <ul className="mt-1 text-xs space-y-1 max-h-20 overflow-y-auto">
              {agentData.memory.slice(-3).map((mem, idx) => (
                <li key={idx} className="text-muted-foreground truncate">
                  • {mem}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-xs mt-1">No recent activity</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}