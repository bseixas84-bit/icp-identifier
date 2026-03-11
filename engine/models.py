from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


# ── Cited claim: every market insight carries provenance ──
class CitedClaim(BaseModel):
    text: str
    source_url: Optional[str] = None
    confidence: str = "inferred"  # "scraped", "inferred", "llm_estimate"


# ── Company DNA (extracted from real website content) ──
class CompanyDNA(BaseModel):
    company_name: str
    tagline: str = ""
    description: str = ""
    industry: str = ""
    sub_industry: str = ""
    business_model: str = ""
    products: list[str] = []
    features: list[str] = []
    target_segments: list[str] = []
    use_cases: list[str] = []
    technologies: list[str] = []
    pricing_model: str = ""
    company_size_signals: str = ""
    founded_year: str = ""
    headquarters: str = ""
    geographic_reach: list[str] = []
    certifications: list[str] = []
    partnerships: list[str] = []
    social_proof: list[str] = []
    hiring_signals: list[str] = []
    content_themes: list[str] = []
    tone_of_voice: str = ""
    sources: dict[str, str] = {}  # field_name -> source_url


# ── Market Intelligence (with citations) ──
class MarketIntel(BaseModel):
    market_size_estimate: Optional[CitedClaim] = None
    growth_trend: Optional[CitedClaim] = None
    likely_competitors: list[CitedClaim] = []
    competitive_advantages: list[CitedClaim] = []
    market_challenges: list[CitedClaim] = []
    customer_pain_points: list[CitedClaim] = []
    buying_triggers: list[CitedClaim] = []
    decision_makers: list[CitedClaim] = []
    sales_cycle_estimate: Optional[CitedClaim] = None
    ideal_customer_characteristics: list[CitedClaim] = []
    anti_icp_signals: list[CitedClaim] = []
    expansion_opportunities: list[CitedClaim] = []
    industry_trends: list[CitedClaim] = []


# ── Customer data models (for CSV upload path) ──
class Company(BaseModel):
    company_name: str
    industry: str
    employee_count: int
    annual_revenue_usd: float
    deal_size_usd: float
    sales_cycle_days: int
    churned: bool
    ltv_usd: float
    nps_score: Optional[int] = None
    tech_stack: str
    country: str
    founding_year: int


class ICPProfile(BaseModel):
    summary: str
    ideal_industries: list[str]
    ideal_employee_range: str
    ideal_revenue_range: str
    ideal_tech_signals: list[str]
    ideal_company_age: str
    key_patterns: list[str]
    anti_icp_summary: str
    anti_icp_signals: list[str]
    raw_analysis: str


class ScoredProspect(BaseModel):
    company_name: str
    score: int  # 0-100
    fit_reasons: list[str]
    risk_flags: list[str]
    recommendation: str  # "hot", "warm", "cold", "avoid"
