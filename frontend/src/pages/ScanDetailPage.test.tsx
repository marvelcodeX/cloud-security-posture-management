import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import ScanDetailPage from "./ScanDetailPage";
import { renderWithProviders } from "../test/utils";

function renderAt(route: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/scans/:id" element={<ScanDetailPage />} />
    </Routes>,
    { route },
  );
}

describe("ScanDetailPage", () => {
  it("renders the scan header and its findings", async () => {
    renderAt("/scans/1");

    expect(await screen.findByText("prod-aws-config.json")).toBeInTheDocument();
    expect(
      screen.getByText("Disable public read access on the S3 bucket."),
    ).toBeInTheDocument();
    expect(screen.getByText("aws_s3_bucket.public_assets")).toBeInTheDocument();
  });

  it("shows a friendly not-found view for an unknown scan (404)", async () => {
    renderAt("/scans/does-not-exist");

    expect(await screen.findByText(/scan not found/i)).toBeInTheDocument();
  });
});
