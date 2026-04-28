from etl.crawler import TripCrawler
from etl.transform import FlightDataTransformer
from datetime import datetime
from etl.load import DBLoader

class FlightService:

    def __init__(self, conn_str):
        self.crawler = TripCrawler()
        self.loader  = DBLoader(conn_str)
        self.transformer = FlightDataTransformer()

    
    # 測試抓取到的資料是否能成功轉成df格式
    def test_transform(self, depart, arrive, date):
        outbound, ret = self.crawler.fetch(depart, arrive, date)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df_out = None
        df_ret = None

        if outbound:
            df_out = self.transformer.parse_flights_to_df(outbound, "outbound", now)
            print("\n===== OUT DF =====")
            print(df_out.head())

        if ret:
            df_ret = self.transformer.parse_flights_to_df(ret, "return", now)
            print("\n===== RET DF =====")
            print(df_ret.head())

        return df_out, df_ret
    
    
    # 執行完整 ETL 流程
    def run(self, depart, arrive, ddate, trip_type="rt"):

        snapshot_time = datetime.now()

        # 1. 抓資料
        result = self.crawler.fetch(depart, arrive, ddate, trip_type)

        # 2️. 根據類型處理
        if trip_type == "rt":
            outbound, ret = result

            snap1, raw1 = self.transformer.parse(
                outbound, "outbound", ddate, snapshot_time
            )

            snap2, raw2 = self.transformer.parse(
                ret, "return", ddate, snapshot_time
            )

            all_snap = snap1 + snap2
            all_raw = raw1 + raw2

        elif trip_type == "ow":
            outbound = result

            snap1, raw1 = self.transformer.parse(
                outbound, "oneway", ddate, snapshot_time
            )

            all_snap = snap1
            all_raw = raw1

        else:
            raise ValueError("trip_type 必須是 'rt' 或 'ow'")


        # 🔥 3. load
        if all_snap:
            print(f"💾 寫入 snapshot {len(all_snap)} 筆")
            self.loader.insert_snapshot(all_snap)

        if all_raw:
            print(f"💾 寫入 raw {len(all_raw)} 筆")
            self.loader.insert_raw(all_raw)

        print("✅ ETL 完成")
