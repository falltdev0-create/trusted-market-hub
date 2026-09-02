import "dotenv/config";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(__dirname, "..");
export const REPO_ROOT = path.resolve(ROOT, "..");

const abs = (p, base = ROOT) => (path.isAbsolute(p) ? p : path.resolve(base, p));

export const config = {
  port: Number(process.env.PORT || 8000),
  publicBaseUrl: process.env.PUBLIC_BASE_URL || "http://localhost:8000",
  allowedOrigins: (process.env.ALLOWED_ORIGINS || "http://localhost:8080,http://localhost:5173")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
  databaseFile: abs(process.env.DATABASE_FILE || "./data/moamalati.db"),
  storageDir: abs(process.env.STORAGE_DIR || "./storage"),
  jwtSecret: process.env.JWT_SECRET || "dev-secret-change-me",
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || "7d",
  pythonBin: process.env.PYTHON_BIN || "python",
  aiBridge: abs(process.env.AI_BRIDGE || "../ai_models/bridge.py"),
  aiTimeoutMs: Number(process.env.AI_TIMEOUT_MS || 120000),
  conditionModel: process.env.CONDITION_MODEL || "mobilenet_v3_small",
  embedModel: process.env.EMBED_MODEL || "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
};
