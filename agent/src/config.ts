/**
 * Configuration for the Telegram AI Agent
 * Loads environment from parent directory's .env file
 */

import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

// Load .env from parent directory (telegram-mcp root)
const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(__dirname, "../..", ".env");

// Load .env file using dotenv
dotenv.config({ path: envPath });

export const config = {
  // Telegram HTTP Bridge
  telegramApiUrl: process.env.TELEGRAM_API_URL || "http://localhost:8765",

  // NIA API
  niaApiKey: process.env.NIA_API_KEY || "",
  niaApiBase: "https://apigcp.trynia.ai/v2",
  niaCodebaseSource: process.env.NIA_CODEBASE_SOURCE || "",

  // ✅ GOOGLE GEMINI MODEL
  model: "gemini-1.5-flash",
} as const;

export function validateConfig() {
  const missing: string[] = [];

  // ✅ GROQ API KEY
  if (!process.env.GROQ_API_KEY) {
    missing.push("GROQ_API_KEY");
  }

  // NIA API ixtiyoriy - olib tashladik
  // if (!config.niaApiKey) {
  //   missing.push("NIA_API_KEY");
  // }

  if (missing.length > 0) {
    console.error(`❌ Missing required environment variables: ${missing.join(", ")}`);
    process.exit(1);
  }
}
