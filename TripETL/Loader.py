class FlightLoader:
    def __init__(self, format="csv"):
        self.format = format

    def load(self, df, filename="flights"):
        if df.empty:
            print("⚠️ 無資料可存檔")
            return
        
        full_name = f"{filename}.{self.format}"
        if self.format == "csv":
            df.to_csv(full_name, index=False, encoding="utf-8-sig")
        elif self.format == "excel":
            df.to_excel(f"{filename}.xlsx", index=False)
            
        print(f"✅ 資料成功儲存至: {full_name}")