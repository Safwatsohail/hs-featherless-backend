from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


STUDIO_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HNS</title>
  <style>
    :root {
      --bg: #f4efe7;
      --panel: rgba(255, 255, 255, 0.92);
      --panel-strong: #ffffff;
      --line: rgba(13, 24, 38, 0.1);
      --ink: #142131;
      --muted: #63707e;
      --brand: #0d6dd7;
      --brand-strong: #0752a4;
      --brand-soft: rgba(13, 109, 215, 0.1);
      --warm: #f1ede5;
      --success: #0b8a61;
      --danger: #b84a3b;
      --shadow: 0 24px 64px rgba(20, 33, 49, 0.08);
      --radius-xl: 30px;
      --radius-lg: 22px;
      --radius-md: 16px;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "IBM Plex Sans", "Avenir Next", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(13, 109, 215, 0.12), transparent 24%),
        radial-gradient(circle at bottom right, rgba(11, 138, 97, 0.1), transparent 26%),
        linear-gradient(180deg, #f8f5f0 0%, var(--bg) 100%);
    }
    .shell {
      width: min(1600px, calc(100vw - 24px));
      margin: 12px auto;
      min-height: calc(100vh - 24px);
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      gap: 14px;
    }
    .sidebar, .workspace {
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
      overflow: hidden;
    }
    .sidebar {
      background: rgba(255, 255, 255, 0.8);
      padding: 18px;
      display: grid;
      grid-template-rows: auto auto auto auto 1fr;
      gap: 14px;
    }
    .workspace {
      background: var(--panel);
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    .brand {
      display: grid;
      gap: 8px;
    }
    .brand h1 {
      margin: 0;
      font-size: 34px;
      line-height: 1;
      font-family: "IBM Plex Serif", Georgia, serif;
    }
    .muted, .subtle, .card p, .section-note, .panel-note {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }
    .hero-chips, .metric-row, .tool-row, .quick-row, .status-row, .memory-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chip, .metric, .tool-pill, .memory-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid rgba(13, 109, 215, 0.14);
      background: rgba(255, 255, 255, 0.82);
      color: var(--muted);
      border-radius: 999px;
      padding: 7px 11px;
      font-size: 12px;
      white-space: nowrap;
    }
    .chip.brand, .tool-pill.active {
      background: linear-gradient(135deg, var(--brand), var(--brand-strong));
      color: white;
      border-color: transparent;
    }
    .section {
      display: grid;
      gap: 10px;
      min-height: 0;
    }
    .section h2 {
      margin: 0;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
    }
    .card {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.86);
      border-radius: var(--radius-lg);
      padding: 14px;
      display: grid;
      gap: 8px;
    }
    .card strong {
      font-size: 14px;
    }
    .key-row {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .key-box {
      min-width: 0;
      flex: 1;
      padding: 11px 12px;
      border-radius: 14px;
      background: #0f1824;
      color: #eef4ff;
      font-family: "IBM Plex Mono", monospace;
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 16px;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
      color: white;
      background: linear-gradient(135deg, var(--brand), var(--brand-strong));
    }
    button.secondary {
      background: rgba(20, 33, 49, 0.08);
      color: var(--ink);
    }
    button.ghost {
      background: transparent;
      color: var(--brand);
      border: 1px solid rgba(13, 109, 215, 0.16);
    }
    .search {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 11px 12px;
      background: rgba(255, 255, 255, 0.92);
      color: var(--ink);
      font: inherit;
      outline: none;
    }
    .scroll {
      min-height: 0;
      overflow: auto;
      display: grid;
      gap: 8px;
      padding-right: 4px;
    }
    .skill-item, .tool-item {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 12px 13px;
      background: rgba(255, 255, 255, 0.82);
      cursor: pointer;
      transition: 120ms ease;
    }
    .skill-item:hover, .tool-item:hover {
      transform: translateY(-1px);
      border-color: rgba(13, 109, 215, 0.24);
    }
    .skill-item.active {
      background: linear-gradient(135deg, rgba(13, 109, 215, 0.1), rgba(11, 138, 97, 0.08));
      border-color: rgba(13, 109, 215, 0.28);
    }
    .skill-item strong, .tool-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 14px;
    }
    .skill-item span, .tool-item span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .topbar {
      padding: 18px 22px 12px;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 10px;
    }
    .topbar h2 {
      margin: 0;
      font-size: 31px;
      font-family: "IBM Plex Serif", Georgia, serif;
    }
    .comparison {
      padding: 18px 18px 8px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
      min-height: 0;
    }
    .panel {
      min-height: 0;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 26px;
      background: rgba(255, 255, 255, 0.88);
      padding: 16px;
    }
    .panel.hns {
      background: linear-gradient(180deg, rgba(13, 109, 215, 0.08), rgba(255, 255, 255, 0.92));
    }
    .panel.raw {
      background: linear-gradient(180deg, rgba(20, 33, 49, 0.04), rgba(255, 255, 255, 0.92));
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 12px;
    }
    .panel-head h3 {
      margin: 0 0 4px;
      font-size: 22px;
      font-family: "IBM Plex Serif", Georgia, serif;
    }
    .result-wrap {
      min-height: 0;
      overflow: auto;
      display: grid;
      gap: 12px;
      align-content: start;
    }
    .empty {
      border: 1px dashed rgba(13, 24, 38, 0.16);
      border-radius: 22px;
      padding: 18px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.7);
      line-height: 1.6;
    }
    .response-block {
      border: 1px solid var(--line);
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.94);
      padding: 16px;
      line-height: 1.66;
      white-space: pre-wrap;
    }
    .response-block p {
      margin: 0 0 12px;
    }
    .response-block p:last-child {
      margin-bottom: 0;
    }
    pre.code {
      margin: 12px 0 0;
      padding: 14px;
      border-radius: 18px;
      background: #101c2b;
      color: #e7eefb;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "IBM Plex Mono", monospace;
      font-size: 13px;
      line-height: 1.55;
    }
    .preview-card {
      border: 1px solid var(--line);
      border-radius: 20px;
      background: rgba(245, 248, 252, 0.96);
      padding: 14px;
      display: grid;
      gap: 8px;
    }
    .preview-card h4 {
      margin: 0;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .result-item {
      display: grid;
      gap: 4px;
      padding-top: 10px;
      border-top: 1px solid rgba(20, 33, 49, 0.08);
    }
    .result-item:first-child {
      border-top: 0;
      padding-top: 0;
    }
    .result-item strong {
      font-size: 14px;
    }
    .result-item a {
      color: var(--brand);
      text-decoration: none;
      word-break: break-all;
    }
    .result-item span {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .composer {
      border-top: 1px solid var(--line);
      padding: 12px 18px 18px;
      display: grid;
      gap: 12px;
      background: rgba(255, 255, 255, 0.75);
    }
    .composer-wrap {
      width: min(980px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 10px;
    }
    .quick-row {
      justify-content: center;
    }
    .tool-pill {
      cursor: pointer;
    }
    .composer-box {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: end;
    }
    textarea {
      width: 100%;
      min-height: 108px;
      max-height: 240px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.95);
      color: var(--ink);
      padding: 16px 18px;
      font: inherit;
      outline: none;
    }
    .composer-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
    }
    .status-strong {
      color: var(--ink);
      font-weight: 600;
    }
    @media (max-width: 1120px) {
      .shell {
        grid-template-columns: 1fr;
      }
      .comparison {
        grid-template-columns: 1fr;
      }
    }
    @media (max-width: 760px) {
      .shell {
        width: min(100vw - 12px, 100%);
        margin: 6px auto;
      }
      .composer-box {
        grid-template-columns: 1fr;
      }
      .panel-head {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>HNS</h1>
        <p class="muted">One higher-level API on top of Featherless or OpenRouter. Same model access, but tuned with skills, tools, and centralized memory.</p>
        <div class="hero-chips">
          <span class="chip brand">tuned api</span>
          <span class="chip" id="heroSkills">skills</span>
          <span class="chip" id="heroTools">tools</span>
          <span class="chip">shared memory</span>
        </div>
      </div>

      <div class="section">
        <h2>HNS API Key</h2>
        <div class="card">
          <strong>Your new API key for the tuned API layer</strong>
          <div class="key-row">
            <div id="apiKeyBox" class="key-box">loading...</div>
            <button id="copyKeyBtn" class="ghost" type="button">Copy</button>
          </div>
          <p>Use this key against <span class="status-strong">/run</span>, <span class="status-strong">/skills/*</span>, <span class="status-strong">/tools/*</span>, and <span class="status-strong">/memory/*</span>.</p>
        </div>
      </div>

      <div class="section">
        <h2>Centralized Memory</h2>
        <div class="card">
          <strong id="memoryHeadline">Shared across providers</strong>
          <p id="memoryBody">A single memory bucket is reused across every upstream API call for this workspace.</p>
          <div class="memory-tags">
            <span class="memory-pill" id="memoryScope">scope: workspace</span>
            <span class="memory-pill" id="memoryKey">context: hackathon-demo</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>Skills</h2>
        <input id="skillSearch" class="search" placeholder="Search 300+ skills">
        <div id="skillList" class="scroll"></div>
      </div>

      <div class="section">
        <h2>Tools</h2>
        <div id="toolList" class="scroll"></div>
      </div>
    </aside>

    <main class="workspace">
      <div class="topbar">
        <div>
          <h2>Raw Model API vs HNS Tuned API</h2>
          <p class="panel-note">The right side shows a plain model call. The left side shows the same upstream model after HNS adds skills, tools, and centralized memory.</p>
        </div>
        <div class="status-row">
          <span class="chip" id="statusSkill">skill: auto</span>
          <span class="chip">provider: openrouter</span>
          <span class="chip">model: openrouter/free</span>
          <span class="chip" id="catalogStatus">loading catalog…</span>
        </div>
      </div>

      <section class="comparison">
        <article class="panel hns">
          <div class="panel-head">
            <div>
              <h3>HNS Tuned API</h3>
              <p class="subtle">Skills, tools, and centralized memory orchestrate the same upstream model before the answer is returned.</p>
            </div>
            <div class="chip brand">/run</div>
          </div>
          <div id="tunedMetrics" class="metric-row"></div>
          <div id="tunedResult" class="result-wrap">
            <div class="empty">
              Use the prompt box below.
              <br><br>
              HNS will automatically choose a skill, load shared memory, run tools if needed, then return a tuned answer from the same provider model.
            </div>
          </div>
        </article>

        <article class="panel raw">
          <div class="panel-head">
            <div>
              <h3>Raw Model API</h3>
              <p class="subtle">Direct upstream response with no tools, no skills, and no centralized memory.</p>
            </div>
            <div class="chip">plain model</div>
          </div>
          <div id="rawMetrics" class="metric-row"></div>
          <div id="rawResult" class="result-wrap">
            <div class="empty">
              This side is the baseline.
              <br><br>
              It only receives the user prompt, so judges can compare HNS against a plain API call on the same task.
            </div>
          </div>
        </article>
      </section>

      <div class="composer">
        <div class="composer-wrap">
          <div class="quick-row">
            <button class="tool-pill" type="button" data-skill="deep_research">Find</button>
            <button class="tool-pill" type="button" data-skill="pdf_analyst">PDF Analyzer</button>
            <button class="tool-pill" type="button" data-skill="code_assistant">Code</button>
            <button class="tool-pill" type="button" data-skill="review">Review</button>
            <button class="tool-pill" type="button" data-more-tools="1">+ More Tools</button>
          </div>
          <div class="composer-box">
            <textarea id="prompt" placeholder="Ask anything. HNS will compare the same request against the raw model and the tuned API."></textarea>
            <div class="hero-chips">
              <button id="sendBtn" type="button">Compare</button>
              <button id="resetBtn" type="button" class="secondary">Reset</button>
            </div>
          </div>
          <div class="composer-meta">
            <span id="routeHint">route: /compare</span>
            <span id="activeSummary">active skill: auto</span>
            <span id="deltaSummary">last delta: not run yet</span>
          </div>
        </div>
      </div>
    </main>
  </div>

  <script>
    const els = {
      apiKeyBox: document.getElementById("apiKeyBox"),
      copyKeyBtn: document.getElementById("copyKeyBtn"),
      memoryHeadline: document.getElementById("memoryHeadline"),
      memoryBody: document.getElementById("memoryBody"),
      memoryScope: document.getElementById("memoryScope"),
      memoryKey: document.getElementById("memoryKey"),
      skillSearch: document.getElementById("skillSearch"),
      skillList: document.getElementById("skillList"),
      toolList: document.getElementById("toolList"),
      statusSkill: document.getElementById("statusSkill"),
      catalogStatus: document.getElementById("catalogStatus"),
      heroSkills: document.getElementById("heroSkills"),
      heroTools: document.getElementById("heroTools"),
      tunedMetrics: document.getElementById("tunedMetrics"),
      rawMetrics: document.getElementById("rawMetrics"),
      tunedResult: document.getElementById("tunedResult"),
      rawResult: document.getElementById("rawResult"),
      prompt: document.getElementById("prompt"),
      sendBtn: document.getElementById("sendBtn"),
      resetBtn: document.getElementById("resetBtn"),
      routeHint: document.getElementById("routeHint"),
      activeSummary: document.getElementById("activeSummary"),
      deltaSummary: document.getElementById("deltaSummary"),
    };

    const state = {
      userId: "00000000-0000-0000-0000-000000000001",
      provider: "openrouter",
      model: "openrouter/free",
      memoryScope: "workspace",
      contextKey: "hackathon-demo",
      auroraApiKey: "",
      skills: [],
      tools: [],
      activeSkill: "",
      conversationId: null,
    };

    async function api(path, options = {}) {
      const headers = { "content-type": "application/json", ...(options.headers || {}) };
      if (state.auroraApiKey) {
        headers["authorization"] = "Bearer " + state.auroraApiKey;
      }
      const response = await fetch(path, { ...options, headers });
      const text = await response.text();
      let body;
      try { body = JSON.parse(text); } catch { body = text; }
      if (!response.ok) {
        throw new Error(typeof body === "string" ? body : JSON.stringify(body, null, 2));
      }
      return body;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function renderTextBlocks(text) {
      const parts = String(text || "").split(/```/);
      return parts.map((part, index) => {
        if (index % 2 === 1) {
          const lines = part.split("\\n");
          const maybeLang = lines[0].trim();
          const code = lines.slice(1).join("\\n") || part;
          const label = maybeLang && maybeLang.length < 24 ? maybeLang : "code";
          return `<pre class="code" data-lang="${escapeHtml(label)}">${escapeHtml(code.trim())}</pre>`;
        }
        return String(part || "")
          .split(/\\n{2,}/)
          .filter(Boolean)
          .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\\n/g, "<br>")}</p>`)
          .join("");
      }).join("");
    }

    function formatUsd(value) {
      return "$" + Number(value || 0).toFixed(4);
    }

    function metric(label, value, tone = "") {
      return `<span class="metric ${tone}"><strong>${escapeHtml(value)}</strong> ${escapeHtml(label)}</span>`;
    }

    function buildMetrics(side, extraLabel) {
      const usage = side.metrics.usage || {};
      return [
        metric("time", `${side.metrics.latency_ms} ms`),
        metric("cost", formatUsd(side.metrics.estimated_cost_usd)),
        metric("efficiency", `${side.metrics.estimated_efficiency}%`),
        metric("accuracy", `${side.metrics.estimated_accuracy}%`),
        metric("tokens", usage.total_tokens ?? 0),
        metric("memory", side.metrics.memory_hits),
        metric(extraLabel, side.skill || side.metrics.tool_count),
      ].join("");
    }

    function normalizeResultItems(value) {
      if (Array.isArray(value)) {
        return value;
      }
      if (value && typeof value === "object") {
        if (Array.isArray(value.results)) return value.results;
        if (Array.isArray(value.items)) return value.items;
        if (Array.isArray(value.matches)) return value.matches;
        return [value];
      }
      return [{ snippet: String(value || "") }];
    }

    function renderToolPreviews(results) {
      if (!Array.isArray(results) || !results.length) {
        return "";
      }
      const cards = results.slice(0, 5).map((entry) => {
        const name = escapeHtml(entry.name || "tool");
        const items = normalizeResultItems(entry.output).slice(0, 4);
        const rows = items.map((item) => {
          const title = item.title || item.path || item.url || item.name || name;
          const snippet = item.snippet || item.preview || item.summary || item.text || item.content || "";
          const href = item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.url)}</a>` : "";
          return `
            <div class="result-item">
              <strong>${escapeHtml(title)}</strong>
              ${href}
              <span>${escapeHtml(String(snippet).slice(0, 280) || "Preview available.")}</span>
            </div>
          `;
        }).join("");
        return `
          <div class="preview-card">
            <h4>${name}</h4>
            ${rows || `<span class="subtle">Tool ran successfully.</span>`}
          </div>
        `;
      }).join("");
      return cards;
    }

    function renderSide(target, side, extraLabel) {
      target.innerHTML = `
        <div class="response-block">${renderTextBlocks(side.output || "")}</div>
        ${renderToolPreviews(side.tool_results)}
      `;
      if (!side.output && (!side.tool_results || !side.tool_results.length)) {
        target.innerHTML = `<div class="empty">No output returned.</div>`;
      }
      if (target === els.tunedResult) {
        els.tunedMetrics.innerHTML = buildMetrics(side, "skill");
      } else {
        els.rawMetrics.innerHTML = buildMetrics(side, extraLabel);
      }
    }

    function setActiveSkill(skillName) {
      state.activeSkill = state.activeSkill === skillName ? "" : skillName;
      els.statusSkill.textContent = "skill: " + (state.activeSkill || "auto");
      els.activeSummary.textContent = "active skill: " + (state.activeSkill || "auto");
      document.querySelectorAll(".skill-item").forEach((node) => {
        node.classList.toggle("active", node.dataset.skill === state.activeSkill);
      });
      document.querySelectorAll(".tool-pill[data-skill]").forEach((node) => {
        node.classList.toggle("active", node.dataset.skill === state.activeSkill);
      });
    }

    function renderSkills() {
      const query = els.skillSearch.value.trim().toLowerCase();
      const filtered = state.skills.filter((skill) => {
        const hay = `${skill.name} ${skill.description} ${skill.when_to_use || ""}`.toLowerCase();
        return !query || hay.includes(query);
      });
      els.skillList.innerHTML = filtered.slice(0, 80).map((skill) => `
        <div class="skill-item ${state.activeSkill === skill.name ? "active" : ""}" data-skill="${escapeHtml(skill.name)}">
          <strong>${escapeHtml(skill.name)}</strong>
          <span>${escapeHtml(skill.description)}</span>
        </div>
      `).join("");
      els.skillList.querySelectorAll(".skill-item").forEach((node) => {
        node.addEventListener("click", () => setActiveSkill(node.dataset.skill));
      });
    }

    function renderTools() {
      els.toolList.innerHTML = state.tools.slice(0, 18).map((tool) => `
        <div class="tool-item">
          <strong>${escapeHtml(tool.name)}</strong>
          <span>${escapeHtml(tool.description || "Tool available in HNS orchestration.")}</span>
        </div>
      `).join("");
      els.catalogStatus.textContent = `${state.skills.length} skills • ${state.tools.length} tools`;
    }

    async function bootstrap() {
      try {
        const [demoKey, skills, tools, memory] = await Promise.all([
          api("/auth/demo-key"),
          api("/v1/skills"),
          api("/tools"),
          api("/memory/context", {
            method: "POST",
            body: JSON.stringify({
              user_id: state.userId,
              memory_scope: state.memoryScope,
              context_key: state.contextKey,
              query: "workspace startup",
              top_k: 3,
              message_limit: 6,
              structured_limit: 6
            }),
          }).catch(() => null),
        ]);
        if (demoKey && demoKey.api_key) {
          state.auroraApiKey = demoKey.api_key;
          state.userId = demoKey.user_id || state.userId;
          els.apiKeyBox.textContent = demoKey.api_key;
        } else {
          els.apiKeyBox.textContent = "demo key unavailable";
        }
        state.skills = Array.isArray(skills) ? skills : [];
        state.tools = Array.isArray(tools) ? tools : [];
        els.heroSkills.textContent = `${state.skills.length} skills`;
        els.heroTools.textContent = `${state.tools.length} tools`;
        renderSkills();
        renderTools();
        if (memory) {
          els.memoryHeadline.textContent = `Shared context: ${memory.recent_messages.length} recent turns`;
          els.memoryBody.textContent = `${memory.retrieved_memories.length} retrieved memories are reusable across upstream API providers inside this workspace.`;
        }
      } catch (error) {
        els.apiKeyBox.textContent = "startup error";
        els.catalogStatus.textContent = "startup failed";
        els.tunedResult.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
      }
    }

    async function runCompare() {
      const prompt = els.prompt.value.trim();
      if (!prompt) {
        return;
      }
      els.sendBtn.disabled = true;
      els.sendBtn.textContent = "Running…";
      els.routeHint.textContent = "route: /compare";
      try {
        const payload = {
          user_id: state.userId,
          input: prompt,
          conversation_id: state.conversationId,
          provider: state.provider,
          model: state.model,
          memory_scope: state.memoryScope,
          context_key: state.contextKey,
          skill_name: state.activeSkill || null,
        };
        const response = await api("/compare", { method: "POST", body: JSON.stringify(payload) });
        state.conversationId = response.conversation_id || state.conversationId;
        if (response.aurora_api_key) {
          state.auroraApiKey = response.aurora_api_key;
          els.apiKeyBox.textContent = response.aurora_api_key;
        }
        renderSide(els.tunedResult, response.tuned, "skill");
        renderSide(els.rawResult, response.baseline, "tools");
        const delta = response.delta || {};
        const sign = delta.latency_gap_ms > 0 ? "faster" : "slower";
        const absGap = Math.abs(delta.latency_gap_ms || 0);
        els.deltaSummary.textContent = `last delta: HNS ${absGap} ms ${sign}, ${delta.efficiency_gap >= 0 ? "+" : ""}${delta.efficiency_gap || 0}% efficiency, ${delta.accuracy_gap >= 0 ? "+" : ""}${delta.accuracy_gap || 0}% accuracy`;
      } catch (error) {
        els.tunedResult.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
        els.rawResult.innerHTML = `<div class="empty">Compare run did not complete.</div>`;
        els.tunedMetrics.innerHTML = "";
        els.rawMetrics.innerHTML = "";
      } finally {
        els.sendBtn.disabled = false;
        els.sendBtn.textContent = "Compare";
      }
    }

    function resetView() {
      state.conversationId = null;
      els.prompt.value = "";
      els.tunedMetrics.innerHTML = "";
      els.rawMetrics.innerHTML = "";
      els.deltaSummary.textContent = "last delta: not run yet";
      els.tunedResult.innerHTML = `<div class="empty">Use the prompt box below.<br><br>HNS will automatically choose a skill, load shared memory, run tools if needed, then return a tuned answer from the same provider model.</div>`;
      els.rawResult.innerHTML = `<div class="empty">This side is the baseline.<br><br>It only receives the user prompt, so judges can compare HNS against a plain API call on the same task.</div>`;
    }

    els.sendBtn.addEventListener("click", runCompare);
    els.resetBtn.addEventListener("click", resetView);
    els.skillSearch.addEventListener("input", renderSkills);
    els.prompt.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        runCompare();
      }
    });
    els.copyKeyBtn.addEventListener("click", async () => {
      if (!state.auroraApiKey) return;
      await navigator.clipboard.writeText(state.auroraApiKey);
      els.copyKeyBtn.textContent = "Copied";
      setTimeout(() => { els.copyKeyBtn.textContent = "Copy"; }, 1200);
    });
    document.querySelectorAll(".tool-pill").forEach((node) => {
      node.addEventListener("click", () => {
        if (node.dataset.moreTools) {
          document.querySelector(".sidebar").scrollTo({ top: document.querySelector(".sidebar").scrollHeight, behavior: "smooth" });
          return;
        }
        setActiveSkill(node.dataset.skill);
      });
    });

    bootstrap();
  </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse(STUDIO_HTML)


@router.get("/studio", response_class=HTMLResponse)
async def studio() -> HTMLResponse:
    return HTMLResponse(STUDIO_HTML)
