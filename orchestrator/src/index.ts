import { createServer, IncomingMessage, ServerResponse } from "http";
import * as formidable from "formidable";

const HTTP_PORT = parseInt(process.env.HTTP_PORT || "10501");
const LLAMA_API_URL = process.env.LLAMA_API_URL || "http://llama-cpp:8080";
const KOKORO_API_URL = process.env.KOKORO_API_URL || "http://kokoro:8880";
const WHISPER_URL = process.env.WHISPER_URL || "http://whisper:10300";
const MODEL_NAME = process.env.MODEL_NAME || "qwen3-next";
const KOKORO_VOICE = process.env.KOKORO_VOICE || "onyx";
const MAX_CONTEXT_PCT = parseFloat(process.env.MAX_CONTEXT_PCT || "0.9");
const ROLL_TO_PCT = parseFloat(process.env.ROLL_TO_PCT || "0.8");
const MESSAGE_TTL_MS = parseInt(process.env.MESSAGE_TTL_MS || "600000");

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface Conversation {
  messages: Message[];
}

const conversation: Conversation = { messages: [] };

function addUserMessage(content: string): void {
  conversation.messages.push({
    role: "user",
    content,
    timestamp: Date.now(),
  });
  periodicCleanup();
}

function addAssistantMessage(content: string): void {
  conversation.messages.push({
    role: "assistant",
    content,
    timestamp: Date.now(),
  });
}

function getMessagesForLlm(): Array<{ role: string; content: string }> {
  return conversation.messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));
}

function estimateContextUsage(): number {
  const totalTokens = conversation.messages.reduce(
    (sum, m) => sum + Math.ceil(m.content.length / 4),
    0
  );
  const maxTokens = 128000;
  return totalTokens / maxTokens;
}

function trimForContext(): void {
  const usage = estimateContextUsage();

  if (usage >= MAX_CONTEXT_PCT) {
    const targetTokens = Math.floor(128000 * ROLL_TO_PCT);

    while (
      conversation.messages.length > 0 &&
      estimateContextUsage() > targetTokens
    ) {
      conversation.messages.shift();
    }
  }
}

let lastCleanup = 0;
const cleanupInterval = 60000;

function periodicCleanup(): void {
  const now = Date.now();
  if (now - lastCleanup < cleanupInterval) return;

  lastCleanup = now;
  const cutoff = now - MESSAGE_TTL_MS;

  conversation.messages = conversation.messages.filter(
    (m) => m.timestamp > cutoff
  );
}

function forceCleanup(): void {
  const cutoff = Date.now() - MESSAGE_TTL_MS;
  conversation.messages = conversation.messages.filter(
    (m) => m.timestamp > cutoff
  );
}

async function callLlm(messages: Array<{ role: string; content: string }>): Promise<string> {
  const response = await fetch(`${LLAMA_API_URL}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL_NAME,
      messages,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`LLM request failed: ${response.status} - ${error}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

async function callTts(text: string, voice?: string): Promise<Uint8Array> {
  const response = await fetch(`${KOKORO_API_URL}/v1/audio/speech`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "kokoro",
      input: text,
      voice: voice || KOKORO_VOICE,
      response_format: "wav",
      speed: 1.0,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`TTS request failed: ${response.status} - ${error}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  return new Uint8Array(arrayBuffer);
}

async function callWhisper(audioBuffer: Buffer): Promise<string> {
  const FormData = (await import("form-data")).default;
  const formData = new FormData();
  formData.append("audio", audioBuffer, {
    filename: "audio.wav",
    contentType: "audio/wav",
  });

  const response = await fetch(`${WHISPER_URL}/transcribe`, {
    method: "POST",
    body: formData as any,
    headers: formData.getHeaders(),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Whisper transcription failed: ${response.status} - ${error}`);
  }

  const data = await response.json();
  return data.text;
}

async function streamTts(text: string, voice: string, res: ServerResponse): Promise<void> {
  res.writeHead(200, {
    "Content-Type": "audio/wav",
    "Transfer-Encoding": "chunked",
  });

  try {
    const response = await fetch(`${KOKORO_API_URL}/v1/audio/speech/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "kokoro",
        input: text,
        voice: voice || KOKORO_VOICE,
        response_format: "wav",
        speed: 1.0,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      res.write(`Error: TTS request failed: ${response.status} - ${error}`);
      res.end();
      return;
    }

    if (!response.body) {
      res.end();
      return;
    }

    const reader = response.body.getReader();
    const encoder = new TextEncoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    console.error("Streaming TTS error:", error);
    try {
      res.write(encoder.encode(`Error: ${String(error)}`));
    } catch (e) {
      // Response may already be closed
    }
  }

  res.end();
}

async function handleRequest(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const url = req.url || "";
  const method = req.method || "";

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (method === "GET" && url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({
      status: "ok",
      conversation_messages: conversation.messages.length,
      context_usage: estimateContextUsage().toFixed(2) + "%",
    }));
    return;
  }

  if (method === "GET" && url === "/v1/audio/voices") {
    const response = await fetch(`${KOKORO_API_URL}/v1/audio/voices`);
    const data = await response.text();
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(data);
    return;
  }

  if (method === "POST" && url === "/v1/chat/completions") {
    let body = "";
    for await (const chunk of req) {
      body += chunk;
    }

    try {
      const payload = JSON.parse(body);
      
      if (!payload.messages || !Array.isArray(payload.messages) || payload.messages.length === 0) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Invalid request: messages array required" }));
        return;
      }

      const userMessage = payload.messages[payload.messages.length - 1]?.content || "";
      const voice = payload.voice;

      if (!userMessage.trim()) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No message content" }));
        return;
      }

      if (userMessage.length > 10000) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Message too long (max 10000 chars)" }));
        return;
      }

      addUserMessage(userMessage);
      trimForContext();

      const messages = getMessagesForLlm();
      const llmResponse = await callLlm(messages);

      addAssistantMessage(llmResponse);

      const audio = await callTts(llmResponse, voice);

      res.writeHead(200, {
        "Content-Type": "application/json",
        "Content-Disposition": 'attachment; filename="audio.wav"',
      });
      res.end(JSON.stringify({
        choices: [{
          message: {
            role: "assistant",
            content: llmResponse,
          },
        }],
        audio: Buffer.from(audio).toString("base64"),
        content_type: "audio/wav",
      }));
    } catch (error) {
      console.error("Error:", error);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: String(error) }));
    }
    return;
  }

  if (method === "POST" && url === "/v1/audio/speech") {
    let body = "";
    for await (const chunk of req) {
      body += chunk;
    }

    try {
      const payload = JSON.parse(body);
      const text = payload.input || "";
      const voice = payload.voice;

      if (!text.trim()) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No input text" }));
        return;
      }

      if (text.length > 5000) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Input text too long (max 5000 chars)" }));
        return;
      }

      const audio = await callTts(text, voice);

      res.writeHead(200, {
        "Content-Type": "audio/wav",
        "Content-Disposition": 'attachment; filename="audio.wav"',
      });
      res.end(Buffer.from(audio));
    } catch (error) {
      console.error("Error:", error);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: String(error) }));
    }
    return;
  }

  if (method === "POST" && url === "/v1/audio/speech/stream") {
    let body = "";
    for await (const chunk of req) {
      body += chunk;
    }

    try {
      const payload = JSON.parse(body);
      const text = payload.input || "";
      const voice = payload.voice;

      if (!text.trim()) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No input text" }));
        return;
      }

      if (text.length > 5000) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Input text too long (max 5000 chars)" }));
        return;
      }

      await streamTts(text, voice, res);
    } catch (error) {
      console.error("Error:", error);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: String(error) }));
    }
    return;
  }

  if (method === "POST" && url === "/v1/audio/process") {
    try {
      // Parse multipart form data
      const form = formidable.formidable({
        maxFileSize: 50 * 1024 * 1024, // 50MB max
      });

      const [fields, files] = await new Promise<[formidable.Fields, formidable.Files]>(
        (resolve, reject) => {
          form.parse(req, (err, fields, files) => {
            if (err) reject(err);
            else resolve([fields, files]);
          });
        }
      );

      // Get audio file and voice preference
      const audioFile = Array.isArray(files.audio) ? files.audio[0] : files.audio;
      if (!audioFile) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No audio file provided" }));
        return;
      }

      const voice = Array.isArray(fields.voice) ? fields.voice[0] : fields.voice || KOKORO_VOICE;

      // Read audio file
      const fs = await import("fs/promises");
      const audioBuffer = await fs.readFile(audioFile.filepath);

      // Step 1: Transcribe with Whisper
      const transcript = await callWhisper(audioBuffer);

      if (!transcript.trim()) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No speech detected in audio" }));
        return;
      }

      // Step 2: Process with LLM (using existing conversation context)
      addUserMessage(transcript);
      trimForContext();

      const messages = getMessagesForLlm();
      const llmResponse = await callLlm(messages);

      addAssistantMessage(llmResponse);

      // Step 3: Stream TTS audio with metadata headers
      res.writeHead(200, {
        "Content-Type": "audio/wav",
        "Transfer-Encoding": "chunked",
        "X-Transcript": transcript,
        "X-Response-Text": llmResponse,
      });

      // Stream audio from TTS
      await streamTts(llmResponse, voice as string, res);

    } catch (error) {
      console.error("Audio processing error:", error);
      try {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: String(error) }));
      } catch (e) {
        // Response may already be sent
      }
    }
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not found" }));
}

const server = createServer(handleRequest);

server.listen(HTTP_PORT, "0.0.0.0", () => {
  console.log(`Voice pipeline REST server listening on port ${HTTP_PORT}`);
  console.log(`LLM: ${LLAMA_API_URL}, model: ${MODEL_NAME}`);
  console.log(`TTS: ${KOKORO_API_URL}, voice: ${KOKORO_VOICE}`);
  console.log(`Context: ${MAX_CONTEXT_PCT * 100}% max, roll to ${ROLL_TO_PCT * 100}%`);
  console.log(`TTL: ${MESSAGE_TTL_MS / 1000}s`);
});
