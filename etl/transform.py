import pandas as pd

def parse_flights_to_df(data, ddate, scrap_day):
    flights = []

    if not data or "itineraryList" not in data:
        print("❌ 沒有 itineraryList")
        return pd.DataFrame()

    # global_currency = data.get("currency") or data.get("context", {}).get("currency", "TWD")

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

            airline = (
                f_info.get("airlineName") or 
                f_info.get("airlineCode") or 
                (f_info.get("flightNo")[:2] if f_info.get("flightNo") else "Unknown")
            )

            flights.append({
                "search_date": ddate,
                "scrap_time": scrap_day,

                "depart_airport": first_seg.get("departPoint", {}).get("airportCode"),
                "arrive_airport": last_seg.get("arrivePoint", {}).get("airportCode"),

                "depart_time": first_seg.get("departDateTime"),
                "arrive_time": last_seg.get("arriveDateTime"),

                "airline": airline,
                "flight_no": f_info.get("flightNo"),

                "price": price_info.get("totalPrice"),
                # "currency": price_info.get("currency") or global_currency,

                "stops": len(sections) - 1
            })

        except Exception as e:
            print(f"⚠️ error: {e}")
            continue

    df = pd.DataFrame(flights)

    if df.empty:
        print("❌ DataFrame 是空的")
        return df

    # ✅ 時間轉換
    df["depart_time"] = pd.to_datetime(df["depart_time"], errors="coerce")
    df["arrive_time"] = pd.to_datetime(df["arrive_time"], errors="coerce")

    # ✅ 飛行時數
    df["flight_hours"] = (df["arrive_time"] - df["depart_time"]).dt.total_seconds() / 3600

    return df