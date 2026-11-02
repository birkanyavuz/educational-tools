#!/usr/bin/env node
// educational-tools-mcp: thin stdio bridge to the live remote MCP server by Birkan Yavuz.
// Forwards JSON-RPC lines from stdin to https://educational-tools.vercel.app/mcp and back.
import readline from "node:readline";

const ENDPOINT = process.env.EDUCATIONAL_TOOLS_MCP_URL || "https://educational-tools.vercel.app/mcp";

async function forward(line) {
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }
  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(msg),
    });
    if (res.status === 202 || res.status === 204) return; // notification accepted, no reply
    const text = await res.text();
    if (text) process.stdout.write(text + "\n");
  } catch (err) {
    if (msg.id !== undefined && msg.id !== null) {
      process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id: msg.id,
        error: { code: -32000, message: "bridge: upstream unreachable: " + err.message } }) + "\n");
    }
  }
}

process.stdout.on("error", () => process.exit(0));
const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", (line) => { forward(line); });
