-- =============================================================================
-- ANÁLISE DE HORÁRIOS SURFÁVEIS - ABORDAGEM SIMPLES
-- Filtra apenas Dawn Patrol, Manhã e Tarde dos dados existentes
-- =============================================================================

-- Query principal: apenas horários surfáveis
WITH surfable_hours AS (
    SELECT 
        *,
        -- Classificação de períodos surfáveis
        CASE 
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 6 AND 9 THEN 'Dawn Patrol'
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 10 AND 12 THEN 'Manhã'
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 13 AND 18 THEN 'Tarde'
            ELSE 'Não Surfável'
        END AS periodo_surfavel,
        
        -- Score com boost por horário premium
        CASE 
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 6 AND 9 THEN surf_rating_br * 1.1   -- Dawn Patrol boost
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 10 AND 12 THEN surf_rating_br * 1.05 -- Manhã boost
            WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 13 AND 18 THEN surf_rating_br * 1.0  -- Tarde normal
            ELSE 0  -- Não surfável
        END AS surf_score_ajustado

    FROM fact_surf_conditions
    WHERE 
        -- FILTRO SIMPLES: apenas horários surfáveis
        EXTRACT(HOUR FROM datetime_utc) BETWEEN 6 AND 18
)

-- Análise por período surfável
SELECT 
    periodo_surfavel,
    
    -- Estatísticas básicas
    COUNT(*) as total_horas,
    ROUND(AVG(surf_rating_br), 2) as rating_br_medio,
    ROUND(AVG(surf_score_ajustado), 2) as score_ajustado_medio,
    
    -- Distribuição de qualidade
    SUM(CASE WHEN surf_rating_br >= 4 THEN 1 ELSE 0 END) as horas_excelente,
    SUM(CASE WHEN surf_rating_br >= 3 THEN 1 ELSE 0 END) as horas_bom_plus,
    ROUND(SUM(CASE WHEN surf_rating_br >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_excelente,
    ROUND(SUM(CASE WHEN surf_rating_br >= 3 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_bom_plus,
    
    -- Condições médias
    ROUND(AVG(surf_height_avg_m), 2) as altura_media_ondas,
    ROUND(AVG(wind_speed_10m_ms), 1) as vento_medio,
    ROUND(AVG(temperature_2m_celsius), 1) as temp_media,
    
    -- Ranking por qualidade
    RANK() OVER (ORDER BY AVG(surf_score_ajustado) DESC) as ranking_periodo

FROM surfable_hours
WHERE periodo_surfavel != 'Não Surfável'
GROUP BY periodo_surfavel
ORDER BY ranking_periodo;

-- =============================================================================
-- QUERY SIMPLES PARA PREVISÃO: PRÓXIMAS 48H SURFÁVEIS
-- =============================================================================

/*
SELECT 
    datetime_utc,
    CASE 
        WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 6 AND 9 THEN 'Dawn Patrol'
        WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 10 AND 12 THEN 'Manhã'
        WHEN EXTRACT(HOUR FROM datetime_utc) BETWEEN 13 AND 17 THEN 'Tarde'
    END AS periodo,
    surf_rating_br_label,
    ROUND(surf_height_avg_m, 1) as ondas_m,
    ROUND(wind_speed_10m_ms, 1) as vento_ms,
    surf_quality_score_br as recomendacao

FROM fact_surf_conditions
WHERE 
    -- Apenas horários surfáveis
    EXTRACT(HOUR FROM datetime_utc) BETWEEN 6 AND 17
    -- Para previsão real, adicionar: AND datetime_utc >= NOW()
    -- AND datetime_utc <= NOW() + INTERVAL '48 hours'
    
ORDER BY datetime_utc
LIMIT 20;
*/
