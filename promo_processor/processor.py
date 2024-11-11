import re
import json
import logging
from typing import Dict, Any, TypeVar, Union, List
from pathlib import Path
from abc import ABC, abstractmethod


T = TypeVar("T", bound="PromoProcessor")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class PromoProcessor(ABC):
    subclasses = []
    results = []
    NUMBER_MAPPING = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        PromoProcessor.subclasses.append(cls)
        cls.logger = logging.getLogger(cls.__name__)

    @classmethod
    def apply_store_brands(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        store_brands = {
            'marianos': ["Private Selection", "Kroger", "Simple Truth", "Simple Truth Organic"],
            'target': ["Deal Worthy", "Good & Gather", "Market Pantry", "Favorite Day", "Kindfull", "Smartly", "Up & Up"],
            'jewel': ['Lucerne', "Signature Select", "O Organics", "Open Nature", "Waterfront Bistro", "Primo Taglio",
                      "Soleil", "Value Corner", "Ready Meals"],
            'walmart': ["Clear American", "Great Value", "Home Bake Value", "Marketside", 
                        "Co Squared", "Best Occasions", "Mash-Up Coffee", "World Table"]
        }
        store_brands_list = [brand for brands in store_brands.values() for brand in brands if brand.casefold() in item["product_title"].casefold()]    
        item["brandStatus"] = any(store_brands_list)
        return item

    @property
    @abstractmethod
    def patterns(self):
        """Each subclass must define its own patterns."""
        pass

    @abstractmethod
    def calculate_deal(self, item_data: Dict[str, Any], match: re.Match) -> Dict[str, Any]:
        """Each subclass should implement deal calculation logic here."""
        pass

    @abstractmethod
    def calculate_coupon(self, item_data: Dict[str, Any], match: re.Match) -> Dict[str, Any]:
        """Each subclass should implement coupon calculation logic here."""
        pass

    @classmethod
    def process_item(cls, item_data: Union[Dict[str, Any], List[Dict[str, Any]])) -> T:
        """Process a list of items or a single item."""
        if isinstance(item_data, list):
            cls.results.extend([cls.apply_store_brands(cls.process_single_item(item)) for item in item_data])
        else:
            cls.results.append(cls.apply_store_brands(cls.process_single_item(item_data)))
        return cls

    @classmethod
    def to_json(cls, filename: Union[str, Path]) -> None:
        with open(filename, "w") as f:
            json.dump(cls.results, f, indent=4)

    @classmethod
    def process_single_item(cls, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a single item, checking all processors and patterns."""
        updated_item = item_data.copy()

        if not hasattr(cls, "logger"):
            cls.logger = logging.getLogger(cls.__name__)

        # Process deals first across all processors and patterns
        deal_processed = False
        for processor_class in cls.subclasses:
            processor = processor_class()

            for pattern in processor.patterns:
                deal_match = re.search(pattern, updated_item.get("volume_deals_description", ""))
                if deal_match:
                    cls.logger.info(f"Pattern matched for deals in {processor_class.__name__}: {item_data['volume_deals_description']}")
                    updated_item = processor.calculate_deal(updated_item, deal_match)
                    cls.logger.info(f"Deal processed by {processor_class.__name__}")
                    deal_processed = True
                    break

            if deal_processed:
                break

        # Process coupons similarly across all processors and patterns
        coupon_processed = False
        for processor_class in cls.subclasses:
            processor = processor_class()

            for pattern in processor.patterns:
                coupon_match = re.search(pattern, updated_item.get("digital_coupon_short_description", ""))
                if coupon_match:
                    cls.logger.info(f"Pattern matched for coupons in {processor_class.__name__}: {item_data['digital_coupon_short_description']}")
                    updated_item = processor.calculate_coupon(updated_item, coupon_match)
                    cls.logger.info(f"Coupon processed by {processor_class.__name__}")
                    coupon_processed = True
                    break

            if coupon_processed:
                break

        return updated_item
