import pyodbc
import pandas as pd


class DBLoader:

    def __init__(self, conn_str):
        self.conn = pyodbc.connect(conn_str)
        self.cursor = self.conn.cursor()

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

    # =========================
    # 🟢 INSERT snapshot
    # =========================
    def insert_snapshot(self, rows):

        sql = """
        INSERT INTO flight_snapshot (
            itinerary_id,
            search_date,
            return_date,
            depart_code,
            arrive_code,
            snapshot_time,
            depart_time,
            arrive_time,
            total_price,
            stops,
            total_duration,
            airline
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for r in rows:
            self.cursor.execute(sql,
                r["itinerary_id"],
                r.get("search_date"),
                None,  # return_date 你之後可補
                r.get("depart_airport"),
                r.get("arrive_airport"),
                r.get("snapshot_time"),
                r.get("depart_time"),
                r.get("arrive_time"),
                r.get("price"),
                r.get("stops"),
                None,  # duration 之後可算
                r.get("airline")
            )

        self.conn.commit()

    # =========================
    # 🟡 INSERT raw log
    # =========================
    def insert_raw(self, rows):

        sql = """
        INSERT INTO flight_raw_jason (
            itinerary_id,
            snapshot_time,
            raw_json
        )
        VALUES (?, ?, ?)
        """

        for r in rows:
            self.cursor.execute(sql,
                r["itinerary_id"],
                r["snapshot_time"],
                str(r["raw_json"])
            )

        self.conn.commit()

    # =========================
    # 🟠 simple dedup check
    # =========================
    def exists_snapshot(self, itinerary_id, snapshot_time):

        sql = """
        SELECT 1 FROM flight_snapshot
        WHERE itinerary_id = ?
        AND snapshot_time = ?
        """

        self.cursor.execute(sql, itinerary_id, snapshot_time)
        return self.cursor.fetchone() is not None