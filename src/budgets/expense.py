import pandas as pd
from typing import Optional, List, Tuple
from tqdm import tqdm
from .config import Config
from .api import BudgetAPI
from .normalizer import DataNormalizer


EXPENSE_COLUMNS = [
    "expense_part", "plan", "adj_plan_consolidated", "adj_plan_regional",
    "adj_plan_growth_rate", "execution_consolidated", "execution_regional",
    "growth_rate_regional", "growth_rate_federal_district", "growth_rate_russia",
    "expense_level", "okato_temp", "region", "year", "month"
]


class ExpenseLoader:
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
                print(f"Warning: Requested date {date_from} is before first available. Using {first_date[:7]}")
                date_from = first_date[:7]
            if date_from > latest_date[:7]:
                print(f"No data available yet for {date_from}. Latest available: {latest_date[:7]}")
                return []
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
                print(f"Warning: Requested end date {date_to} is before first available. Using {first_date[:7]}")
                date_to = first_date[:7]
            if date_to > latest_date[:7]:
                print(f"Warning: Requested end date {date_to} not yet available. Using latest: {latest_date[:7]}")
                date_to = latest_date[:7]
            date_to_item = next((d for d in dates if d[0].startswith(date_to)), None)
        else:
            date_to_item = dates[-1]
        
        print(f"Loading from {date_from_item[0][:7]} to {date_to_item[0][:7]}")
        
        start_idx = dates.index(date_from_item)
        end_idx = dates.index(date_to_item) + 1
        return dates[start_idx:end_idx]
    
    def download(self, date_from: str = None, date_to: str = None,
                 existing_dates: List[str] = None) -> pd.DataFrame:
        """Download expense data for specified date range"""
        dates_to_load = self.get_dates_to_load(date_from, date_to, existing_dates)
        if not dates_to_load:
            return pd.DataFrame()
        
        regions = self.api.get_regions()
        
        results = []
        total = len(regions) * len(dates_to_load)
        failed = []

        with tqdm(total=total, desc="Downloading expenses") as pbar:
            for reg in regions:
                for date in dates_to_load:
                    try:
                        data = self.api.get_expense_data(reg[0], date[0])
                        for row in data:
                            row.extend([reg[0], reg[1], date[0][:4], date[0][5:7]])
                        results.extend(data)
                    except Exception as e:
                        print(f"Error {reg[1]} {date[0]}: {e}")
                        failed.append((reg, date))
                    pbar.update(1)

        max_retries = 5
        for retry_num in range(1, max_retries + 1):
            if not failed:
                break
            print(f"Retrying {len(failed)} failed items (attempt {retry_num}/{max_retries})...")
            still_failed = []
            for reg, date in failed:
                try:
                    data = self.api.get_expense_data(reg[0], date[0])
                    for row in data:
                        row.extend([reg[0], reg[1], date[0][:4], date[0][5:7]])
                    results.extend(data)
                except Exception as e:
                    print(f"Error {reg[1]} {date[0]}: {e}")
                    still_failed.append((reg, date))
            failed = still_failed

        if failed:
            failed_list = ", ".join(f"{reg[1]} {date[0][:7]}" for reg, date in failed)
            raise RuntimeError(
                f"Failed to download expense data for {len(failed)} region-date pairs "
                f"after {max_retries} retries: {failed_list}"
            )
        
        if not results:
            print("[Download] No data collected - all API calls may have failed")
            return pd.DataFrame()
        
        print(f"[Download] Creating DataFrame from {len(results)} rows...")
        df = pd.DataFrame(results, columns=EXPENSE_COLUMNS)
        df = df.drop(columns=["okato_temp"])
        print("[Download] Starting normalization...")
        return self.normalizer.normalize_expense(df)

