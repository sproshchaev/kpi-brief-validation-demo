SELECT
    date(day, '-6 days', 'weekday 1') AS week,
    channel,
    SUM(sessions) AS sessions,
    SUM(orders) AS orders
FROM daily_totals
GROUP BY week, channel
ORDER BY week, channel;
