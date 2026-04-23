from crawler import TripCrawler
from transform import FlightDataTransformer
from datetime import datetime
from config.dbconfig import DB_CONN_STR
from load import DBLoader

class FlightService:

    def __init__(self):
        self.crawler = TripCrawler()
        self.db = DBLoader(DB_CONN_STR)
        self.transformer = FlightDataTransformer()

    def run_etl(self, depart, arrive, date):
        outbound, ret = self.crawler.fetch(depart, arrive, date)

        if not outbound:
            print("❌ outbound 失敗")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df_out = self.transformer.parse_to_df(outbound, "outbound", now)
        self.db.insert_dataframe(df_out, "flight_prices")

        if ret:
            df_ret = self.transformer.parse_to_df(ret, "return", now)
            self.db.insert_dataframe(df_ret, "flight_prices")

        print("✅ ETL 完成")

    def _combine(self, df_out, df_ret):
        df = df_out.merge(df_ret, how="cross", suffixes=("_out", "_ret"))

        df["total_price"] = df["price_out"] + df["price_ret"]

        # 過濾不合理回程
        df = df[df["depart_time_ret"] > df["arrive_time_out"]]

        return df.sort_values("total_price")