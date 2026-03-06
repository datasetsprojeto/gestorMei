import { cp, mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const distDir = resolve(root, "dist");

async function main() {
  await rm(distDir, { recursive: true, force: true });
  await mkdir(distDir, { recursive: true });

  await cp(resolve(root, "index.html"), resolve(distDir, "index.html"));
  await cp(resolve(root, "css"), resolve(distDir, "css"), { recursive: true });
  await cp(resolve(root, "js"), resolve(distDir, "js"), { recursive: true });

  console.log("Static frontend build completed in dist/");
}

main().catch((error) => {
  console.error("Static frontend build failed:", error);
  process.exit(1);
});
