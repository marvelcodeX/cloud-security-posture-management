import { beforeEach, describe, expect, it, vi } from "vitest";
  import { fireEvent, screen, waitFor } from "@testing-library/react";
  import userEvent from "@testing-library/user-event";
  import UploadPage from "./UploadPage";
  import { renderWithProviders } from "../test/utils";
  import { uploadScan } from "../api/scans";

  // The upload flow sends multipart FormData; axios + FormData over MSW hangs in
  // jsdom, so here we mock the api function directly and assert the component's
  // UI states. The GET-based tests (Scans/Detail/Dashboard) still exercise the
  // real MSW handlers.
  vi.mock("../api/scans", async (importOriginal) => {
    const actual = await importOriginal<typeof import("../api/scans")>();
    return { ...actual, uploadScan: vi.fn() };
  });

  const mockedUpload = vi.mocked(uploadScan);

  function selectFile(name: string, type = "application/json") {
    const file = new File(["{}"], name, { type });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    return file;
  }

  beforeEach(() => {
    mockedUpload.mockReset();
  });

  describe("UploadPage", () => {
    it("uploads a valid file and shows the result with a link to the scan", async () => {
      mockedUpload.mockResolvedValue({ scan_id: "1", status: "COMPLETED", findings_count: 3 });

      renderWithProviders(<UploadPage />);

      selectFile("config.json");
      await userEvent.click(screen.getByRole("button", { name: /upload & scan/i }));

      expect(await screen.findByText(/upload successful/i)).toBeInTheDocument();
      expect(screen.getByText(/findings:\s*3/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /view scan details/i })).toHaveAttribute(
        "href",
        "/scans/1",
      );
    });

    it("shows the server error detail when the upload is rejected", async () => {
      // Member 1's Axios client rejects with the plain `detail` string.
      mockedUpload.mockRejectedValue("Unsupported file type.");

      renderWithProviders(<UploadPage />);

      selectFile("config.json");
      await userEvent.click(screen.getByRole("button", { name: /upload & scan/i }));

      expect(await screen.findByText(/unsupported file type/i)).toBeInTheDocument();
    });

    it("rejects a disallowed file type client-side before uploading", async () => {
      renderWithProviders(<UploadPage />);

      selectFile("notes.txt", "text/plain");

      await waitFor(() =>
        expect(screen.getByText(/only json and yaml files are allowed/i)).toBeInTheDocument(),
      );
      expect(mockedUpload).not.toHaveBeenCalled();
    });
  });