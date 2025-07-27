export function MessageLog() {
  return (
    <div className="border rounded-md p-4 bg-background mb-4 h-48 overflow-y-auto">
      <h2 className="font-semibold text-lg mb-2">Message Log</h2>
      <ul className="text-sm space-y-1">
        <li>[Scout] Moved north.</li>
        <li>[Strategist] Suggested building at (2, 3).</li>
        <li>[Builder] Started construction.</li>
      </ul>
    </div>
  );
}
