/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Phase 2 backend, e.g. http://localhost:8000 */
  readonly VITE_API_BASE_URL: string;
  /** "true" starts the MSW mock backend instead of hitting the real API */
  readonly VITE_USE_MOCKS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
