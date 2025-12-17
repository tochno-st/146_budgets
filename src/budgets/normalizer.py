import pandas as pd
from typing import Optional
from .config import Config


class DataNormalizer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._matcher = None
    
    @property
    def matcher(self):
        if self._matcher is None:
            from reg_normalizer import RegionMatcher
            self._matcher = RegionMatcher()
        return self._matcher
    
    def normalize_regions(self, df: pd.DataFrame, region_col: str = "region") -> pd.DataFrame:
        """Normalize region names and add okato, oktmo, object_level columns"""
        df = self.matcher.match_dataframe(
            df,
            region_col,
            weights=self.config.normalizer_weights,
            approach_weights=self.config.normalizer_approach_weights,
            threshold=self.config.normalizer_threshold
        ).drop(columns=[region_col, "levenshtein_score"])
        
        df = self.matcher.attach_fields(df, "ter", ["okato", "oktmo", "level"])
        df = df.rename(columns={"ter": "object_name", "level": "object_level"})
        return df
    
    def normalize_income(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full normalization pipeline for income data"""
        df.loc[df["income_part"] == "ИТОГО ДОХОДОВ ", "income_level"] = 0
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        
        df = self.normalize_regions(df)
        
        columns_order = [
            "year", "month", "income_level", "income_part", "plan",
            "adj_plan_consolidated", "adj_plan_regional", "adj_plan_growth_rate",
            "execution_consolidated", "execution_regional", "growth_rate_regional",
            "growth_rate_federal_district", "growth_rate_russia",
            "object_name", "okato", "oktmo", "object_level"
        ]
        return df[columns_order]
    
    def normalize_expense(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full normalization pipeline for expense data"""
        df.loc[df["expense_part"] == "ИТОГО РАСХОДОВ ", "expense_level"] = 0
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        
        df = self.normalize_regions(df)
        
        columns_order = [
            "year", "month", "expense_level", "expense_part", "plan",
            "adj_plan_consolidated", "adj_plan_regional", "adj_plan_growth_rate",
            "execution_consolidated", "execution_regional", "growth_rate_regional",
            "growth_rate_federal_district", "growth_rate_russia",
            "object_name", "okato", "oktmo", "object_level"
        ]
        return df[columns_order]

