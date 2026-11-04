-- name|placed|revenue, highest first, ties broken by name.
SELECT name,
       placed,
       printf('%.2f', cents / 100.0) AS revenue
  FROM customer_revenue
 ORDER BY cents DESC, name;
