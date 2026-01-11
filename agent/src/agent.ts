// =================================================================
// AGENT.TS FAYLINING TO'LIQ YANGI KODI (YAKUNIY VERSIYA 2.0)
// =================================================================

import {
  StreamData,
  // StreamingTextResponse, // <<< BU QATORNI BUTUNLAY O'CHIRIB TASHLADIK
  Tool,
  CoreMessage,
} from "ai";
import pc from "picocolors";
import { config } from "./config";
import { telegramTools } from "./tools/telegram";
import { niaTools } from "./tools/nia";
import { aiifyTools } from "./tools/aiify";

// Combine all tools
export const tools: Record<string, Tool> = {
  ...telegramTools,
  ...niaTools,
  ...aiifyTools,
};

// System prompt that defines the agent's behavior
export const SYSTEM_PROMPT = `You are a charming AI assistant helping a guy communicate with his girlfriend on Telegram. You have access to tools for:

1. **Telegram** - Reading and sending messages
2. **searchPickupLines** - YOUR MAIN TOOL for pickup lines, dating advice, relationship tips (searches the indexed codebase)
3. **niaSearch** - General search (only if searchPickupLines doesn't help)
4. **AI-ify** - Transforming her messages into clever responses

## Your Personality
- Witty and charming but not cringe
- Supportive wingman energy
- Know when to be romantic vs funny
- Never sound robotic or generic

## How to Help
- When asked to read messages, use getChats first to find the right chat, then getMessages
- When crafting responses, ALWAYS use searchPickupLines FIRST for inspiration
- When sending messages, confirm with the user before sending unless they explicitly said to send
- Match the energy and tone of the conversation

## Important Rules
1. ALWAYS use tools to get real data - don't make up message content
2. **USE searchPickupLines** for ANY relationship/dating/flirting question - it has the indexed pickup lines!
3. Be concise in your explanations
4. If something fails, explain what went wrong clearly
5. Never send a message without user confirmation (unless they said "send it")
6. When sending ANY Telegram message, ALWAYS append "\\n\\n— Sent by Arlan AI" at the end of the message content

## Response Style
- Keep responses natural and conversational
- DO NOT use markdown formatting (no **, no ##, no bullet points with -)
- Use plain text only since this is a terminal CLI
- Use emojis sparingly for visual cues
- When suggesting messages, put them in quotes like: "hey, how are you?"
- Keep it brief and scannable
- IMPORTANT: All suggested messages to send should be lowercase, never uppercase. Type like a normal person texting, not formal.`;

// Message history for the conversation
let messageHistory: CoreMessage[] = [];

// --- GROQ API BILAN ISHLASH ---
// Groq API - tez va bepul, OpenAI formatida ishlaydi
async function* streamGroq(
  options: {
    system?: string;
    messages: CoreMessage[];
  }
): AsyncGenerator<string, void, unknown> {
  const GROQ_API_KEY = process.env.GROQ_API_KEY;

  if (!GROQ_API_KEY) {
    throw new Error("GROQ_API_KEY environment variable is not set!");
  }

  const MODEL_NAME = "llama-3.3-70b-versatile";
  const url = "https://api.groq.com/openai/v1/chat/completions";

  const messages = [
    { role: "system", content: options.system || "" },
    ...options.messages.map(msg => ({
      role: msg.role,
      content: msg.content as string,
    })),
  ];

  const body = {
    model: MODEL_NAME,
    messages: messages,
    stream: true,
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${GROQ_API_KEY}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    const errorText = await response.text();
    throw new Error(`Groq API Error: ${response.status} ${errorText}`);
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    const lines = value.split("\n");
    for (const line of lines) {
      if (line.startsWith("data: ") && !line.includes("[DONE]")) {
        try {
          const json = JSON.parse(line.substring(6));
          const text = json.choices?.[0]?.delta?.content || "";
          if (text) {
            yield text;
          }
        } catch (e) {
          // ignore parse errors
        }
      }
    }
  }
}


/**
 * Process a user message and stream the response
 */
export async function chat(userMessage: string): Promise<AsyncIterable<string>> {
  messageHistory.push({
    role: "user",
    content: userMessage,
  });

  // Groq API funksiyasini chaqiramiz
  const stream = streamGroq({
    system: SYSTEM_PROMPT,
    messages: messageHistory,
  });

  return (async function* () {
    let fullResponse = "";
    for await (const chunk of stream) {
      fullResponse += chunk;
      yield chunk;
    }
    messageHistory.push({
      role: "assistant",
      content: fullResponse,
    });
  })();
}

/**
 * Clear conversation history
 */
export function clearHistory() {
  messageHistory = [];
}

/**
 * Get current message count
 */
export function getHistoryLength(): number {
  return messageHistory.length;
}
