from crawler import TripCrawler
from transform import FlightDataTransformer
from datetime import datetime


class FlightService:

    def __init__(self):
        self.crawler = TripCrawler()
        self.transformer = FlightDataTransformer()

    def get_round_trip_df(self, depart, arrive, date):
        outbound, ret = self.crawler.fetch(depart, arrive, date)

        if not outbound or not ret:
            print("❌ 抓取失敗")
            return None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df_out = self.transformer.parse_to_df(outbound, "outbound", now)
        df_ret = self.transformer.parse_to_df(ret, "return", now)

        return self._combine(df_out, df_ret)

    def _combine(self, df_out, df_ret):
        df = df_out.merge(df_ret, how="cross", suffixes=("_out", "_ret"))

        df["total_price"] = df["price_out"] + df["price_ret"]

        # 過濾不合理回程
        df = df[df["depart_time_ret"] > df["arrive_time_out"]]

        return df.sort_values("total_price")