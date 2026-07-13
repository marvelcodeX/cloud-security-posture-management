import { useMemo, useState } from "react";
import type { Finding, Severity } from "../api/types";
import SeverityBadge from "./SeverityBadge";

/**
 * Member 3 — FindingsTable
 *
 * Renders a scan's findings with columns for resource, type, severity, rule,
 * and message. Supports sorting by severity and filtering by severity.
 * risk_score renders as "—" until Phase 5 populates it (it's nullable in the
 * shared types). is_anomaly is a plain boolean per Member 1's types.
 */

const SEVERITY_ORDER: Record<Severity, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
};

const ALL_SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];

type SortDirection = "asc" | "desc";

export default function FindingsTable({ findings }: { findings: Finding[] }) {
  const [severityFilter, setSeverityFilter] = useState<Severity | "All">("All");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const visibleFindings = useMemo(() => {
    const filtered =
      severityFilter === "All"
        ? findings
        : findings.filter((f) => f.severity === severityFilter);

    return [...filtered].sort((a, b) => {
      const diff = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
      return sortDirection === "asc" ? diff : -diff;
    });
  }, [findings, severityFilter, sortDirection]);

  function toggleSort() {
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
  }

  if (findings.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No findings for this scan — nothing to show.
      </p>
    );
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-sm">
        <label htmlFor="severity-filter" className="text-gray-600">
          Filter by severity:
        </label>
        <select
          id="severity-filter"
          className="rounded border px-2 py-1"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as Severity | "All")}
        >
          <option value="All">All</option>
          {ALL_SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="py-2 pr-4">Resource</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">
              <button
                type="button"
                onClick={toggleSort}
                className="flex items-center gap-1 font-medium hover:text-gray-900"
              >
                Severity {sortDirection === "asc" ? "↑" : "↓"}
              </button>
            </th>
            <th className="py-2 pr-4">Rule</th>
            <th className="py-2 pr-4">Message</th>
            <th className="py-2 pr-4">Risk score</th>
            <th className="py-2 pr-4">Anomaly</th>
          </tr>
        </thead>
        <tbody>
          {visibleFindings.map((finding) => (
            <tr key={`${finding.resource_id}-${finding.rule_id}`} className="border-b">
              <td className="py-2 pr-4 font-mono text-xs">{finding.resource_id}</td>
              <td className="py-2 pr-4">{finding.resource_type}</td>
              <td className="py-2 pr-4">
                <SeverityBadge severity={finding.severity} />
              </td>
              <td className="py-2 pr-4">{finding.rule_id}</td>
              <td className="py-2 pr-4">{finding.message}</td>
              <td className="py-2 pr-4">{finding.risk_score ?? "—"}</td>
              <td className="py-2 pr-4">{finding.is_anomaly ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
