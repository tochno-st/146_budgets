import time
import requests
from typing import List, Tuple, Optional
from .config import Config


class BudgetAPI:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.headers = {"User-agent": self.config.user_agent}
    
    def _get(self, url: str) -> dict:
        """Make GET request with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                r = requests.get(url, headers=self.headers, timeout=30)
                r.raise_for_status()
                return r.json()
            except (requests.RequestException, requests.JSONDecodeError) as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (attempt + 1)  # exponential backoff
                    print(f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise last_exception
    
    def get_regions(self) -> List[Tuple[str, str]]:
        """Get list of available regions as [(code, name), ...]"""
        url = f"{self.config.base_url}?uuid={self.config.income_uuid}&dataVersion=07.03.2017 07.10.12.980&dsCode=TerritoryOnlySubject&TERRITORIES_paramPeriod=2014-05-28T00:00:00.000Z&_dc=1737443788154"
        return self._get(url)["data"]
    
    def get_available_dates(self) -> List[Tuple[str, str]]:
        """Get list of available date periods"""
        url = f"{self.config.base_url}?uuid={self.config.income_uuid}&dataVersion=07.03.2017 07.10.12.980&dsCode=ds_FK_Passport_MONTH_Periods&verified=true&latest=false&_dc=1737443788160"
        return self._get(url)["data"]
    
    def get_income_data(self, region_code: str, date_str: str) -> List[List]:
        """Get income data for a specific region and date"""
        url = f"{self.config.base_url}?uuid={self.config.income_uuid}&dataVersion=07.03.2017 07.10.12.980&dsCode=PassportFK_002_001_incomesDataAfter01052019&territory={region_code}&paramPeriod={date_str}&_dc=1737443590492"
        time.sleep(self.config.request_delay)
        return self._get(url)["data"]
    
    def get_expense_data(self, region_code: str, date_str: str) -> List[List]:
        """Get expense data for a specific region and date"""
        url = f"{self.config.base_url}?uuid={self.config.expense_uuid}&dataVersion=07.03.2017 07.11.21.305&dsCode=PassportFK_002_002_outcomesDataAfter01052019&territory={region_code}&PassportFK_002_002_outcomesType=2&paramPeriod={date_str}&_dc=1765489263390"
        time.sleep(self.config.request_delay)
        return self._get(url)["data"]
    
    def get_first_date(self) -> str:
        dates = self.get_available_dates()
        return dates[0][0]
    
    def get_latest_date(self) -> str:
        dates = self.get_available_dates()
        return dates[-1][0]

