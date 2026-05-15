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
    let currentAuroraKeys = []; // Multiple API keys per user
    let selectedModelPersistent = null; // Persistent model selection

    // ---------- Device-based User ID Detection ----------
    function generateUUID() {
        // Generate a proper RFC 4122 v4 UUID
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    function getOrCreateDeviceUserId() {
        const STORAGE_KEY = "hs_device_user_id";
        let deviceUserId = localStorage.getItem(STORAGE_KEY);
        
        if (!deviceUserId) {
            // Generate a unique device ID based on browser fingerprint
            const fingerprint = [
                navigator.userAgent,
                navigator.language,
                new Date().getTimezoneOffset(),
                screen.width + 'x' + screen.height,
                navigator.hardwareConcurrency || 'unknown'
            ].join('|');
            
            // Hash the fingerprint to seed the UUID generation
            let hash = 0;
            for (let i = 0; i < fingerprint.length; i++) {
                const char = fingerprint.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32bit integer
            }
            
            // Use hash to seed random for deterministic UUID
            const seed = Math.abs(hash);
            const seededRandom = function() {
                const x = Math.sin(seed++) * 10000;
                return x - Math.floor(x);
            };
            
            // Generate UUID with seeded randomness for device consistency
            deviceUserId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = seededRandom() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
            
            localStorage.setItem(STORAGE_KEY, deviceUserId);
            console.log("✓ Generated new device user ID:", deviceUserId);
        } else {
            console.log("✓ Using existing device user ID:", deviceUserId);
        }
        
        return deviceUserId;
    }
    
    // Initialize device user ID on page load
    currentUserId = getOrCreateDeviceUserId();
    // Restore Aurora key from localStorage so memory/dashboard work after reload
    currentAuroraKey = localStorage.getItem("hs_aurora_key") || null;

    // ---------- small helpers ----------
    const $  = (s, r = document) => r.querySelector(s);
    const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
    const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    const rand = (min, max) => Math.random() * (max - min) + min;
    const randInt = (min, max) => Math.floor(rand(min, max + 1));

    // ---------- Auth State Management ----------
    function updateNavForAuthState() {
        const isSignedIn = !!currentAuroraKey;
        const signInBtn = $('[data-testid="nav-signin-btn"]');
        const getStartedBtn = $('[data-testid="nav-getstarted-btn"]');
        if (signInBtn) signInBtn.hidden = isSignedIn;
        if (getStartedBtn) getStartedBtn.textContent = isSignedIn ? "Generate Another Key" : "Get Enhanced Key";
    }

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
    const VALID_ROUTES = ["landing", "auth", "tutorial", "onboarding", "dashboard"];

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
        // Always sync nav state on every route change
        updateNavForAuthState();
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
    // ========================================================
    // AUTH — mode switch (SSO-only flow, no email form)
    // ========================================================
    function setAuthMode(mode) {
        // Auth is now SSO-only — no email/password fields exist
        // Just update title/subtitle text safely
        const titleEl = $("#authTitle");
        const subEl = $("#authSub");
        if (titleEl) titleEl.textContent = mode === "signup" ? "Create your workspace." : "Welcome to H&S Layer";
        if (subEl) subEl.textContent = mode === "signup"
            ? "Sign up to start bridging your Featherless API key into an enhanced key."
            : "Continue with SSO to access your enhanced workspace.";
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
        // Use the device-based user ID (already set on page load)
        toast(`Welcome ${email}! Set up your API key next`);
        go("onboarding");
    }
    $("#authForm")?.addEventListener("submit", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSubmit")?.addEventListener("click", (e) => { e.preventDefault(); proceedFromAuth(); });
    $("#authSsoBtn")?.addEventListener("click", () => { 
        // Use the device-based user ID (already set on page load)
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

            // Persist key to localStorage so it survives page reloads
            localStorage.setItem("hs_aurora_key", currentAuroraKey);

            bridgeOut.textContent = currentAuroraKey;
            const dashKeyShortEl = $("#dashKeyShort");
            if (dashKeyShortEl) {
                dashKeyShortEl.textContent = currentAuroraKey.slice(0, 10) + "···" + currentAuroraKey.slice(-6);
            }
            
            // Add to multiple keys list
            currentAuroraKeys.push({
                key: currentAuroraKey,
                name: "H&S Enhanced Key",
                created_at: new Date().toISOString(),
                scopes: ["chat", "memory", "tools", "skills"]
            });
            
            // Update nav state + reload dashboard data now that we have a key
            updateNavForAuthState();
            loadSkills();
            loadMemory();
            
            // Fill in the compare form with the REAL user ID (not hardcoded)
            const compareAuroraKeyEl = $("#compareAuroraKey");
            if (compareAuroraKeyEl) compareAuroraKeyEl.value = currentAuroraKey;
            const compareUserIdEl = $("#compareUserId");
            if (compareUserIdEl) compareUserIdEl.value = currentUserId;
            const compareOpenRouterKeyEl = $("#compareOpenRouterKey");
            if (compareOpenRouterKeyEl) compareOpenRouterKeyEl.value = fl;
            
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
            if (tab === "apikey") { refreshApiKeyTab(); loadApiKeys(); }
            if (tab === "docs") renderDocsSnippets($("#docsLang")?.value || "curl");
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
        
        // For instant display with proper formatting
        const formatted = formatMarkdownish(text);
        el.innerHTML = formatted;
        
        // Small delay to show it's "streaming"
        await sleep(100);
        el.classList.remove("streaming");
    }

    function formatMarkdownish(text) {
        const parts = String(text || "").split(/```([A-Za-z0-9_+#.-]*)\n([\s\S]*?)```/g);
        let html = "";

        for (let i = 0; i < parts.length; i += 3) {
            const prose = parts[i] || "";
            if (prose.trim()) {
                html += `<div class="plain-response">${escapeHtml(prose).replace(/\n/g, "<br>")}</div>`;
            }

            const lang = parts[i + 1];
            const code = parts[i + 2];
            if (code !== undefined) {
                const language = lang || "text";
                const cleanCode = code.trim();
                html += '<div class="code-block-container">' +
                    '<div class="code-block-header">' +
                    '<span class="code-block-lang">' + escapeHtml(language.toUpperCase()) + '</span>' +
                    '<button class="code-copy-btn" onclick="copyCodeBlock(this)" data-code="' + encodeURIComponent(cleanCode) + '">Copy</button>' +
                    '</div>' +
                    '<pre class="code-block-content"><code>' + escapeHtml(cleanCode) + '</code></pre>' +
                    '</div>';
            }
        }

        return html || `<div class="plain-response">${escapeHtml(text)}</div>`;
    }

    function highlightCode(code, language) {
        if (!code) return "";
        return escapeHtml(code);
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
        
        // Always use the real device user ID — never the form field which may be stale
        const auroraKey = currentAuroraKey || $("#compareAuroraKey")?.value?.trim();
        const userId = currentUserId;  // always the real device ID
        const openRouterKey = $("#compareOpenRouterKey")?.value?.trim();

        // Keep form fields in sync for display
        const compareUserIdEl = $("#compareUserId");
        if (compareUserIdEl) compareUserIdEl.value = userId;
        const compareAuroraKeyEl = $("#compareAuroraKey");
        if (compareAuroraKeyEl && auroraKey) compareAuroraKeyEl.value = auroraKey;

        // If OpenRouter key is filled, sync it to the backend under the REAL user ID
        if (openRouterKey && userId) {
            try {
                await fetch(`${API_BASE}/apikey`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: userId, provider: "openrouter", api_key: openRouterKey })
                });
                await fetch(`${API_BASE}/apikey`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: userId, provider: "featherless", api_key: openRouterKey })
                });
            } catch(e) { /* silent */ }
        }

        if (!auroraKey) { 
            toast("Generate an Aurora key first (bridge your API key)"); 
            go("onboarding");
            return; 
        }

        compareRun.disabled = true;
        const model = compareModel?.value || "openrouter/auto";
        const intent = detectIntent(q);

        // reset UI
        $("#rawBody").innerHTML = `<div class="pane__empty"><span class="mono-dim">// enhanced · thinking…</span></div>`;
        $("#enhBody").innerHTML = `<div class="pane__empty"><span class="mono-dim">// ${model} · thinking…</span></div>`;
        $("#rawLatency").textContent = "…";
        $("#rawTps").textContent = "…";
        $("#rawTokens").textContent = "…";
        $("#enhCost").textContent = "…";
        $("#enhTools").textContent = "…";
        $("#enhIntent").textContent = "…";

        // Show thought process on enhanced side (left pane) while waiting
        const thoughtBox = document.createElement("div");
        thoughtBox.className = "thought";
        $("#rawBody").innerHTML = "";
        $("#rawBody").appendChild(thoughtBox);

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
                    model: "openai/gpt-oss-120b:free",
                    memory_scope: "user"
                })
            });

            await thoughtPromise;

            if (!res.ok) {
                let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
                try {
                    const errorText = await res.text();
                    try {
                        const errorData = JSON.parse(errorText);
                        if (errorData.detail) errorMsg = JSON.stringify(errorData.detail);
                        else errorMsg = errorText;
                    } catch {
                        errorMsg = errorText || errorMsg;
                    }
                } catch (e) { /* use default errorMsg */ }
                throw new Error(errorMsg);
            }

            const data = await res.json();
            console.log("API Response:", data);
            const baseline = data.baseline;
            const tuned = data.tuned;

            // SWAPPED: Left pane shows ENHANCED (tuned), Right pane shows RAW (baseline)
            
            // Left pane - ENHANCED (was raw) - WITH syntax highlighting
            const rawBodyEl = $("#rawBody");
            rawBodyEl.innerHTML = "";
            await streamInto(rawBodyEl, tuned.output || "(no response)");
            $("#rawLatency").textContent = (tuned.metrics?.latency_ms ?? "—") + " ms";
            $("#rawTps").textContent = tuned.metrics?.usage?.total_tokens ?? "—";
            $("#rawTokens").textContent = tuned.metrics?.usage?.total_tokens ?? "—";

            // Right pane - RAW (was enhanced) - NO syntax highlighting (plain text)
            const enhBodyEl = $("#enhBody");
            enhBodyEl.innerHTML = "";
            // Display as plain text without markdown formatting
            const plainText = document.createElement("pre");
            plainText.style.whiteSpace = "pre-wrap";
            plainText.style.fontFamily = "var(--font-mono)";
            plainText.style.fontSize = "13px";
            plainText.style.lineHeight = "1.6";
            plainText.style.color = "#999";
            plainText.textContent = baseline.output || "(no response)";
            enhBodyEl.appendChild(plainText);
            
            $("#enhCost").textContent = baseline.metrics?.estimated_cost_usd != null
                ? "$" + baseline.metrics.estimated_cost_usd.toFixed(5)
                : "$ —";
            $("#enhTools").textContent = (tuned.metrics?.tool_count ?? 0) + " used";
            $("#enhIntent").textContent = tuned.skill || intent;

            // Sidebar stats — update with real values from response
            $("#dashModel").textContent = tuned.model || model;
            // Reload memory count after chat (facts may have been auto-stored)
            setTimeout(() => loadMemory(), 1500);

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

    function memoryHeaders() {
        return {
            "X-Api-Key": currentAuroraKey,
            "Authorization": `Bearer ${currentAuroraKey}`,
            "Content-Type": "application/json"
        };
    }

    function normalizeMemoryText(value) {
        return String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
    }

    function factTextFromStructured(item) {
        const data = item.data || {};
        const kind = item.kind || "";

        // Skip raw conversation turns
        if (kind === "turn" || kind === "assistant_summary" || kind === "message" || kind === "tool_calls") return "";

        // Handle fact_* kinds from backend auto-extraction
        if (kind.startsWith("fact_") || data.type) {
            const type = data.type || kind.replace("fact_", "");
            const value = data.value;
            if (!value) return "";
            if (type === "name") return `Name: ${value}`;
            if (type === "age") return `Age: ${value}`;
            if (type === "color" || type === "favourite_color" || type === "favorite_color" || type === "favorite") return `Favourite color: ${value}`;
            if (type === "preference") return `Prefers: ${value}`;
            if (type === "dislike") return `Dislikes: ${value}`;
            if (type === "project") return `Project: ${value}`;
            if (type === "role") return `Role: ${value}`;
            if (type === "company") return `Company: ${value}`;
            if (type === "location") return `Location: ${value}`;
            if (type === "technology") return `Uses: ${value}`;
            if (type === "goal") return `Goal: ${value}`;
            if (type === "learning") return `Learning: ${value}`;
            return `${type}: ${value}`;
        }

        // Manually stored facts have data.text
        if (data.text) return String(data.text);
        if (data.value) return `${data.type || kind}: ${data.value}`;
        return "";
    }

    async function persistMemory(item) {
        if (item.metadataId && !item.metadataId.startsWith("local-") && !item.metadataId.startsWith("vector-")) {
            // Existing backend fact — PATCH it
            const res = await fetch(`${API_BASE}/v1/memory/${encodeURIComponent(item.metadataId)}`, {
                method: "PATCH",
                headers: memoryHeaders(),
                body: JSON.stringify({
                    user_id: currentUserId,
                    text: item.fact,
                    kind: item.tag || "note",
                    memory_scope: "user",
                    metadata: { source: item.source || "manual" }
                })
            });
            const rawBody = await res.text();
            if (!res.ok) throw new Error(rawBody);
            return JSON.parse(rawBody);
        } else {
            // New fact — POST it
            const res = await fetch(`${API_BASE}/v1/memory`, {
                method: "POST",
                headers: memoryHeaders(),
                body: JSON.stringify({
                    user_id: currentUserId,
                    text: item.fact,
                    kind: item.tag || "note",
                    memory_scope: "user",
                    metadata: { source: item.source || "manual" }
                })
            });
            const rawBody = await res.text();
            if (!res.ok) throw new Error(rawBody);
            const data = JSON.parse(rawBody);
            item.metadataId = data.metadata_id || data.id;
            item.source = "manual";
            return data;
        }
    }

    async function deleteMemory(item) {
        if (!item.metadataId || item.metadataId.startsWith("local-") || item.metadataId.startsWith("vector-")) {
            return; // local-only item, nothing to delete on backend
        }
        const res = await fetch(
            `${API_BASE}/v1/memory/${encodeURIComponent(item.metadataId)}?user_id=${encodeURIComponent(currentUserId)}`,
            { method: "DELETE", headers: memoryHeaders() }
        );
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt);
        }
    }

    async function loadMemory() {
        if (!currentAuroraKey || !currentUserId) return;
        try {
            const response = await fetch(`${API_BASE}/v1/memory/context`, {
                method: "POST",
                headers: memoryHeaders(),
                body: JSON.stringify({
                    user_id: currentUserId,
                    query: "name age color preference technology goal project role company location learning dislike",
                    memory_scope: "user",
                    top_k: 50,
                    structured_limit: 200,
                    exclude_kinds: ["turn", "assistant_summary", "message", "tool_calls", "tool_result"]
                })
            });
            if (!response.ok) return;

            const data = await response.json();
            const structured = data.structured_memories || [];
            const retrieved = data.retrieved_memories || [];
            const seen = new Set();
            memory = [];

            // Backend now filters out conversation turns, so we only get real facts
            structured.forEach((item) => {
                const fact = factTextFromStructured(item);
                if (!fact || fact.length < 3) return;

                const key = normalizeMemoryText(fact);
                if (seen.has(key)) return;
                seen.add(key);

                // Map kind → display tag
                const k = (item.kind || "").replace(/^fact_/, "");
                let tag = "context";
                if (["name","age","role","company","location"].includes(k)) tag = "identity";
                else if (["preference","color","favourite_color","favorite_color","technology","learning","favorite"].includes(k)) tag = "preference";
                else if (["goal","project","dislike"].includes(k)) tag = "context";
                else if (item.kind === "note" || item.kind === "identity") tag = "identity";

                memory.push({
                    id: item.id,
                    metadataId: item.id,
                    fact,
                    tag,
                    source: item.data?.metadata?.source || (item.data?.original_text ? "conversation" : "manual"),
                    learned: String(item.created_at || "").slice(0, 10) || new Date().toISOString().slice(0, 10),
                    conf: 100
                });
            });

            // Add vector hits that aren't already shown
            retrieved.forEach((m, i) => {
                const fact = String(m.text || "").trim();
                if (!fact || fact.length < 5) return;
                // Skip conversation turns (user messages and assistant summaries)
                if (m.metadata?.role === "assistant_summary" || m.metadata?.role === "user") return;
                // Only show extracted facts (role: "user_fact") or manual facts
                if (m.metadata?.role && m.metadata.role !== "user_fact") return;
                const key = normalizeMemoryText(fact);
                if (seen.has(key)) return;
                seen.add(key);
                memory.push({
                    id: `vector-${m.id || i}`,
                    fact,
                    tag: "context",
                    source: "conversation",
                    learned: new Date().toISOString().slice(0, 10),
                    conf: 85  // fixed confidence for vector hits
                });
            });

            renderMemory();
            const el = $("#dashFactCount");
            if (el) el.textContent = memory.length;
        } catch (e) {
            console.error("loadMemory failed:", e);
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
            tr.dataset.id = String(m.id);
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

    $("#memoryTbody")?.addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const tr = btn.closest("tr");
        const id = tr.dataset.id;
        const action = btn.getAttribute("data-action");
        const item = memory.find(m => String(m.id) === id);
        if (!item) return;

        if (action === "forget") {
            try {
                await deleteMemory(item);
                memory = memory.filter(m => String(m.id) !== id);
                toast(`Fact forgotten`);
                renderMemory();
            } catch (error) {
                console.error("Failed to delete memory:", error);
                toast("Could not delete memory");
            }
        } else if (action === "edit") {
            const td = tr.querySelector("td:first-child");
            const current = item.fact;
            td.innerHTML = `<input class="fact-input" value="${escapeHtml(current)}" />`;
            const input = td.querySelector("input");
            input.focus(); input.select();
            let saved = false;
            const save = async () => {
                if (saved) return;
                saved = true;
                item.fact = input.value.trim() || current;
                try {
                    await persistMemory(item);
                    renderMemory();
                    toast("Fact updated");
                } catch (error) {
                    console.error("Failed to update memory:", error);
                    item.fact = current;
                    renderMemory();
                    toast("Could not update memory");
                }
            };
            input.addEventListener("blur", save, { once: true });
            input.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter") input.blur();
                if (ev.key === "Escape") renderMemory();
            });
        }
    });

    $("#memoryAddBtn")?.addEventListener("click", async () => {
        if (!currentAuroraKey || !currentUserId) {
            toast("Bridge your API key first");
            return;
        }
        const newItem = {
            id: `local-${Date.now()}`,
            fact: "New fact — click edit to describe…",
            tag: "context",
            source: "manual",
            learned: new Date().toISOString().slice(0, 10),
            conf: 100,
            pinned: false,
        };
        memory.unshift(newItem);
        renderMemory();

        // Save to backend immediately
        try {
            const res = await fetch(`${API_BASE}/v1/memory`, {
                method: "POST",
                headers: memoryHeaders(),
                body: JSON.stringify({
                    user_id: currentUserId,
                    text: newItem.fact,
                    kind: "note",
                    memory_scope: "user",
                    metadata: { source: "manual" }
                })
            });
            if (res.ok) {
                const data = await res.json();
                newItem.metadataId = data.metadata_id || data.id;
                toast("Fact added — click edit to update it");
            } else {
                toast("Fact added locally");
            }
        } catch(e) {
            toast("Fact added locally");
        }
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

    $("#toolAddBtn")?.addEventListener("click", async () => {
        const n = TOOLS.length + 1;
        const newTool = {
            name: `untitled_${n}.js`,
            code:
`// New tool scaffold
export const schema = {
    intent: "untitled_${n}",
    params: { input: "string" },
    returns: { result: "string" }
};

export async function run(params) {
    // Write your tool logic here
    return { result: "Tool executed: " + params.input };
}`
        };
        TOOLS.push(newTool);
        loadTool(TOOLS.length - 1);
        toast("New tool scaffolded — edit and click Run to test");

        // Save to backend if authenticated
        if (currentAuroraKey) {
            try {
                await fetch(`${API_BASE}/tools`, {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${currentAuroraKey}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        name: `untitled_${n}`,
                        description: "Custom tool",
                        endpoint_url: `${API_BASE}/v1/tools/untitled_${n}`,
                        method: "POST",
                        input_schema: { input: "string" }
                    })
                });
            } catch(e) { /* tool saved locally, backend save optional */ }
        }
    });

    $("#toolRunBtn")?.addEventListener("click", async () => {
        const console_ = $("#toolConsole");
        console_.innerHTML = "";
        const t = TOOLS[activeTool];
        if (!t) { toast("No tool selected"); return; }

        const intentMatch = t.code.match(/intent:\s*["']([^"']+)["']/);
        const intent = intentMatch ? intentMatch[1] : t.name.replace(".js", "");

        // Build sensible test params from schema — use real types not "test_X" strings
        const paramsMatch = t.code.match(/params:\s*(\{[\s\S]*?\})\s*[,\n]/);
        let testParams = {};
        try {
            if (paramsMatch) {
                const paramStr = paramsMatch[1];
                // Extract key: "type" pairs
                const pairs = [...paramStr.matchAll(/"?(\w+)"?\s*:\s*["'](\w+)["']/g)];
                pairs.forEach(([, key, type]) => {
                    if (type === "string") testParams[key] = key === "query" ? "hello world" : key === "code" ? "print('hello')" : key === "url" ? "https://example.com" : "test";
                    else if (type === "number" || type === "integer") testParams[key] = 1;
                    else if (type === "boolean") testParams[key] = true;
                    else testParams[key] = "test";
                });
            }
        } catch(e) { /* use empty params */ }

        const log = (cls, txt) => {
            const line = document.createElement("div");
            line.className = cls;
            line.textContent = txt;
            console_.appendChild(line);
            console_.scrollTop = console_.scrollHeight;
        };

        log("c-dim", `› running tool: ${intent}`);
        log("c-dim", `› params: ${JSON.stringify(testParams)}`);

        if (!currentAuroraKey) {
            log("c-err", "✗ no aurora key — bridge your API key first");
            return;
        }

        try {
            const t0 = Date.now();
            const res = await fetch(`${API_BASE}/v1/tools/${encodeURIComponent(intent)}`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${currentAuroraKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user_id: currentUserId,
                    name: intent,
                    input: testParams
                })
            });
            const elapsed = Date.now() - t0;
            const rawBody = await res.text();

            if (!res.ok) {
                log("c-err", `✗ HTTP ${res.status}: ${rawBody.slice(0, 300)}`);
                return;
            }

            let data;
            try { data = JSON.parse(rawBody); } catch { data = { output: rawBody }; }
            log("c-ok", `✓ exit 0 · ${elapsed}ms`);
            const out = data.output ?? data.result ?? data;
            log("c-ok", `✓ ${typeof out === "object" ? JSON.stringify(out).slice(0, 300) : String(out).slice(0, 300)}`);
            toast(`Tool "${intent}" ran · ${elapsed}ms`);
        } catch (err) {
            log("c-err", `✗ ${err.message}`);
        }
    });

    if (TOOLS.length > 0) loadTool(0);

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
            updateNavForAuthState();
            toast("New key generated!");
        } catch (e) {
            toast("Failed to regenerate key: " + e.message);
        }
    });

    $("#apikeyGenerateAnotherBtn")?.addEventListener("click", async () => {
        if (!currentUserId) { toast("Please sign in first"); return; }
        toast("Generating new API key…");
        try {
            const res = await fetch(`${API_BASE}/auth/issue-key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    user_id: currentUserId, 
                    name: `H&S Key ${new Date().toLocaleDateString()}`,
                    scopes: ["chat","memory","tools","skills"] 
                })
            });
            const data = await res.json();
            currentAuroraKeys.push({
                key: data.api_key,
                name: `H&S Key ${new Date().toLocaleDateString()}`,
                created_at: new Date().toISOString(),
                scopes: ["chat", "memory", "tools", "skills"],
                is_active: true
            });
            renderApiKeysList();
            toast("New API key generated!");
        } catch (e) {
            toast("Failed to generate key: " + e.message);
        }
    });

    async function loadApiKeys() {
        if (!currentUserId) return;
        try {
            const res = await fetch(`${API_BASE}/auth/keys?user_id=${currentUserId}`, {
                headers: { "Authorization": `Bearer ${currentAuroraKey || ""}` }
            });
            if (res.ok) {
                currentAuroraKeys = await res.json();
                renderApiKeysList();
            }
        } catch (e) {
            console.error("Failed to load API keys:", e);
        }
        refreshApiKeyTab();
    }

    function renderApiKeysList() {
        const container = $("#apikeysList");
        if (!container) return;
        
        container.innerHTML = "";
        if (currentAuroraKeys.length === 0) {
            container.innerHTML = '<div class="mono-dim">No additional keys yet</div>';
            return;
        }

        currentAuroraKeys.forEach((key, idx) => {
            const card = document.createElement("div");
            card.className = "apikey-card";
            card.innerHTML = `
                <div class="apikey-card__label">
                    <span class="dot"></span>
                    <span class="mono-dim">${escapeHtml(key.name || "Key " + (idx + 1))}</span>
                    <span class="tag">${key.is_active ? "active" : "inactive"}</span>
                </div>
                <div class="apikey-card__key">
                    <code>${key.key_prefix}••••••••••••••••••••</code>
                    <button class="btn btn--ghost" onclick="copyToClipboard('${key.key_prefix}')">Copy Prefix</button>
                </div>
                <div class="apikey-card__meta">
                    <span class="mono-dim">CREATED</span>
                    <code>${new Date(key.created_at).toLocaleDateString()}</code>
                </div>
            `;
            container.appendChild(card);
        });
    }

    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(() => toast("Copied!"));
    };

    // ========================================================
    // DEV DOCS TAB
    // ========================================================
    const DOCS_SNIPPETS = {
        curl: {
            quickstart: `curl -X POST http://localhost:8000/v1/run \\
  -H "Authorization: Bearer hs_FL7x2Q9mK3vN1pB4rD6s" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "What is my most used model?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openai/gpt-oss-120b:free"
  }'`,
            chat: `curl -X POST http://localhost:8000/v1/run \\
  -H "Authorization: Bearer hs_FL7x2Q9mK3vN1pB4rD6s" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Search for recent AI breakthroughs",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openai/gpt-oss-120b:free"
  }'`,
            memory: `curl -X POST http://localhost:8000/v1/memory \\
  -H "Authorization: Bearer hs_FL7x2Q9mK3vN1pB4rD6s" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "text": "User prefers DeepSeek for code tasks",
    "kind": "preference",
    "memory_scope": "user",
    "metadata": {"source": "user_feedback"}
  }'`
        },
        python: {
            quickstart: `import requests

api_key = "hs_FL7x2Q9mK3vN1pB4rD6s"
user_id = "00000000-0000-0000-0000-000000000001"

response = requests.post(
    "http://localhost:8000/v1/run",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "user_id": user_id,
        "input": "What is my most used model?",
        "memory_scope": "user",
        "provider": "openrouter",
        "model": "openai/gpt-oss-120b:free"
    }
)

print(response.json())`,
            chat: `import requests

response = requests.post(
    "http://localhost:8000/v1/run",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "user_id": user_id,
        "input": "Search for recent AI breakthroughs",
        "memory_scope": "user",
        "provider": "openrouter",
        "model": "openai/gpt-oss-120b:free"
    }
)

data = response.json()
print(f"Skill: {data['skill']}")
print(f"Output: {data['output']}")
print(f"Memory hits: {data['metrics']['memory_hits']}")`,
            memory: `import requests

response = requests.post(
    "http://localhost:8000/v1/memory",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "user_id": user_id,
        "text": "User prefers DeepSeek for code tasks",
        "kind": "preference",
        "memory_scope": "user",
        "metadata": {"source": "user_feedback"}
    }
)

print(response.json())`
        },
        javascript: {
            quickstart: `const apiKey = "hs_FL7x2Q9mK3vN1pB4rD6s";
const userId = "00000000-0000-0000-0000-000000000001";

const response = await fetch("http://localhost:8000/v1/run", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    input: "What is my most used model?",
    memory_scope: "user",
    provider: "openrouter",
    model: "openai/gpt-oss-120b:free"
  })
});

const data = await response.json();
console.log(data);`,
            chat: `const response = await fetch("http://localhost:8000/v1/run", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    input: "Search for recent AI breakthroughs",
    memory_scope: "user",
    provider: "openrouter",
    model: "openai/gpt-oss-120b:free"
  })
});

const data = await response.json();
console.log(\`Skill: \${data.skill}\`);
console.log(\`Output: \${data.output}\`);
console.log(\`Memory hits: \${data.metrics.memory_hits}\`);`,
            memory: `const response = await fetch("http://localhost:8000/v1/memory", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    text: "User prefers DeepSeek for code tasks",
    kind: "preference",
    memory_scope: "user",
    metadata: { source: "user_feedback" }
  })
});

const data = await response.json();
console.log(data);`
        },
        typescript: {
            quickstart: `interface RunRequest {
  user_id: string;
  input: string;
  memory_scope: string;
  provider: string;
  model: string;
}

const response = await fetch("http://localhost:8000/v1/run", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    input: "What is my most used model?",
    memory_scope: "user",
    provider: "openrouter",
    model: "openai/gpt-oss-120b:free"
  } as RunRequest)
});

const data = await response.json();
console.log(data);`,
            chat: `const response = await fetch("http://localhost:8000/v1/run", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    input: "Search for recent AI breakthroughs",
    memory_scope: "user",
    provider: "openrouter",
    model: "openai/gpt-oss-120b:free"
  } as RunRequest)
});

const data = await response.json();
console.log(\`Skill: \${data.skill}\`);
console.log(\`Output: \${data.output}\`);
console.log(\`Memory hits: \${data.metrics.memory_hits}\`);`,
            memory: `interface MemoryRequest {
  user_id: string;
  text: string;
  kind: string;
  memory_scope: string;
  metadata: Record<string, any>;
}

const response = await fetch("http://localhost:8000/v1/memory", {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: userId,
    text: "User prefers DeepSeek for code tasks",
    kind: "preference",
    memory_scope: "user",
    metadata: { source: "user_feedback" }
  } as MemoryRequest)
});

const data = await response.json();
console.log(data);`
        }
    };

    // Add missing snippet keys to all languages
    const MISSING_SNIPPETS = {
        compare: {
            curl: `curl -X POST http://localhost:8000/v1/compare \\
  -H "Authorization: Bearer YOUR_AURORA_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "input": "What are the latest AI breakthroughs?",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'`,
            python: `response = requests.post(
    "http://localhost:8000/v1/compare",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "user_id": user_id,
        "input": "What are the latest AI breakthroughs?",
        "provider": "openrouter",
        "model": "openrouter/auto",
        "memory_scope": "user"
    }
)
data = response.json()
print("Raw:", data["baseline"]["output"][:100])
print("Enhanced:", data["tuned"]["output"][:100])
print("Memory hits:", data["tuned"]["metrics"]["memory_hits"])`,
            javascript: `const res = await fetch("http://localhost:8000/v1/compare", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: userId,
    input: "What are the latest AI breakthroughs?",
    provider: "openrouter",
    model: "openrouter/auto",
    memory_scope: "user"
  })
});
const data = await res.json();
console.log("Raw:", data.baseline.output);
console.log("Enhanced:", data.tuned.output);
console.log("Memory hits:", data.tuned.metrics.memory_hits);`,
            typescript: `const res = await fetch("http://localhost:8000/v1/compare", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: userId, input: "Latest AI news?", provider: "openrouter", model: "openrouter/auto", memory_scope: "user" })
});
const data = await res.json();
console.log(data.baseline.output, data.tuned.output);`
        },
        skill: {
            curl: `# Invoke a specific skill directly
curl -X POST http://localhost:8000/v1/skills/research \\
  -H "Authorization: Bearer YOUR_AURORA_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "input": "Latest developments in quantum computing 2025"
  }'

# Available skills: research, analysis, code, math, summary, web_search`,
            python: `# Invoke a specific skill
response = requests.post(
    "http://localhost:8000/v1/skills/research",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={"user_id": user_id, "input": "Latest developments in quantum computing 2025"}
)
data = response.json()
print(f"Skill: {data['skill']}")
print(f"Output: {data['output'][:200]}")`,
            javascript: `// Invoke a specific skill
const res = await fetch("http://localhost:8000/v1/skills/research", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: userId, input: "Latest developments in quantum computing 2025" })
});
const data = await res.json();
console.log(\`Skill: \${data.skill}, Output: \${data.output}\`);`,
            typescript: `const res = await fetch("http://localhost:8000/v1/skills/research", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: userId, input: "Latest AI news" })
});
const data = await res.json();
console.log(data.output);`
        },
        tools: {
            curl: `# Run a specific tool
curl -X POST http://localhost:8000/v1/tools/web_search \\
  -H "Authorization: Bearer YOUR_AURORA_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "name": "web_search",
    "input": {"query": "OpenAI GPT-5 release date"}
  }'

# Other tools: python, bash, url_fetch, pdf_analyze, db_query`,
            python: `# Execute a tool directly
response = requests.post(
    "http://localhost:8000/v1/tools/web_search",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "user_id": user_id,
        "name": "web_search",
        "input": {"query": "OpenAI GPT-5 release date"}
    }
)
data = response.json()
print(f"Tool output: {data['output']}")`,
            javascript: `// Execute a tool directly
const res = await fetch("http://localhost:8000/v1/tools/web_search", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: userId,
    name: "web_search",
    input: { query: "OpenAI GPT-5 release date" }
  })
});
const data = await res.json();
console.log(data.output);`,
            typescript: `const res = await fetch("http://localhost:8000/v1/tools/web_search", {
  method: "POST",
  headers: { "Authorization": \`Bearer \${apiKey}\`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: userId, name: "web_search", input: { query: "AI news" } })
});
const data = await res.json();
console.log(data.output);`
        },
        errors: {
            curl: `# 401 Unauthorized — invalid or expired Aurora key
# Solution: regenerate your key via POST /auth/issue-key

# 402 Payment Required — OpenRouter credits exhausted
# Solution: add credits at openrouter.ai/credits

# 404 Not Found — memory/tool ID doesn't exist
# Solution: check the ID is correct and belongs to your user

# 429 Rate Limited — too many requests
# Solution: add exponential backoff

# 502 Bad Gateway — upstream LLM provider error
# Solution: retry after a short delay`,
            python: `import time

def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = fn()
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 402:
                raise Exception("OpenRouter credits exhausted — add credits at openrouter.ai")
            if response.status_code == 401:
                raise Exception("Invalid Aurora key — regenerate via /auth/issue-key")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)`,
            javascript: `async function callWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const res = await fn();
    if (res.status === 429) { await sleep(2 ** i * 1000); continue; }
    if (res.status === 402) throw new Error("OpenRouter credits exhausted");
    if (res.status === 401) throw new Error("Invalid Aurora key");
    if (!res.ok) throw new Error(\`HTTP \${res.status}\`);
    return res.json();
  }
}

// Usage
const data = await callWithRetry(() =>
  fetch("http://localhost:8000/v1/run", { method: "POST", headers, body })
);`,
            typescript: `async function callWithRetry<T>(fn: () => Promise<Response>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    const res = await fn();
    if (res.status === 429) { await new Promise(r => setTimeout(r, 2 ** i * 1000)); continue; }
    if (!res.ok) throw new Error(\`HTTP \${res.status}\`);
    return res.json() as T;
  }
  throw new Error("Max retries exceeded");
}`
        }
    };

    // Merge missing snippets into DOCS_SNIPPETS
    ["curl","python","javascript","typescript"].forEach(lang => {
        if (!DOCS_SNIPPETS[lang]) DOCS_SNIPPETS[lang] = {};
        Object.keys(MISSING_SNIPPETS).forEach(key => {
            DOCS_SNIPPETS[lang][key] = MISSING_SNIPPETS[key][lang] || "";
        });
    });

    // ========================================================
    // MODEL SELECTOR — Persistent Selection
    // ========================================================
    function loadPersistentModel() {
        selectedModelPersistent = localStorage.getItem("hs_selected_model") || "openrouter/auto";
        const compareModel = $("#compareModel");
        if (compareModel) {
            compareModel.value = selectedModelPersistent;
        }
    }

    function savePersistentModel(model) {
        selectedModelPersistent = model;
        localStorage.setItem("hs_selected_model", model);
    }

    $("#compareModel")?.addEventListener("change", (e) => {
        savePersistentModel(e.target.value);
    });

    // Load persistent model on page load
    loadPersistentModel();

    // ========================================================
    // DEV DOCS TAB
    // ========================================================

    function renderDocsSnippets(lang) {
        console.log("renderDocsSnippets called with lang:", lang);
        console.log("currentAuroraKey:", currentAuroraKey ? currentAuroraKey.slice(0, 20) + "..." : "null");
        console.log("currentUserId:", currentUserId);
        
        const snippets = DOCS_SNIPPETS[lang] || DOCS_SNIPPETS.curl;
        const ids = ["quickstart","project","chat","compare","memory","skill","tools","errors"];
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
    // INIT — runs once on page load
    // ========================================================
    (function initApp() {
        // 1. Fill compare form with real device user ID
        const compareUserIdEl = $("#compareUserId");
        if (compareUserIdEl) compareUserIdEl.value = currentUserId;

        // 2. If we have a saved Aurora key, fill compare form and update nav
        if (currentAuroraKey) {
            const compareAuroraKeyEl = $("#compareAuroraKey");
            if (compareAuroraKeyEl) compareAuroraKeyEl.value = currentAuroraKey;
            const dashKeyShortEl = $("#dashKeyShort");
            if (dashKeyShortEl) dashKeyShortEl.textContent = currentAuroraKey.slice(0, 10) + "···" + currentAuroraKey.slice(-6);
            // Load dashboard data since we're already authenticated
            loadSkills();
            loadMemory();
        }

        // 3. Refresh API key tab display
        refreshApiKeyTab();

        // 4. Render docs snippets
        renderDocsSnippets("curl");

        // 5. Update nav (hide sign-in if already have key)
        updateNavForAuthState();
    })();

    // ========================================================
    // TUTORIAL DECK
    // ========================================================
    let currentTutorialSlide = 0;
    const totalTutorialSlides = 8;

    function initTutorialDeck() {
        const dotsContainer = $("#progressDots");
        if (dotsContainer) {
            dotsContainer.innerHTML = "";
            for (let i = 0; i < totalTutorialSlides; i++) {
                const dot = document.createElement("div");
                dot.className = `progress-dot ${i === 0 ? "is-active" : ""}`;
                dot.addEventListener("click", () => showTutorialSlide(i));
                dotsContainer.appendChild(dot);
            }
        }
        showTutorialSlide(0);
    }

    function showTutorialSlide(index) {
        currentTutorialSlide = Math.max(0, Math.min(index, totalTutorialSlides - 1));
        $$(".tutorial-slide").forEach(s => s.classList.remove("is-active"));
        const slide = $(`.tutorial-slide[data-slide="${currentTutorialSlide}"]`);
        if (slide) slide.classList.add("is-active");
        $$(".progress-dot").forEach((dot, i) => dot.classList.toggle("is-active", i === currentTutorialSlide));
        const prevBtn = $("#tutorialPrevBtn");
        const nextBtn = $("#tutorialNextBtn");
        if (prevBtn) prevBtn.disabled = currentTutorialSlide === 0;
        if (nextBtn) nextBtn.textContent = currentTutorialSlide === totalTutorialSlides - 1 ? "Go to Dashboard →" : "Next →";
    }

    $("#authTutorialBtn")?.addEventListener("click", () => {
        go("tutorial");
        initTutorialDeck();
    });

    $("#tutorialPrevBtn")?.addEventListener("click", () => showTutorialSlide(currentTutorialSlide - 1));

    $("#tutorialNextBtn")?.addEventListener("click", () => {
        if (currentTutorialSlide === totalTutorialSlides - 1) {
            go("dashboard");
        } else {
            showTutorialSlide(currentTutorialSlide + 1);
        }
    });

    document.addEventListener("keydown", (e) => {
        if (location.hash.replace("#", "").split("#")[0] !== "tutorial") return;
        if (e.key === "ArrowLeft") showTutorialSlide(currentTutorialSlide - 1);
        if (e.key === "ArrowRight") showTutorialSlide(currentTutorialSlide + 1);
    });


})();
