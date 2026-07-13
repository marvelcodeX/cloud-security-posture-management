import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listScans } from "../api/scans";
import Card from "../components/ui/Card";
import Spinner from "../components/ui/Spinner";

/**
 * Member 3 — ScansPage
 *
 * Fetches listScans(), renders a table (filename, type, status, timestamp)
 * newest first, each row links to its detail page. Handles loading / empty
 * / error states.
 *
 * Note: Member 1's api client rejects with a plain string (not an object),
 * so `error` below is used directly as the message.
 */
export default function ScansPage() {
  const {
    data: scans,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["scans"],
    queryFn: listScans,
  });

  if (isLoading) {
    return (
      <Card>
        <Spinner />
      </Card>
    );
  }

  if (isError) {
    const message = typeof error === "string" ? error : "Failed to load scans.";
    return (
      <Card>
        <p className="text-red-700">{message}</p>
      </Card>
    );
  }

  if (!scans || scans.length === 0) {
    return (
      <Card>
        <p className="text-sm text-gray-500">
          No scans yet. Upload a config to run your first scan.
        </p>
      </Card>
    );
  }

  const sorted = [...scans].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  return (
    <Card>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="py-2 pr-4">Filename</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((scan) => (
            <tr key={scan.scan_id} className="border-b hover:bg-gray-50">
              <td className="py-2 pr-4">
                <Link
                  to={`/scans/${scan.scan_id}`}
                  className="text-blue-600 hover:underline"
                >
                  {scan.filename}
                </Link>
              </td>
              <td className="py-2 pr-4">{scan.scan_type}</td>
              <td className="py-2 pr-4">{scan.status}</td>
              <td className="py-2 pr-4">
                {new Date(scan.timestamp).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
