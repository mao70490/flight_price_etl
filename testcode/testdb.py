import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\MSSQLLocalDB;"
    "DATABASE=flight_db;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

cursor.execute("""
INSERT INTO flight_snapshot (trip_type, search_time, price)
VALUES (?, GETDATE(), ?)
""", ("test", 1234))

conn.commit()
cursor.close()
conn.close()

print("✅ 寫入成功")