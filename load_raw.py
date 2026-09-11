import duckdb

con = duckdb.connect("raw.duckdb")
con.sql("INSTALL httpfs; LOAD httpfs;")
con.sql("CREATE SCHEMA IF NOT EXISTS jaffle_shop;")
con.sql("CREATE SCHEMA IF NOT EXISTS stripe;")

base = "https://dbt-tutorial-public.s3.amazonaws.com"

con.sql(f"CREATE OR REPLACE TABLE jaffle_shop.customers AS "
        f"SELECT * FROM read_csv_auto('{base}/jaffle_shop_customers.csv')")

con.sql(f"CREATE OR REPLACE TABLE jaffle_shop.orders AS "
        f"SELECT *, current_timestamp AS _etl_loaded_at "
        f"FROM read_csv_auto('{base}/jaffle_shop_orders.csv')")

con.sql(f"CREATE OR REPLACE TABLE stripe.payment AS "
        f"SELECT *, current_timestamp AS _batched_at "
        f"FROM read_csv_auto('{base}/stripe_payments.csv')")

print(con.sql("SHOW ALL TABLES"))
con.close()
print("Pronto! raw.duckdb criado.")