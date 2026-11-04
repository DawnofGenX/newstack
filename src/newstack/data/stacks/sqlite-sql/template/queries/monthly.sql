-- month|orders|revenue for every month that saw an order.
SELECT substr(placed_on, 1, 7)            AS month,
       COUNT(*)                           AS orders,
       printf('%.2f', SUM(cents) / 100.0) AS revenue
  FROM order_totals
 GROUP BY month
 ORDER BY month;
