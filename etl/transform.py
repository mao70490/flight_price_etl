
class FlightDataTransformer:

    # 轉成要寫入 DB 的格式
    def parse(self, data, trip_type, ddate, snapshot_time):
        snapshot_rows = []
        raw_rows = []
        segment_rows = []

        if not data or "itineraryList" not in data:
            return [], [], []

        for item in data.get("itineraryList", []):
            try:
                journey = item.get("journeyList", [{}])[0]
                sections = journey.get("transSectionList", [])

                if not sections:
                    continue

                itinerary_id = journey.get("uniqueId")

                # 防呆（避免 NULL insert 爆掉）
                if not itinerary_id:
                    print("沒有 uniqueId，跳過")
                    continue
                
                first_seg = sections[0]
                last_seg = sections[-1]

                f_info = first_seg.get("flightInfo", {})

                policies = item.get("policies", [])
                price_info = policies[0].get("price", {}) if policies else {}               

                total_duration = journey.get("duration")
                
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
                    # 搭機總時長，含轉機時間(從API拿的)
                    "total_duration": total_duration,

                    "stops": len(sections) - 1,
                    "snapshot_time": snapshot_time
                })

                # 🟡 raw（debug 用）
                raw_rows.append({
                    "itinerary_id": itinerary_id,
                    "snapshot_time": snapshot_time,
                    "raw_json": item
                })

                # 🔵 segment
                for seg in sections:
                    seg_info = seg.get("flightInfo", {})

                    segment_rows.append({
                        "itinerary_id": itinerary_id,
                        "segment_no": seg.get("segmentNo"),

                        "depart_airport": seg.get("departPoint", {}).get("airportCode"),
                        "arrive_airport": seg.get("arrivePoint", {}).get("airportCode"),

                        "depart_time": seg.get("departDateTime"),
                        "arrive_time": seg.get("arriveDateTime"),

                        "airline": seg_info.get("airlineCode"),
                        "flight_no": seg_info.get("flightNo"),

                        # 航段飛行時間（不包含轉機等待）
                        "duration": seg.get("duration"),

                        # 轉機等待時間（只有第2段開始才會有）
                        "transfer_duration": seg.get("transferDuration")
                    })

            except Exception as e:
                print(f"⚠️ error: {e}")
                continue

        return snapshot_rows, raw_rows, segment_rows