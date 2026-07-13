import Badge from "../components/ui/Badge";
import type { Severity } from "../api/types";

/**
 * Member 3 — SeverityBadge
 *
 * Member 1's `Badge` component already takes a `severity` prop and colors
 * itself (Critical→red, High→orange, Medium→yellow, Low→gray), so this is a
 * thin, named wrapper around it. Kept as its own component (rather than
 * using Badge directly everywhere) so Member 4's charts, and anyone else,
 * import a stable, semantically-named piece — if the underlying color
 * component ever changes, only this file needs to change.
 */
export default function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge severity={severity} />;
}
