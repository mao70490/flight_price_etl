
class FlightDataTransformer:

    # 轉成要寫入 DB 的格式
    def parse(self, data, trip_type, ddate, snapshot_time):
        snapshot_rows = []
        raw_rows = []

        if not data or "itineraryList" not in data:
            return [], []

        for item in data.get("itineraryList", []):
            try:
                journey = item.get("journeyList", [{}])[0]
                sections = journey.get("transSectionList", [])

                if not sections:
                    continue

                first_seg = sections[0]
                last_seg = sections[-1]

                f_info = first_seg.get("flightInfo", {})

                policies = item.get("policies", [])
                price_info = policies[0].get("price", {}) if policies else {}

                itinerary_id = journey.get("uniqueId")

                airline = (
                    f_info.get("airlineName") or 
                    f_info.get("airlineCode") or 
                    (f_info.get("flightNo")[:2] if f_info.get("flightNo") else "Unknown")
                )

                # 🟢 snapshot（乾淨表）
                snapshot_rows.append({
                    "itinerary_id": itinerary_id,
                    "trip_type": trip_type,
                    "search_date": ddate,

                    "depart_airport": first_seg.get("departPoint", {}).get("airportCode"),
                    "arrive_airport": last_seg.get("arrivePoint", {}).get("airportCode"),

                    "depart_time": first_seg.get("departDateTime"),
                    "arrive_time": last_seg.get("arriveDateTime"),

                    "airline": airline,
                    "flight_no": f_info.get("flightNo"),

                    "price": price_info.get("totalPrice"),

                    "stops": len(sections) - 1,
                    "snapshot_time": snapshot_time
                })

                # 🟡 raw（debug 用）
                raw_rows.append({
                    "itinerary_id": itinerary_id,
                    "snapshot_time": snapshot_time,
                    "raw_json": item
                })

            except Exception as e:
                print(f"⚠️ error: {e}")
                continue

        return snapshot_rows, raw_rows