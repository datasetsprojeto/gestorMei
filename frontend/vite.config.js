import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  server: {
    host: true,
    port: 5501,
  },
  preview: {
    host: true,
    port: 5501,
  },
});
