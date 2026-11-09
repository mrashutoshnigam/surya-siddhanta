import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Bind every interface (IPv4 0.0.0.0 + IPv6) so the app is reachable at
    // both http://localhost:5173 and http://127.0.0.1:5173. Vite's default
    // binds IPv6 ::1 only, which refuses IPv4 127.0.0.1 and reads as "app down".
    host: true,
    port: 5173,
    // Fail loudly if 5173 is taken instead of silently cascading to 5174/5175,
    // which leaves the app at an unexpected URL.
    strictPort: true,
    proxy: {
      "/api": {
        // Explicit IPv4 to match uvicorn's default 127.0.0.1 bind and avoid
        // localhost resolving to ::1 where the API is not listening.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
