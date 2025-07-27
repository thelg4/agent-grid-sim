import { useEffect, useRef } from "react";

interface MessageLogProps {
  logs: string[];
}

export function MessageLog({ logs }: MessageLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const getMessageStyle = (log: string) => {
    if (log.includes("[Scout]") || log.includes("Scout")) {
      return "text-blue-500";
    } else if (log.includes("[Builder]") || log.includes("Builder")) {
      return "text-yellow-600";
    } else if (log.includes("[Strategist]") || log.includes("Strategist")) {
      return "text-green-600";
    } else if (log.includes("[ERROR]")) {
      return "text-red-500 font-semibold";
    } else if (log.includes("[Step")) {
      return "text-purple-500";
    }
    return "text-muted-foreground";
  };

  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm h-64 overflow-y-auto space-y-2">
      <h2 className="text-xl font-semibold mb-2 sticky top-0 bg-background">
        Message Log ({logs.length})
      </h2>
      
      {logs.length === 0 ? (
        <p className="text-muted-foreground italic">No messages yet. Click "Step Simulation" to start.</p>
      ) : (
        <ul className="text-sm font-mono space-y-1">
          {logs.map((log, index) => (
            <li 
              key={index} 
              className={getMessageStyle(log)}
            >
              {log}
            </li>
          ))}
        </ul>
      )}
      
      <div ref={logEndRef} />
    </div>
  );
}