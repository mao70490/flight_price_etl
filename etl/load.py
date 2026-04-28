import pyodbc
import pandas as pd


class DBLoader:

    def __init__(self, conn_str):
        self.conn = pyodbc.connect(conn_str)
        self.cursor = self.conn.cursor()

    # =========================
    # 🟢 INSERT snapshot
    # =========================
    def insert_snapshot(self, rows):

        sql = """
        INSERT INTO flight_snapshot (
            itinerary_id,
            search_date,
            trip_type,
            depart_airport,
            arrive_airport,
            snapshot_time,
            depart_time,
            arrive_time,
            price,
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
                r.get("trip_type"),
                r.get("depart_airport"),
                r.get("arrive_airport"),
                r.get("snapshot_time"),
                r.get("depart_time"),
                r.get("arrive_time"),
                r.get("price"),
                r.get("stops"),
                r.get("total_duration"),
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
    

    # =========================
    # 🔵 insert segment
    # =========================
    def insert_segment(self, rows):
        sql = """
        INSERT INTO flight_segment (
            itinerary_id,
            segment_no,
            depart_airport,
            arrive_airport,
            depart_time,
            arrive_time,
            airline,
            flight_no,
            duration,
            transfer_duration
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for r in rows:
            self.cursor.execute(sql,
                r["itinerary_id"],
                r["segment_no"],
                r["depart_airport"],
                r["arrive_airport"],
                r["depart_time"],
                r["arrive_time"],
                r["airline"],
                r["flight_no"],
                r["duration"],
                r.get("transfer_duration")
            )

        self.conn.commit()