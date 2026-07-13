import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import DashboardPage from "./DashboardPage";
import { renderWithProviders } from "../../test/utils";
import { server } from "../../test/setup";

describe("DashboardPage", () => {
  it("aggregates findings from the mock data into the charts", async () => {
    renderWithProviders(<DashboardPage />);

    // Mock data: scan 1 has 3 findings, scan 2 has 1 -> 4 across 2 scans.
    expect(await screen.findByText(/4 findings across 2 scans/i)).toBeInTheDocument();

    expect(screen.getByText("Findings by severity")).toBeInTheDocument();
    expect(screen.getByText("Findings by resource type")).toBeInTheDocument();

    // Severity summary derived from the findings (Critical/High/Medium once each).
    expect(screen.getByText("Critical: 1")).toBeInTheDocument();
    expect(screen.getByText("High: 1")).toBeInTheDocument();
    expect(screen.getByText("Low: 1")).toBeInTheDocument();
  });

  it("shows an empty state when there are no scans", async () => {
    server.use(http.get("*/scans", () => HttpResponse.json([])));

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/nothing to show yet/i)).toBeInTheDocument();
  });
});
