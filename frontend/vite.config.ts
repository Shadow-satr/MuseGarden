import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, ".", "");
  const gardenApiPort = environment.MUSEGARDEN_API_PORT ?? "8000";
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": `http://127.0.0.1:${gardenApiPort}`,
      },
    },
    test: {
      environment: "node",
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
