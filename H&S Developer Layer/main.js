/* ============================================================
   H&S Layer — Prototype logic
   Vanilla JS. No libraries. Mocked interactions.
   ============================================================ */

(() => {
    "use strict";

    // ---------- small helpers ----------
    const $  = (s, r = document) => r.querySelector(s);
    const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
    const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    const rand = (min, max) => Math.random() * (max - min) + min;
    const randInt = (min, max) => Math.floor(rand(min, max + 1));

    const toastEl = $("#toast");
    let toastTimer;
    function toast(msg) {
        if (!toastEl) return;
        toastEl.textContent = msg;
        toastEl.hidden = false;
        requestAnimationFrame(() => toastEl.classList.add("is-visible"));
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toastEl.classList.remove("is-visible");
            setTimeout(() => { toastEl.hidden = true; }, 250);
        }, 2200);
    }

    // ---------- router ----------
    const VALID_ROUTES = ["landing", "auth", "onboarding", "dashboard"];

    function go(route, opts = {}) {
        if (!VALID_ROUTES.includes(route)) route = "landing";
        $$(".route").forEach(el => {
            el.hidden = el.getAttribute("data-route") !== route;
        });
        if (opts.authMode) setAuthMode(opts.authMode);
        window.scrollTo({ top: 0, behavior: "instant" });
        if (location.hash.replace("#", "").split("#")[0] !== route) {
            history.replaceState(null, "", `#${route}`);
        }
    }

    document.addEventListener("click", (e) => {
        // only nav elements (anchors/buttons) should trigger routing —
        // the section wrappers also carry data-route for CSS, but we must
        // not treat them as nav links
        const link = e.target.closest("a[data-route], button[data-route]");
        if (!link) return;
        e.preventDefault();
        const route = link.getAttribute("data-route");
        const authMode = link.getAttribute("data-auth-mode");
        go(route, { authMode });
    });

    // hashchange fallback (works even if a preview overlay intercepts clicks)
    window.addEventListener("hashchange", () => {
        const r = (location.hash || "#landing").replace("#", "").split("#")[0];
        go(r);
    });

    // initial route from hash
    const initRoute = (location.hash || "#landing").replace("#", "").split("#")[0];
    go(VALID_ROUTES.includes(initRoute) ? initRoute : "landing");

    // ========================================================
    // HERO TERMINAL (typed animation)
    // ========================================================
    const TERM_SCRIPT = [
        { type: "cmd",  text: "$ curl https://api.featherless.ai/v1/chat/completions \\" },
        { type: "cmd",  text: "    -H \"Authorization: Bearer fl_•••••\" \\" },
        { type: "cmd",  text: "    -d '{ \"model\": \"deepseek-v3.2\", \"messages\": [...] }'" },
        { type: "dim",  text: "→ response: 1 completion. no memory. no tools. you ship the rest." },
        { type: "gap",  text: "" },
        { type: "cmd",  text: "$ curl https://api.hs-layer.dev/v1/chat \\" },
        { type: "cmd",  text: "    -H \"Authorization: Bearer hs_FL7x•••\" \\" },
        { type: "cmd",  text: "    -d '{ \"model\": \"deepseek-v3.2\", \"messages\": [...] }'" },
        { type: "ok",   text: "✓ memory hit: 6 facts recalled" },
        { type: "ok",   text: "✓ tool: web_search → 3 sources" },
        { type: "ok",   text: "✓ intent: analysis · cost $0.00084" },
        { type: "kw",   text: "→ response: grounded, stateful, production-ready." },
    ];

    async function runTerminal() {
        const host = $("#terminalBody");
        if (!host) return;
        host.innerHTML = "";

        for (const line of TERM_SCRIPT) {
            const el = document.createElement("span");
            el.className = `term-line term-${line.type === "gap" ? "dim" : line.type}`;
            host.appendChild(el);

            if (line.type === "gap") {
                el.textContent = "\u00A0";
                await sleep(160);
                continue;
            }

            // type
            el.classList.add("term-cur");
            for (let i = 0; i < line.text.length; i++) {
                el.textContent = line.text.slice(0, i + 1);
                await sleep(line.type === "cmd" ? 8 : 14);
            }
            el.classList.remove("term-cur");
            el.textContent = line.text + "\n";
            await sleep(line.type === "ok" ? 140 : 280);
        }

        // loop after pause
        await sleep(3200);
        runTerminal();
    }
    runTerminal();

    // ========================================================
    // AUTH — mode switch
    // ========================================================
    function setAuthMode(mode) {
        const isSignup = mode === "signup";
        $$(".auth__switch").forEach(b => {
            b.classList.toggle("is-active", b.getAttribute("data-mode") === mode);
        });
        $("#authTitle").textContent = isSignup ? "Create your workspace." : "Welcome back.";
        $("#authSub").textContent = isSignup
            ? "Sign up to start bridging your Featherless API key into an enhanced key."
            : "Sign in to your H&S workspace. Next you'll bridge your Featherless key.";
        $("#nameField").hidden = !isSignup;
        $("#authSubmit").textContent = isSignup ? "Create account & continue →" : "Continue →";
    }
    $$(".auth__switch").forEach(b => {
        b.addEventListener("click", () => setAuthMode(b.getAttribute("data-mode")));
    });

    function proceedFromAuth() {
        const email = $("#authForm input[type='email']")?.value?.trim();
        if (!email) {
            toast("Enter an email to continue");
            $("#authForm input[type='email']")?.focus();
            return;
        }
        toast("Signed in · bridge your key next");
        go("onboarding");
    }
    $("#authForm")?.addEventListener("submit", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSubmit")?.addEventListener("click", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSsoBtn")?.addEventListener("click", () => { toast("SSO · visual prototype"); go("onboarding"); });

    // ========================================================
    // API BRIDGE — generate enhanced key
    // ========================================================
    const bridgeInput   = $("#flKeyInput");
    const bridgeOut     = $("#hsKeyOutput");
    const bridgeFill    = $("#bridgePipeFill");
    const bridgeLabel   = $("#bridgePipeLabel");
    const bridgeRunBtn  = $("#bridgeRunBtn");
    const bridgeCont    = $("#bridgeContinueBtn");
    const bridgeLog     = $("#bridgeLog");

    function genHsKey(fl) {
        const seed = (fl || "default").replace(/[^a-zA-Z0-9]/g, "").slice(-6).padStart(6, "x");
        const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        let body = "";
        for (let i = 0; i < 20; i++) body += chars[randInt(0, chars.length - 1)];
        return `hs_FL${seed}${body}`;
    }

    function logLine(txt, cls = "log-dim") {
        const s = document.createElement("span");
        s.className = `log-line ${cls}`;
        s.textContent = txt;
        bridgeLog.appendChild(s);
        bridgeLog.scrollTop = bridgeLog.scrollHeight;
    }

    async function runBridge() {
        const fl = (bridgeInput.value || "").trim();
        if (!fl) {
            toast("Paste a Featherless key first");
            bridgeInput.focus();
            return;
        }
        bridgeRunBtn.disabled = true;
        bridgeLog.innerHTML = "";
        bridgeFill.style.width = "0%";
        bridgeCont.hidden = true;

        const steps = [
            { w: 18,  lbl: "VERIFY",    log: "› verifying featherless key", ok: "✓ key valid · tier: premium" },
            { w: 42,  lbl: "INTROSPECT", log: "› probing available models", ok: "✓ 30,184 models reachable" },
            { w: 68,  lbl: "BIND",      log: "› binding memory + tool layer", ok: "✓ sandbox provisioned" },
            { w: 88,  lbl: "SIGN",      log: "› signing enhanced key", ok: "✓ hmac:sha256 · rotated 90d" },
            { w: 100, lbl: "READY",     log: "› enhanced key ready", ok: "✓ drop-in ready — same endpoints" },
        ];

        bridgeOut.textContent = "hs_•••• transforming ••••";

        for (const s of steps) {
            logLine(s.log, "log-dim");
            bridgeFill.style.width = s.w + "%";
            bridgeLabel.textContent = s.lbl;
            await sleep(420);
            logLine(s.ok, "log-ok");
        }

        const newKey = genHsKey(fl);
        bridgeOut.textContent = newKey;
        $("#dashKeyShort").textContent = newKey.slice(0, 7) + "···" + newKey.slice(-4);
        bridgeRunBtn.disabled = false;
        bridgeRunBtn.textContent = "Regenerate";
        bridgeCont.hidden = false;
        toast("Enhanced key generated");
    }
    bridgeRunBtn?.addEventListener("click", runBridge);
    bridgeCont?.addEventListener("click", () => go("dashboard"));

    // ========================================================
    // DASHBOARD — tab switching
    // ========================================================
    $$(".dash__navbtn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tab = btn.getAttribute("data-tab");
            $$(".dash__navbtn").forEach(b => b.classList.toggle("is-active", b === btn));
            $$(".dash__panel").forEach(p => p.classList.toggle("is-active", p.getAttribute("data-panel") === tab));
        });
    });

    // ========================================================
    // COMPARE TAB — A/B simulation
    // ========================================================
    const compareInput = $("#compareInput");
    const compareRun   = $("#compareRunBtn");
    const compareModel = $("#compareModel");

    // chip suggestions
    $$(".suggest").forEach(b => {
        b.addEventListener("click", () => {
            compareInput.value = b.getAttribute("data-prompt");
            compareInput.focus();
        });
    });

    // scripted responses for demo variety
    const RAW_RESPONSES = [
        "Based on general knowledge, churn rates vary by industry. SaaS typically ranges 5–7% monthly. Without access to your data, I cannot compute your specific Q3 churn.",
        "DeepSeek V3.2 is a 685B parameter mixture-of-experts model focused on reasoning and agentic tasks. Exact release notes are not available in my training data.",
        "I don't have access to your telemetry or the current date. I can describe how a 30-day rolling average is computed mathematically if that helps.",
    ];

    const ENH_RESPONSES = [
        `Your Q3 churn was **4.2%** (down from 5.1% in Q2) — computed from workspace telemetry. SaaS industry median for Q3 2025 sits at **5.6%** per the latest OpenSaaS benchmark, so you're ~1.4pp better than peers. The improvement tracks your March onboarding redesign.`,
        `DeepSeek V3.2 (685B MoE) — released via Featherless 2025-12-14. Key changes: **+32% agentic benchmark**, **256k context stable**, **tool-call latency -40%**. I retrieved this from featherless.ai/blog and the official HF model card.`,
        `Your 30-day rolling average latency is **p50 = 184ms, p95 = 612ms**, computed across 142,883 requests. Trend: **-8% vs previous 30d window**. Top contributor: DeepSeek-V3.2 (2.1M tokens, $12.40 spend).`,
    ];

    const THOUGHTS_BY_INTENT = {
        analysis: [
            ["RECALL",   "accessing unified memory · 6 facts matched"],
            ["TOOL",     "web_search('saas churn benchmark q3 2025') → 4 sources"],
            ["TOOL",     "sql_exec('select churn_rate from ...') → 12 rows"],
            ["REASON",   "synthesising across 3 contexts"],
            ["RESPOND",  "streaming grounded answer"],
        ],
        summary: [
            ["RECALL",   "no personal context required"],
            ["TOOL",     "web_search('deepseek v3.2 release notes') → 3 sources"],
            ["TOOL",     "fetch(featherless.ai/blog/deepseek-v3-2)"],
            ["REASON",   "extracting changelog bullets"],
            ["RESPOND",  "streaming summary"],
        ],
        compute: [
            ["RECALL",   "workspace analytics scope located"],
            ["TOOL",     "math_exec('rolling_avg(latency_ms, 30d)')"],
            ["TOOL",     "code_exec(python) · 142,883 rows"],
            ["REASON",   "formatting numeric output"],
            ["RESPOND",  "streaming result"],
        ],
    };

    function detectIntent(q) {
        const s = q.toLowerCase();
        if (/(summar|release|what is|explain|docs)/.test(s)) return "summary";
        if (/(compute|average|avg|sum|rolling|calc|math|count)/.test(s)) return "compute";
        return "analysis";
    }
    function pickResponse(q, arr) {
        const intent = detectIntent(q);
        const i = intent === "summary" ? 1 : intent === "compute" ? 2 : 0;
        return arr[i];
    }

    async function streamInto(el, text, speed = 9) {
        el.innerHTML = "";
        el.classList.add("streaming");
        const p = document.createElement("p");
        el.appendChild(p);
        for (let i = 0; i < text.length; i++) {
            p.textContent = text.slice(0, i + 1);
            // faster on long texts
            if (i % 3 === 0) await sleep(speed);
        }
        el.classList.remove("streaming");
    }

    function formatMarkdownish(text) {
        return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    }

    async function runCompare() {
        const q = (compareInput.value || "").trim();
        if (!q) { toast("Type a prompt to compare"); compareInput.focus(); return; }

        compareRun.disabled = true;
        const model = compareModel.value;
        const intent = detectIntent(q);

        // reset
        $("#rawBody").innerHTML = `<div class="pane__empty"><span class="mono-dim">// ${model} · thinking…</span></div>`;
        $("#enhBody").innerHTML = "";
        $("#rawLatency").textContent = "…";
        $("#rawTps").textContent = "…";
        $("#rawTokens").textContent = "…";
        $("#enhCost").textContent = "…";
        $("#enhTools").textContent = "…";
        $("#enhIntent").textContent = "…";

        // Enhanced side: thought process FIRST, then stream response
        const thoughtBox = document.createElement("div");
        thoughtBox.className = "thought";
        $("#enhBody").appendChild(thoughtBox);

        const steps = THOUGHTS_BY_INTENT[intent];
        for (const [tag, txt] of steps) {
            const line = document.createElement("div");
            line.className = "thought-line";
            line.innerHTML = `<span class="mono-dim">${tag}</span><span class="tl-ok">${txt}</span>`;
            thoughtBox.appendChild(line);
            // reveal with small delay
            requestAnimationFrame(() => line.classList.add("show"));
            await sleep(240);
        }

        // raw response appears "fast" but dumb
        await sleep(300);
        const rawText = pickResponse(q, RAW_RESPONSES);
        const rawLat = randInt(310, 520);
        const rawTps = randInt(58, 86);
        const rawTok = randInt(64, 140);
        const rawBodyEl = $("#rawBody");
        rawBodyEl.innerHTML = "";
        const rawP = document.createElement("p");
        rawBodyEl.appendChild(rawP);
        // type raw
        (async () => {
            rawBodyEl.classList.add("streaming");
            for (let i = 0; i < rawText.length; i++) {
                rawP.textContent = rawText.slice(0, i + 1);
                if (i % 3 === 0) await sleep(10);
            }
            rawBodyEl.classList.remove("streaming");
            $("#rawLatency").textContent = rawLat + " ms";
            $("#rawTps").textContent = rawTps + " tok/s";
            $("#rawTokens").textContent = rawTok;
        })();

        // enhanced response
        const enhText = pickResponse(q, ENH_RESPONSES);
        const target = document.createElement("p");
        $("#enhBody").appendChild(target);
        $("#enhBody").classList.add("streaming");
        // stream with bold markers
        for (let i = 0; i < enhText.length; i++) {
            target.innerHTML = formatMarkdownish(enhText.slice(0, i + 1));
            if (i % 3 === 0) await sleep(9);
        }
        $("#enhBody").classList.remove("streaming");

        const toolCount = intent === "compute" ? 2 : 2;
        const cost = (rand(0.0006, 0.0018)).toFixed(5);
        $("#enhCost").textContent = "$" + cost;
        $("#enhTools").textContent = toolCount + " used";
        $("#enhIntent").textContent = intent;

        compareRun.disabled = false;
    }
    compareRun?.addEventListener("click", runCompare);
    $("#compareForm")?.addEventListener("submit", (e) => { e.preventDefault(); runCompare(); });

    // ========================================================
    // MEMORY TAB
    // ========================================================
    const MEMORY_SEED = [
        { id: 1, fact: "Prefers concise, bullet-pointed answers under 120 words",           tag: "preference", source: "user setting",               learned: "2026-01-18", conf: 99, pinned: true  },
        { id: 2, fact: "Workspace primary model is DeepSeek-V3.2 for analytics tasks",      tag: "context",    source: "inferred · 142 requests",    learned: "2026-02-02", conf: 96, pinned: true  },
        { id: 3, fact: "Team name is 'ada-labs' with 12 developers",                        tag: "identity",   source: "onboarding",                  learned: "2026-01-12", conf: 100, pinned: false },
        { id: 4, fact: "Q3 2025 churn rate was 4.2% (down from 5.1% in Q2)",                tag: "context",    source: "analytics.csv upload",       learned: "2026-01-30", conf: 94, pinned: false },
        { id: 5, fact: "Usually codes in TypeScript + Rust, never Java",                    tag: "preference", source: "inferred · 28 conversations", learned: "2026-02-04", conf: 88, pinned: false },
        { id: 6, fact: "Internal API base URL is api.ada-labs.internal (treat as secret)",  tag: "secret",     source: "tool config",                learned: "2026-02-05", conf: 100, pinned: true  },
    ];
    let memory = [...MEMORY_SEED];
    let memoryTag = "all";
    let memoryQuery = "";

    function renderMemory() {
        const tb = $("#memoryTbody");
        tb.innerHTML = "";
        const filtered = memory.filter(m => {
            if (memoryTag !== "all" && m.tag !== memoryTag) return false;
            if (memoryQuery && !(`${m.fact} ${m.source} ${m.tag}`).toLowerCase().includes(memoryQuery.toLowerCase())) return false;
            return true;
        });
        if (!filtered.length) {
            tb.innerHTML = `<tr><td colspan="6" style="padding:32px;text-align:center;color:var(--text-mute);font-family:var(--font-mono);font-size:12px;">// no facts match</td></tr>`;
            $("#dashFactCount").textContent = memory.length;
            return;
        }
        filtered.forEach(m => {
            const tr = document.createElement("tr");
            tr.dataset.id = m.id;
            tr.innerHTML = `
                <td><span class="fact-text">${escapeHtml(m.fact)}</span></td>
                <td><span class="tag tag--muted">${m.tag}</span></td>
                <td><span class="mono-dim" style="font-size:12px">${escapeHtml(m.source)}</span></td>
                <td><span class="mono-dim" style="font-size:12px">${m.learned}</span></td>
                <td>
                    <div class="conf-bar">
                        <div class="conf-bar__track"><div class="conf-bar__fill" style="width:${m.conf}%"></div></div>
                        <span>${m.conf}%</span>
                    </div>
                </td>
                <td>
                    <div class="row-actions">
                        <button data-action="edit"   data-testid="memory-edit-${m.id}">edit</button>
                        <button data-action="forget" class="is-danger" data-testid="memory-forget-${m.id}">forget</button>
                    </div>
                </td>`;
            tb.appendChild(tr);
        });
        $("#dashFactCount").textContent = memory.length;
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    }

    $("#memoryTbody")?.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const tr = btn.closest("tr");
        const id = Number(tr.dataset.id);
        const action = btn.getAttribute("data-action");
        const item = memory.find(m => m.id === id);
        if (!item) return;

        if (action === "forget") {
            memory = memory.filter(m => m.id !== id);
            toast(`Fact forgotten`);
            renderMemory();
        } else if (action === "edit") {
            const td = tr.querySelector("td:first-child");
            const current = item.fact;
            td.innerHTML = `<input class="fact-input" value="${escapeHtml(current)}" />`;
            const input = td.querySelector("input");
            input.focus(); input.select();
            const save = () => {
                item.fact = input.value.trim() || current;
                renderMemory();
                toast("Fact updated");
            };
            input.addEventListener("blur", save, { once: true });
            input.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter") input.blur();
                if (ev.key === "Escape") renderMemory();
            });
        }
    });

    $("#memoryAddBtn")?.addEventListener("click", () => {
        const id = Math.max(0, ...memory.map(m => m.id)) + 1;
        memory.unshift({
            id,
            fact: "New fact — click edit to describe…",
            tag: "context",
            source: "manual",
            learned: new Date().toISOString().slice(0, 10),
            conf: 100,
            pinned: false,
        });
        renderMemory();
        toast("Fact added");
    });

    $("#memorySearch")?.addEventListener("input", (e) => {
        memoryQuery = e.target.value;
        renderMemory();
    });
    $$(".memfilter__tags .tag--btn").forEach(btn => {
        btn.addEventListener("click", () => {
            $$(".memfilter__tags .tag--btn").forEach(b => b.classList.toggle("is-active", b === btn));
            memoryTag = btn.getAttribute("data-tag");
            renderMemory();
        });
    });
    renderMemory();

    // ========================================================
    // SKILL STORE
    // ========================================================
    const SKILLS = [
        { id: "search",  name: "Web Search",      on: true,  cost: "~180ms",
          desc: "Grounds answers in up-to-date sources via a vector+BM25 retriever.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>` },
        { id: "math",    name: "Math Engine",     on: true,  cost: "~12ms",
          desc: "Deterministic arithmetic, stats, symbolic algebra. No hallucinated numbers.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5h16M4 12h10M4 19h16"/><path d="m17 9 4 4M21 9l-4 4"/></svg>` },
        { id: "code",    name: "Code Exec",       on: true,  cost: "~50ms",
          desc: "Sandboxed Python + JS runtime with 50ms budget and memory caps.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="m8 7-4 5 4 5M16 7l4 5-4 5M14 4l-4 16"/></svg>` },
        { id: "memory",  name: "Long-term Memory", on: false, cost: "~0.4ms",
          desc: "Persistent typed fact store, per-workspace and per-user.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 6h16v12H4z"/><path d="M8 10h8M8 14h6"/></svg>` },
        { id: "browser", name: "Browser Agent",   on: false, cost: "~800ms",
          desc: "Headless browser for tasks that require login, JS, or multi-step nav.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16"/><path d="M3 9h18"/></svg>` },
        { id: "vision",  name: "Vision",          on: false, cost: "~220ms",
          desc: "Image understanding for any vision-capable Featherless model.",
          icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>` },
    ];

    function renderSkills() {
        const grid = $("#skillsGrid");
        if (!grid) return;
        grid.innerHTML = "";
        SKILLS.forEach(s => {
            const card = document.createElement("article");
            card.className = "skill" + (s.on ? " is-on" : "");
            card.dataset.id = s.id;
            card.setAttribute("data-testid", `skill-${s.id}`);
            card.innerHTML = `
                <header class="skill__head">
                    <div class="skill__icon">${s.icon}</div>
                    <div class="toggle ${s.on ? "is-on" : ""}" data-testid="skill-toggle-${s.id}" role="switch" aria-checked="${s.on}"></div>
                </header>
                <div>
                    <h4>${s.name}</h4>
                </div>
                <p>${s.desc}</p>
                <div class="skill__foot">
                    <span class="skill__cost">overhead · ${s.cost}</span>
                    <span class="mono-dim">${s.on ? "ENABLED" : "OFF"}</span>
                </div>`;
            grid.appendChild(card);
        });
        const on = SKILLS.filter(s => s.on).length;
        $("#skillsTotal").textContent = `${on} enabled / ${SKILLS.length} available`;
        $("#dashSkillCount").textContent = `${on} on`;
    }

    document.addEventListener("click", (e) => {
        const t = e.target.closest(".skill");
        if (!t || !t.contains(e.target.closest(".toggle, .skill__head, .skill__foot, h4, p, .skill__icon"))) {
            // only react on clicks within a skill card
        }
        const skillCard = e.target.closest(".skill");
        if (!skillCard) return;
        const id = skillCard.dataset.id;
        const s = SKILLS.find(x => x.id === id);
        if (!s) return;
        s.on = !s.on;
        renderSkills();
        toast(`${s.name} · ${s.on ? "enabled" : "disabled"}`);
    });
    renderSkills();

    // ========================================================
    // TOOL BUILDER
    // ========================================================
    const TOOLS = [
        {
            name: "weather.js",
            code:
`// Tool: weather
// Runs in a sandboxed isolate. Return value is sent back to the model.
// Featherless model will call this when intent matches schema.intent.

export const schema = {
    intent: "weather.current",
    params: { city: "string" },
    returns: { tempC: "number", condition: "string" }
};

export async function run({ city }) {
    const res = await fetch(\`https://wttr.in/\${encodeURIComponent(city)}?format=j1\`);
    const j = await res.json();
    return {
        tempC: Number(j.current_condition[0].temp_C),
        condition: j.current_condition[0].weatherDesc[0].value
    };
}`
        },
        {
            name: "crm.lookup.js",
            code:
`// Tool: crm.lookup — look up an account by email in the internal CRM.
export const schema = {
    intent: "crm.lookup",
    params: { email: "string" },
    returns: { account: "object" }
};

export async function run({ email }, ctx) {
    const r = await ctx.http.get(\`\${ctx.env.CRM_BASE}/accounts?email=\${email}\`, {
        headers: { Authorization: \`Bearer \${ctx.env.CRM_TOKEN}\` }
    });
    if (!r.ok) throw new Error("CRM lookup failed: " + r.status);
    const data = await r.json();
    return { account: data.account };
}`
        },
        {
            name: "metrics.rollup.js",
            code:
`// Tool: metrics.rollup — compute a rolling average over workspace telemetry.
export const schema = {
    intent: "metrics.rollup",
    params: { field: "string", windowDays: "number" },
    returns: { avg: "number", n: "number" }
};

export async function run({ field, windowDays }, ctx) {
    const rows = await ctx.db.query(
        "SELECT " + field + " FROM telemetry WHERE ts > now() - interval '" + windowDays + " days'"
    );
    const values = rows.map(r => r[field]).filter(Number.isFinite);
    const avg = values.reduce((a,b)=>a+b,0) / (values.length || 1);
    return { avg: Number(avg.toFixed(2)), n: values.length };
}`
        }
    ];
    let activeTool = 0;

    function renderToolList() {
        const list = $("#toolList");
        list.innerHTML = "";
        TOOLS.forEach((t, i) => {
            const li = document.createElement("li");
            li.className = i === activeTool ? "is-active" : "";
            li.dataset.i = i;
            li.setAttribute("data-testid", `tool-file-${i}`);
            li.innerHTML = `<span>${escapeHtml(t.name)}</span><span class="ide__dot"></span>`;
            list.appendChild(li);
        });
    }
    function loadTool(i) {
        activeTool = i;
        const t = TOOLS[i];
        $("#toolActiveName").textContent = t.name;
        $("#toolCode").value = t.code;
        updateGutter();
        renderToolList();
    }
    function updateGutter() {
        const text = $("#toolCode").value;
        const lines = text.split("\n").length;
        const g = $("#ideGutter");
        g.innerHTML = Array.from({ length: lines }, (_, i) => `<div>${i + 1}</div>`).join("");
    }

    $("#toolList")?.addEventListener("click", (e) => {
        const li = e.target.closest("li"); if (!li) return;
        TOOLS[activeTool].code = $("#toolCode").value; // persist before switch
        loadTool(Number(li.dataset.i));
    });
    $("#toolCode")?.addEventListener("input", () => {
        TOOLS[activeTool].code = $("#toolCode").value;
        updateGutter();
    });
    $("#toolCode")?.addEventListener("scroll", () => {
        $("#ideGutter").scrollTop = $("#toolCode").scrollTop;
    });

    $("#toolAddBtn")?.addEventListener("click", () => {
        const n = TOOLS.length + 1;
        TOOLS.push({
            name: `untitled_${n}.js`,
            code:
`// New tool scaffold
export const schema = {
    intent: "untitled.${n}",
    params: {},
    returns: {}
};

export async function run(params, ctx) {
    return { ok: true };
}`
        });
        loadTool(TOOLS.length - 1);
        toast("New tool scaffolded");
    });

    $("#toolRunBtn")?.addEventListener("click", async () => {
        const console_ = $("#toolConsole");
        console_.innerHTML = "";
        const t = TOOLS[activeTool];
        const logs = [
            ["c-dim",  `› compiling ${t.name}`],
            ["c-dim",  `› binding sandbox · mem=64mb · wall=50ms`],
            ["c-dim",  `› intent=${(t.code.match(/intent:\s*"([^"]+)"/) || [])[1] || "unknown"}`],
            ["c-ok",   `✓ built in 38ms`],
            ["c-ok",   `✓ run({city:"Tokyo"}) → { tempC: 12, condition: "Partly cloudy" }`],
            ["c-dim",  `› exit 0 · 42ms wall · 0 warnings`],
        ];
        for (const [cls, txt] of logs) {
            const line = document.createElement("div");
            line.className = cls;
            line.textContent = txt;
            console_.appendChild(line);
            await sleep(180);
        }
        toast("Tool run · exit 0");
    });

    loadTool(0);

})();

