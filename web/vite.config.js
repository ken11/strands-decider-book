import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api へのリクエストは、Python の API サーバ（server.py）に転送する
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
