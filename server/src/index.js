import fs from "node:fs";
import http from "node:http";
import express from "express";
import cors from "cors";
import { WebSocketServer } from "ws";
import jwt from "jsonwebtoken";

import { config } from "./config.js";
import { db } from "./db.js";
import { optionalAuth } from "./auth.js";
import { ai } from "./ai.js";

import { router as authRouter } from "./routes/auth.js";
import { router as usersRouter } from "./routes/users.js";
import { router as kycRouter } from "./routes/kyc.js";
import { router as listingsRouter } from "./routes/listings.js";
import { router as uploadRouter } from "./routes/upload.js";
import { router as verificationRouter } from "./routes/verification.js";
import { router as chatRouter, registerSocket } from "./routes/chat.js";
import { router as notificationsRouter } from "./routes/notifications.js";
import { router as adminRouter } from "./routes/admin.js";
import { router as ragRouter } from "./routes/rag.js";

const app = express();
app.disable("x-powered-by");

app.use(
  cors({
    origin(origin, cb) {
      if (!origin || config.allowedOrigins.includes(origin) || config.allowedOrigins.includes("*")) return cb(null, true);
      return cb(null, true); // بيئة تطوير محلية
    },
    credentials: true,
  }),
);
app.use(express.json({ limit: "5mb" }));
app.use(express.urlencoded({ extended: true }));

fs.mkdirSync(config.storageDir, { recursive: true });
app.use("/uploads", express.static(config.storageDir));

app.use(optionalAuth);

const api = express.Router();
api.get("/health", async (_req, res) => {
  res.json({ status: "ok", db: "sqlite", time: new Date().toISOString() });
});
api.get("/ai/health", async (_req, res) => res.json(await ai.health()));

api.use("/auth", authRouter);
api.use("/users", usersRouter);
api.use("/kyc", kycRouter);
api.use("/listings", listingsRouter);
api.use("/upload", uploadRouter);
api.use("/verification", verificationRouter);
api.use("/chat", chatRouter);
api.use("/notifications", notificationsRouter);
api.use("/admin", adminRouter);
api.use("/rag", ragRouter);

app.use("/api/v1", api);

app.use((req, res) => res.status(404).json({ detail: `المسار غير موجود: ${req.path}` }));
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(err.status || 500).json({ detail: err.message || "خطأ داخلي في الخادم" });
});

const server = http.createServer(app);

/** WebSocket للمحادثات: ws://localhost:8000/ws/chat/:conversationId?token=... */
const wss = new WebSocketServer({ noServer: true });
server.on("upgrade", (req, socket, head) => {
  const url = new URL(req.url, "http://localhost");
  const m = url.pathname.match(/^\/ws\/chat\/([^/]+)$/);
  if (!m) return socket.destroy();
  let user = null;
  try {
    const payload = jwt.verify(url.searchParams.get("token") || "", config.jwtSecret);
    user = db.prepare("SELECT * FROM users WHERE id = ?").get(payload.sub);
  } catch {
    /* anonymous */
  }
  if (!user) return socket.destroy();
  wss.handleUpgrade(req, socket, head, (ws) => registerSocket(wss, ws, m[1], user));
});

server.listen(config.port, () => {
  console.log(`✅ معاملاتي API → http://localhost:${config.port}/api/v1`);
  console.log(`   ملفات الرفع  → http://localhost:${config.port}/uploads`);
});
