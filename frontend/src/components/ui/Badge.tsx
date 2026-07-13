type Severity = "Low" | "Medium" | "High" | "Critical";

type BadgeProps = {
  severity: Severity;
};

const colors = {
  Low: "bg-gray-500",
  Medium: "bg-yellow-500",
  High: "bg-orange-500",
  Critical: "bg-red-600",
};

export default function Badge({ severity }: BadgeProps) {
  return (
    <span
      className={`px-2 py-1 rounded text-white text-sm ${colors[severity]}`}
    >
      {severity}
    </span>
  );
}