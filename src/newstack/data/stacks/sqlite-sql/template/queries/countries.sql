-- country|revenue, so the report has a second dimension to get wrong.
SELECT country,
       printf('%.2f', SUM(cents) / 100.0) AS revenue
  FROM customer_revenue
 GROUP BY country
 ORDER BY revenue DESC, country;
