#!/usr/bin/env node
/**
 * Enhanced AI API - Node.js Chatbot Example
 * A simple command-line chatbot using the Enhanced AI API
 */

const readline = require('readline');

// Configuration
const API_BASE = 'http://localhost:8000';
const AURORA_KEY = 'aurora_live_ZNTshOqnNk8LvKYKuuW5hZpW-3WHI1Ko';
const USER_ID = '00000000-0000-0000-0000-000000000001';

class EnhancedAIClient {
  constructor(apiBase, auroraKey, userId) {
    this.apiBase = apiBase;
    this.auroraKey = auroraKey;
    this.userId = userId;
    this.headers = {
      'Authorization': `Bearer ${auroraKey}`,
      'Content-Type': 'application/json'
    };
  }

  async chat(message, conversationId = null) {
    const payload = {
      user_id: this.userId,
      input: message,
      memory_scope: 'user',
      provider: 'openrouter',
      model: 'openrouter/auto'
    };

    if (conversationId) {
      payload.conversation_id = conversationId;
    }

    const response = await fetch(`${this.apiBase}/v1/run`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async compare(message) {
    const payload = {
      user_id: this.userId,
      input: message,
      provider: 'openrouter',
      model: 'openrouter/auto',
      memory_scope: 'user'
    };

    const response = await fetch(`${this.apiBase}/v1/compare`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async executeTool(toolName, toolInput) {
    const payload = {
      name: toolName,
      input: toolInput
    };

    const response = await fetch(`${this.apiBase}/v1/tools/${toolName}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async storeMemory(text, kind = 'context') {
    const payload = {
      user_id: this.userId,
      text: text,
      kind: kind,
      memory_scope: 'user'
    };

    const response = await fetch(`${this.apiBase}/v1/memory`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║                                                              ║');
  console.log('║          Enhanced AI API - Node.js Chatbot                   ║');
  console.log('║                                                              ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log();
  console.log("Type 'quit' to exit, 'compare <message>' to compare responses");
  console.log("Type 'tool <name> <input>' to execute a tool");
  console.log("Type 'remember <text>' to store a memory");
  console.log();

  const client = new EnhancedAIClient(API_BASE, AURORA_KEY, USER_ID);
  let conversationId = null;

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: 'You: '
  });

  rl.prompt();

  rl.on('line', async (line) => {
    const userInput = line.trim();

    if (!userInput) {
      rl.prompt();
      return;
    }

    if (userInput.toLowerCase() === 'quit') {
      console.log('Goodbye!');
      rl.close();
      return;
    }

    try {
      // Handle special commands
      if (userInput.startsWith('compare ')) {
        const message = userInput.substring(8);
        console.log('\n🔄 Comparing raw vs enhanced...\n');
        const result = await client.compare(message);
        console.log(`📊 Baseline (raw):`);
        console.log(`   ${result.baseline.output.substring(0, 200)}...`);
        console.log(`   Latency: ${result.baseline.metrics.latency_ms}ms`);
        console.log();
        console.log(`✨ Enhanced (tuned):`);
        console.log(`   ${result.tuned.output.substring(0, 200)}...`);
        console.log(`   Skill: ${result.tuned.skill}`);
        console.log(`   Tools: ${result.tuned.metrics.tool_count}`);
        console.log(`   Memory hits: ${result.tuned.metrics.memory_hits}`);
        console.log(`   Latency: ${result.tuned.metrics.latency_ms}ms`);
        console.log();
        rl.prompt();
        return;
      }

      if (userInput.startsWith('tool ')) {
        const parts = userInput.substring(5).split(' ');
        if (parts.length >= 2) {
          const toolName = parts[0];
          const toolInputStr = parts.slice(1).join(' ');
          try {
            const toolInput = JSON.parse(toolInputStr);
            const result = await client.executeTool(toolName, toolInput);
            console.log(`\n🛠️ Tool result: ${result.output}\n`);
          } catch (e) {
            console.log('❌ Invalid JSON input');
          }
        } else {
          console.log('❌ Usage: tool <name> <json_input>');
        }
        rl.prompt();
        return;
      }

      if (userInput.startsWith('remember ')) {
        const text = userInput.substring(9);
        await client.storeMemory(text);
        console.log('✅ Memory stored\n');
        rl.prompt();
        return;
      }

      // Regular chat
      const result = await client.chat(userInput, conversationId);
      conversationId = result.conversation_id;

      console.log(`\nAI (${result.skill}): ${result.output}`);

      // Show tool usage if any
      if (result.tool_calls && result.tool_calls.length > 0) {
        console.log(`\n🛠️ Tools used: ${result.tool_calls.map(t => t.name).join(', ')}`);
      }

      // Show memory hits
      if (result.metrics.memory_hits > 0) {
        console.log(`🧠 Memory hits: ${result.metrics.memory_hits}`);
      }

      console.log();
      rl.prompt();

    } catch (error) {
      console.log(`\n❌ Error: ${error.message}\n`);
      rl.prompt();
    }
  });

  rl.on('close', () => {
    console.log('\nGoodbye!');
    process.exit(0);
  });
}

main().catch(console.error);
