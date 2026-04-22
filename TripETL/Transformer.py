import pandas as pd

class FlightTransformer:
    def transform(self, raw_data):
        if not raw_data or "itineraryList" not in raw_data:
            return pd.DataFrame()

        records = []
        for item in raw_data["itineraryList"]:
            flight_info = self._parse_single_item(item)
            if flight_info:
                records.append(flight_info)
        
        df = pd.DataFrame(records)
        return self._clean_data(df)

    def _parse_single_item(self, item):
        try:
            out_seg = item["journeyList"][0]["transSectionList"][0]
            policy = item["policies"][0]
            return {
                "airline": out_seg["flightInfo"]["airlineCode"],
                "flight_no": out_seg["flightInfo"]["flightNo"],
                "depart_time": out_seg["departDateTime"],
                "price": policy["price"]["totalPrice"],
                "seat": policy.get("seatCount")
            }
        except: return None

    def _clean_data(self, df):
        if df.empty: return df
        df["depart_time"] = pd.to_datetime(df["depart_time"])
        df["price"] = pd.to_numeric(df["price"])
        return df.sort_values("price")