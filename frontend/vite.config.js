import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api to Flask so the session cookie stays same-origin (no CORS setup needed).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:5000" } },
});
