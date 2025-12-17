import pandas as pd
from typing import Optional, List, Tuple
from tqdm import tqdm
from .config import Config
from .api import BudgetAPI
from .normalizer import DataNormalizer


INCOME_COLUMNS = [
    "income_part", "plan", "adj_plan_consolidated", "adj_plan_regional",
    "adj_plan_growth_rate", "execution_consolidated", "execution_regional",
    "growth_rate_regional", "growth_rate_federal_district", "growth_rate_russia",
    "income_level", "code", "region", "year", "month"
]


class IncomeLoader:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.api = BudgetAPI(self.config)
        self.normalizer = DataNormalizer(self.config)
    
    def get_dates_to_load(self, date_from: str = None, date_to: str = None, 
                          existing_dates: List[str] = None) -> List[Tuple[str, str]]:
        """Determine which dates need to be loaded"""
        dates = self.api.get_available_dates()
        first_date = dates[0][0]
        latest_date = dates[-1][0]
        
        if date_from:
            if date_from < first_date[:7]:
                raise ValueError(f"Data not available. First available: {first_date[:7]}")
            if date_from > latest_date[:7]:
                raise ValueError(f"Data not yet available. Latest: {latest_date[:7]}")
            date_from_item = next((d for d in dates if d[0].startswith(date_from)), None)
        else:
            if existing_dates:
                last_existing = sorted(existing_dates)[-1]
                idx = next((i for i, d in enumerate(dates) if d[0].startswith(last_existing)), -1)
                if idx + 1 >= len(dates):
                    print(f"No new data available. Latest existing: {last_existing}")
                    return []
                date_from_item = dates[idx + 1]
            else:
                date_from_item = dates[0]
        
        if date_to:
            if date_to < first_date[:7]:
                raise ValueError(f"Data not available. First available: {first_date[:7]}")
            if date_to > latest_date[:7]:
                raise ValueError(f"Data not yet available. Latest: {latest_date[:7]}")
            date_to_item = next((d for d in dates if d[0].startswith(date_to)), None)
        else:
            date_to_item = dates[-1]
        
        print(f"Loading from {date_from_item[0][:7]} to {date_to_item[0][:7]}")
        
        start_idx = dates.index(date_from_item)
        end_idx = dates.index(date_to_item) + 1
        return dates[start_idx:end_idx]
    
    def download(self, date_from: str = None, date_to: str = None,
                 existing_dates: List[str] = None) -> pd.DataFrame:
        """Download income data for specified date range"""
        dates_to_load = self.get_dates_to_load(date_from, date_to, existing_dates)
        if not dates_to_load:
            return pd.DataFrame()
        
        regions = self.api.get_regions()
        
        results = []
        total = len(regions) * len(dates_to_load)
        
        with tqdm(total=total, desc="Downloading income") as pbar:
            for reg in regions:
                for date in dates_to_load:
                    try:
                        data = self.api.get_income_data(reg[0], date[0])
                        for row in data:
                            row.extend([reg[0], reg[1], date[0][:4], date[0][5:7]])
                        results.extend(data)
                    except Exception as e:
                        print(f"Error {reg[1]} {date[0]}: {e}")
                    pbar.update(1)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=INCOME_COLUMNS)
        df = df.drop(columns=["code"])
        return self.normalizer.normalize_income(df)

