"""
Advanced skill generation system for creating hundreds of domain-specific skills.
Inspired by Claude's skill architecture with lazy loading and intelligent routing.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillTemplate:
    name: str
    description: str
    version: str
    triggers: list[str]
    when_to_use: str
    argument_hint: str | None
    prompt_template: str
    tool_permissions: list[str]
    memory_rules: dict
    tags: list[str]
    complexity: str  # simple, moderate, advanced
    domain: str


# Comprehensive domain taxonomy
DOMAINS = [
    # Engineering & Development
    {"slug": "backend", "label": "Backend Engineering", "keywords": ["backend", "api", "server", "microservice"]},
    {"slug": "frontend", "label": "Frontend Development", "keywords": ["frontend", "ui", "react", "vue", "angular"]},
    {"slug": "mobile", "label": "Mobile Development", "keywords": ["mobile", "ios", "android", "flutter", "react-native"]},
    {"slug": "devops", "label": "DevOps & Infrastructure", "keywords": ["devops", "deploy", "kubernetes", "docker", "ci/cd"]},
    {"slug": "database", "label": "Database Engineering", "keywords": ["database", "sql", "nosql", "postgres", "mongodb"]},
    {"slug": "security", "label": "Security Engineering", "keywords": ["security", "auth", "encryption", "vulnerability"]},
    {"slug": "ml", "label": "Machine Learning", "keywords": ["ml", "machine learning", "ai", "model", "training"]},
    {"slug": "data-eng", "label": "Data Engineering", "keywords": ["data pipeline", "etl", "spark", "airflow"]},
    {"slug": "qa", "label": "Quality Assurance", "keywords": ["qa", "test", "testing", "automation", "selenium"]},
    {"slug": "performance", "label": "Performance Engineering", "keywords": ["performance", "optimization", "profiling", "benchmark"]},
    
    # Product & Design
    {"slug": "product", "label": "Product Management", "keywords": ["product", "roadmap", "feature", "requirements"]},
    {"slug": "ux", "label": "UX Design", "keywords": ["ux", "user experience", "usability", "wireframe"]},
    {"slug": "ui", "label": "UI Design", "keywords": ["ui", "interface", "design system", "component"]},
    {"slug": "research", "label": "User Research", "keywords": ["user research", "interview", "survey", "persona"]},
    
    # Business & Strategy
    {"slug": "strategy", "label": "Business Strategy", "keywords": ["strategy", "competitive", "market", "positioning"]},
    {"slug": "marketing", "label": "Marketing", "keywords": ["marketing", "campaign", "brand", "positioning"]},
    {"slug": "sales", "label": "Sales", "keywords": ["sales", "prospect", "pipeline", "deal"]},
    {"slug": "growth", "label": "Growth", "keywords": ["growth", "acquisition", "retention", "funnel"]},
    {"slug": "analytics", "label": "Analytics", "keywords": ["analytics", "metrics", "kpi", "dashboard"]},
    
    # Operations
    {"slug": "operations", "label": "Operations", "keywords": ["operations", "process", "workflow", "efficiency"]},
    {"slug": "support", "label": "Customer Support", "keywords": ["support", "ticket", "customer", "help"]},
    {"slug": "success", "label": "Customer Success", "keywords": ["success", "onboarding", "retention", "churn"]},
    {"slug": "finance", "label": "Finance", "keywords": ["finance", "budget", "forecast", "revenue"]},
    {"slug": "legal", "label": "Legal", "keywords": ["legal", "contract", "compliance", "policy"]},
    {"slug": "hr", "label": "Human Resources", "keywords": ["hr", "hiring", "recruiting", "people"]},
    
    # Content & Communication
    {"slug": "content", "label": "Content Creation", "keywords": ["content", "blog", "article", "copy"]},
    {"slug": "docs", "label": "Documentation", "keywords": ["docs", "documentation", "guide", "tutorial"]},
    {"slug": "technical-writing", "label": "Technical Writing", "keywords": ["technical writing", "api docs", "specification"]},
    {"slug": "seo", "label": "SEO", "keywords": ["seo", "search", "ranking", "keyword"]},
    {"slug": "social", "label": "Social Media", "keywords": ["social", "twitter", "linkedin", "post"]},
    
    # Specialized Domains
    {"slug": "blockchain", "label": "Blockchain", "keywords": ["blockchain", "crypto", "smart contract", "web3"]},
    {"slug": "iot", "label": "IoT", "keywords": ["iot", "embedded", "sensor", "device"]},
    {"slug": "gaming", "label": "Game Development", "keywords": ["game", "gaming", "unity", "unreal"]},
    {"slug": "ar-vr", "label": "AR/VR", "keywords": ["ar", "vr", "augmented reality", "virtual reality"]},
    {"slug": "audio", "label": "Audio Engineering", "keywords": ["audio", "sound", "music", "podcast"]},
    {"slug": "video", "label": "Video Production", "keywords": ["video", "editing", "production", "streaming"]},
]

# Skill patterns (verbs/actions)
PATTERNS = [
    {"slug": "architect", "verb": "architect", "desc": "Design system architecture", "complexity": "advanced"},
    {"slug": "implement", "verb": "implement", "desc": "Implement features", "complexity": "moderate"},
    {"slug": "debug", "verb": "debug", "desc": "Debug and troubleshoot", "complexity": "moderate"},
    {"slug": "optimize", "verb": "optimize", "desc": "Optimize performance", "complexity": "advanced"},
    {"slug": "review", "verb": "review", "desc": "Review code/content", "complexity": "moderate"},
    {"slug": "test", "verb": "test", "desc": "Test and validate", "complexity": "simple"},
    {"slug": "document", "verb": "document", "desc": "Document systems", "complexity": "simple"},
    {"slug": "analyze", "verb": "analyze", "desc": "Analyze data/systems", "complexity": "moderate"},
    {"slug": "plan", "verb": "plan", "desc": "Plan and strategize", "complexity": "moderate"},
    {"slug": "research", "verb": "research", "desc": "Research and investigate", "complexity": "moderate"},
    {"slug": "migrate", "verb": "migrate", "desc": "Migrate systems", "complexity": "advanced"},
    {"slug": "refactor", "verb": "refactor", "desc": "Refactor code", "complexity": "moderate"},
    {"slug": "monitor", "verb": "monitor", "desc": "Monitor systems", "complexity": "simple"},
    {"slug": "secure", "verb": "secure", "desc": "Secure systems", "complexity": "advanced"},
    {"slug": "scale", "verb": "scale", "desc": "Scale infrastructure", "complexity": "advanced"},
    {"slug": "integrate", "verb": "integrate", "desc": "Integrate systems", "complexity": "moderate"},
    {"slug": "automate", "verb": "automate", "desc": "Automate workflows", "complexity": "moderate"},
    {"slug": "deploy", "verb": "deploy", "desc": "Deploy applications", "complexity": "moderate"},
    {"slug": "configure", "verb": "configure", "desc": "Configure systems", "complexity": "simple"},
    {"slug": "troubleshoot", "verb": "troubleshoot", "desc": "Troubleshoot issues", "complexity": "moderate"},
]

# Additional specialized patterns
SPECIALIZED_PATTERNS = [
    {"slug": "compare", "verb": "compare", "desc": "Compare options", "complexity": "simple"},
    {"slug": "evaluate", "verb": "evaluate", "desc": "Evaluate solutions", "complexity": "moderate"},
    {"slug": "estimate", "verb": "estimate", "desc": "Estimate effort/cost", "complexity": "moderate"},
    {"slug": "prioritize", "verb": "prioritize", "desc": "Prioritize tasks", "complexity": "simple"},
    {"slug": "summarize", "verb": "summarize", "desc": "Summarize information", "complexity": "simple"},
    {"slug": "extract", "verb": "extract", "desc": "Extract data", "complexity": "simple"},
    {"slug": "transform", "verb": "transform", "desc": "Transform data", "complexity": "moderate"},
    {"slug": "validate", "verb": "validate", "desc": "Validate inputs", "complexity": "simple"},
    {"slug": "generate", "verb": "generate", "desc": "Generate content", "complexity": "moderate"},
    {"slug": "explain", "verb": "explain", "desc": "Explain concepts", "complexity": "simple"},
]

ALL_PATTERNS = PATTERNS + SPECIALIZED_PATTERNS


def get_tools_for_domain(domain_slug: str, pattern_slug: str) -> list[str]:
    """Intelligently assign tools based on domain and pattern."""
    tools: list[str] = []
    
    # Research-heavy domains
    if domain_slug in {"research", "marketing", "seo", "sales", "growth", "strategy", "analytics"}:
        tools.extend(["web_search", "deep_search", "url_fetch"])
    
    # Engineering domains
    if domain_slug in {"backend", "frontend", "mobile", "database", "ml", "data-eng", "qa", "performance"}:
        tools.extend(["code_analyze", "python"])
        if pattern_slug in {"debug", "troubleshoot", "test"}:
            tools.append("bash")
    
    # Database work
    if domain_slug in {"database", "data-eng", "analytics", "finance"}:
        tools.append("db_query")
    
    # DevOps and infrastructure
    if domain_slug in {"devops", "performance", "security"}:
        tools.extend(["bash", "code_analyze"])
    
    # Content and documentation
    if domain_slug in {"docs", "content", "technical-writing", "seo"}:
        tools.extend(["url_fetch", "pdf_analyze"])
    
    # Analysis patterns
    if pattern_slug in {"analyze", "research", "compare", "evaluate"}:
        if "web_search" not in tools:
            tools.append("web_search")
    
    return list(dict.fromkeys(tools))  # Remove duplicates


def get_memory_rules(domain_slug: str, pattern_slug: str, complexity: str) -> dict:
    """Configure memory rules based on skill characteristics."""
    return {
        "short_term": True,
        "vector_store": pattern_slug not in {"summarize", "extract", "generate"},
        "structured": complexity in {"moderate", "advanced"},
        "compose": [],
        "builtin": True,
        "_skill_config": {
            "invocation_mode": "auto",
            "context_mode": "inline",
            "preferred_effort": "high" if complexity == "advanced" else "normal",
        },
    }


def generate_prompt_template(domain_label: str, pattern_desc: str, pattern_verb: str, complexity: str) -> str:
    """Generate contextual prompt templates."""
    base = f"You are a specialized {domain_label.lower()} skill focused on {pattern_desc.lower()}.\n\n"
    
    if complexity == "advanced":
        base += "Apply deep expertise and consider edge cases, scalability, and long-term implications.\n"
    elif complexity == "moderate":
        base += "Balance thoroughness with practical execution.\n"
    else:
        base += "Focus on clear, actionable output.\n"
    
    base += "\nUser request: {user_input}\n"
    base += "Relevant context: {memory_context}\n"
    base += "\nAvailable tools: {tool_permissions}\n"
    
    return base


def generate_all_skills() -> list[SkillTemplate]:
    """Generate comprehensive skill catalog."""
    skills: list[SkillTemplate] = []
    
    for domain in DOMAINS:
        domain_slug = str(domain["slug"])
        domain_label = str(domain["label"])
        keywords = [str(k) for k in domain["keywords"]]
        
        for pattern in ALL_PATTERNS:
            pattern_slug = str(pattern["slug"])
            pattern_verb = str(pattern["verb"])
            pattern_desc = str(pattern["desc"])
            complexity = str(pattern["complexity"])
            
            skill_name = f"{domain_slug}_{pattern_slug}"
            tools = get_tools_for_domain(domain_slug, pattern_slug)
            memory_rules = get_memory_rules(domain_slug, pattern_slug, complexity)
            
            skills.append(
                SkillTemplate(
                    name=skill_name,
                    description=f"{pattern_desc} for {domain_label.lower()} with specialized expertise.",
                    version="1.0.0",
                    triggers=[pattern_verb, domain_label.lower(), *keywords[:3]],
                    when_to_use=f"Use when the request involves {domain_label.lower()} and requires {pattern_desc.lower()}.",
                    argument_hint=None,
                    prompt_template=generate_prompt_template(domain_label, pattern_desc, pattern_verb, complexity),
                    tool_permissions=tools,
                    memory_rules=memory_rules,
                    tags=[domain_slug, pattern_slug, complexity],
                    complexity=complexity,
                    domain=domain_slug,
                )
            )
    
    return skills


# Generate the full catalog
GENERATED_SKILL_CATALOG = generate_all_skills()

print(f"Generated {len(GENERATED_SKILL_CATALOG)} skills across {len(DOMAINS)} domains and {len(ALL_PATTERNS)} patterns")
