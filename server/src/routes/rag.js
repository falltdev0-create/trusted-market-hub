import { Router } from "express";
import { db, uid, json } from "../db.js";
import { requireAuth } from "../auth.js";
import { ai } from "../ai.js";

export const router = Router();

const CHUNK = 700;

function chunkText(text) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  const out = [];
  for (let i = 0; i < clean.length; i += CHUNK) out.push(clean.slice(i, i + CHUNK));
  return out.length ? out : [""];
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

async function embedAll(texts) {
  const r = await ai.embed(texts);
  if (r?.ok && Array.isArray(r.embeddings)) return r.embeddings;
  // بديل خفيف: تمثيل حقيبة أحرف (hashing) عند غياب بايثون
  return texts.map((t) => {
    const v = new Array(256).fill(0);
    for (const ch of String(t)) v[ch.charCodeAt(0) % 256] += 1;
    const n = Math.sqrt(v.reduce((s, x) => s + x * x, 0)) || 1;
    return v.map((x) => x / n);
  });
}

router.get("/status", async (_req, res) => {
  const count = db.prepare("SELECT COUNT(*) c FROM rag_documents").get().c;
  const sources = db.prepare("SELECT source, COUNT(*) c FROM rag_documents GROUP BY source").all();
  const health = await ai.health();
  res.json({ documents: count, sources, ai: health, ready: count > 0 });
});

router.post("/index", requireAuth, async (req, res) => {
  const { source = "manual", source_id = null, title = null, content } = req.body || {};
  if (!content) return res.status(422).json({ detail: "المحتوى مطلوب" });
  const chunks = chunkText(content);
  const embeddings = await embedAll(chunks);
  const stmt = db.prepare(
    "INSERT INTO rag_documents (id, source, source_id, title, chunk_index, content, embedding) VALUES (?,?,?,?,?,?,?)",
  );
  chunks.forEach((c, i) => stmt.run(uid(), source, source_id, title, i, c, JSON.stringify(embeddings[i])));
  res.status(201).json({ indexed: chunks.length });
});

router.post("/index/listings", requireAuth, async (_req, res) => {
  const rows = db.prepare("SELECT * FROM listings WHERE status = 'published'").all();
  db.prepare("DELETE FROM rag_documents WHERE source = 'listing'").run();
  let indexed = 0;
  const stmt = db.prepare(
    "INSERT INTO rag_documents (id, source, source_id, title, chunk_index, content, embedding, metadata) VALUES (?,?,?,?,?,?,?,?)",
  );
  for (const l of rows) {
    const text = [
      l.title, l.description, l.city, l.district, l.brand, l.model,
      l.price ? `السعر ${l.price} ${l.currency}` : null,
      l.price_tier ? `تصنيف السعر ${l.price_tier}` : null,
      l.condition_grade ? `حالة السلعة ${l.condition_grade}` : null,
    ].filter(Boolean).join(" — ");
    const chunks = chunkText(text);
    const embeddings = await embedAll(chunks);
    chunks.forEach((c, i) =>
      stmt.run(uid(), "listing", l.id, l.title, i, c, JSON.stringify(embeddings[i]), JSON.stringify({ price: l.price, city: l.city })),
    );
    indexed += chunks.length;
  }
  res.json({ listings: rows.length, indexed });
});

async function retrieve(query, topK = 5, source) {
  const [qv] = await embedAll([query]);
  const rows = source
    ? db.prepare("SELECT * FROM rag_documents WHERE source = ?").all(source)
    : db.prepare("SELECT * FROM rag_documents").all();
  return rows
    .map((r) => ({
      id: r.id,
      source: r.source,
      source_id: r.source_id,
      title: r.title,
      content: r.content,
      metadata: json(r.metadata, {}),
      score: cosine(qv, json(r.embedding, [])),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

router.post("/search", async (req, res) => {
  const { query, top_k = 5, source } = req.body || {};
  if (!query) return res.status(422).json({ detail: "أدخل نص البحث" });
  res.json({ query, results: await retrieve(query, Number(top_k), source) });
});

router.post("/ask", async (req, res) => {
  const { question, top_k = 5, source } = req.body || {};
  if (!question) return res.status(422).json({ detail: "أدخل سؤالك" });
  const results = await retrieve(question, Number(top_k), source);
  const gen = await ai.generate(question, results.map((r) => r.content));
  const answer =
    gen?.ok && gen.answer
      ? gen.answer
      : results.length
        ? `استناداً إلى البيانات المتاحة:\n\n${results.slice(0, 3).map((r, i) => `${i + 1}) ${r.content}`).join("\n")}`
        : "لا توجد بيانات مفهرسة كافية للإجابة. جرّب فهرسة الإعلانات أولاً.";
  res.json({ question, answer, sources: results });
});

router.delete("/documents/:id", requireAuth, (req, res) => {
  db.prepare("DELETE FROM rag_documents WHERE id = ? OR source_id = ?").run(req.params.id, req.params.id);
  res.json({ deleted: req.params.id });
});
