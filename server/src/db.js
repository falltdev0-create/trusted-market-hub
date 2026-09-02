import fs from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";
import { randomUUID } from "node:crypto";
import { config } from "./config.js";

fs.mkdirSync(path.dirname(config.databaseFile), { recursive: true });
fs.mkdirSync(config.storageDir, { recursive: true });

export const db = new Database(config.databaseFile);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

const schemaPath = path.resolve(path.dirname(new URL(import.meta.url).pathname), "schema.sql");
db.exec(fs.readFileSync(schemaPath, "utf8"));

export const uid = () => randomUUID();
export const now = () => new Date().toISOString();

export const json = (v, fallback = null) => {
  if (v == null) return fallback;
  try {
    return JSON.parse(v);
  } catch {
    return fallback;
  }
};
