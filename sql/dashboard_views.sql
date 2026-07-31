DROP VIEW IF EXISTS executive_dashboard;

CREATE VIEW executive_dashboard AS
SELECT
    fiscal_year,
    fiscal_period,

    MAX(CASE WHEN metric = 'revenue' THEN value END) AS revenue,
    MAX(CASE WHEN metric = 'gross_profit' THEN value END) AS gross_profit,
    MAX(CASE WHEN metric = 'operating_income' THEN value END) AS operating_income,
    MAX(CASE WHEN metric = 'net_income' THEN value END) AS net_income,

    ROUND(
        MAX(CASE WHEN metric = 'gross_profit' THEN value END) * 100.0 /
        MAX(CASE WHEN metric = 'revenue' THEN value END),
        2
    ) AS gross_margin_pct,

    ROUND(
        MAX(CASE WHEN metric = 'operating_income' THEN value END) * 100.0 /
        MAX(CASE WHEN metric = 'revenue' THEN value END),
        2
    ) AS operating_margin_pct,

    ROUND(
        MAX(CASE WHEN metric = 'net_income' THEN value END) * 100.0 /
        MAX(CASE WHEN metric = 'revenue' THEN value END),
        2
    ) AS net_margin_pct

FROM quarterly_financials
GROUP BY
    fiscal_year,
    fiscal_period;