import pyodbc
import pandas as pd


class DBLoader:

    def __init__(self, conn_str):
        self.conn_str = conn_str

    def insert_dataframe(self, df, table_name):
        if df.empty:
            print("❌ DataFrame 是空的")
            return

        # 👉 處理 NaN → None
        df = df.where(pd.notnull(df), None)

        conn = pyodbc.connect(self.conn_str)
        cursor = conn.cursor()

        columns = ",".join(df.columns)
        placeholders = ",".join(["?"] * len(df.columns))

        sql = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        """

        for _, row in df.iterrows():
            cursor.execute(sql, tuple(row))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ 寫入 {len(df)} 筆資料")