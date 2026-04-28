from etl.crawler import TripCrawler
from etl.transform import FlightDataTransformer
from datetime import datetime
from etl.load import DBLoader

class FlightService:

    def __init__(self, conn_str):
        self.crawler = TripCrawler()
        self.loader  = DBLoader(conn_str)
        self.transformer = FlightDataTransformer()
    
    
    # 執行完整 ETL 流程
    def run(self, depart, arrive, ddate, trip_type="rt"):

        snapshot_time = datetime.now()

        # 1. 抓資料
        result = self.crawler.fetch(depart, arrive, ddate, trip_type)

        # 2️. 根據類型處理
        if trip_type == "rt":
            outbound, ret = result

            snap1, raw1, seg1 = self.transformer.parse(
                outbound, "outbound", ddate, snapshot_time
            )

            snap2, raw2, seg2 = self.transformer.parse(
                ret, "return", ddate, snapshot_time
            )

            all_snap = snap1 + snap2
            all_raw = raw1 + raw2
            all_seg = seg1 + seg2

        elif trip_type == "ow":
            outbound = result

            snap1, raw1, seg1 = self.transformer.parse(
                outbound, "oneway", ddate, snapshot_time
            )

            all_snap = snap1
            all_raw = raw1
            all_seg = seg1

        else:
            raise ValueError("trip_type 必須是 'rt' 或 'ow'")


        # 🔥 3. load
        if all_snap:
            print(f"💾 寫入 snapshot {len(all_snap)} 筆")
            self.loader.insert_snapshot(all_snap)

        if all_raw:
            print(f"💾 寫入 raw {len(all_raw)} 筆")
            self.loader.insert_raw(all_raw)

        if all_seg:
            print(f"💾 寫入 segment {len(all_seg)} 筆")
            self.loader.insert_segment(all_seg)

        print("✅ ETL 完成")
