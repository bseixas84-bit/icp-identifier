"""
Internationalization (i18n) for ICP Identifier
Auto-detects PT-BR vs EN based on browser language.
"""

TRANSLATIONS = {
    # ── Page / Header ──
    "page_title": {"pt": "ICP Identifier", "en": "ICP Identifier"},
    "powered_by": {"pt": "Powered by AI", "en": "Powered by AI"},
    "header_title": {"pt": "ICP Identifier", "en": "ICP Identifier"},
    "header_subtitle": {"pt": "Descubra seu cliente ideal a partir dos seus dados", "en": "Discover your ideal customer from your data"},

    # ── Sidebar ──
    "data_source": {"pt": "Fonte de Dados", "en": "Data Source"},
    "choose_option": {"pt": "Escolha uma opção", "en": "Choose an option"},
    "preloaded_company": {"pt": "Empresa pré-carregada", "en": "Pre-loaded company"},
    "research_new": {"pt": "Pesquisar nova empresa", "en": "Research new company"},
    "upload_csv": {"pt": "Upload CSV", "en": "Upload CSV"},
    "instant_loading": {"pt": "Carregamento instantâneo", "en": "Instant loading"},
    "instant_help": {"pt": "Dados completos pré-analisados. Carregamento imediato.", "en": "Complete pre-analyzed data. Instant loading."},
    "preloaded_data": {"pt": "Dados pré-carregados", "en": "Pre-loaded data"},
    "source_cache": {"pt": "Fonte: Cache local + IA (Llama 3.3 70B)", "en": "Source: Local cache + AI (Llama 3.3 70B)"},
    "b3_companies": {"pt": "Empresas B3 (exemplos)", "en": "B3 Companies (examples)"},
    "select_placeholder": {"pt": "Selecionar...", "en": "Select..."},
    "type_url": {"pt": "Ou digite uma URL", "en": "Or enter a URL"},
    "url_placeholder": {"pt": "exemplo.com.br", "en": "example.com"},
    "research_btn": {"pt": "Pesquisar", "en": "Research"},
    "employees_label": {"pt": "funcionários", "en": "employees"},
    "revenue_label": {"pt": "receita", "en": "revenue"},
    "founded_in": {"pt": "Fundada em", "en": "Founded in"},
    "source_label": {"pt": "Fonte", "en": "Source"},
    "upload_customers": {"pt": "Upload CSV de clientes", "en": "Upload customer CSV"},
    "use_sample": {"pt": "Usar dados de exemplo", "en": "Use sample data"},
    "prospects_label": {"pt": "Prospects", "en": "Prospects"},
    "upload_prospects": {"pt": "Upload CSV de prospects", "en": "Upload prospect CSV"},
    "url_invalid": {"pt": "URL inválida ou bloqueada (IPs privados/locais não são permitidos).", "en": "Invalid or blocked URL (private/local IPs are not allowed)."},
    "file_too_large": {"pt": "Arquivo muito grande ({size} MB). Limite: 5 MB.", "en": "File too large ({size} MB). Limit: 5 MB."},
    "language": {"pt": "Idioma", "en": "Language"},

    # ── Pipeline ──
    "configure_api": {"pt": "Configure GROQ_API_KEY no arquivo .env", "en": "Set GROQ_API_KEY in .env file"},
    "pipeline_title": {"pt": "Intelligence Pipeline", "en": "Intelligence Pipeline"},
    "pipeline_error": {"pt": "Erro no pipeline: {e}", "en": "Pipeline error: {e}"},
    "phase_1": {"pt": "Discovery", "en": "Discovery"},
    "phase_2": {"pt": "Company DNA", "en": "Company DNA"},
    "phase_3": {"pt": "Market Intel", "en": "Market Intel"},
    "phase_4": {"pt": "Client Generation", "en": "Client Generation"},
    "phase_5": {"pt": "Dossier", "en": "Dossier"},

    # ── Company DNA Card ──
    "products_services": {"pt": "Produtos & Serviços", "en": "Products & Services"},
    "technologies": {"pt": "Tecnologias", "en": "Technologies"},
    "target_segments": {"pt": "Segmentos-alvo", "en": "Target Segments"},
    "social_proof": {"pt": "Prova Social", "en": "Social Proof"},
    "partnerships": {"pt": "Parcerias", "en": "Partnerships"},
    "scrape_source": {"pt": "Scraping do site oficial + análise por IA (Llama 3.3 70B via Groq)", "en": "Official website scraping + AI analysis (Llama 3.3 70B via Groq)"},

    # ── Market Intel ──
    "market_intel_title": {"pt": "Inteligência de Mercado", "en": "Market Intelligence"},
    "competitors_mapped": {"pt": "Competidores Mapeados", "en": "Mapped Competitors"},
    "buying_triggers": {"pt": "Gatilhos de Compra", "en": "Buying Triggers"},
    "typical_decision_makers": {"pt": "Decisores Típicos", "en": "Typical Decision Makers"},
    "ideal_customer_chars": {"pt": "Características do Cliente Ideal", "en": "Ideal Customer Characteristics"},
    "anti_icp_signals_title": {"pt": "Sinais de Anti-ICP", "en": "Anti-ICP Signals"},

    # ── Dossier ──
    "dossier_title": {"pt": "{name} — Intelligence Dossier", "en": "{name} — Intelligence Dossier"},
    "dossier_available": {"pt": "Relatório disponível para download", "en": "Report available for download"},
    "download_dossier": {"pt": "Baixar Dossier (.md)", "en": "Download Dossier (.md)"},

    # ── Metrics ──
    "customers": {"pt": "Clientes", "en": "Customers"},
    "active": {"pt": "Ativos", "en": "Active"},
    "churn_rate": {"pt": "Churn Rate", "en": "Churn Rate"},
    "avg_ltv": {"pt": "LTV Médio", "en": "Avg LTV"},
    "avg_cycle": {"pt": "Ciclo Médio", "en": "Avg Cycle"},

    # ── Tabs ──
    "tab_tiers": {"pt": "ICP Tiers", "en": "ICP Tiers"},
    "tab_health": {"pt": "Saúde do Cliente", "en": "Customer Health"},
    "tab_finance": {"pt": "Análise Financeira", "en": "Financial Analysis"},
    "tab_segment": {"pt": "Segmentação & Tech", "en": "Segmentation & Tech"},
    "tab_risk": {"pt": "Risco & Cohort", "en": "Risk & Cohort"},
    "tab_summary": {"pt": "Resumo Executivo", "en": "Executive Summary"},
    "visual_analysis": {"pt": "Análise Visual", "en": "Visual Analysis"},

    # ── Tier Labels ──
    "tier_ideal": {"pt": "Ideal", "en": "Ideal"},
    "tier_good": {"pt": "Bom", "en": "Good"},
    "tier_risky": {"pt": "Arriscado", "en": "Risky"},
    "tier_avoid": {"pt": "Evitar", "en": "Avoid"},
    "of_base": {"pt": "da base", "en": "of base"},

    # ── Tier Charts ──
    "tier_distribution": {"pt": "Distribuição por Tier", "en": "Tier Distribution"},
    "tier_how_calculated": {
        "pt": "<strong>Como os Tiers são calculados?</strong> Score composto de 0-100 baseado em 5 dimensões:",
        "en": "<strong>How are Tiers calculated?</strong> Composite score 0-100 based on 5 dimensions:",
    },
    "tier_dim_nps": {"pt": "NPS (30%) — satisfação do cliente", "en": "NPS (30%) — customer satisfaction"},
    "tier_dim_retention": {"pt": "Retenção (25%) — se o cliente deu churn ou não", "en": "Retention (25%) — whether the customer churned"},
    "tier_dim_tech": {"pt": "Tech Stack (15%) — maturidade tecnológica (Cloud vs Legacy)", "en": "Tech Stack (15%) — tech maturity (Cloud vs Legacy)"},
    "tier_dim_cycle": {"pt": "Ciclo de Vendas (15%) — eficiência de aquisição", "en": "Sales Cycle (15%) — acquisition efficiency"},
    "tier_dim_roi": {"pt": "ROI (15%) — LTV em relação ao deal size", "en": "ROI (15%) — LTV relative to deal size"},
    "tier_comparison_radar": {"pt": "Comparação entre Tiers (Radar)", "en": "Tier Comparison (Radar)"},
    "retention_pct": {"pt": "Retenção %", "en": "Retention %"},
    "ltv_norm": {"pt": "LTV (norm)", "en": "LTV (norm)"},
    "deal_size_norm": {"pt": "Deal Size (norm)", "en": "Deal Size (norm)"},
    "cycle_speed": {"pt": "Velocidade Ciclo", "en": "Cycle Speed"},
    "radar_explain": {
        "pt": "<strong>O que estou vendo?</strong> Comparação multi-dimensional entre tiers. Quanto maior a área, melhor o perfil.",
        "en": "<strong>What am I seeing?</strong> Multi-dimensional comparison between tiers. The larger the area, the better the profile.",
    },
    "radar_insight_1": {
        "pt": "Tier 1 deve dominar em todas as dimensões — é o formato ideal de cliente.",
        "en": "Tier 1 should dominate all dimensions — it's the ideal customer profile.",
    },
    "radar_insight_2": {
        "pt": "Gaps entre tiers revelam onde clientes de menor tier falham (ex: tech legado, ciclo longo).",
        "en": "Gaps between tiers reveal where lower-tier customers fall short (e.g., legacy tech, long cycles).",
    },
    "avg_ltv_per_tier": {"pt": "LTV Médio por Tier", "en": "Avg LTV per Tier"},
    "avg_cycle_per_tier": {"pt": "Ciclo Médio por Tier (dias)", "en": "Avg Cycle per Tier (days)"},
    "tier_label": {"pt": "Tier", "en": "Tier"},
    "avg_ltv_usd": {"pt": "LTV Médio (USD)", "en": "Avg LTV (USD)"},
    "cycle_days": {"pt": "Ciclo (dias)", "en": "Cycle (days)"},
    "clients_by_tier": {"pt": "Clientes por Tier", "en": "Customers by Tier"},
    "func": {"pt": "func", "en": "emp"},

    # ── Tier Methodology ──
    "tier_methodology_title": {"pt": "<strong>Metodologia de Tiering</strong>", "en": "<strong>Tiering Methodology</strong>"},
    "tier_methodology_intro": {
        "pt": "Baseada nos frameworks de Gartner, Inverta (4 Levels of ICP Segmentation) e DataBees (Account Tiering).",
        "en": "Based on Gartner, Inverta (4 Levels of ICP Segmentation) and DataBees (Account Tiering) frameworks.",
    },
    "tier_1_desc": {
        "pt": "Tier 1 (85+): Top 10-15% — clientes ideais que merecem tratamento high-touch e ABM personalizado.",
        "en": "Tier 1 (85+): Top 10-15% — ideal customers deserving high-touch treatment and personalized ABM.",
    },
    "tier_2_desc": {
        "pt": "Tier 2 (65-84): Clientes bons com campanhas semi-personalizadas e processos padronizados.",
        "en": "Tier 2 (65-84): Good customers with semi-personalized campaigns and standardized processes.",
    },
    "tier_3_desc": {
        "pt": "Tier 3 (40-64): Sinais mistos — nurture até amadurecerem ou descarte se não evoluírem.",
        "en": "Tier 3 (40-64): Mixed signals — nurture until they mature or discard if they don't evolve.",
    },
    "tier_4_desc": {
        "pt": "Tier 4 (<40): Anti-ICP — evitar investimento, redirecionar recursos para tiers superiores.",
        "en": "Tier 4 (<40): Anti-ICP — avoid investment, redirect resources to upper tiers.",
    },

    # ── Health Tab ──
    "health_matrix": {"pt": "Matriz de Saúde do Cliente", "en": "Customer Health Matrix"},
    "sales_cycle_days": {"pt": "Ciclo de Vendas (dias)", "en": "Sales Cycle (days)"},
    "nps_score_label": {"pt": "NPS Score", "en": "NPS Score"},
    "churned_label": {"pt": "Churned", "en": "Churned"},
    "ideal_quadrant": {"pt": "Ideal", "en": "Ideal"},
    "slow_loyal": {"pt": "Lento mas leal", "en": "Slow but loyal"},
    "fast_unhappy": {"pt": "Rápido mas insatisfeito", "en": "Fast but unhappy"},
    "danger_zone": {"pt": "Zona de Perigo", "en": "Danger Zone"},
    "health_explain": {
        "pt": "<strong>O que estou vendo?</strong> Cada bolha é um cliente. Eixo X = ciclo de vendas, Y = NPS, tamanho = LTV.",
        "en": "<strong>What am I seeing?</strong> Each bubble is a customer. X axis = sales cycle, Y = NPS, size = LTV.",
    },
    "health_insight_1": {
        "pt": "Quadrante superior esquerdo = perfil ideal (ciclo curto + NPS alto).",
        "en": "Upper left quadrant = ideal profile (short cycle + high NPS).",
    },
    "health_insight_2": {
        "pt": "Quadrante inferior direito = zona de perigo (ciclo longo + NPS baixo).",
        "en": "Lower right quadrant = danger zone (long cycle + low NPS).",
    },
    "health_insight_3": {
        "pt": "Bolhas vermelhas são churned — note a concentração na zona de perigo.",
        "en": "Red bubbles are churned — note the concentration in the danger zone.",
    },
    "nps_distribution": {"pt": "Distribuição de NPS", "en": "NPS Distribution"},
    "active_label": {"pt": "Ativos", "en": "Active"},
    "churned_status": {"pt": "Churned", "en": "Churned"},
    "detractors": {"pt": "Detratores", "en": "Detractors"},
    "neutrals": {"pt": "Neutros", "en": "Neutrals"},
    "promoters": {"pt": "Promotores", "en": "Promoters"},
    "quantity": {"pt": "Quantidade", "en": "Quantity"},
    "nps_explain": {
        "pt": "<strong>O que estou vendo?</strong> Distribuição NPS separada por status (ativo vs churned).",
        "en": "<strong>What am I seeing?</strong> NPS distribution separated by status (active vs churned).",
    },
    "nps_insight_1": {
        "pt": "NPS Net Score: {nps_net} — % Promotores (9-10) menos % Detratores (0-6).",
        "en": "NPS Net Score: {nps_net} — % Promoters (9-10) minus % Detractors (0-6).",
    },
    "nps_insight_2": {
        "pt": "{promoters} promotores e {detractors} detratores na base.",
        "en": "{promoters} promoters and {detractors} detractors in the base.",
    },
    "nps_insight_3": {
        "pt": "Clientes churned se concentram na faixa de detratores — NPS baixo é forte preditor de churn.",
        "en": "Churned customers concentrate in the detractor range — low NPS is a strong churn predictor.",
    },

    "churn_by_cycle": {"pt": "Churn por Ciclo de Vendas", "en": "Churn Rate by Sales Cycle"},
    "demo_data_disclaimer": {
        "pt": "Dados demo — as métricas de clientes são estimativas ilustrativas. NPS não está incluído por questões de integridade metodológica.",
        "en": "Demo data — client metrics are estimates for illustration only. NPS is excluded for methodological integrity.",
    },

    # ── Finance Tab ──
    "ltv_per_customer": {"pt": "LTV por Cliente", "en": "LTV per Customer"},
    "ltv_usd": {"pt": "LTV (USD)", "en": "LTV (USD)"},
    "ltv_explain": {
        "pt": "<strong>O que estou vendo?</strong> LTV de cada cliente, ordenado de menor para maior.",
        "en": "<strong>What am I seeing?</strong> LTV for each customer, sorted from lowest to highest.",
    },
    "ltv_insight_1": {
        "pt": "LTV médio ativos: ${active_ltv} vs churned: ${churned_ltv} — diferença de {ratio}x.",
        "en": "Avg LTV active: ${active_ltv} vs churned: ${churned_ltv} — {ratio}x difference.",
    },
    "ltv_insight_2": {
        "pt": "Churned = LTV igual ao deal (1x). Ativos alcançam 3-6x o contrato.",
        "en": "Churned = LTV equals the deal (1x). Active customers reach 3-6x the contract.",
    },
    "ltv_insight_3": {
        "pt": "Reter clientes bons gera muito mais valor que adquirir perfis errados.",
        "en": "Retaining good customers generates much more value than acquiring wrong profiles.",
    },
    "deal_vs_ltv": {"pt": "Deal Size vs LTV (Retorno do Cliente)", "en": "Deal Size vs LTV (Customer Return)"},
    "deal_size_usd": {"pt": "Deal Size (USD)", "en": "Deal Size (USD)"},
    "roi_explain": {
        "pt": "<strong>O que estou vendo?</strong> Deal inicial vs LTV total. Linhas tracejadas = múltiplos de ROI.",
        "en": "<strong>What am I seeing?</strong> Initial deal vs total LTV. Dashed lines = ROI multiples.",
    },
    "roi_insight_1": {
        "pt": "Ativos geram {active_roi}x o contrato. Churned ficam em {churned_roi}x.",
        "en": "Active customers generate {active_roi}x the contract. Churned stay at {churned_roi}x.",
    },
    "roi_insight_2": {
        "pt": "Acima da linha 1x = lucro. Clientes bons ficam entre 3x e 6x.",
        "en": "Above the 1x line = profit. Good customers land between 3x and 6x.",
    },
    "roi_insight_3": {
        "pt": "Tamanho das bolhas = porte (funcionários).",
        "en": "Bubble size = company size (employees).",
    },
    "roi_label": {"pt": "ROI", "en": "ROI"},

    # ── Segment Tab ──
    "status_industry_dist": {"pt": "Distribuição por Status e Indústria", "en": "Distribution by Status and Industry"},
    "active_status": {"pt": "Ativo", "en": "Active"},
    "sunburst_explain": {
        "pt": "<strong>O que estou vendo?</strong> Anel interno: Ativo/Churned. Anel externo: indústrias. Clique para expandir.",
        "en": "<strong>What am I seeing?</strong> Inner ring: Active/Churned. Outer ring: industries. Click to expand.",
    },
    "top3_industries": {
        "pt": "Top 3 indústrias por LTV (ativos):",
        "en": "Top 3 industries by LTV (active):",
    },
    "problematic_segments": {
        "pt": "Indústrias concentradas no vermelho são segmentos problemáticos.",
        "en": "Industries concentrated in red are problematic segments.",
    },
    "tech_maturity_title": {"pt": "Maturidade Tecnológica vs Retenção", "en": "Tech Maturity vs Retention"},
    "tech_stack": {"pt": "Tech Stack", "en": "Tech Stack"},
    "status_label": {"pt": "Status", "en": "Status"},
    "tech_explain": {
        "pt": "<strong>O que estou vendo?</strong> Clientes Cloud vs Legacy e impacto na retenção.",
        "en": "<strong>What am I seeing?</strong> Cloud vs Legacy customers and retention impact.",
    },
    "tech_insight_1": {
        "pt": "Churn: Cloud {cloud}% vs Legacy {legacy}%.",
        "en": "Churn: Cloud {cloud}% vs Legacy {legacy}%.",
    },
    "tech_insight_2": {
        "pt": "NPS: Cloud {cloud_nps} vs Legacy {legacy_nps}.",
        "en": "NPS: Cloud {cloud_nps} vs Legacy {legacy_nps}.",
    },
    "tech_insight_3": {
        "pt": "Empresas com stack moderno são muito melhores clientes — sinal forte de ICP.",
        "en": "Companies with modern tech stack are much better customers — strong ICP signal.",
    },

    # ── Risk Tab ──
    "cohort_revenue": {"pt": "Cohort por Faixa de Receita", "en": "Cohort by Revenue Band"},
    "avg_ltv_chart": {"pt": "LTV Médio (USD)", "en": "Avg LTV (USD)"},
    "retention_chart": {"pt": "Retenção %", "en": "Retention %"},
    "annual_revenue_band": {"pt": "Faixa de Receita Anual", "en": "Annual Revenue Band"},
    "cohort_explain": {
        "pt": "<strong>O que estou vendo?</strong> LTV médio (barras) e retenção (linha verde) por faixa de receita.",
        "en": "<strong>What am I seeing?</strong> Avg LTV (bars) and retention (green line) by revenue band.",
    },
    "cohort_insight_1": {
        "pt": "Melhor faixa: {band} — LTV ${ltv}, retenção {retention}%.",
        "en": "Best band: {band} — LTV ${ltv}, retention {retention}%.",
    },
    "cohort_insight_2": {
        "pt": "Revela o \"sweet spot\" de porte do cliente ideal.",
        "en": "Reveals the ideal customer size \"sweet spot\".",
    },
    "cohort_insight_3": {
        "pt": "Retenção abaixo de 70% = sinal de anti-ICP naquela faixa.",
        "en": "Retention below 70% = anti-ICP signal in that band.",
    },
    "age_vs_size": {"pt": "Idade vs Porte da Empresa", "en": "Age vs Company Size"},
    "age_years": {"pt": "Idade (anos)", "en": "Age (years)"},
    "employees": {"pt": "Funcionários", "en": "Employees"},
    "age_explain": {
        "pt": "<strong>O que estou vendo?</strong> Idade e porte dos clientes. Tamanho = deal size.",
        "en": "<strong>What am I seeing?</strong> Customer age and size. Bubble size = deal size.",
    },
    "age_insight_1": {
        "pt": "Ativos: média {age} anos, {size} funcionários.",
        "en": "Active: avg {age} years, {size} employees.",
    },
    "age_insight_2": {
        "pt": "Churned: média {age} anos, {size} funcionários.",
        "en": "Churned: avg {age} years, {size} employees.",
    },
    "age_insight_3": {
        "pt": "Empresas muito jovens ou pequenas tendem a dar mais churn.",
        "en": "Very young or small companies tend to churn more.",
    },

    # ── Executive Summary ──
    "key_findings": {"pt": "Descobertas Principais", "en": "Key Findings"},
    "best_industry": {
        "pt": "Melhor indústria: {industry} — maior LTV médio entre ativos",
        "en": "Best industry: {industry} — highest avg LTV among active",
    },
    "worst_industry": {
        "pt": "Indústria de maior risco: {industry} — maior taxa de churn",
        "en": "Highest risk industry: {industry} — highest churn rate",
    },
    "best_nps_customer": {
        "pt": "Cliente mais satisfeito: {name} (NPS {nps})",
        "en": "Most satisfied customer: {name} (NPS {nps})",
    },
    "top_ltv_customer": {
        "pt": "Maior LTV: {name} (${ltv})",
        "en": "Highest LTV: {name} (${ltv})",
    },
    "tech_predictor": {
        "pt": "Tech stack é preditor: Cloud tem {diff}pp menos churn que Legacy",
        "en": "Tech stack is a predictor: Cloud has {diff}pp less churn than Legacy",
    },
    "roi_comparison": {
        "pt": "ROI médio: Ativos geram {active}x o contrato vs {churned}x dos churned",
        "en": "Avg ROI: Active generate {active}x the contract vs {churned}x from churned",
    },
    "recommendations": {"pt": "Recomendações", "en": "Recommendations"},
    "rec_1": {
        "pt": "Priorize prospects da indústria {industry} com stack Cloud/Moderno",
        "en": "Prioritize prospects from {industry} industry with Cloud/Modern stack",
    },
    "rec_2": {
        "pt": "Evite empresas com menos de {size} funcionários e stack legado",
        "en": "Avoid companies with fewer than {size} employees and legacy stack",
    },
    "rec_3": {
        "pt": "Foco na faixa de receita {band} — melhor retenção e LTV",
        "en": "Focus on {band} revenue band — best retention and LTV",
    },
    "rec_4": {
        "pt": "Investir em onboarding rápido — ciclos acima de 50 dias correlacionam com churn",
        "en": "Invest in fast onboarding — cycles above 50 days correlate with churn",
    },

    # ── ICP Generation ──
    "generate_icp": {"pt": "Gerar Perfil de Cliente Ideal", "en": "Generate Ideal Customer Profile"},
    "generate_icp_btn": {"pt": "Gerar ICP com IA", "en": "Generate ICP with AI"},
    "analyzing_patterns": {"pt": "Analisando padrões...", "en": "Analyzing patterns..."},
    "ideal_customer": {"pt": "Cliente Ideal", "en": "Ideal Customer"},
    "profile_to_avoid": {"pt": "Perfil a Evitar", "en": "Profile to Avoid"},
    "ideal_industries": {"pt": "Indústrias Ideais", "en": "Ideal Industries"},
    "profile": {"pt": "Perfil", "en": "Profile"},
    "tech_signals": {"pt": "Sinais Tecnológicos", "en": "Tech Signals"},
    "key_patterns": {"pt": "Padrões-chave", "en": "Key Patterns"},
    "warning_signals": {"pt": "Sinais de Alerta", "en": "Warning Signals"},

    # ── Scoring ──
    "prospect_scoring": {"pt": "Scoring de Prospects", "en": "Prospect Scoring"},
    "no_prospects": {
        "pt": "Nenhum CSV de prospects enviado. Usando clientes atuais para demonstração.",
        "en": "No prospect CSV uploaded. Using current customers for demo.",
    },
    "score_prospects_btn": {"pt": "Pontuar Prospects", "en": "Score Prospects"},
    "scoring_prospects": {"pt": "Pontuando prospects...", "en": "Scoring prospects..."},
    "prospect_ranking": {"pt": "Ranking de Prospects", "en": "Prospect Ranking"},
    "details": {"pt": "Detalhes", "en": "Details"},
    "fit": {"pt": "Fit", "en": "Fit"},
    "risks": {"pt": "Riscos", "en": "Risks"},

    # ── Security ──
    "security_title": {"pt": "Seus dados estão seguros", "en": "Your data is safe"},
    "security_badge": {"pt": "Segurança", "en": "Security"},
    "security_no_storage": {
        "pt": "Nenhum dado é armazenado no servidor. Uploads de CSV são processados em memória e descartados ao fechar a sessão.",
        "en": "No data is stored on the server. CSV uploads are processed in memory and discarded when the session ends.",
    },
    "security_no_logs": {
        "pt": "Sem logs ou rastreamento. Não registramos consultas, resultados ou dados de empresas analisadas.",
        "en": "No logs or tracking. We don't record queries, results, or analyzed company data.",
    },
    "security_ssrf": {
        "pt": "Proteção contra SSRF. URLs são validadas — IPs privados, localhost e esquemas não-HTTP são bloqueados.",
        "en": "SSRF protection. URLs are validated — private IPs, localhost, and non-HTTP schemes are blocked.",
    },
    "security_xss": {
        "pt": "Proteção contra XSS. Todos os dados de entrada são sanitizados antes de renderização.",
        "en": "XSS protection. All input data is sanitized before rendering.",
    },
    "security_csv_limit": {
        "pt": "Limite de upload: 5 MB. Arquivos maiores são rejeitados para prevenir abuso.",
        "en": "Upload limit: 5 MB. Larger files are rejected to prevent abuse.",
    },
    "security_session": {
        "pt": "Sessões isoladas. Cada usuário tem sessão independente — sem vazamento entre usuários.",
        "en": "Isolated sessions. Each user has an independent session — no cross-user leakage.",
    },

    # ── Company Card Meta ──
    "founded": {"pt": "Fundada em", "en": "Founded"},
    "company_size": {"pt": "Porte da Empresa", "en": "Company Size"},

    # ── CSV Templates ──
    "download_template_customers": {"pt": "⬇ Baixar template de clientes (CSV)", "en": "⬇ Download customer template (CSV)"},
    "download_template_prospects": {"pt": "⬇ Template Prospects CSV", "en": "⬇ Prospect Template CSV"},

    # ── Beta / Suggestions ──
    "beta_badge": {"pt": "Versão Beta — Protótipo", "en": "Beta Version — Prototype"},
    "beta_disclaimer": {
        "pt": "Esta ferramenta está em fase beta. Os resultados gerados por IA são indicativos e servem como ponto de partida para análise — não devem embasar decisões críticas sem validação adicional. O ICP Identifier está em evolução contínua.",
        "en": "This tool is in beta. AI-generated results are directional and meant as a starting point for analysis — do not base critical decisions solely on this output without further validation. ICP Identifier is continuously improving.",
    },
    "suggestions_title": {"pt": "Sugestões & Feedback", "en": "Suggestions & Feedback"},
    "suggestions_placeholder": {"pt": "O que você mudaria ou gostaria de ver nessa ferramenta?", "en": "What would you change or like to see in this tool?"},
    "suggestions_send": {"pt": "Enviar sugestão", "en": "Send suggestion"},
    "suggestions_hint": {"pt": "Escreva sua sugestão acima para habilitar o envio.", "en": "Write your suggestion above to enable sending."},

    # ── Empty State ──
    "empty_title": {
        "pt": "Selecione uma empresa pré-carregada ou faça upload de um CSV",
        "en": "Select a pre-loaded company or upload a CSV",
    },
    "empty_subtitle": {
        "pt": "Selecione uma empresa pré-carregada para explorar o potencial da ferramenta, pesquise uma nova empresa a partir do seu site ou faça upload de um CSV para analisar seus próprios dados.",
        "en": "Select a pre-loaded company to understand the potential of the tool, research a new one from their website, or upload a CSV to analyze your own data.",
    },

    # ── Status ──
    "ATIVO": {"pt": "ATIVO", "en": "ACTIVE"},
    "CHURNED": {"pt": "CHURNED", "en": "CHURNED"},
}


def get_lang(session_state) -> str:
    """Get current language from session state."""
    return session_state.get("_lang", "pt")


def t(key: str, lang: str = "pt", **kwargs) -> str:
    """Translate a key. Supports {placeholder} formatting."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("pt", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
