export function MessageLog() {
  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm h-48 overflow-y-auto space-y-2">
      <h2 className="text-xl font-semibold mb-2">Message Log</h2>
      <ul className="text-sm font-mono">
        <li className="text-blue-500">[Scout] Moved north.</li>
        <li className="text-green-600">[Strategist] Suggested building at (2, 3).</li>
        <li className="text-yellow-600">[Builder] Started construction.</li>
      </ul>
    </div>
  );
}
