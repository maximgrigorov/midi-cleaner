function flattenConfig(config: Record<string, unknown>): Record<string, string> {
  const flat: Record<string, string> = {};
  for (const [key, value] of Object.entries(config)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      for (const [subKey, subVal] of Object.entries(
        value as Record<string, unknown>
      )) {
        flat[`${key}.${subKey}`] = String(subVal);
      }
    } else if (Array.isArray(value)) {
      flat[key] = value.join(', ');
    } else {
      flat[key] = String(value);
    }
  }
  return flat;
}

interface ComparisonTableProps {
  before: Record<string, unknown>;
  after: Record<string, unknown>;
}

export default function ComparisonTable({
  before,
  after,
}: ComparisonTableProps) {
  const flatBefore = flattenConfig(before);
  const flatAfter = flattenConfig(after);
  const allKeys = [
    ...new Set([...Object.keys(flatBefore), ...Object.keys(flatAfter)]),
  ];

  return (
    <div className="rounded-lg border border-border overflow-hidden animate-fade-in">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-surface-2">
            <th className="text-left px-3 py-2 text-muted-foreground font-medium">
              Parameter
            </th>
            <th className="text-left px-3 py-2 text-muted-foreground font-medium">
              Before
            </th>
            <th className="text-left px-3 py-2 text-muted-foreground font-medium">
              After
            </th>
          </tr>
        </thead>
        <tbody>
          {allKeys.map((key) => {
            const changed = flatBefore[key] !== flatAfter[key];
            return (
              <tr key={key} className="border-t border-border">
                <td className="px-3 py-1.5 font-mono text-muted-foreground">
                  {key}
                </td>
                <td className="px-3 py-1.5">{flatBefore[key] ?? '—'}</td>
                <td
                  className={`px-3 py-1.5 ${changed ? 'text-primary font-medium' : ''}`}
                >
                  {flatAfter[key] ?? '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
