from promo_processor.processor import PromoProcessor
import pandas as pd
import json
from pathlib import Path


def main():
    cur_dir = Path(__file__).resolve().parent
    data = pd.read_json(cur_dir / "target_08.json")
    data.fillna("", inplace=True)
    data = data.to_dict(orient="records")

    # data = [i for i in data if  "Buy 4 get 10%" in  i.get("volume_deals_description")]
    processed_data = PromoProcessor.process_item(data)
    # processed_data.results = [i for i in processed_data.results if i.get("volume_deals_description") or i.get("digital_coupon_description")]
    processed_data.to_json("test.json")


if __name__ == '__main__':
    main()
 



