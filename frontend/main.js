/* ============================================================
   H&S Layer — Prototype logic
   Vanilla JS. No libraries. Mocked interactions.
   ============================================================ */

(() => {
    "use strict";

    // ---------- API Configuration (LOCAL ONLY) ----------
    const API_BASE = "http://localhost:8000";
    let currentUserId = null; // User must sign up/sign in
    let currentAuroraKey = null; // Generated after auth

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
        // Generate a deterministic UUID from email using a simple hash
        // This ensures the same email always gets the same UUID
        function emailToUUID(email) {
            // Simple hash function to convert email to UUID
            let hash = 0;
            for (let i = 0; i < email.length; i++) {
                hash = ((hash << 5) - hash) + email.charCodeAt(i);
                hash = hash & hash; // Convert to 32bit integer
            }
            // Convert hash to hex and pad to create UUID format
            const hex = Math.abs(hash).toString(16).padStart(8, '0');
            // Create a valid UUID v4 format
            return `${hex.slice(0,8)}-${hex.slice(0,4)}-4${hex.slice(0,3)}-a${hex.slice(0,3)}-${hex.slice(0,12).padEnd(12, '0')}`;
        }
        currentUserId = emailToUUID(email.toLowerCase());
        toast(`Welcome ${email}! Set up your API key next`);
        go("onboarding");
    }
    $("#authForm")?.addEventListener("submit", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSubmit")?.addEventListener("click", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSsoBtn")?.addEventListener("click", () => { 
        // Generate a demo user ID for SSO
        currentUserId = "00000000-0000-0000-0000-000000000001";
        toast("SSO · visual prototype"); 
        go("onboarding"); 
    });

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
        
        // Check if user is logged in
        if (!currentUserId) {
            toast("Please sign in first");
            go("auth");
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

        // Step 1: Store key for BOTH openrouter AND featherless (same key works for testing)
        try {
            logLine("› storing api key for openrouter + featherless", "log-dim");
            bridgeFill.style.width = "18%";
            bridgeLabel.textContent = "VERIFY";

            for (const provider of ["openrouter", "featherless"]) {
                const res = await fetch(`${API_BASE}/apikey`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: currentUserId, provider, api_key: fl })
                });
                if (!res.ok) {
                    const errorText = await res.text();
                    console.error(`Failed to store key for ${provider}:`, errorText);
                    throw new Error(`Failed to store key for ${provider}: ${res.status}`);
                }
            }

            logLine("✓ key stored for openrouter + featherless", "log-ok");
            await sleep(420);
        } catch (error) {
            logLine("✗ " + error.message, "log-err");
            bridgeRunBtn.disabled = false;
            toast("Failed to store API key");
            return;
        }

        // Step 2: Generate Aurora enhanced key
        try {
            logLine("› generating enhanced aurora key", "log-dim");
            bridgeFill.style.width = "68%";
            bridgeLabel.textContent = "BIND";
            
            const auroraResponse = await fetch(`${API_BASE}/auth/issue-key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: currentUserId,
                    name: "H&S Enhanced Key",
                    scopes: ["chat", "memory", "tools", "skills"]
                })
            });
            
            if (!auroraResponse.ok) {
                throw new Error("Failed to generate Aurora key");
            }
            
            const auroraData = await auroraResponse.json();
            currentAuroraKey = auroraData.api_key;
            
            logLine("✓ aurora key generated", "log-ok");
            await sleep(420);
            
            bridgeFill.style.width = "100%";
            bridgeLabel.textContent = "READY";
            logLine("› enhanced key ready", "log-dim");
            await sleep(200);
            logLine("✓ drop-in ready — same endpoints", "log-ok");

            bridgeOut.textContent = currentAuroraKey;
            const dashKeyShortEl = $("#dashKeyShort");
            if (dashKeyShortEl) {
                dashKeyShortEl.textContent = currentAuroraKey.slice(0, 10) + "···" + currentAuroraKey.slice(-6);
            }
            
            // Fill in the compare form
            const compareAuroraKeyEl = $("#compareAuroraKey");
            if (compareAuroraKeyEl) {
                compareAuroraKeyEl.value = currentAuroraKey;
            }
            const compareUserIdEl = $("#compareUserId");
            if (compareUserIdEl) {
                compareUserIdEl.value = currentUserId;
            }
            
            bridgeRunBtn.disabled = false;
            bridgeRunBtn.textContent = "Regenerate";
            bridgeCont.hidden = false;
            toast("Enhanced key generated successfully!");
            
            // Update API key display if on that tab
            const apikeyDisplay = $("#apikeyDisplay");
            if (apikeyDisplay) {
                apikeyDisplay.textContent = "aurora_live_••••••••••••••••••••";
            }
            const apikeyUserId = $("#apikeyUserId");
            if (apikeyUserId) {
                apikeyUserId.textContent = currentUserId;
            }
            
        } catch (error) {
            logLine("✗ failed to generate aurora key: " + error.message, "log-err");
            bridgeRunBtn.disabled = false;
            toast("Failed to generate enhanced key");
            return;
        }
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
            if (tab === "memory") loadMemory();
            if (tab === "skills") loadSkills();
            if (tab === "tools") loadTools();
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
        return text
            // Code blocks with syntax highlighting
            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                const language = lang || 'text';
                const highlighted = highlightCode(code.trim(), language);
                return '<div class="code-block-container"><div class="code-block-header"><span class="code-block-lang">' + language.toUpperCase() + '</span><button class="code-copy-btn" onclick="copyCodeBlock(this)" data-code="' + encodeURIComponent(code.trim()) + '">Copy</button></div><pre class="code-block-content"><code>' + highlighted + '</code></pre></div>';
            })
            // Inline code
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
            // Bold text
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            // Italic text
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            // Headers
            .replace(/^### (.*$)/gm, '<h3 class="md-header">$1</h3>')
            .replace(/^## (.*$)/gm, '<h2 class="md-header">$1</h2>')
            .replace(/^# (.*$)/gm, '<h1 class="md-header">$1</h1>')
            // Lists
            .replace(/^\* (.+)$/gm, '<li class="md-list-item">$1</li>')
            .replace(/(<li class="md-list-item">.*<\/li>)/gs, '<ul class="md-list">$1</ul>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="md-link">$1</a>');
    }

    function highlightCode(code, language) {
        // Enhanced syntax highlighting for common languages
        if (!code) return '';
        
        // Escape HTML first
        let highlighted = code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        const lang = language.toLowerCase();
        
        if (lang === 'python') {
            // Python syntax highlighting
            highlighted = highlighted
                // Comments (must be first to avoid highlighting keywords in comments)
                .replace(/(#.*$)/gm, '<span class="syntax-comment">$1</span>')
                // Strings (triple quotes first, then single/double)
                .replace(/("""[\s\S]*?"""|'''[\s\S]*?''')/g, '<span class="syntax-string">$1</span>')
                .replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="syntax-string">$1</span>')
                // Keywords
                .replace(/\b(def|class|if|elif|else|for|while|try|except|finally|import|from|return|yield|async|await|with|as|lambda|pass|break|continue|global|nonlocal|raise|assert|del|in|is|not|and|or)\b/g, '<span class="syntax-keyword">$1</span>')
                // Built-in functions
                .replace(/\b(print|input|len|range|str|int|float|list|dict|set|tuple|bool|type|isinstance|enumerate|zip|map|filter|sum|max|min|abs|round|sorted|reversed|open|read|write|close)\b/g, '<span class="syntax-builtin">$1</span>')
                // Function definitions (def function_name)
                .replace(/\b(def)\s+([a-zA-Z_][a-zA-Z0-9_]*)/g, '<span class="syntax-keyword">$1</span> <span class="syntax-function">$2</span>')
                // Class definitions (class ClassName)
                .replace(/\b(class)\s+([a-zA-Z_][a-zA-Z0-9_]*)/g, '<span class="syntax-keyword">$1</span> <span class="syntax-class">$2</span>')
                // Numbers
                .replace(/\b(\d+\.?\d*)\b/g, '<span class="syntax-number">$1</span>')
                // Boolean and None
                .replace(/\b(True|False|None)\b/g, '<span class="syntax-constant">$1</span>');
                
        } else if (lang === 'javascript' || lang === 'js') {
            // JavaScript syntax highlighting
            highlighted = highlighted
                .replace(/(\/\/.*$)/gm, '<span class="syntax-comment">$1</span>')
                .replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="syntax-comment">$1</span>')
                .replace(/(`(?:[^`\\]|\\.)*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="syntax-string">$1</span>')
                .replace(/\b(const|let|var|function|return|if|else|for|while|async|await|try|catch|throw|new|class|extends|import|export|default|case|switch|break|continue)\b/g, '<span class="syntax-keyword">$1</span>')
                .replace(/\b(console|document|window|Array|Object|String|Number|Boolean|Math|Date|JSON|Promise|setTimeout|setInterval)\b/g, '<span class="syntax-builtin">$1</span>')
                .replace(/\b(\d+\.?\d*)\b/g, '<span class="syntax-number">$1</span>')
                .replace(/\b(true|false|null|undefined)\b/g, '<span class="syntax-constant">$1</span>');
                
        } else if (lang === 'typescript' || lang === 'ts') {
            // TypeScript syntax highlighting
            highlighted = highlighted
                .replace(/(\/\/.*$)/gm, '<span class="syntax-comment">$1</span>')
                .replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="syntax-comment">$1</span>')
                .replace(/(`(?:[^`\\]|\\.)*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="syntax-string">$1</span>')
                .replace(/\b(interface|type|enum|declare|const|let|var|function|return|if|else|for|while|async|await|try|catch|throw|new|class|extends|implements|import|export|default|public|private|protected|readonly)\b/g, '<span class="syntax-keyword">$1</span>')
                .replace(/\b(\d+\.?\d*)\b/g, '<span class="syntax-number">$1</span>')
                .replace(/\b(true|false|null|undefined)\b/g, '<span class="syntax-constant">$1</span>');
        }
        
        return highlighted;
    }

    function copyCodeBlock(button) {
        const code = decodeURIComponent(button.getAttribute('data-code'));
        navigator.clipboard.writeText(code).then(() => {
            const originalText = button.textContent;
            button.textContent = '✓ Copied';
            button.classList.add('copied');
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        });
    }
    // Make it globally available for onclick
    window.copyCodeBlock = copyCodeBlock;

    async function runCompare() {
        const q = (compareInput?.value || "").trim();
        if (!q) { toast("Type a prompt to compare"); compareInput?.focus(); return; }
        
        // Get credentials from form inputs (they're auto-filled after key generation)
        const auroraKey = $("#compareAuroraKey")?.value || currentAuroraKey;
        const userId = $("#compareUserId")?.value || currentUserId;
        
        if (!auroraKey) { 
            toast("Enter your Aurora key first"); 
            $("#compareAuroraKey")?.focus();
            return; 
        }
        
        if (!userId) {
            toast("Please sign in first");
            go("auth");
            return;
        }

        compareRun.disabled = true;
        const model = compareModel?.value || "openrouter/auto";
        const intent = detectIntent(q);

        // reset UI
        $("#rawBody").innerHTML = `<div class="pane__empty"><span class="mono-dim">// ${model} · thinking…</span></div>`;
        $("#enhBody").innerHTML = `<div class="pane__empty"><span class="mono-dim">// enhanced · thinking…</span></div>`;
        $("#rawLatency").textContent = "…";
        $("#rawTps").textContent = "…";
        $("#rawTokens").textContent = "…";
        $("#enhCost").textContent = "…";
        $("#enhTools").textContent = "…";
        $("#enhIntent").textContent = "…";

        // Show thought process on enhanced side while waiting
        const thoughtBox = document.createElement("div");
        thoughtBox.className = "thought";
        $("#enhBody").innerHTML = "";
        $("#enhBody").appendChild(thoughtBox);

        const steps = THOUGHTS_BY_INTENT[intent] || THOUGHTS_BY_INTENT.analysis;
        const thoughtPromise = (async () => {
            for (const [tag, txt] of steps) {
                const line = document.createElement("div");
                line.className = "thought-line";
                line.innerHTML = `<span class="mono-dim">${tag}</span><span class="tl-ok">${txt}</span>`;
                thoughtBox.appendChild(line);
                requestAnimationFrame(() => line.classList.add("show"));
                await sleep(240);
            }
        })();

        // Call /v1/compare which runs both raw + enhanced in one shot
        try {
            console.log("Calling /v1/compare with:", { userId, auroraKey: auroraKey.slice(0, 20) + "..." });
            const res = await fetch(`${API_BASE}/v1/compare`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${auroraKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user_id: userId,
                    input: q,
                    provider: "openrouter",
                    model: "openrouter/auto",
                    memory_scope: "user"
                })
            });

            await thoughtPromise;

            if (!res.ok) {
                let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
                try {
                    const errorData = await res.json();
                    console.error("API Error:", errorData);
                    if (errorData.detail) {
                        errorMsg = JSON.stringify(errorData.detail);
                    }
                } catch (e) {
                    errorMsg = await res.text();
                }
                throw new Error(errorMsg);
            }

            const data = await res.json();
            console.log("API Response:", data);
            const baseline = data.baseline;
            const tuned = data.tuned;

            // Raw pane
            const rawBodyEl = $("#rawBody");
            rawBodyEl.innerHTML = "";
            await streamInto(rawBodyEl, baseline.output || "(no response)");
            $("#rawLatency").textContent = (baseline.metrics?.latency_ms ?? "—") + " ms";
            $("#rawTps").textContent = baseline.metrics?.usage?.total_tokens ?? "—";
            $("#rawTokens").textContent = baseline.metrics?.usage?.total_tokens ?? "—";

            // Enhanced pane
            const enhBodyEl = $("#enhBody");
            enhBodyEl.innerHTML = "";
            await streamInto(enhBodyEl, tuned.output || "(no response)");
            $("#enhCost").textContent = tuned.metrics?.estimated_cost_usd != null
                ? "$" + tuned.metrics.estimated_cost_usd.toFixed(5)
                : "$ —";
            $("#enhTools").textContent = (tuned.metrics?.tool_count ?? 0) + " used";
            $("#enhIntent").textContent = tuned.skill || intent;

            // Sidebar stats
            $("#dashModel").textContent = tuned.model || model;

        } catch (err) {
            console.error("Compare failed:", err);
            await thoughtPromise;
            
            // Parse error message for specific issues
            const errMsg = err.message || String(err);
            let userMessage = "API error";
            let detailMessage = errMsg;
            
            if (errMsg.includes("credits") || errMsg.includes("quota") || errMsg.includes("insufficient")) {
                userMessage = "⚠️ API Credits Exhausted";
                detailMessage = "Your OpenRouter API credits have run out. Please add credits to your OpenRouter account.";
            } else if (errMsg.includes("Invalid") || errMsg.includes("invalid") || errMsg.includes("uuid")) {
                userMessage = "⚠️ Invalid API Key or User ID";
                detailMessage = "Your Aurora key or User ID format is invalid. Please regenerate your keys.";
            } else if (errMsg.includes("rate limit") || errMsg.includes("429")) {
                userMessage = "⚠️ Rate Limited";
                detailMessage = "Too many requests. Please wait a moment and try again.";
            } else if (errMsg.includes("timeout") || errMsg.includes("ETIMEDOUT")) {
                userMessage = "⚠️ Request Timeout";
                detailMessage = "The request took too long. Please try again.";
            } else if (errMsg.includes("network") || errMsg.includes("fetch") || errMsg.includes("Failed to fetch")) {
                userMessage = "⚠️ Network Error";
                detailMessage = "Cannot connect to the API. Check if the backend is running on port 8000.";
            }
            
            toast(userMessage);
            $("#rawBody").innerHTML = `<div class="pane__empty" style="padding:20px;text-align:center;">
                <div style="font-size:24px;margin-bottom:10px;">❌</div>
                <div style="font-weight:600;margin-bottom:10px;">${escapeHtml(userMessage)}</div>
                <div class="mono-dim" style="font-size:12px;">${escapeHtml(detailMessage)}</div>
            </div>`;
            $("#enhBody").innerHTML = `<div class="pane__empty" style="padding:20px;text-align:center;">
                <div style="font-size:24px;margin-bottom:10px;">❌</div>
                <div style="font-weight:600;margin-bottom:10px;">${escapeHtml(userMessage)}</div>
                <div class="mono-dim" style="font-size:12px;">${escapeHtml(detailMessage)}</div>
            </div>`;
        }
        compareRun.disabled = false;
    }
    
    // Attach event listeners
    compareRun?.addEventListener("click", runCompare);
    $("#compareForm")?.addEventListener("submit", (e) => { e.preventDefault(); runCompare(); });

    // ========================================================
    // MEMORY TAB
    // ========================================================
    let memory = [];

    async function loadMemory() {
        if (!currentAuroraKey || !currentUserId) {
            console.log("Skipping memory load - no auth");
            return;
        }
        try {
            const response = await fetch(`${API_BASE}/v1/memory/context`, {
                method: "POST",
                headers: {
                    "X-Api-Key": currentAuroraKey,
                    "Authorization": `Bearer ${currentAuroraKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user_id: currentUserId,
                    query: "all facts",
                    memory_scope: "user",
                    top_k: 50
                })
            });
            if (response.ok) {
                const memoryData = await response.json();
                // Map structured_memories + retrieved_memories into display format
                const structured = memoryData.structured_memories || [];
                const retrieved = memoryData.retrieved_memories || [];
                const seen = new Set();
                memory = [];
                retrieved.forEach((m, i) => {
                    if (seen.has(m.text)) return;
                    seen.add(m.text);
                    memory.push({
                        id: i + 1,
                        fact: m.text,
                        tag: m.metadata?.fact_type || m.metadata?.kind || "context",
                        source: m.metadata?.role || "conversation",
                        learned: new Date().toISOString().slice(0, 10),
                        conf: Math.round((m.score || 0.8) * 100)
                    });
                });
                renderMemory();
            }
        } catch (error) {
            console.error("Failed to load memory:", error);
        }
    }

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
    let SKILLS = [];

    async function loadSkills() {
        if (!currentAuroraKey) {
            console.log("Skipping skills load - no auth");
            return;
        }
        try {
            const response = await fetch(`${API_BASE}/v1/skills`, {
                headers: { "X-Api-Key": currentAuroraKey }
            });
            if (response.ok) {
                const skillsData = await response.json();
                SKILLS = skillsData.map(skill => ({
                    id: skill.name,
                    name: skill.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    on: true,
                    cost: "~" + Math.floor(Math.random() * 200 + 50) + "ms",
                    desc: skill.description || "Specialized skill for domain-specific tasks",
                    icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24"/></svg>`
                }));
                renderSkills();
            }
        } catch (error) {
            console.error("Failed to load skills:", error);
        }
    }

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
    
    // Load real data from backend
    loadSkills();
    loadTools();
    loadMemory();
    renderSkills();

    // ========================================================
    // TOOL BUILDER
    // ========================================================
    let TOOLS = [];

    async function loadTools() {
        try {
            const response = await fetch(`${API_BASE}/tools`, {
                headers: { "X-Api-Key": currentAuroraKey || "" }
            });
            if (response.ok) {
                const toolsData = await response.json();
                TOOLS = toolsData.map(tool => ({
                    name: tool.name + ".js",
                    code: `// Tool: ${tool.name}
// Runs in a sandboxed isolate. Return value is sent back to the model.
// Featherless model will call this when intent matches schema.intent.

export const schema = {
    intent: "${tool.name}",
    params: ${JSON.stringify(tool.input_schema || {})},
    returns: { result: "any" }
};

export async function run(params) {
    // Tool implementation for ${tool.name}
    // ${tool.description}
    return { result: "Tool executed successfully" };
}`
                }));
                renderToolList();
                if (TOOLS.length > 0) {
                    loadTool(0);
                }
            }
        } catch (error) {
            console.error("Failed to load tools:", error);
            // Set default tool if API fails
            TOOLS = [{
                name: "example.js",
                code: `// Example tool\nexport const schema = {\n  intent: "example",\n  params: {},\n  returns: {}\n};\n\nexport async function run(params) {\n  return { ok: true };\n}`
            }];
            renderToolList();
            loadTool(0);
        }
    }
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

    // ========================================================
    // API KEY TAB
    // ========================================================
    function refreshApiKeyTab() {
        const display = $("#apikeyDisplay");
        const userId = $("#apikeyUserId");
        if (display) display.textContent = currentAuroraKey ? "aurora_live_••••••••••••••••••••" : "— generate a key first —";
        if (userId) userId.textContent = currentUserId;
    }

    let apikeyRevealed = false;
    $("#apikeyRevealBtn")?.addEventListener("click", () => {
        const display = $("#apikeyDisplay");
        if (!currentAuroraKey) { toast("No key yet — bridge your API key first"); return; }
        apikeyRevealed = !apikeyRevealed;
        display.textContent = apikeyRevealed ? currentAuroraKey : "aurora_live_••••••••••••••••••••";
        $("#apikeyRevealBtn").textContent = apikeyRevealed ? "Hide" : "Show";
    });

    $("#apikeyCopyBtn")?.addEventListener("click", () => {
        if (!currentAuroraKey) { toast("No key yet"); return; }
        navigator.clipboard.writeText(currentAuroraKey).then(() => toast("Aurora key copied!"));
    });

    $("#apikeyUserIdCopy")?.addEventListener("click", () => {
        navigator.clipboard.writeText(currentUserId).then(() => toast("User ID copied!"));
    });

    $("#apikeyTestBtn")?.addEventListener("click", async () => {
        if (!currentAuroraKey) { toast("No key yet"); return; }
        const result = $("#apikeyTestResult");
        result.hidden = false;
        result.textContent = "Testing key…";
        try {
            const res = await fetch(`${API_BASE}/v1/run`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${currentAuroraKey}`, "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: currentUserId, input: "ping", memory_scope: "user", provider: "openrouter", model: "openrouter/auto" })
            });
            const data = await res.json();
            result.textContent = `✓ Key valid\nskill: ${data.skill}\noutput: ${data.output?.slice(0,80)}…\nmemory_hits: ${data.metrics?.memory_hits}`;
            result.style.color = "#4ade80";
        } catch (e) {
            result.textContent = `✗ ${e.message}`;
            result.style.color = "#f87171";
        }
    });

    $("#apikeyRevokeBtn")?.addEventListener("click", async () => {
        if (!currentAuroraKey) { toast("No key to revoke"); return; }
        toast("Regenerating key…");
        try {
            const res = await fetch(`${API_BASE}/auth/issue-key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: currentUserId, name: "H&S Enhanced Key", scopes: ["chat","memory","tools","skills"] })
            });
            const data = await res.json();
            currentAuroraKey = data.api_key;
            apikeyRevealed = false;
            refreshApiKeyTab();
            toast("New key generated!");
        } catch(e) { toast("Failed: " + e.message); }
    });

    // ========================================================
    // DEV DOCS TAB
    // ========================================================
    const DOCS_SNIPPETS = {
        curl: {
            quickstart: `# Store your provider key once
curl -X POST http://localhost:8000/apikey \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "provider": "openrouter",
    "api_key": "sk-or-v1-..."
  }'

# Generate your Aurora enhanced key
curl -X POST http://localhost:8000/auth/issue-key \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "name": "My Key",
    "scopes": ["chat","memory","tools","skills"]
  }'`,
            chat: `curl -X POST http://localhost:8000/v1/run \\
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "input": "Debug my Python API performance",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
  }'`,
            compare: `curl -X POST http://localhost:8000/v1/compare \\
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "input": "What are the latest React 19 features?",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'`,
            memory: `# Store a fact
curl -X POST http://localhost:8000/v1/memory \\
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "text": "User prefers TypeScript over JavaScript",
    "kind": "preference",
    "memory_scope": "user"
  }'

# Retrieve memory context
curl -X POST http://localhost:8000/v1/memory/context \\
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "query": "language preferences",
    "memory_scope": "user"
  }'`,
            skill: `# Invoke the research skill directly
curl -X POST http://localhost:8000/v1/skills/research \\
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "input": "Latest AI developments in 2025"
  }'`
        },
        python: {
            quickstart: `import requests

API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY"
USER_ID = "YOUR_USER_ID"

headers = {
    "Authorization": f"Bearer {AURORA_KEY}",
    "Content-Type": "application/json"
}`,
            chat: `def chat(message, skill=None):
    payload = {
        "user_id": USER_ID,
        "input": message,
        "memory_scope": "user",
        "provider": "openrouter",
        "model": "openrouter/auto"
    }
    if skill:
        payload["skill_name"] = skill
    r = requests.post(f"{API_BASE}/v1/run", headers=headers, json=payload)
    data = r.json()
    print(f"Skill: {data['skill']}")
    print(f"Tools: {[t['name'] for t in data['tool_calls']]}")
    print(f"Memory hits: {data['metrics']['memory_hits']}")
    return data["output"]

# Auto-routes to best skill
print(chat("Debug my FastAPI performance issue"))`,
            compare: `def compare(prompt):
    r = requests.post(f"{API_BASE}/v1/compare", headers=headers, json={
        "user_id": USER_ID,
        "input": prompt,
        "provider": "openrouter",
        "model": "openrouter/auto",
        "memory_scope": "user"
    })
    data = r.json()
    print("RAW:", data["baseline"]["output"][:100])
    print("ENHANCED:", data["tuned"]["output"][:100])
    print("Skill used:", data["tuned"]["skill"])
    print("Latency gap:", data["delta"]["latency_gap_ms"], "ms")
    return data`,
            memory: `# Store a fact
requests.post(f"{API_BASE}/v1/memory", headers=headers, json={
    "user_id": USER_ID,
    "text": "User prefers TypeScript",
    "kind": "preference",
    "memory_scope": "user"
})

# Retrieve — shared across ALL Aurora keys for same user_id
r = requests.post(f"{API_BASE}/v1/memory/context", headers=headers, json={
    "user_id": USER_ID,
    "query": "language preferences",
    "memory_scope": "user",
    "top_k": 10
})
for m in r.json()["retrieved_memories"]:
    print(m["text"], "score:", m["score"])`,
            skill: `# Force a specific skill
r = requests.post(f"{API_BASE}/v1/skills/deep_research", headers=headers, json={
    "user_id": USER_ID,
    "input": "Compare GPT-4o vs Claude 3.5 Sonnet benchmarks"
})
data = r.json()
print(data["output"])
print("Tools used:", [t["name"] for t in data["tool_calls"]])`
        },
        javascript: {
            quickstart: `const API_BASE = "http://localhost:8000";
const AURORA_KEY = "aurora_live_YOUR_KEY";
const USER_ID = "YOUR_USER_ID";

const headers = {
  "Authorization": \`Bearer \${AURORA_KEY}\`,
  "Content-Type": "application/json"
};`,
            chat: `async function chat(message) {
  const res = await fetch(\`\${API_BASE}/v1/run\`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID,
      input: message,
      memory_scope: "user",
      provider: "openrouter",
      model: "openrouter/auto"
    })
  });
  const data = await res.json();
  console.log("Skill:", data.skill);
  console.log("Tools:", data.tool_calls.map(t => t.name));
  console.log("Memory hits:", data.metrics.memory_hits);
  return data.output;
}

await chat("What are the latest React 19 features?");`,
            compare: `async function compare(prompt) {
  const res = await fetch(\`\${API_BASE}/v1/compare\`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID, input: prompt,
      provider: "openrouter", model: "openrouter/auto",
      memory_scope: "user"
    })
  });
  const { baseline, tuned, delta } = await res.json();
  console.log("Raw:", baseline.output.slice(0, 100));
  console.log("Enhanced:", tuned.output.slice(0, 100));
  console.log("Latency gap:", delta.latency_gap_ms + "ms");
  console.log("Skill:", tuned.skill);
}`,
            memory: `// Store — shared across all keys for same user_id
await fetch(\`\${API_BASE}/v1/memory\`, {
  method: "POST", headers,
  body: JSON.stringify({
    user_id: USER_ID,
    text: "User prefers dark mode",
    kind: "preference",
    memory_scope: "user"
  })
});

// Retrieve
const res = await fetch(\`\${API_BASE}/v1/memory/context\`, {
  method: "POST", headers,
  body: JSON.stringify({
    user_id: USER_ID,
    query: "UI preferences",
    memory_scope: "user"
  })
});
const { retrieved_memories } = await res.json();`,
            skill: `// Invoke research skill with web search
const res = await fetch(\`\${API_BASE}/v1/skills/research\`, {
  method: "POST", headers,
  body: JSON.stringify({
    user_id: USER_ID,
    input: "Latest AI developments 2025"
  })
});
const data = await res.json();
console.log(data.output);
console.log("Tools:", data.tool_calls);`
        },
        typescript: {
            quickstart: `const API_BASE = "http://localhost:8000";
const AURORA_KEY = "aurora_live_YOUR_KEY";
const USER_ID = "YOUR_USER_ID";

interface RunResponse {
  conversation_id: string;
  skill: string;
  output: string;
  tool_calls: { name: string; input: object }[];
  metrics: { memory_hits: number; tool_count: number; usage: object };
}`,
            chat: `async function chat(message: string): Promise<string> {
  const res = await fetch(\`\${API_BASE}/v1/run\`, {
    method: "POST",
    headers: {
      "Authorization": \`Bearer \${AURORA_KEY}\`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: USER_ID,
      input: message,
      memory_scope: "user",
      provider: "openrouter",
      model: "openrouter/auto"
    })
  });
  const data: RunResponse = await res.json();
  return data.output;
}`,
            compare: `interface CompareResponse {
  baseline: { output: string; metrics: { latency_ms: number } };
  tuned: { output: string; skill: string; metrics: { latency_ms: number } };
  delta: { latency_gap_ms: number; accuracy_gap: number };
}

async function compare(prompt: string): Promise<CompareResponse> {
  const res = await fetch(\`\${API_BASE}/v1/compare\`, {
    method: "POST",
    headers: { "Authorization": \`Bearer \${AURORA_KEY}\`, "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: USER_ID, input: prompt, provider: "openrouter", model: "openrouter/auto" })
  });
  return res.json();
}`,
            memory: `// Store typed memory
await fetch(\`\${API_BASE}/v1/memory\`, {
  method: "POST",
  headers: { "Authorization": \`Bearer \${AURORA_KEY}\`, "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: USER_ID,
    text: "User is building a SaaS product",
    kind: "context",
    memory_scope: "user"
  })
});`,
            skill: `// Invoke a specific skill
const res = await fetch(\`\${API_BASE}/v1/skills/code_assistant\`, {
  method: "POST",
  headers: { "Authorization": \`Bearer \${AURORA_KEY}\`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: USER_ID, input: "Review this TypeScript function for bugs" })
});
const data: RunResponse = await res.json();`
        }
    };

    function renderDocsSnippets(lang) {
        console.log("renderDocsSnippets called with lang:", lang);
        console.log("currentAuroraKey:", currentAuroraKey ? currentAuroraKey.slice(0, 20) + "..." : "null");
        console.log("currentUserId:", currentUserId);
        
        const snippets = DOCS_SNIPPETS[lang] || DOCS_SNIPPETS.curl;
        const ids = ["quickstart","chat","compare","memory","skill"];
        ids.forEach(id => {
            const el = $(`#docsSnippet${id.charAt(0).toUpperCase()+id.slice(1)}`);
            console.log(`Element for ${id}:`, el ? "found" : "NOT FOUND");
            if (!el) return;
            const code = (snippets[id] || "").replace(
                /YOUR_KEY/g, currentAuroraKey || "YOUR_AURORA_KEY_HERE"
            ).replace(/YOUR_USER_ID/g, currentUserId || "YOUR_USER_ID_HERE");
            el.innerHTML = `
                <div class="docs-snippet__header">
                    <span class="docs-snippet__lang">${lang}</span>
                    <button class="docs-snippet__copy" onclick="(function(b){
                        navigator.clipboard.writeText(b.closest('.docs-snippet').querySelector('pre').textContent).then(()=>{b.textContent='✓ Copied';setTimeout(()=>b.textContent='Copy',1500)})
                    })(this)">Copy</button>
                </div>
                <pre>${syntaxHL(code, lang)}</pre>`;
            console.log(`Rendered snippet for ${id}, length:`, el.innerHTML.length);
        });
    }

    function syntaxHL(code, lang) {
        const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
        let s = esc(code);
        if (lang === "curl") {
            s = s.replace(/(#[^\n]*)/g, '<span class="sc">$1</span>');
            s = s.replace(/("(?:[^"\\]|\\.)*")/g, '<span class="ss">$1</span>');
            s = s.replace(/\b(curl|POST|GET|PUT|DELETE)\b/g, '<span class="sk">$1</span>');
            s = s.replace(/(-[A-Za-z]+)/g, '<span class="sp">$1</span>');
        } else if (lang === "python") {
            s = s.replace(/(#[^\n]*)/g, '<span class="sc">$1</span>');
            s = s.replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="ss">$1</span>');
            s = s.replace(/\b(def|class|import|from|return|if|else|elif|for|while|async|await|with|as|print|True|False|None)\b/g, '<span class="sk">$1</span>');
            s = s.replace(/\b(\d+)\b/g, '<span class="sn">$1</span>');
        } else if (lang === "javascript" || lang === "typescript") {
            s = s.replace(/(\/\/[^\n]*)/g, '<span class="sc">$1</span>');
            s = s.replace(/(`(?:[^`\\]|\\.)*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="ss">$1</span>');
            s = s.replace(/\b(const|let|var|function|async|await|return|interface|type|import|export|new|class)\b/g, '<span class="sk">$1</span>');
            s = s.replace(/\b(\d+)\b/g, '<span class="sn">$1</span>');
        }
        return s;
    }

    $("#docsLang")?.addEventListener("change", (e) => renderDocsSnippets(e.target.value));

    // ========================================================
    // COMPARE — real tool preview rendering
    // ========================================================
    function renderToolPreview(toolCalls, toolResults, container) {
        if (!toolCalls || toolCalls.length === 0) return;
        toolCalls.forEach((tc, i) => {
            const result = toolResults?.[i];
            const preview = document.createElement("div");
            preview.className = "tool-preview";
            const outputText = result?.output
                ? String(result.output).slice(0, 400)
                : "running…";
            preview.innerHTML = `
                <div class="tool-preview__head">
                    <span class="dot"></span>
                    <span>TOOL · ${tc.name}</span>
                    <span style="margin-left:auto;color:#666">${JSON.stringify(tc.input || {}).slice(0,60)}</span>
                </div>
                <div class="tool-preview__body">${escapeHtml(outputText)}</div>
                ${result ? `<div class="tool-preview__result">✓ completed · ${String(result.output||"").length} chars</div>` : ""}`;
            container.appendChild(preview);
        });
    }

    // ========================================================
    // COMPARE — accurate live stats from API response
    // ========================================================
    function updateCompareStats(data) {
        const baseline = data.baseline;
        const tuned = data.tuned;
        const delta = data.delta;

        // Raw pane metrics
        $("#rawLatency").textContent = (baseline.metrics?.latency_ms ?? "—") + " ms";
        const rawTok = baseline.metrics?.usage?.total_tokens;
        const rawLat = baseline.metrics?.latency_ms || 1;
        $("#rawTps").textContent = rawTok && rawLat ? Math.round((rawTok / rawLat) * 1000) + " tok/s" : "—";
        $("#rawTokens").textContent = rawTok ?? "—";

        // Enhanced pane metrics
        const cost = tuned.metrics?.estimated_cost_usd;
        $("#enhCost").textContent = cost != null ? "$" + cost.toFixed(5) : "$ —";
        $("#enhTools").textContent = (tuned.metrics?.tool_count ?? 0) + " used";
        $("#enhIntent").textContent = tuned.skill || "—";

        // Sidebar
        $("#dashModel").textContent = (tuned.model || "").split("/").pop() || "—";
        $("#dashSkillCount").textContent = tuned.skill || "—";

        // Delta badge
        const existingBadge = $(".compare-delta");
        if (existingBadge) existingBadge.remove();
        if (delta) {
            const badge = document.createElement("div");
            badge.className = "compare-delta";
            const faster = delta.latency_gap_ms > 0 ? `+${delta.latency_gap_ms}ms faster` : `${Math.abs(delta.latency_gap_ms)}ms slower`;
            badge.innerHTML = `<span class="tag">Enhanced</span> ${faster} · accuracy +${delta.accuracy_gap ?? 0}pts · ${tuned.metrics?.memory_hits ?? 0} memory hits`;
            badge.style.cssText = "padding:8px 16px;font-size:12px;color:var(--text-mute);font-family:var(--font-mono);border-top:1px solid var(--border);";
            const split = $(".split");
            if (split) split.before(badge);
        }
    }

    // ========================================================
    // INIT — refresh docs + apikey tab on load
    // ========================================================
    refreshApiKeyTab();
    renderDocsSnippets("curl");

    // Re-render docs snippets with real key when tab is opened
    $$(".dash__navbtn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tab = btn.getAttribute("data-tab");
            if (tab === "docs") renderDocsSnippets($("#docsLang")?.value || "curl");
            if (tab === "apikey") refreshApiKeyTab();
        });
    });

})();