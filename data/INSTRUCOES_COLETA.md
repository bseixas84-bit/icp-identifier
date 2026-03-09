# Instrucoes para Coleta de Dados de Clientes

## Objetivo

Para gerar seu Perfil de Cliente Ideal (ICP), precisamos de um arquivo CSV com os dados da sua base de clientes. Quanto mais completo, melhor sera a analise.

---

## Formato do Arquivo

- Tipo: **CSV** (separado por virgula)
- Codificacao: **UTF-8**
- Primeira linha: nomes das colunas (exatamente como listado abaixo)

---

## Colunas Obrigatorias

| Coluna | Tipo | Descricao | Exemplo |
|--------|------|-----------|---------|
| `company_name` | Texto | Nome da empresa cliente | Magazine Luiza |
| `industry` | Texto | Setor de atuacao | Varejo |
| `employee_count` | Numero | Quantidade de funcionarios | 40000 |
| `annual_revenue_usd` | Numero | Receita anual em USD | 5000000000 |
| `deal_size_usd` | Numero | Valor do contrato/deal em USD | 480000 |
| `sales_cycle_days` | Numero | Dias entre primeiro contato e fechamento | 25 |
| `churned` | true/false | O cliente cancelou o servico? | false |
| `ltv_usd` | Numero | Lifetime Value (receita total gerada pelo cliente) em USD | 2400000 |
| `nps_score` | Numero (0-10) | Nota de satisfacao do cliente | 9 |
| `tech_stack` | Texto | Tecnologias usadas, separadas por ponto e virgula | Cloud;AWS;Salesforce |
| `country` | Texto | Pais da empresa | Brazil |
| `founding_year` | Numero | Ano de fundacao da empresa | 1957 |

---

## Como preencher cada campo

### company_name
Nome oficial da empresa. Evite abreviacoes.

### industry
Use termos padronizados. Exemplos:
- SaaS, Fintech, HealthTech, EdTech, Varejo, Industria, Logistica, Agronegocio, Construcao Civil, Servicos Financeiros, Saude, Tecnologia, Alimentacao, Moda, Energia, Telecomunicacoes

### employee_count
Numero aproximado de funcionarios. Consulte LinkedIn ou sites como Glassdoor se nao souber o valor exato.

### annual_revenue_usd
Receita anual em dolares americanos. Se tiver o valor em BRL, divida por 5 (ou pela cotacao atual).

### deal_size_usd
Valor total do contrato fechado com o cliente. Se for recorrente (mensal), multiplique pelo periodo do contrato.

### sales_cycle_days
Dias corridos entre o primeiro contato comercial e a assinatura do contrato. Se nao tiver o dado exato, estime:
- Venda rapida (self-service): 7-15 dias
- Venda mid-market: 30-60 dias
- Venda enterprise: 60-120+ dias

### churned
- `true` — cliente cancelou ou nao renovou
- `false` — cliente ativo

### ltv_usd
Receita total que o cliente ja gerou desde o inicio do contrato. Se nao tiver, use: `deal_size_usd x numero de renovacoes`.

### nps_score
Nota de 0 a 10 de satisfacao. Se nao tiver NPS formal, use uma estimativa:
- 9-10: Cliente promotor, indica para outros
- 7-8: Cliente satisfeito
- 5-6: Cliente neutro
- 0-4: Cliente insatisfeito

### tech_stack
Tecnologias que o cliente usa, separadas por ponto e virgula. Foque em:
- **Infraestrutura:** Cloud, On-premise, Legacy
- **Cloud provider:** AWS, Azure, GCP
- **CRM/ERP:** Salesforce, HubSpot, SAP, Oracle, Proprio, Excel, Nenhum

Exemplo: `Cloud;AWS;Salesforce`

### country
Pais onde a empresa esta sediada.

### founding_year
Ano de fundacao da empresa.

---

## Exemplo de CSV

```csv
company_name,industry,employee_count,annual_revenue_usd,deal_size_usd,sales_cycle_days,churned,ltv_usd,nps_score,tech_stack,country,founding_year
Magazine Luiza,Varejo,40000,5000000000,480000,25,false,2400000,9,Cloud;AWS;Salesforce,Brazil,1957
Natura,Cosmeticos,35000,3800000000,420000,28,false,2100000,10,Cloud;AWS;Salesforce,Brazil,1969
MRV Engenharia,Construcao Civil,25000,1800000000,95000,80,true,95000,3,Legacy;On-premise;Excel,Brazil,1979
```

---

## Dicas importantes

1. **Minimo recomendado:** 15 clientes (ideal: 50+)
2. **Inclua clientes bons E ruins** — a IA precisa dos dois para identificar padroes
3. **Inclua clientes que cancelaram (churned)** — isso e essencial para o Anti-ICP
4. **Nao arredonde demais** — valores mais precisos geram analises melhores
5. **Mantenha consistencia** — use o mesmo padrao para todas as linhas (ex: sempre USD, sempre o mesmo formato de industria)

---

## Onde conseguir esses dados

| Dado | Fonte sugerida |
|------|---------------|
| Receita e deal size | CRM (HubSpot, Salesforce, Pipedrive) |
| Funcionarios e industria | LinkedIn da empresa |
| Tech stack | BuiltWith, Wappalyzer, ou pergunte ao cliente |
| NPS | Pesquisas de satisfacao, CS team |
| Churn | CRM ou financeiro |
| Ano de fundacao | LinkedIn, site da empresa, Wikipedia |

---

## Pronto?

Salve o arquivo como `.csv` e faca upload na ferramenta ICP Identifier.
