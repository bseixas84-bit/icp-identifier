from pydantic import BaseModel


class Company(BaseModel):
    company_name: str
    industry: str
    employee_count: int
    annual_revenue_usd: float
    deal_size_usd: float
    sales_cycle_days: int
    churned: bool
    ltv_usd: float
    nps_score: int
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
