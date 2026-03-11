"""
Company Intelligence Pipeline
Discovery → Company DNA → Market Intel (with citations) → Dossier
No synthetic data. Only real, scraped, verifiable information.
"""

import json
import os
import re
import socket
import ipaddress
from datetime import datetime
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI


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


LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")


def _llm(api_key: str, prompt: str, max_tokens: int = 3000, temp: float = 0.4, retries: int = 2) -> str:
    client = OpenAI(api_key=api_key, base_url=LLM_BASE_URL)
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            if attempt < retries:
                import time
                time.sleep(2)
    raise last_err


def _extract_meta(soup: BeautifulSoup) -> dict:
    """Extract structured metadata from HTML: meta tags, og:*, ld+json."""
    meta = {}
    # Standard meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta["meta_description"] = desc_tag["content"]

    # Open Graph
    for prop in ["og:title", "og:description", "og:site_name", "og:type"]:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            meta[prop] = tag["content"]

    # LD+JSON structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                for key in ("name", "description", "foundingDate", "numberOfEmployees",
                            "address", "sameAs", "url"):
                    if key in data:
                        meta[f"ld_{key}"] = data[key]
        except (json.JSONDecodeError, TypeError):
            continue

    return meta


def _discover_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract internal links from page HTML, prioritizing informative pages."""
    priority_keywords = {
        "about", "sobre", "quem-somos", "about-us", "company", "empresa",
        "products", "produtos", "services", "servicos", "solucoes", "solutions",
        "customers", "clientes", "cases", "case-studies", "case-study",
        "pricing", "precos", "planos", "plans",
        "partners", "parceiros", "integrations", "integracoes",
        "blog", "press", "news", "noticias", "imprensa",
        "careers", "vagas", "trabalhe-conosco", "jobs",
        "investors", "investidores", "relacao-investidores",
        "team", "equipe", "leadership", "lideranca",
    }
    parsed_base = urlparse(base_url)
    found = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        # Same domain only
        if parsed.hostname != parsed_base.hostname:
            continue
        path = parsed.path.rstrip("/").lower()
        # Check if path contains priority keywords
        if any(kw in path for kw in priority_keywords):
            found.add(full_url.split("?")[0].split("#")[0])

    return list(found)[:30]


def _try_sitemap(base_url: str, client: httpx.Client) -> list[str]:
    """Try to fetch sitemap.xml and extract URLs."""
    urls = []
    sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
    try:
        resp = client.get(sitemap_url)
        if resp.status_code == 200 and "xml" in resp.headers.get("content-type", ""):
            soup = BeautifulSoup(resp.text, "html.parser")
            for loc in soup.find_all("loc"):
                url = loc.text.strip()
                if url:
                    urls.append(url)
    except Exception:
        pass
    return urls[:50]


def _scrape(url: str, paths: list[str] | None = None) -> dict:
    """
    Scrape multiple pages from a domain.
    Returns {"pages": {url: text}, "meta": {...}}
    """
    if not url.startswith("http"):
        url = "https://" + url
    if not _is_safe_url(url):
        return {"pages": {}, "meta": {}}
    base = url.rstrip("/")

    default_paths = [
        "", "/about", "/sobre", "/quem-somos", "/about-us",
        "/products", "/produtos", "/services", "/servicos", "/solucoes",
        "/customers", "/clientes", "/cases", "/case-studies",
        "/blog", "/careers", "/vagas", "/trabalhe-conosco",
        "/pricing", "/precos", "/planos",
        "/partners", "/parceiros", "/integrations", "/integracoes",
        "/press", "/news", "/investors", "/team", "/leadership",
    ]
    targets = set(base + p for p in (paths or default_paths))
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    results = {}
    all_meta = {}

    with httpx.Client(follow_redirects=True, timeout=12, headers=headers) as c:
        # Try sitemap first
        sitemap_urls = _try_sitemap(base, c)
        if sitemap_urls:
            # Add high-value sitemap URLs
            priority = {"about", "product", "service", "customer", "case", "pricing",
                        "blog", "press", "team", "partner", "investor"}
            for surl in sitemap_urls:
                path = urlparse(surl).path.lower()
                if any(kw in path for kw in priority):
                    targets.add(surl)

        # Scrape homepage first to discover links
        homepage_url = base + "/"
        try:
            resp = c.get(homepage_url)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                soup = BeautifulSoup(resp.text, "html.parser")
                all_meta = _extract_meta(soup)

                # Discover internal links
                discovered = _discover_links(soup, homepage_url)
                targets.update(discovered)

                for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer"]):
                    tag.decompose()
                text = "\n".join(l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip())
                if len(text) > 100:
                    results[homepage_url] = text[:6000]
        except Exception:
            pass

        # Scrape remaining targets
        for page_url in targets:
            if page_url.rstrip("/") == base or page_url in results:
                continue
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
                        results[page_url] = text[:6000]
            except Exception:
                continue

            # Cap total pages
            if len(results) >= 25:
                break

    return {"pages": results, "meta": all_meta}


# ── PHASE 1: Deep Scrape ──
def phase_discovery(url: str) -> dict:
    scrape_result = _scrape(url)
    pages = scrape_result["pages"]
    meta = scrape_result["meta"]
    combined = ""
    for page_url, text in pages.items():
        combined += f"\n\n--- {page_url} ---\n{text}"
    return {
        "pages_found": len(pages),
        "urls": list(pages.keys()),
        "content": combined[:30000],
        "meta": meta,
    }


# ── PHASE 2: Company DNA (with source tracking) ──
def phase_company_dna(content: str, url: str, api_key: str, meta: dict = None, lang: str = "en") -> dict:
    meta_context = ""
    if meta:
        meta_context = f"\n\nStructured metadata found:\n{json.dumps(meta, ensure_ascii=False, indent=2)}"

    prompt = f"""Analyze this company website content thoroughly and extract a complete company DNA profile.
IMPORTANT: Only include information that is directly stated or clearly implied in the content below.
Do NOT invent or assume data that is not present. If something is not found, use "unknown" or empty list.

Website: {url}
{meta_context}

Content:
{content[:18000]}

For each field, also track which page URL the information was found on.

Return a JSON object with:
{{
    "company_name": "...",
    "tagline": "Their main tagline or slogan found on the site",
    "description": "3-4 sentence description based on what the site says",
    "industry": "Primary industry",
    "sub_industry": "More specific niche",
    "business_model": "B2B, B2C, B2B2C, marketplace, SaaS, etc.",
    "products": ["list of products/services mentioned on the site"],
    "features": ["key features or capabilities mentioned"],
    "target_segments": ["customer segments explicitly mentioned or clearly targeted"],
    "use_cases": ["concrete use cases mentioned on the site"],
    "technologies": ["tech stack, platforms, integrations mentioned"],
    "pricing_model": "pricing model if mentioned, otherwise unknown",
    "company_size_signals": "any clues about size found on site",
    "founded_year": "year if mentioned, otherwise unknown",
    "headquarters": "location if mentioned, otherwise unknown",
    "geographic_reach": ["countries/regions mentioned"],
    "certifications": ["ISO, SOC2, LGPD, etc. if mentioned"],
    "partnerships": ["partner companies mentioned on the site"],
    "social_proof": ["customer logos, testimonials, case study names mentioned"],
    "hiring_signals": ["roles they're hiring for, if visible"],
    "content_themes": ["main topics from blog/content"],
    "tone_of_voice": "professional, casual, technical, enterprise, startup, etc.",
    "sources": {{
        "company_name": "https://page-url-where-found",
        "description": "https://page-url-where-found",
        ...
    }}
}}

Be thorough but ONLY include verifiable information from the content. Return ONLY valid JSON.
Answer in {"Portuguese (Brazil)" if lang == "pt" else "English"}."""

    raw = _llm(api_key, prompt)
    return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    """Extract and parse JSON from LLM response, handling common issues."""
    # Try direct parse first
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    # Try removing markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(cleaned[start:end])
    raise json.JSONDecodeError("No valid JSON found in response", raw, 0)


# ── PHASE 3: Market Intelligence (with citations) ──
def phase_market_intel(dna: dict, content: str, api_key: str, lang: str = "en") -> dict:
    prompt = f"""You are a senior market analyst. Based on this company profile AND the scraped website content,
generate a market intelligence report.

CRITICAL RULES:
- For each claim, indicate the confidence level:
  - "scraped": information directly found on the company website
  - "inferred": logical inference from the scraped data
  - "llm_estimate": based on your general knowledge (mark clearly)
- Include source_url when the info comes from a specific scraped page
- Do NOT present estimates as facts. Be honest about what is verified vs estimated.

Company: {dna.get('company_name', 'Unknown')}
Industry: {dna.get('industry', 'Unknown')} / {dna.get('sub_industry', '')}
Business Model: {dna.get('business_model', 'Unknown')}
Products: {', '.join(dna.get('products', [])[:8])}
Target Segments: {', '.join(dna.get('target_segments', [])[:6])}
Social Proof: {', '.join(dna.get('social_proof', [])[:5])}

Scraped content (for reference):
{content[:10000]}

Return JSON:
{{
    "market_size_estimate": {{"text": "...", "source_url": null, "confidence": "llm_estimate"}},
    "growth_trend": {{"text": "...", "source_url": null, "confidence": "inferred"}},
    "likely_competitors": [
        {{"text": "Competitor name - brief description", "source_url": "url if mentioned on site", "confidence": "scraped|inferred|llm_estimate"}}
    ],
    "competitive_advantages": [{{"text": "...", "source_url": "...", "confidence": "..."}}],
    "market_challenges": [{{"text": "...", "source_url": null, "confidence": "..."}}],
    "customer_pain_points": [{{"text": "...", "source_url": null, "confidence": "..."}}],
    "buying_triggers": [{{"text": "...", "source_url": null, "confidence": "..."}}],
    "decision_makers": [{{"text": "...", "source_url": null, "confidence": "..."}}],
    "sales_cycle_estimate": {{"text": "...", "source_url": null, "confidence": "llm_estimate"}},
    "ideal_customer_characteristics": [
        {{"text": "specific characteristic", "source_url": null, "confidence": "..."}}
    ],
    "anti_icp_signals": [
        {{"text": "red flag signal", "source_url": null, "confidence": "..."}}
    ],
    "expansion_opportunities": [{{"text": "...", "source_url": null, "confidence": "..."}}],
    "industry_trends": [{{"text": "...", "source_url": null, "confidence": "..."}}]
}}

Be specific and honest about confidence levels. Return ONLY valid JSON.
Answer in {"Portuguese (Brazil)" if lang == "pt" else "English"}."""

    for attempt in range(2):
        raw = _llm(api_key, prompt, max_tokens=4000)
        try:
            return _parse_json(raw)
        except json.JSONDecodeError:
            if attempt == 0:
                continue
            raise


# ── PHASE 4: Build Dossier (no fake data) ──
def build_dossier(url: str, discovery: dict, dna: dict, market: dict, lang: str = "pt") -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    def _claim_text(claim):
        """Extract text from a CitedClaim dict or plain string."""
        if isinstance(claim, dict):
            text = claim.get("text", str(claim))
            conf = claim.get("confidence", "")
            url = claim.get("source_url")
            badge = ""
            if conf == "scraped":
                badge = " [verified]"
            elif conf == "llm_estimate":
                badge = " [estimated]"
            elif conf == "inferred":
                badge = " [inferred]"
            link = f" ([source]({url}))" if url else ""
            return f"{text}{badge}{link}"
        return str(claim)

    def _claim_list(items):
        return "\n".join(f"- {_claim_text(c)}" for c in (items or []))

    if lang == "pt":
        md = f"""# Dossier de Inteligência
## {dna.get('company_name', url)}
> {dna.get('tagline', '')}

**Gerado em:** {now}
**URL:** {url}
**Páginas analisadas:** {discovery['pages_found']}

---

## 1. Visão Geral

**Indústria:** {dna.get('industry', 'N/A')} / {dna.get('sub_industry', '')}
**Modelo de negócio:** {dna.get('business_model', 'N/A')}
**Sede:** {dna.get('headquarters', 'N/A')}
**Fundação:** {dna.get('founded_year', 'N/A')}
**Porte:** {dna.get('company_size_signals', 'N/A')}
**Tom de voz:** {dna.get('tone_of_voice', 'N/A')}

{dna.get('description', '')}

## 2. Produtos & Serviços

"""
    else:
        md = f"""# Intelligence Dossier
## {dna.get('company_name', url)}
> {dna.get('tagline', '')}

**Generated:** {now}
**URL:** {url}
**Pages analyzed:** {discovery['pages_found']}

---

## 1. Overview

**Industry:** {dna.get('industry', 'N/A')} / {dna.get('sub_industry', '')}
**Business model:** {dna.get('business_model', 'N/A')}
**Headquarters:** {dna.get('headquarters', 'N/A')}
**Founded:** {dna.get('founded_year', 'N/A')}
**Size:** {dna.get('company_size_signals', 'N/A')}
**Tone of voice:** {dna.get('tone_of_voice', 'N/A')}

{dna.get('description', '')}

## 2. Products & Services

"""

    for p in dna.get("products", []):
        md += f"- {p}\n"

    key_features = "Features Principais" if lang == "pt" else "Key Features"
    md += f"\n### {key_features}\n"
    for f in dna.get("features", []):
        md += f"- {f}\n"

    pricing_title = "Modelo de Pricing" if lang == "pt" else "Pricing Model"
    md += f"\n### {pricing_title}\n{dna.get('pricing_model', 'N/A')}\n"

    mkt_title = "3. Mercado & Competição" if lang == "pt" else "3. Market & Competition"
    md += f"\n## {mkt_title}\n"

    tam_label = "TAM estimado" if lang == "pt" else "Estimated TAM"
    trend_label = "Tendência" if lang == "pt" else "Trend"
    md += f"\n**{tam_label}:** {_claim_text(market.get('market_size_estimate', 'N/A'))}\n"
    md += f"**{trend_label}:** {_claim_text(market.get('growth_trend', 'N/A'))}\n"

    comp_title = "Competidores" if lang == "pt" else "Competitors"
    md += f"\n### {comp_title}\n{_claim_list(market.get('likely_competitors', []))}\n"

    adv_title = "Vantagens Competitivas" if lang == "pt" else "Competitive Advantages"
    md += f"\n### {adv_title}\n{_claim_list(market.get('competitive_advantages', []))}\n"

    challenges_title = "Desafios do Mercado" if lang == "pt" else "Market Challenges"
    md += f"\n### {challenges_title}\n{_claim_list(market.get('market_challenges', []))}\n"

    trends_title = "Tendências da Indústria" if lang == "pt" else "Industry Trends"
    md += f"\n### {trends_title}\n{_claim_list(market.get('industry_trends', []))}\n"

    profile_title = "4. Perfil do Cliente" if lang == "pt" else "4. Customer Profile"
    md += f"\n## {profile_title}\n"

    segments_title = "Segmentos-alvo" if lang == "pt" else "Target Segments"
    md += f"\n### {segments_title}\n"
    for s in dna.get("target_segments", []):
        md += f"- {s}\n"

    uc_title = "Casos de Uso" if lang == "pt" else "Use Cases"
    md += f"\n### {uc_title}\n"
    for u in dna.get("use_cases", []):
        md += f"- {u}\n"

    pain_title = "Dores dos Clientes" if lang == "pt" else "Customer Pain Points"
    md += f"\n### {pain_title}\n{_claim_list(market.get('customer_pain_points', []))}\n"

    trigger_title = "Gatilhos de Compra" if lang == "pt" else "Buying Triggers"
    md += f"\n### {trigger_title}\n{_claim_list(market.get('buying_triggers', []))}\n"

    dm_title = "Decisores Típicos" if lang == "pt" else "Typical Decision Makers"
    md += f"\n### {dm_title}\n{_claim_list(market.get('decision_makers', []))}\n"

    cycle_label = "Ciclo de vendas estimado" if lang == "pt" else "Estimated sales cycle"
    md += f"\n**{cycle_label}:** {_claim_text(market.get('sales_cycle_estimate', 'N/A'))}\n"

    icp_title = "5. Pré-análise ICP" if lang == "pt" else "5. ICP Pre-analysis"
    md += f"\n## {icp_title}\n"

    ideal_title = "Características do Cliente Ideal" if lang == "pt" else "Ideal Customer Characteristics"
    md += f"\n### {ideal_title}\n{_claim_list(market.get('ideal_customer_characteristics', []))}\n"

    anti_title = "Sinais de Anti-ICP (Evitar)" if lang == "pt" else "Anti-ICP Signals (Avoid)"
    md += f"\n### {anti_title}\n{_claim_list(market.get('anti_icp_signals', []))}\n"

    signals_title = "6. Sinais Adicionais" if lang == "pt" else "6. Additional Signals"
    md += f"\n## {signals_title}\n"

    tech_title = "Tecnologias Identificadas" if lang == "pt" else "Technologies Identified"
    md += f"\n### {tech_title}\n"
    for t in dna.get("technologies", []):
        md += f"- {t}\n"

    cert_title = "Certificações" if lang == "pt" else "Certifications"
    md += f"\n### {cert_title}\n"
    for c in dna.get("certifications", []):
        md += f"- {c}\n"

    partner_title = "Parcerias" if lang == "pt" else "Partnerships"
    md += f"\n### {partner_title}\n"
    for p in dna.get("partnerships", []):
        md += f"- {p}\n"

    sp_title = "Prova Social" if lang == "pt" else "Social Proof"
    md += f"\n### {sp_title}\n"
    for s in dna.get("social_proof", []):
        md += f"- {s}\n"

    exp_title = "Oportunidades de Expansão" if lang == "pt" else "Expansion Opportunities"
    md += f"\n### {exp_title}\n{_claim_list(market.get('expansion_opportunities', []))}\n"

    # Pages analyzed
    pages_title = "Páginas Analisadas" if lang == "pt" else "Pages Analyzed"
    md += f"\n## {pages_title}\n"
    for u in discovery.get("urls", []):
        md += f"- {u}\n"

    if lang == "pt":
        md += f"""
---

*Dossier gerado automaticamente por ICP Identifier*
*Fontes: Scraping do site oficial ({discovery['pages_found']} páginas) + Análise por IA (Llama 3.3 70B via Groq)*
*Dados de mercado marcados com [estimated] são baseados em conhecimento do modelo de IA e devem ser verificados*
"""
    else:
        md += f"""
---

*Dossier automatically generated by ICP Identifier*
*Sources: Official website scraping ({discovery['pages_found']} pages) + AI Analysis (Llama 3.3 70B via Groq)*
*Market data marked with [estimated] is based on AI model knowledge and should be verified*
"""

    return md


# ── MAIN PIPELINE ──
def run_intelligence_pipeline(url: str, api_key: str, progress_callback=None, lang: str = "en"):
    """
    Run the intelligence pipeline (4 phases, no synthetic data).
    progress_callback(phase_num, phase_name, status) for UI updates.
    Returns (dna, market, dossier_md)
    """

    def update(phase, name, status):
        if progress_callback:
            progress_callback(phase, name, status)

    # Phase 1: Discovery
    update(1, "Discovery", "Scanning website...")
    discovery = phase_discovery(url)
    if not discovery["content"]:
        raise ValueError(f"Could not access: {url}")
    update(1, "Discovery", f"{discovery['pages_found']} pages found")

    # Phase 2: Company DNA
    update(2, "Company DNA", "Extracting company profile...")
    dna = phase_company_dna(discovery["content"], url, api_key,
                            meta=discovery.get("meta"), lang=lang)
    update(2, "Company DNA", f"{dna.get('company_name', 'OK')}")

    # Phase 3: Market Intel
    update(3, "Market Intel", "Analyzing market and competitors...")
    market = phase_market_intel(dna, discovery["content"], api_key, lang=lang)
    update(3, "Market Intel", f"{len(market.get('likely_competitors', []))} competitors mapped")

    # Phase 4: Dossier
    update(4, "Dossier", "Compiling report...")
    dossier_md = build_dossier(url, discovery, dna, market, lang=lang)
    update(4, "Dossier", "Report ready")

    return dna, market, dossier_md
