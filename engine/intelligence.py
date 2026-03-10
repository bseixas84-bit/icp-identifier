"""
Company Intelligence Pipeline
Deep research → Dossier → Client Generation → Pre-ICP
"""

import json
import io
import os
import re
import socket
import ipaddress
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd


def _is_safe_url(url: str) -> bool:
    """Block SSRF: reject private/loopback/link-local IPs and non-http schemes."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = socket.gethostbyname(hostname)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
            return False
    except (socket.gaierror, ValueError):
        return False
    return True


def _llm(api_key: str, prompt: str, max_tokens: int = 3000, temp: float = 0.4) -> str:
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_tokens,
    )
    return r.choices[0].message.content.strip()


def _scrape(url: str, paths: list[str] | None = None) -> dict[str, str]:
    """Scrape multiple pages from a domain. Returns {url: text}."""
    if not url.startswith("http"):
        url = "https://" + url
    if not _is_safe_url(url):
        return {}
    base = url.rstrip("/")

    default_paths = [
        "", "/about", "/sobre", "/quem-somos", "/about-us",
        "/products", "/produtos", "/services", "/servicos", "/solucoes",
        "/customers", "/clientes", "/cases", "/case-studies",
        "/blog", "/careers", "/vagas", "/trabalhe-conosco",
        "/pricing", "/precos", "/planos",
        "/partners", "/parceiros", "/integrations", "/integracoes",
    ]
    targets = paths or default_paths
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    results = {}
    with httpx.Client(follow_redirects=True, timeout=12, headers=headers) as c:
        for path in targets:
            page_url = base + path
            if not _is_safe_url(page_url):
                continue
            try:
                resp = c.get(page_url)
                if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer"]):
                        tag.decompose()
                    text = "\n".join(l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip())
                    if len(text) > 100:
                        results[page_url] = text[:4000]
            except Exception:
                continue
    return results


# ── PHASE 1: Deep Scrape ──
def phase_discovery(url: str) -> dict:
    pages = _scrape(url)
    combined = ""
    for page_url, text in pages.items():
        combined += f"\n\n--- {page_url} ---\n{text}"
    return {
        "pages_found": len(pages),
        "urls": list(pages.keys()),
        "content": combined[:20000],
    }


# ── PHASE 2: Company DNA ──
def phase_company_dna(content: str, url: str, api_key: str, lang: str = "en") -> dict:
    prompt = f"""Analyze this company website content thoroughly and extract a complete company DNA profile.

Website: {url}
Content:
{content[:15000]}

Return a JSON object with:
{{
    "company_name": "...",
    "tagline": "Their main tagline or slogan",
    "description": "3-4 sentence comprehensive description",
    "industry": "Primary industry",
    "sub_industry": "More specific niche",
    "business_model": "B2B, B2C, B2B2C, marketplace, SaaS, etc.",
    "products": ["detailed list of products/services"],
    "features": ["key features or capabilities"],
    "target_segments": ["specific customer segments they target"],
    "use_cases": ["concrete use cases mentioned"],
    "technologies": ["tech stack, platforms, integrations mentioned"],
    "pricing_model": "freemium, subscription, per-user, custom, etc. or unknown",
    "company_size_signals": "any clues about size - team, offices, customers count",
    "founded_year": "year or unknown",
    "headquarters": "location or unknown",
    "geographic_reach": ["countries/regions"],
    "certifications": ["ISO, SOC2, LGPD, etc."],
    "partnerships": ["partner companies mentioned"],
    "social_proof": ["customer logos, testimonials, case study names mentioned"],
    "hiring_signals": ["roles they're hiring for, if visible"],
    "content_themes": ["main topics from blog/content"],
    "tone_of_voice": "professional, casual, technical, enterprise, startup, etc."
}}

Be thorough. Infer from context when not explicit. Return ONLY valid JSON.
Answer in {"Portuguese (Brazil)" if lang == "pt" else "English"}."""

    raw = _llm(api_key, prompt)
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


# ── PHASE 3: Market Intelligence ──
def phase_market_intel(dna: dict, api_key: str, lang: str = "en") -> dict:
    prompt = f"""You are a senior market analyst. Based on this company profile, generate a comprehensive market intelligence report.

Company: {dna.get('company_name', 'Unknown')}
Industry: {dna.get('industry', 'Unknown')} / {dna.get('sub_industry', '')}
Business Model: {dna.get('business_model', 'Unknown')}
Products: {', '.join(dna.get('products', [])[:8])}
Target Segments: {', '.join(dna.get('target_segments', [])[:6])}

Return JSON:
{{
    "market_size_estimate": "Estimated TAM for their market in Brazil",
    "growth_trend": "growing, stable, declining + brief explanation",
    "likely_competitors": ["list 5-8 likely competitors with brief description"],
    "competitive_advantages": ["what likely differentiates them"],
    "market_challenges": ["key challenges in their market"],
    "customer_pain_points": ["what problems their customers likely face"],
    "buying_triggers": ["events that trigger purchase decisions for their product"],
    "decision_makers": ["typical job titles of buyers"],
    "sales_cycle_estimate": "estimated days for typical deal",
    "ideal_customer_characteristics": [
        "list 10 specific, actionable characteristics of their ideal customer"
    ],
    "anti_icp_signals": [
        "list 7 red flags that indicate a bad-fit customer"
    ],
    "expansion_opportunities": ["potential growth vectors"],
    "industry_trends": ["3-5 relevant trends affecting their market"]
}}

Be specific and data-driven. Use your knowledge of the Brazilian market. Return ONLY valid JSON.
Answer in {"Portuguese (Brazil)" if lang == "pt" else "English"}."""

    raw = _llm(api_key, prompt)
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


# ── PHASE 4: Generate Client Dataset ──
def phase_generate_clients(dna: dict, market: dict, api_key: str) -> pd.DataFrame:
    prompt = f"""Generate a realistic CSV dataset of 20 companies that would be clients of {dna.get('company_name', 'this company')}.

Context:
- Industry: {dna.get('industry', '')}
- Products: {', '.join(dna.get('products', [])[:6])}
- Target: {', '.join(dna.get('target_segments', [])[:5])}
- Ideal customer: {', '.join(market.get('ideal_customer_characteristics', [])[:5])}
- Anti-ICP signals: {', '.join(market.get('anti_icp_signals', [])[:4])}
- Sales cycle: {market.get('sales_cycle_estimate', '30-60 days')}

Generate EXACTLY this CSV (20 rows, header + 20 data rows):
company_name,industry,employee_count,annual_revenue_usd,deal_size_usd,sales_cycle_days,churned,ltv_usd,nps_score,tech_stack,country,founding_year

Rules:
- 13 good clients: NPS 7-10, cycle 15-45 days, churned=false, LTV=deal*3-6x, modern tech
- 7 bad clients: NPS 2-5, cycle 55-100 days, churned=true, LTV=deal*1x, legacy tech
- Use realistic Brazilian company names (can be fictional but believable)
- Vary industries among client companies
- tech_stack format: "Tech1;Tech2;Tech3"
- All values should be proportional and realistic

Return ONLY the CSV. No markdown, no explanation."""

    raw = _llm(api_key, prompt, max_tokens=3000, temp=0.7)
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])

    df = pd.read_csv(io.StringIO(raw))
    df["churned"] = df["churned"].apply(lambda x: str(x).strip().lower() in ("true", "1", "yes"))
    return df


# ── PHASE 5: Build Dossier ──
def build_dossier(url: str, discovery: dict, dna: dict, market: dict, df: pd.DataFrame) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    churn_rate = df["churned"].mean() * 100
    avg_ltv = df["ltv_usd"].mean()
    avg_nps = df["nps_score"].mean()

    md = f"""# Company Intelligence Dossier
## {dna.get('company_name', url)}
> {dna.get('tagline', '')}

**Gerado em:** {now}
**URL:** {url}
**Paginas analisadas:** {discovery['pages_found']}

---

## 1. Visao Geral

**Industria:** {dna.get('industry', 'N/A')} / {dna.get('sub_industry', '')}
**Modelo de negocio:** {dna.get('business_model', 'N/A')}
**Sede:** {dna.get('headquarters', 'N/A')}
**Fundacao:** {dna.get('founded_year', 'N/A')}
**Porte:** {dna.get('company_size_signals', 'N/A')}
**Tom de voz:** {dna.get('tone_of_voice', 'N/A')}

{dna.get('description', '')}

## 2. Produtos & Servicos

"""
    for p in dna.get("products", []):
        md += f"- {p}\n"

    md += f"""
### Features Principais
"""
    for f in dna.get("features", []):
        md += f"- {f}\n"

    md += f"""
### Modelo de Pricing
{dna.get('pricing_model', 'N/A')}

## 3. Mercado & Competicao

**TAM estimado:** {market.get('market_size_estimate', 'N/A')}
**Tendencia:** {market.get('growth_trend', 'N/A')}

### Competidores Provaveis
"""
    for c in market.get("likely_competitors", []):
        md += f"- {c}\n"

    md += """
### Vantagens Competitivas
"""
    for a in market.get("competitive_advantages", []):
        md += f"- {a}\n"

    md += """
### Desafios do Mercado
"""
    for ch in market.get("market_challenges", []):
        md += f"- {ch}\n"

    md += """
### Tendencias da Industria
"""
    for t in market.get("industry_trends", []):
        md += f"- {t}\n"

    md += f"""
## 4. Perfil do Cliente

### Segmentos-alvo
"""
    for s in dna.get("target_segments", []):
        md += f"- {s}\n"

    md += """
### Casos de Uso
"""
    for u in dna.get("use_cases", []):
        md += f"- {u}\n"

    md += """
### Dores dos Clientes
"""
    for p in market.get("customer_pain_points", []):
        md += f"- {p}\n"

    md += """
### Gatilhos de Compra
"""
    for b in market.get("buying_triggers", []):
        md += f"- {b}\n"

    md += """
### Decisores Tipicos
"""
    for d in market.get("decision_makers", []):
        md += f"- {d}\n"

    md += f"""
**Ciclo de vendas estimado:** {market.get('sales_cycle_estimate', 'N/A')}

## 5. ICP Pre-Analise

### Caracteristicas do Cliente Ideal
"""
    for i, ic in enumerate(market.get("ideal_customer_characteristics", []), 1):
        md += f"{i}. {ic}\n"

    md += """
### Sinais de Anti-ICP (Evitar)
"""
    for a in market.get("anti_icp_signals", []):
        md += f"- {a}\n"

    md += f"""
## 6. Sinais Adicionais

### Tecnologias Identificadas
"""
    for t in dna.get("technologies", []):
        md += f"- {t}\n"

    md += """
### Certificacoes
"""
    for c in dna.get("certifications", []):
        md += f"- {c}\n"

    md += """
### Parcerias
"""
    for p in dna.get("partnerships", []):
        md += f"- {p}\n"

    md += """
### Prova Social
"""
    for s in dna.get("social_proof", []):
        md += f"- {s}\n"

    md += """
### Sinais de Contratacao
"""
    for h in dna.get("hiring_signals", []):
        md += f"- {h}\n"

    md += """
### Oportunidades de Expansao
"""
    for e in market.get("expansion_opportunities", []):
        md += f"- {e}\n"

    md += f"""
## 7. Base de Clientes Simulada

**Total:** {len(df)} empresas
**Ativos:** {len(df[~df['churned']])}
**Churn rate:** {churn_rate:.0f}%
**LTV medio:** ${avg_ltv:,.0f}
**NPS medio:** {avg_nps:.1f}

---

*Dossier gerado automaticamente por ICP Identifier*
*Fontes: Scraping do site oficial ({discovery['pages_found']} paginas) + Analise por IA (Llama 3.3 70B via Groq)*
*As informacoes de mercado sao estimativas baseadas em conhecimento do modelo de IA*
"""

    return md


# ── MAIN PIPELINE ──
def run_intelligence_pipeline(url: str, api_key: str, progress_callback=None, lang: str = "en"):
    """
    Run the full intelligence pipeline.
    progress_callback(phase_num, phase_name, status) for UI updates.
    Returns (dna, market, df, dossier_path, dossier_md)
    """

    def update(phase, name, status):
        if progress_callback:
            progress_callback(phase, name, status)

    # Phase 1
    update(1, "Discovery", "Escaneando site...")
    discovery = phase_discovery(url)
    if not discovery["content"]:
        raise ValueError(f"Nao foi possivel acessar: {url}")
    update(1, "Discovery", f"{discovery['pages_found']} paginas encontradas")

    # Phase 2
    update(2, "Company DNA", "Extraindo perfil da empresa...")
    dna = phase_company_dna(discovery["content"], url, api_key, lang=lang)
    update(2, "Company DNA", f"{dna.get('company_name', 'OK')}")

    # Phase 3
    update(3, "Market Intel", "Analisando mercado e competidores...")
    market = phase_market_intel(dna, api_key, lang=lang)
    update(3, "Market Intel", f"{len(market.get('likely_competitors', []))} competidores mapeados")

    # Phase 4
    update(4, "Client Generation", "Gerando base de clientes simulada...")
    df = phase_generate_clients(dna, market, api_key)
    update(4, "Client Generation", f"{len(df)} clientes gerados")

    # Phase 5
    update(5, "Dossier", "Compilando relatorio...")
    dossier_md = build_dossier(url, discovery, dna, market, df)

    update(5, "Dossier", "Relatorio pronto")

    return dna, market, df, "", dossier_md
