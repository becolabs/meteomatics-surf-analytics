# 🏄‍♂️ Projeto de Análise de Dados de Surf - Pipeline dbt

## 🎯 Sumário Executivo

Este projeto implementa um pipeline de dados completo para análise de condições de surf, integrando dados meteorológicos da **Meteomatics** com ratings de surf do **Surfline**. A solução utiliza dbt para criar camadas bronze, silver e gold, transformando dados brutos em insights acionáveis para surfistas e profissionais do setor.

## 📈 O Desafio de Negócio

Surfistas e escolas de surf precisam de informações precisas e em tempo real sobre:
- **Condições das ondas** (altura, período, direção)
- **Condições meteorológicas** (vento, temperatura, luz solar)
- **Classificação das condições de surf** (poor, fair, good, excellent)
- **Dados de maré** para planejamento de sessões

O desafio é **integrar múltiplas fontes de dados** com diferentes escalas e métricas, criando uma visão unificada e confiável das condições de surf.

## 🏗️ Arquitetura da Solução

### 📊 Camadas de Dados

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BRONZE LAYER  │    │  SILVER LAYER   │    │   GOLD LAYER    │    │   DATA MARTS    │
│   (Raw Data)    │    │ (Cleaned Data)  │    │ (Business Ready)│    │ (Analytics)     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Meteomatics   │───▶│ • stg_wind      │───▶│ • dim_date      │───▶│ • Rain Analysis │
│ • Surfline      │    │ • stg_meteomatics│   │ • dim_weather   │    │ • Quality Trends│
│ • APIs Externas │    │ • stg_rating    │    │ • dim_swell     │    │ • Ideal Conditions│
│                 │    │ • stg_surf      │    │ • fact_surf_    │    │ • Wind Analysis │
│                 │    │ • stg_swells    │    │   conditions    │    │ • Season Patterns│
│                 │    │ • stg_tides     │    │                 │    │ • Surf Alerts   │
│                 │    │ • stg_sunlight  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🌊 Fluxo de Dados

1. **Extração**: Scripts Python coletam dados das APIs (Meteomatics, Surfline)
2. **Bronze**: Dados brutos armazenados em DuckDB sem transformações
3. **Silver**: Limpeza, padronização e enriquecimento dos dados
4. **Gold**: Dimensões e fatos prontos para análise (Star Schema)
5. **Data Marts**: Análises especializadas para diferentes casos de uso

## 🛠️ Tech Stack

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Transformação** | dbt Core | Padronização, versionamento e documentação de transformações |
| **Banco de Dados** | DuckDB | OLAP embarcado, ideal para desenvolvimento e prototipagem |
| **Extração** | Python | Flexibilidade para integrar APIs diversas |
| **Orquestração** | Python Scripts | Controle de execução do pipeline ETL |
| **Configuração** | YAML | Regras de negócio parametrizáveis |

## 📁 Estrutura do Projeto

```
📦 meteomatics/
├── 📁 dbt_meteomatics/           # Projeto dbt principal
│   ├── models/
│   │   ├── bronze/
│   │   │   └── sources.yml       # Definição das fontes de dados
│   │   ├── silver/               # Modelos de limpeza e padronização
│   │   │   ├── stg_wind.sql
│   │   │   ├── stg_meteomatics.sql
│   │   │   ├── stg_rating.sql
│   │   │   ├── stg_surf.sql
│   │   │   ├── stg_swells.sql
│   │   │   ├── stg_tides.sql
│   │   │   └── stg_sunlight.sql
│   │   ├── gold/                 # Modelos analíticos (Star Schema)
│   │   │   ├── dim_date.sql
│   │   │   ├── dim_weather.sql
│   │   │   ├── dim_swell.sql
│   │   │   └── fact_surf_conditions.sql
│   │   └── marts/                # Data Marts especializados
│   │       ├── mart_rain_surf_analysis.sql
│   │       ├── mart_surf_quality_trends.sql
│   │       ├── mart_ideal_conditions.sql
│   │       ├── mart_wind_analysis.sql
│   │       ├── mart_seasonal_patterns.sql
│   │       └── mart_surf_alerts.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── 📁 src/                       # Scripts de extração
│   └── surfline_extractor.py
├── 📁 pipelines/                 # Orquestração
│   ├── run_bronze_pipeline.py
│   └── run_full_etl.py
├── 📁 config/                    # Configurações parametrizáveis
│   └── config.yaml
├── 📁 data/                      # Dados processados
│   ├── bronze/
│   ├── landing/
│   └── dbt_meteomatics.duckdb
├── 📁 notebooks/                 # Análises exploratórias
│   ├── EDA.ipynb
│   ├── silver.ipynb
│   └── gold.ipynb
└── README.md
```

## 🚀 Guia de Execução

### ✅ Pré-requisitos

- Python 3.8+
- dbt Core instalado
- DuckDB
- Dependências do projeto

### ⚙️ Configuração Inicial

1. **Clone o repositório e configure o ambiente:**
   ```bash
   git clone <repository-url>
   cd meteomatics
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure o ambiente dbt:**
   ```bash
   cd dbt_meteomatics
   dbt deps  # Instala dependências do dbt
   ```

### 🔄 Execução do Pipeline

#### **Opção 1: Pipeline Automatizado Completo**
```bash
python run_full_etl.py
```

#### **Opção 2: Execução Manual por Etapas**
```bash
# 1. Extração de dados (Bronze)
python pipelines/run_bronze_pipeline.py

# 2. Transformações dbt (Silver + Gold + Marts)
cd dbt_meteomatics
dbt run

# 3. Execução de testes de qualidade
dbt test

# 4. Geração de documentação
dbt docs generate
dbt docs serve
```

## 📊 Regras de Negócio Parametrizáveis

O projeto utiliza o arquivo [`config/config.yaml`](config/config.yaml) para definir todas as regras de negócio, permitindo ajustes sem modificar código:

### 🌡️ **Classificações de Temperatura**
- **Frio**: < 18°C
- **Ameno**: 18°C - 24°C  
- **Quente**: 24°C - 30°C
- **Muito Quente**: > 30°C

### 💨 **Classificações de Vento**
- **Calmo**: ≤ 3 m/s
- **Moderado**: 3-7 m/s
- **Forte**: 7-12 m/s
- **Muito Forte**: > 12 m/s

### 🌊 **Qualidade do Surf**
- **Excelente**: Ondas ≥ 0.9m, Vento ≤ 6 m/s, Chuva ≤ 2 mm/h
- **Bom**: Ondas ≥ 0.6m, Vento ≤ 8 m/s
- **Regular**: Ondas ≥ 0.3m

### 🎯 **Condições Ideais**
- **Ideais**: Sem chuva, Vento ≤ 5 m/s, Ondas ≥ 0.6m
- **Boas**: Sem chuva, Vento ≤ 8 m/s

## 🔍 Dados e Fontes

### 📊 **Bronze Layer - Fontes Principais**

1. **Meteomatics** (Dados meteorológicos precisos)
   - Velocidade/direção do vento
   - Altura/período/direção das ondas
   - Temperatura, umidade, pressão
   - Radiação solar, precipitação

2. **Surfline** (Ratings e condições de surf)
   - Rating de surf (poor, fair, good, excellent)
   - Medições de altura de ondas
   - Informações de maré
   - Dados de vento local

### 🥈 **Silver Layer - Modelos Padronizados**

- [`stg_meteomatics`](dbt_meteomatics/models/silver/stg_meteomatics.sql): Dados meteorológicos consolidados
- [`stg_wind`](dbt_meteomatics/models/silver/stg_wind.sql): Dados de vento limpos e padronizados
- [`stg_rating`](dbt_meteomatics/models/silver/stg_rating.sql): Ratings de surf normalizados
- [`stg_surf`](dbt_meteomatics/models/silver/stg_surf.sql): Condições de ondas unificadas
- [`stg_swells`](dbt_meteomatics/models/silver/stg_swells.sql): Dados detalhados de ondulações
- [`stg_tides`](dbt_meteomatics/models/silver/stg_tides.sql): Informações de maré
- [`stg_sunlight`](dbt_meteomatics/models/silver/stg_sunlight.sql): Dados de luminosidade

### 🥇 **Gold Layer - Star Schema**

- [`dim_date`](dbt_meteomatics/models/gold/dim_date.sql): Dimensão temporal completa
- [`dim_weather`](dbt_meteomatics/models/gold/dim_weather.sql): Dimensão meteorológica
- [`dim_swell`](dbt_meteomatics/models/gold/dim_swell.sql): Dimensão de ondulações
- [`fact_surf_conditions`](dbt_meteomatics/models/gold/fact_surf_conditions.sql): Tabela fato principal (26,305 registros)

### 🎯 **Data Marts - Análises Especializadas**

#### **1. Análise de Chuva vs Surf** [`mart_rain_surf_analysis`]
- **Objetivo**: Correlação entre precipitação e qualidade do surf
- **Insights**: Sem chuva = 75% surf excelente, Chuva moderada/forte = 0% excelente

#### **2. Tendências de Qualidade** [`mart_surf_quality_trends`]
- **Objetivo**: Padrões temporais de qualidade de surf
- **Insights**: Abril (84.2%) e Fevereiro (82.6%) são os melhores meses

#### **3. Condições Ideais** [`mart_ideal_conditions`]
- **Objetivo**: Identificação de condições perfeitas para surf
- **Insights**: Madrugada (63.9%) e Manhã (62.5%) têm melhores condições

#### **4. Análise de Vento** [`mart_wind_analysis`]
- **Objetivo**: Impacto do vento na qualidade do surf
- **Insights**: Vento calmo (≤3m/s) = Rating 2.2, Vento forte = Rating 0.5

#### **5. Padrões Sazonais** [`mart_seasonal_patterns`]
- **Objetivo**: Variações sazonais das condições
- **Insights**: Outono (74.2%) > Verão (73.4%) > Inverno (71.9%) > Primavera (69.5%)

#### **6. Sistema de Alertas** [`mart_surf_alerts`]
- **Objetivo**: Alertas automáticos para melhores condições
- **Insights**: 13,624 alertas de "Condições Perfeitas" identificados

## ⚖️ Resolução de Conflitos: Surfline vs Meteomatics

### 🎯 **Estratégia de Harmonização de Ratings**

Um dos principais desafios é reconciliar as diferentes escalas de rating entre as fontes:

#### **Surfline Rating Scale:**
- `poor` / `very poor` / `poor to fair`
- `fair` / `fair to good` 
- `good` / `good to excellent`
- `excellent`

#### **Meteomatics Wave Height:**
- Dados numéricos precisos em metros
- Múltiplas métricas: significant wave height, maximum wave height

#### **Nossa Solução - Regras de Negócio Unificadas:**

```sql
-- Exemplo de lógica de harmonização
CASE 
    -- Conversão Surfline para numérico
    WHEN surfline_rating IN ('poor', 'very poor') THEN 1
    WHEN surfline_rating IN ('poor to fair', 'fair') THEN 2  
    WHEN surfline_rating IN ('fair to good', 'good') THEN 3
    WHEN surfline_rating IN ('good to excellent', 'excellent') THEN 4
    ELSE NULL
END AS rating_numeric,

-- Derivação de rating a partir de altura Meteomatics
CASE 
    WHEN meteomatics_wave_height < 0.5 THEN 1  -- Poor
    WHEN meteomatics_wave_height < 1.0 THEN 2  -- Fair
    WHEN meteomatics_wave_height < 1.8 THEN 3  -- Good  
    WHEN meteomatics_wave_height >= 1.8 THEN 4 -- Excellent
    ELSE NULL
END AS height_derived_rating,

-- Cálculo de desvio para validação
ABS(rating_numeric - height_derived_rating) AS rating_deviation
```

### 🔍 **Validação Cruzada**

```sql
-- Identificar discrepâncias entre fontes
SELECT 
    date_hour,
    surfline_rating,
    meteomatics_wave_height,
    rating_deviation,
    CASE 
        WHEN rating_deviation <= 1 THEN 'Consistente'
        WHEN rating_deviation = 2 THEN 'Moderada Discrepância'
        ELSE 'Alta Discrepância'
    END AS consistency_level
FROM fact_surf_conditions
WHERE rating_deviation IS NOT NULL
ORDER BY rating_deviation DESC;
```

## 📈 Resultados e Insights Principais

### 🎯 **Análises Realizadas (26,305 registros - 2020-2022)**

#### **☔ Impacto da Chuva no Surf:**
- **Sem Chuva**: 1,094 dias | 75.0% surf excelente | Ondas 1.51m
- **Chuva Fraca**: 498 dias | 70.3% surf excelente | Ondas 1.53m  
- **Chuva Moderada**: 256 dias | 0.0% surf excelente | Ondas 1.56m
- **Chuva Forte**: 30 dias | 0.0% surf excelente | Ondas 1.37m

#### **📅 Melhores Meses para Surf:**
1. **Abril (Outono)**: 84.2% excelente | Ondas 1.72m | Vento 4.2m/s
2. **Fevereiro (Verão)**: 82.6% excelente | Ondas 1.38m | Vento 3.3m/s
3. **Julho (Inverno)**: 81.2% excelente | Ondas 1.52m | Vento 4.4m/s
4. **Março (Outono)**: 80.6% excelente | Ondas 1.23m | Vento 3.9m/s

#### **🌅 Melhores Períodos do Dia:**
- **Madrugada**: 63.9% condições ideais | Score 86.2/100
- **Manhã**: 62.5% condições ideais | Score 86.2/100
- **Noite**: 51.3% condições ideais | Score 84.1/100
- **Tarde**: 43.8% condições ideais | Score 83.2/100

#### **🍂 Padrões Sazonais:**
1. **Outono**: 74.2% excelente | 21.9°C | 1.54m | "Ondas Grandes e Vento Calmo"
2. **Verão**: 73.4% excelente | 24.4°C | 1.4m | "Ondas Grandes e Vento Calmo"  
3. **Inverno**: 71.9% excelente | 17.4°C | 1.51m | "Ondas Grandes e Vento Calmo"
4. **Primavera**: 69.5% excelente | 20.0°C | 1.58m | "Ondas Grandes e Vento Calmo"

#### **🚨 Sistema de Alertas:**
- **Condições Perfeitas**: 13,624 ocorrências | Score médio 92.0
- **Condições Excelentes**: 4,290 ocorrências | Score médio 86.2
- **Boas Condições**: 4,151 ocorrências | Score médio 79.2
- **Ondas Grandes**: 2,674 ocorrências | Score médio 81.6

#### **💨 Análise de Vento:**
- **Vento Calmo** (≤3m/s): 7,393 horas | Rating 2.2
- **Vento Moderado** (3-7m/s): 16,044 horas | Rating 1.5
- **Vento Forte** (7-12m/s): 2,824 horas | Rating 0.5
- **Vento Muito Forte** (>12m/s): 44 horas | Rating 0.0

## 📈 Próximos Passos e Roadmap

### 🎯 **Análises Prioritárias**

#### **1. Correlação Avançada de Fontes**
```sql
-- Validar consistência temporal entre Surfline e Meteomatics
SELECT 
    d.month_name,
    d.hour_of_day,
    AVG(rating_numeric) as avg_surfline_rating,
    AVG(height_derived_rating) as avg_meteomatics_rating,
    CORR(rating_numeric, height_derived_rating) as correlation
FROM fact_surf_conditions f
JOIN dim_date d ON f.date_key = d.date_key
WHERE rating_numeric IS NOT NULL AND height_derived_rating IS NOT NULL
GROUP BY d.month_name, d.hour_of_day
ORDER BY correlation DESC;
```

#### **2. Previsão de Condições Ideais**
```sql
-- Padrões para modelo de Machine Learning
SELECT 
    w.wind_speed_10m_ms,
    w.wind_direction_10m_deg,
    w.pressure_msl_hpa,
    s.significant_wave_height_m,
    s.mean_wave_period_s,
    d.hour_of_day,
    d.day_of_week,
    d.month_of_year,
    f.surf_rating,
    CASE WHEN f.surf_rating >= 3 THEN 1 ELSE 0 END as good_surf_flag
FROM fact_surf_conditions f
JOIN dim_weather w ON f.weather_key = w.weather_key
JOIN dim_swell s ON f.swell_key = s.swell_key
JOIN dim_date d ON f.date_key = d.date_key;
```

#### **3. Análise de Tendências Temporais**
```sql
-- Identificar padrões de melhoria/degradação
SELECT 
    d.year,
    d.month_name,
    AVG(condition_score) as avg_score,
    LAG(AVG(condition_score), 12) OVER (ORDER BY d.year, d.month_of_year) as prev_year_score,
    AVG(condition_score) - LAG(AVG(condition_score), 12) OVER (ORDER BY d.year, d.month_of_year) as year_over_year_change
FROM mart_ideal_conditions m
JOIN dim_date d ON DATE(m.datetime_utc) = d.date_key
GROUP BY d.year, d.month_of_year, d.month_name
ORDER BY d.year, d.month_of_year;
```

### 🚀 **Roadmap de Desenvolvimento**

#### **Fase 1: Validação e Qualidade** ✅
- [x] Estrutura dbt implementada (17 modelos)
- [x] Modelos Silver criados (7 modelos)
- [x] Modelos Gold implementados (4 modelos - Star Schema)
- [x] Data Marts criados (6 marts especializados)
- [x] Regras de negócio parametrizáveis (config.yaml)
- [x] Pipeline ETL automatizado
- [ ] Testes de qualidade robustos
- [ ] Validação cruzada de fontes

#### **Fase 2: Análises Avançadas** 🔄
- [ ] Dashboard interativo (Metabase/Streamlit)
- [ ] Alertas em tempo real para condições ideais
- [ ] API REST para consulta de condições
- [ ] Modelo de ML para previsão de rating
- [ ] Análise de correlação entre fontes
- [ ] Sistema de recomendações personalizadas

#### **Fase 3: Escalabilidade e Produção** 📋
- [ ] Migração para cloud (BigQuery/Snowflake)
- [ ] Automação com Airflow/Dagster
- [ ] Integração com mais fontes de dados
- [ ] Sistema de monitoramento e alertas
- [ ] CI/CD para pipeline de dados
- [ ] Documentação automática de lineage

#### **Fase 4: Produto e Negócio** 🎯
- [ ] Aplicativo mobile para surfistas
- [ ] API comercial para parceiros
- [ ] Sistema de assinatura premium
- [ ] Integração com escolas de surf
- [ ] Marketplace de dados

### 📊 **Casos de Uso e Insights Esperados**

#### **1. Para Surfistas Individuais:**
- **Quando surfar?** Identificar as próximas 48h com condições ideais
- **Onde surfar?** Comparação entre diferentes spots (futuro multi-spot)
- **Alertas personalizados** baseados em preferências individuais
- **Histórico de sessões** e correlação com performance

#### **2. Para Escolas de Surf:**
- **Planejamento de aulas** baseado em previsões de 7 dias
- **Otimização de recursos humanos** alocando instrutores por condição
- **Relatórios de segurança** com alertas de condições perigosas
- **Análise de receita** correlacionada com qualidade das condições

#### **3. Para Pesquisa e Meteorologia:**
- **Validação de modelos** de previsão oceanográfica
- **Padrões climáticos regionais** e mudanças de longo prazo
- **Correlação entre variáveis** meteorológicas e oceanográficas
- **Benchmarking** entre diferentes fontes de dados

#### **4. Para Desenvolvimento de Produto:**
- **Testes A/B** de diferentes algoritmos de rating
- **Feedback loop** com usuários para calibrar modelos
- **Análise de usage patterns** para otimizar features
- **Monetização** através de insights premium

### 🔧 **Comandos Úteis do Projeto**

```bash
# Pipeline completo automatizado
python run_full_etl.py

# Executar apenas extração Bronze
python pipelines/run_bronze_pipeline.py

# Executar apenas camada Silver
dbt run --select models.meteomatics.silver

# Executar apenas camada Gold
dbt run --select models.meteomatics.gold

# Executar apenas Data Marts
dbt run --select models.meteomatics.marts

# Executar modelo específico
dbt run --select mart_surf_alerts

# Executar testes de qualidade
dbt test

# Gerar documentação
dbt docs generate && dbt docs serve

# Executar com refresh completo
dbt run --full-refresh

# Validar configurações
dbt parse

# Executar apenas modelos alterados
dbt run --modified-state
```

### 📊 **Consultas Úteis para Análise**

```sql
-- Top 10 dias com melhores condições
SELECT 
    date,
    AVG(condition_score) as avg_score,
    COUNT(*) as hours_count,
    AVG(wave_height) as avg_waves,
    AVG(wind_speed) as avg_wind
FROM mart_ideal_conditions 
WHERE is_ideal = true
GROUP BY date
ORDER BY avg_score DESC
LIMIT 10;

-- Análise de fim de semana vs dias úteis
SELECT 
    is_weekend,
    AVG(condition_score) as avg_score,
    SUM(CASE WHEN is_ideal THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as ideal_percentage
FROM mart_ideal_conditions
GROUP BY is_weekend;

-- Condições por hora do dia
SELECT 
    period_of_day,
    COUNT(*) as total_hours,
    AVG(condition_score) as avg_score,
    MAX(condition_score) as max_score
FROM mart_ideal_conditions
GROUP BY period_of_day
ORDER BY avg_score DESC;
```

## 📚 Documentação e Recursos

### 📖 **Documentação Técnica**
- **Notebooks de Análise**: [`EDA.ipynb`](EDA.ipynb), [`silver.ipynb`](silver.ipynb), [`gold.ipynb`](gold.ipynb)
- **Configurações**: [`config/config.yaml`](config/config.yaml) - Regras de negócio parametrizáveis
- **Scripts de Extração**: [`src/surfline_extractor.py`](src/surfline_extractor.py)
- **Pipeline ETL**: [`run_full_etl.py`](run_full_etl.py) - Automação completa
- **dbt Documentation**: Execute `dbt docs serve` para documentação interativa

### 🎯 **Arquivos de Configuração Principais**
- [`dbt_project.yml`](dbt_meteomatics/dbt_project.yml): Configuração do projeto dbt
- [`profiles.yml`](dbt_meteomatics/profiles.yml): Configuração de conexão DuckDB
- [`config.yaml`](config/config.yaml): Regras de negócio e parâmetros

### 📊 **Dados de Exemplo**
- **Período**: Janeiro 2020 - Dezembro 2022 (3 anos completos)
- **Granularidade**: Dados horários (26,305 registros)
- **Localização**: Spot específico do Surfline (ID: 5842041f4e65fad6a7708cee)
- **Métricas**: >30 variáveis entre meteorológicas e oceanográficas

## 📊 **Documentação das Variáveis Meteomatics**

### 🌊 **Variáveis Oceanográficas**
- **`significant_wave_height:m`**: Altura significativa das ondas em metros
- **`mean_wave_period:s`**: Período médio espectral das ondas obtido usando o momento de frequência recíproca do espectro completo de ondas
- **`mean_wave_direction:d`**: Direção média espectral em graus sobre todas as frequências e direções do espectro bidimensional de ondas

### 🌡️ **Variáveis Meteorológicas**
- **`t_2m:C`**: Temperatura instantânea a 2m acima do solo em graus Celsius
- **`wind_speed_10m:ms`**: Velocidade instantânea do vento a 10m acima do solo em m/s
- **`wind_dir_10m:d`**: Direção instantânea do vento a 10m acima do solo em graus
- **`pressure_2m:hPa`**: Pressão ajustada ao nível do mar em hPa, considerando condições atmosféricas como temperatura
- **`precip_1h:mm`**: Precipitação acumulada na última hora em milímetros (equivalente a litros por metro quadrado)

### 📍 **Localização e Período**
- **Spot**: Praia de Moçambique, Florianópolis, SC
- **Período**: 2020-01-01 até 2022-12-31 (3 anos completos)
- **Granularidade**: Dados horários (26,305 registros)

## 🤝 Contribuição e Desenvolvimento

### 🔄 **Workflow de Desenvolvimento**
1. **Fork** do repositório
2. **Branch** para nova feature: `git checkout -b feature/nova-analise`
3. **Commit** das mudanças: `git commit -m 'Adiciona análise X'`
4. **Push** para branch: `git push origin feature/nova-analise`
5. **Pull Request** com descrição detalhada

### 🧪 **Testes e Qualidade**
```bash
# Executar todos os testes dbt
dbt test

# Testes específicos de qualidade de dados
dbt test --select test_type:data

# Validação de schema
dbt run-operation validate_schema

# Verificação de performance
dbt run --profile timer
```

### 📋 **Padrões de Código**
- **SQL**: Seguir padrões dbt (CTE, naming conventions)
- **Python**: PEP 8, docstrings, type hints
- **YAML**: Indentação consistente, documentação de modelos
- **Git**: Commits semânticos, branches descritivas

---

**Status do Projeto:** 🔄 Em Desenvolvimento Ativo  
**Última Atualização:** Janeiro 2025  
**Versão Atual:** 2.0.0  
**Contribuidores:** Marcos Reis
**Licença:** MIT


