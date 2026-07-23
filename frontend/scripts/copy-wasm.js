// Copies MediaPipe Tasks Vision WASM files to public/ so they can be self-hosted.
// Runs automatically after npm install via the postinstall hook.
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const src = path.resolve(__dirname, "../node_modules/@mediapipe/tasks-vision/wasm");
const dest = path.resolve(__dirname, "../public/mediapipe/wasm");

if (!fs.existsSync(src)) {
  console.warn("[copy-wasm] @mediapipe/tasks-vision wasm folder not found, skipping.");
  process.exit(0);
}

fs.mkdirSync(dest, { recursive: true });

for (const file of fs.readdirSync(src)) {
  fs.copyFileSync(path.join(src, file), path.join(dest, file));
}

console.log("[copy-wasm] MediaPipe WASM files copied to public/mediapipe/wasm/");
