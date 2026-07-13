import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { setupServer } from "msw/node";
import { handlers } from "../mocks/handlers";

// Node-side MSW server built from the SAME handlers Member 1 wrote for the
// browser worker, so tests exercise the exact mock contract the app uses.
// Exported so individual tests can override a handler (e.g. force a 400/404)
// via `server.use(...)`.
export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
