import fs from "node:fs";
import path from "node:path";
import multer from "multer";
import { randomUUID } from "node:crypto";
import { config } from "./config.js";

const storage = multer.diskStorage({
  destination(req, _file, cb) {
    const dir = path.join(config.storageDir, req.uploadBucket || "misc");
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename(_req, file, cb) {
    const ext = path.extname(file.originalname || "").toLowerCase() || ".bin";
    cb(null, `${Date.now()}-${randomUUID().slice(0, 8)}${ext}`);
  },
});

export const upload = multer({ storage, limits: { fileSize: 15 * 1024 * 1024 } });

export const bucket = (name) => (req, _res, next) => {
  req.uploadBucket = name;
  next();
};

export function publicUrl(filePath) {
  const rel = path.relative(config.storageDir, filePath).split(path.sep).join("/");
  return `${config.publicBaseUrl}/uploads/${rel}`;
}
