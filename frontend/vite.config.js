import { defineConfig } from "vite";

// Dev-server setting only. The page itself calls relative /api paths.
const backend = "http://localhost:8000";

// "/api/" so the proxy does not swallow the module frontend/api.js.
const apiProxy = {
  "/api/": {
    target: backend,
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
});
