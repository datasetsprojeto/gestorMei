import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        chunkFileNames: "assets/chunks/[name]-[hash].js",
        entryFileNames: "assets/entry/[name]-[hash].js",
        assetFileNames: "assets/static/[name]-[hash][extname]",
        manualChunks(id) {
          if (id.includes("node_modules")) return "vendor";
          if (id.includes("/js/modules/")) return "app-modules";
          return undefined;
        },
      },
    },
  },
  server: {
    host: true,
    port: 5501,
  },
  preview: {
    host: true,
    port: 5501,
  },
});
