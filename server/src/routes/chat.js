import { Router } from "express";
import { db, uid } from "../db.js";
import { requireAuth, publicUser } from "../auth.js";

export const router = Router();

/** فلترة معلومات التواصل لحماية الوساطة */
const PATTERNS = [
  /(\+?\d[\d\s\-()]{7,}\d)/g,
  /[\w.+-]+@[\w-]+\.[\w.]+/g,
  /(?:https?:\/\/|www\.)\S+/gi,
  /\b(واتساب|whatsapp|تلجرام|telegram|فيسبوك|facebook|انستقرام|instagram)\b/gi,
];

export function filterContacts(text) {
  let filtered = false;
  let out = String(text || "");
  for (const p of PATTERNS) {
    out = out.replace(p, () => {
      filtered = true;
      return "•••";
    });
  }
  return { body: out, filtered };
}

function convoOf(id, user) {
  const c = db.prepare("SELECT * FROM conversations WHERE id = ?").get(id);
  if (!c) return { error: [404, "المحادثة غير موجودة"] };
  if (c.buyer_id !== user.id && c.seller_id !== user.id)
    return { error: [403, "لا تملك صلاحية هذه المحادثة"] };
  return { c };
}

function hydrate(c, meId) {
  const other = db.prepare("SELECT * FROM users WHERE id = ?").get(c.buyer_id === meId ? c.seller_id : c.buyer_id);
  const listing = db.prepare("SELECT id, title, price, price_tier FROM listings WHERE id = ?").get(c.listing_id);
  const last = db
    .prepare("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 1")
    .get(c.id);
  const unread = db
    .prepare("SELECT COUNT(*) c FROM messages WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL")
    .get(c.id, meId).c;
  const image = listing
    ? db.prepare("SELECT url FROM listing_images WHERE listing_id = ? ORDER BY sort_order LIMIT 1").get(listing.id)?.url
    : null;
  return { ...c, other_user: publicUser(other), listing: listing ? { ...listing, image } : null, last_message: last || null, unread };
}

router.get("/conversations", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM conversations WHERE buyer_id = ? OR seller_id = ? ORDER BY updated_at DESC")
    .all(req.user.id, req.user.id);
  res.json({ items: rows.map((c) => hydrate(c, req.user.id)) });
});

/** بدء/فتح محادثة حول إعلان */
router.post("/conversations", requireAuth, (req, res) => {
  const listingId = req.body?.listing_id;
  const listing = db.prepare("SELECT * FROM listings WHERE id = ?").get(listingId);
  if (!listing) return res.status(404).json({ detail: "الإعلان غير موجود" });
  if (listing.owner_id === req.user.id)
    return res.status(422).json({ detail: "لا يمكنك بدء محادثة مع إعلانك" });

  let c = db
    .prepare("SELECT * FROM conversations WHERE listing_id = ? AND buyer_id = ?")
    .get(listing.id, req.user.id);
  if (!c) {
    const id = uid();
    db.prepare("INSERT INTO conversations (id, listing_id, buyer_id, seller_id) VALUES (?,?,?,?)").run(
      id, listing.id, req.user.id, listing.owner_id,
    );
    db.prepare("INSERT INTO notifications (id, user_id, title, body, type, link) VALUES (?,?,?,?,?,?)").run(
      uid(), listing.owner_id, "محادثة جديدة", `مشترٍ مهتم بإعلانك: ${listing.title || ""}`, "chat", `/chat/${id}`,
    );
    c = db.prepare("SELECT * FROM conversations WHERE id = ?").get(id);
  }
  res.status(201).json(hydrate(c, req.user.id));
});

router.get("/conversations/:id", requireAuth, (req, res) => {
  const { c, error } = convoOf(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  res.json(hydrate(c, req.user.id));
});

router.get("/conversations/:id/messages", requireAuth, (req, res) => {
  const { c, error } = convoOf(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const items = db.prepare("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at").all(c.id);
  db.prepare(
    "UPDATE messages SET read_at = datetime('now') WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL",
  ).run(c.id, req.user.id);
  res.json({ items });
});

export function createMessage(conversationId, senderId, text) {
  const { body, filtered } = filterContacts(text);
  const id = uid();
  db.prepare(
    "INSERT INTO messages (id, conversation_id, sender_id, body, filtered) VALUES (?,?,?,?,?)",
  ).run(id, conversationId, senderId, body, filtered ? 1 : 0);
  db.prepare("UPDATE conversations SET updated_at = datetime('now') WHERE id = ?").run(conversationId);
  const c = db.prepare("SELECT * FROM conversations WHERE id = ?").get(conversationId);
  const target = c.buyer_id === senderId ? c.seller_id : c.buyer_id;
  db.prepare("INSERT INTO notifications (id, user_id, title, body, type, link) VALUES (?,?,?,?,?,?)").run(
    uid(), target, "رسالة جديدة", body.slice(0, 80), "chat", `/chat/${conversationId}`,
  );
  return db.prepare("SELECT * FROM messages WHERE id = ?").get(id);
}

router.post("/conversations/:id/messages", requireAuth, (req, res) => {
  const { c, error } = convoOf(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const text = req.body?.body || req.body?.message || "";
  if (!String(text).trim()) return res.status(422).json({ detail: "الرسالة فارغة" });
  const msg = createMessage(c.id, req.user.id, text);
  broadcast(c.id, { type: "message", message: msg });
  res.status(201).json(msg);
});

/* ---------------- WebSocket ---------------- */
const rooms = new Map();

function broadcast(conversationId, payload) {
  const set = rooms.get(conversationId);
  if (!set) return;
  const data = JSON.stringify(payload);
  for (const ws of set) {
    if (ws.readyState === 1) ws.send(data);
  }
}

export function registerSocket(_wss, ws, conversationId, user) {
  const c = db.prepare("SELECT * FROM conversations WHERE id = ?").get(conversationId);
  if (!c || (c.buyer_id !== user.id && c.seller_id !== user.id)) return ws.close();

  if (!rooms.has(conversationId)) rooms.set(conversationId, new Set());
  rooms.get(conversationId).add(ws);
  ws.send(JSON.stringify({ type: "connected", conversation_id: conversationId }));

  ws.on("message", (raw) => {
    let payload = {};
    try {
      payload = JSON.parse(raw.toString());
    } catch {
      payload = { body: raw.toString() };
    }
    const text = payload.body || payload.message;
    if (!text || !String(text).trim()) return;
    const msg = createMessage(conversationId, user.id, text);
    broadcast(conversationId, { type: "message", message: msg });
  });

  ws.on("close", () => {
    rooms.get(conversationId)?.delete(ws);
  });
}
