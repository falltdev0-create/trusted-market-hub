/**
 * جسر الذكاء الاصطناعي — Node ⇄ Python
 * يستدعي ai_models/bridge.py كعملية فرعية ويتبادل JSON عبر stdin/stdout.
 * كل النماذج خفيفة على المعالج (MobileNetV3-Small / MiniLM / heuristics).
 */
import { spawn } from "node:child_process";
import { config } from "./config.js";

export function runAI(task, payload = {}) {
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(config.pythonBin, [config.aiBridge], {
        cwd: config.aiBridge.replace(/[\\/][^\\/]+$/, ""),
        env: {
          ...process.env,
          CONDITION_MODEL: config.conditionModel,
          EMBED_MODEL: config.embedModel,
        },
      });
    } catch (e) {
      return resolve({ ok: false, error: `python spawn failed: ${e.message}` });
    }

    let out = "";
    let err = "";
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      resolve({ ok: false, error: "AI timeout" });
    }, config.aiTimeoutMs);

    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (err += d.toString()));
    child.on("error", (e) => {
      clearTimeout(timer);
      resolve({ ok: false, error: `python not available: ${e.message}` });
    });
    child.on("close", () => {
      clearTimeout(timer);
      try {
        const line = out.trim().split("\n").filter(Boolean).pop();
        resolve(JSON.parse(line));
      } catch {
        resolve({ ok: false, error: err.trim().slice(-500) || "invalid AI response" });
      }
    });

    child.stdin.write(JSON.stringify({ task, ...payload }));
    child.stdin.end();
  });
}

export const ai = {
  health: () => runAI("health"),
  assessCondition: (imagePaths, category) =>
    runAI("condition", { images: imagePaths, category }),
  matchDocuments: (idDoc, ownershipDoc, category) =>
    runAI("documents", { id_doc: idDoc, ownership_doc: ownershipDoc, category }),
  estimatePrice: (data) => runAI("pricing", data),
  embed: (texts) => runAI("embed", { texts }),
  generate: (question, contexts) => runAI("generate", { question, contexts }),
};

/** تصنيف السعر مقارنة بالسعر المقترح — لا سقف إلزامي */
export function computeTier(price, suggested) {
  if (!price || !suggested) return "medium";
  const ratio = price / suggested;
  if (ratio <= 0.85) return "cheap";
  if (ratio >= 1.15) return "expensive";
  return "medium";
}
