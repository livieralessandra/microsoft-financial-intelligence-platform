-- =====================================================
-- Microsoft Financial Intelligence Platform
-- Analytics Views
-- =====================================================

DROP VIEW IF EXISTS vw_quarterly_financials;

CREATE VIEW vw_quarterly_financials AS
SELECT
    fiscal_year,
    fiscal_period,

    MAX(CASE WHEN metric = 'revenue' THEN value END) AS revenue,

    MAX(CASE WHEN metric = 'gross_profit' THEN value END) AS gross_profit,

    MAX(CASE WHEN metric = 'operating_income' THEN value END) AS operating_income,

    MAX(CASE WHEN metric = 'net_income' THEN value END) AS net_income

FROM quarterly_financials

GROUP BY
    fiscal_year,
    fiscal_period

ORDER BY
    fiscal_year,
    CASE fiscal_period
        WHEN 'Q1' THEN 1
        WHEN 'Q2' THEN 2
        WHEN 'Q3' THEN 3
        WHEN 'Q4' THEN 4
    END;

-- =====================================================
-- Quarterly analytics: growth and margins
-- =====================================================

DROP VIEW IF EXISTS vw_quarterly_analytics;

CREATE VIEW vw_quarterly_analytics AS
WITH ordered_financials AS (
    SELECT
        fiscal_year,
        fiscal_period,
        revenue,
        gross_profit,
        operating_income,
        net_income,

        CASE fiscal_period
            WHEN 'Q1' THEN 1
            WHEN 'Q2' THEN 2
            WHEN 'Q3' THEN 3
            WHEN 'Q4' THEN 4
        END AS quarter_number,

        revenue - LAG(revenue, 1) OVER (
            ORDER BY
                fiscal_year,
                CASE fiscal_period
                    WHEN 'Q1' THEN 1
                    WHEN 'Q2' THEN 2
                    WHEN 'Q3' THEN 3
                    WHEN 'Q4' THEN 4
                END
        ) AS revenue_qoq_change,

        revenue - LAG(revenue, 4) OVER (
            ORDER BY
                fiscal_year,
                CASE fiscal_period
                    WHEN 'Q1' THEN 1
                    WHEN 'Q2' THEN 2
                    WHEN 'Q3' THEN 3
                    WHEN 'Q4' THEN 4
                END
        ) AS revenue_yoy_change,

        LAG(revenue, 1) OVER (
            ORDER BY
                fiscal_year,
                CASE fiscal_period
                    WHEN 'Q1' THEN 1
                    WHEN 'Q2' THEN 2
                    WHEN 'Q3' THEN 3
                    WHEN 'Q4' THEN 4
                END
        ) AS previous_quarter_revenue,

        LAG(revenue, 4) OVER (
            ORDER BY
                fiscal_year,
                CASE fiscal_period
                    WHEN 'Q1' THEN 1
                    WHEN 'Q2' THEN 2
                    WHEN 'Q3' THEN 3
                    WHEN 'Q4' THEN 4
                END
        ) AS prior_year_quarter_revenue

    FROM vw_quarterly_financials
)

SELECT
    fiscal_year,
    fiscal_period,
    quarter_number,

    revenue,
    gross_profit,
    operating_income,
    net_income,

    previous_quarter_revenue,
    prior_year_quarter_revenue,

    revenue_qoq_change,
    ROUND(
        100.0 * revenue_qoq_change
        / NULLIF(previous_quarter_revenue, 0),
        2
    ) AS revenue_qoq_growth_pct,

    revenue_yoy_change,
    ROUND(
        100.0 * revenue_yoy_change
        / NULLIF(prior_year_quarter_revenue, 0),
        2
    ) AS revenue_yoy_growth_pct,

    ROUND(
        100.0 * gross_profit
        / NULLIF(revenue, 0),
        2
    ) AS gross_margin_pct,

    ROUND(
        100.0 * operating_income
        / NULLIF(revenue, 0),
        2
    ) AS operating_margin_pct,

    ROUND(
        100.0 * net_income
        / NULLIF(revenue, 0),
        2
    ) AS net_margin_pct

FROM ordered_financials;
-- =====================================================
-- Latest quarter executive snapshot
-- =====================================================

DROP VIEW IF EXISTS vw_latest_quarter;

CREATE VIEW vw_latest_quarter AS
SELECT
    fiscal_year,
    fiscal_period,
    quarter_number,

    revenue,
    gross_profit,
    operating_income,
    net_income,

    previous_quarter_revenue,
    prior_year_quarter_revenue,

    revenue_qoq_change,
    revenue_qoq_growth_pct,

    revenue_yoy_change,
    revenue_yoy_growth_pct,

    gross_margin_pct,
    operating_margin_pct,
    net_margin_pct

FROM vw_quarterly_analytics

ORDER BY
    fiscal_year DESC,
    quarter_number DESC

LIMIT 1;
-- =====================================================
-- Annual financial performance
-- =====================================================

DROP VIEW IF EXISTS vw_annual_financials;

CREATE VIEW vw_annual_financials AS
WITH annual_totals AS (
    SELECT
        fiscal_year,

        SUM(revenue) AS revenue,
        SUM(gross_profit) AS gross_profit,
        SUM(operating_income) AS operating_income,
        SUM(net_income) AS net_income

    FROM vw_quarterly_financials

    GROUP BY fiscal_year
),

annual_comparisons AS (
    SELECT
        fiscal_year,

        revenue,
        gross_profit,
        operating_income,
        net_income,

        LAG(revenue, 1) OVER (
            ORDER BY fiscal_year
        ) AS prior_year_revenue,

        LAG(operating_income, 1) OVER (
            ORDER BY fiscal_year
        ) AS prior_year_operating_income,

        LAG(net_income, 1) OVER (
            ORDER BY fiscal_year
        ) AS prior_year_net_income

    FROM annual_totals
)

SELECT
    fiscal_year,

    revenue,
    gross_profit,
    operating_income,
    net_income,

    prior_year_revenue,

    revenue - prior_year_revenue
        AS revenue_yoy_change,

    ROUND(
        100.0 * (revenue - prior_year_revenue)
        / NULLIF(prior_year_revenue, 0),
        2
    ) AS revenue_yoy_growth_pct,

    ROUND(
        100.0 * gross_profit
        / NULLIF(revenue, 0),
        2
    ) AS gross_margin_pct,

    ROUND(
        100.0 * operating_income
        / NULLIF(revenue, 0),
        2
    ) AS operating_margin_pct,

    ROUND(
        100.0 * net_income
        / NULLIF(revenue, 0),
        2
    ) AS net_margin_pct,

    ROUND(
        100.0 * (operating_income - prior_year_operating_income)
        / NULLIF(prior_year_operating_income, 0),
        2
    ) AS operating_income_yoy_growth_pct,

    ROUND(
        100.0 * (net_income - prior_year_net_income)
        / NULLIF(prior_year_net_income, 0),
        2
    ) AS net_income_yoy_growth_pct

FROM annual_comparisons;