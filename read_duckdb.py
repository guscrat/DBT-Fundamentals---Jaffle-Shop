import duckdb

con = duckdb.connect('raw.duckdb')

print(
    con.sql("SHOW ALL TABLES")
    )

print(
    con.sql(
        """
            SELECT * FROM stripe.payment
        """
    )
)