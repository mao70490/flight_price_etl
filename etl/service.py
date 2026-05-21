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
    def run(self, depart, arrive, ddate, trip_type="rt",return_date=None):

        snapshot_time = datetime.now()

        # 1. 抓資料
        result = self.crawler.fetch(depart, arrive, ddate, trip_type,return_date)

        if not result:
            print("❌ 沒抓到資料")
            return

        all_snap = []
        all_raw = []
        all_seg = []

        # 2. outbound
        outbound = result["outbound"]

        if outbound:

            snap, raw, seg = self.transformer.parse(
                outbound,
                trip_type,
                ddate,
                snapshot_time
            )

            all_snap.extend(snap)
            all_raw.extend(raw)
            all_seg.extend(seg)

        # 3. return
        return_data = result["return"]

        if return_data:

            snap, raw, seg = self.transformer.parse(
                return_data,
                trip_type,
                ddate,
                snapshot_time
            )

            all_snap.extend(snap)
            all_raw.extend(raw)
            all_seg.extend(seg)


        # 4. load
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
