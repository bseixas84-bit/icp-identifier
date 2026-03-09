import json
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel


class CompanyProfile(BaseModel):
    name: str
    description: str
    industry: str
    products_services: list[str]
    target_customers: list[str]
    value_proposition: str
    technologies_mentioned: list[str]
    company_size_signals: str
    geographic_focus: list[str]
    key_differentiators: list[str]
    potential_icp_hints: list[str]


RESEARCH_PROMPT = """You are an expert business analyst. Analyze this website content and extract a detailed company profile.

## Website URL: {url}

## Website Content:
{content}

Extract the following in valid JSON:
{{
    "name": "Company name",
    "description": "2-3 sentence description of what the company does",
    "industry": "Primary industry/sector",
    "products_services": ["list of products or services offered"],
    "target_customers": ["who are their likely customers based on website content"],
    "value_proposition": "Their main value proposition",
    "technologies_mentioned": ["any technologies, platforms, integrations mentioned"],
    "company_size_signals": "Any signals about company size (team size, office locations, revenue mentions, etc.)",
    "geographic_focus": ["countries or regions they operate in"],
    "key_differentiators": ["what makes them unique vs competitors"],
    "potential_icp_hints": ["based on their positioning, who would be their ideal customer - list 5-7 characteristics"]
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no code blocks.
Be thorough. Infer what you can from the content. Answer in Portuguese (Brazil)."""


def scrape_website(url: str) -> str:
    """Scrape website content, following common pages."""
    if not url.startswith("http"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    all_text = []

    # Scrape main page + common subpages
    pages = [url]
    for suffix in ["/about", "/sobre", "/services", "/servicos", "/products", "/produtos", "/clientes", "/customers", "/cases", "/portfolio"]:
        pages.append(url.rstrip("/") + suffix)

    with httpx.Client(follow_redirects=True, timeout=15, headers=headers) as client:
        for page_url in pages:
            try:
                resp = client.get(page_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Remove scripts, styles, nav, footer noise
                    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
                        tag.decompose()

                    text = soup.get_text(separator="\n", strip=True)
                    # Deduplicate empty lines and limit size
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    page_text = "\n".join(lines)

                    if page_text:
                        all_text.append(f"--- PAGE: {page_url} ---\n{page_text}")
            except Exception:
                continue

    combined = "\n\n".join(all_text)
    # Limit to ~12k chars to fit in context
    return combined[:12000] if combined else ""


def research_company(url: str, api_key: str) -> CompanyProfile:
    """Scrape a company website and extract structured profile using AI."""
    content = scrape_website(url)

    if not content:
        raise ValueError(f"Nao foi possivel acessar o site: {url}")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": RESEARCH_PROMPT.format(url=url, content=content),
            }
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    raw_text = response.choices[0].message.content
    json_start = raw_text.find("{")
    json_end = raw_text.rfind("}") + 1
    parsed = json.loads(raw_text[json_start:json_end])

    return CompanyProfile(**parsed)
