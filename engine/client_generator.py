import json
import io
from openai import OpenAI
import pandas as pd
from .researcher import CompanyProfile


GENERATE_PROMPT = """You are an expert B2B sales data analyst.
Given this company profile, generate a realistic CSV dataset of 18-20 companies that would be their clients.

## Company Profile:
Name: {name}
Industry: {industry}
Description: {description}
Products/Services: {products}
Target Customers: {target_customers}
Value Proposition: {value_proposition}

## Requirements:
- Generate 18-20 rows of realistic client companies
- Include a MIX: ~65% good clients (not churned, high NPS) and ~35% bad clients (churned, low NPS)
- Use real-sounding Brazilian company names appropriate for the sector
- Make the data realistic and varied
- churned column must be lowercase: true or false

## CSV Format (use exactly these columns):
company_name,industry,employee_count,annual_revenue_usd,deal_size_usd,sales_cycle_days,churned,ltv_usd,nps_score,tech_stack,country,founding_year

## Rules for realistic data:
- Good clients: NPS 7-10, sales_cycle 15-40 days, churned=false, LTV = deal_size * 3-6x
- Bad clients: NPS 2-5, sales_cycle 60-100 days, churned=true, LTV = deal_size * 1x
- tech_stack format: "Tech1;Tech2;Tech3" (e.g. "Cloud;AWS;Salesforce" or "Legacy;On-premise;Excel")
- Good clients tend to use modern tech stacks, bad ones tend to use legacy
- Revenue and deal sizes should be proportional and realistic for the sector
- Include variety in industries of the client companies

IMPORTANT: Return ONLY the CSV data. No markdown, no code blocks, no explanation. Start directly with the header row."""


def generate_clients(profile: CompanyProfile, api_key: str) -> pd.DataFrame:
    """Generate realistic client data based on company profile."""
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": GENERATE_PROMPT.format(
                    name=profile.name,
                    industry=profile.industry,
                    description=profile.description,
                    products=", ".join(profile.products_services[:8]),
                    target_customers=", ".join(profile.target_customers[:6]),
                    value_proposition=profile.value_proposition,
                ),
            }
        ],
        temperature=0.7,
        max_tokens=3000,
    )

    raw_text = response.choices[0].message.content.strip()

    # Remove markdown code block if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    df = pd.read_csv(io.StringIO(raw_text))
    df["churned"] = df["churned"].apply(lambda x: str(x).strip().lower() in ("true", "1", "yes", "sim"))

    return df
