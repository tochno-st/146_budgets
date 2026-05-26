import time
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
        t0 = time.time()
        n_unique = df[region_col].nunique()
        print(f"[Normalize] Matching regions for {len(df)} rows ({n_unique} unique)...", flush=True)

        # Remove rows with excluded regions
        excluded_regions = [
            "Донецкая Народная Республика",
            "Запорожская область",
            "Луганская Народная Республика",
            "Херсонская область"
        ]
        rows_before = len(df)
        df = df[~df[region_col].isin(excluded_regions)].copy()
        rows_removed = rows_before - len(df)
        if rows_removed > 0:
            print(f"[Normalize] Removed {rows_removed} rows with excluded regions", flush=True)

        t1 = time.time()
        # Lazy-init log: первый доступ к self.matcher может занять время (NLTK, etalon data)
        _ = self.matcher
        t2 = time.time()
        if t2 - t1 > 0.1:
            print(f"[Normalize] RegionMatcher init: {t2-t1:.2f}s", flush=True)

        print(f"[Normalize] Running match_dataframe ({df[region_col].nunique()} unique regions)...", flush=True)
        t3 = time.time()
        df = self.matcher.match_dataframe(
            df,
            region_col,
            weights=self.config.normalizer_weights,
            approach_weights=self.config.normalizer_approach_weights,
            threshold=self.config.normalizer_threshold
        ).drop(columns=[region_col, "levenshtein_score"])
        t4 = time.time()
        print(f"[Normalize] match_dataframe done in {t4-t3:.2f}s", flush=True)

        print("[Normalize] Attaching okato, oktmo, level fields...", flush=True)
        t5 = time.time()
        df = self.matcher.attach_fields(df, "object_name", ["okato", "oktmo", "level"])
        t6 = time.time()
        print(f"[Normalize] attach_fields done in {t6-t5:.2f}s", flush=True)

        df = df.rename(columns={"level": "object_level"})
        print(f"[Normalize] Region normalization complete in {t6-t0:.2f}s total", flush=True)
        return df
    
    def normalize_income(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full normalization pipeline for income data"""
        print(f"[Normalize] Starting income normalization for {len(df)} rows...", flush=True)

        print("[Normalize] Setting income levels...", flush=True)
        df.loc[df["income_part"] == "ИТОГО ДОХОДОВ ", "income_level"] = 0
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

        df = self.normalize_regions(df)

        print("[Normalize] Reordering columns...", flush=True)
        columns_order = [
            "year", "month", "income_level", "income_part", "plan",
            "adj_plan_consolidated", "adj_plan_regional", "adj_plan_growth_rate",
            "execution_consolidated", "execution_regional", "growth_rate_regional",
            "growth_rate_federal_district", "growth_rate_russia",
            "object_name", "okato", "oktmo", "object_level"
        ]
        df = df[columns_order]
        
        print("[Normalize] Applying column types...", flush=True)
        column_types = {
            'year': 'int16',
            'month': 'int8',
            'income_level': 'int8',
            'income_part': 'string',
            'plan': 'float64',
            'adj_plan_consolidated': 'float64',
            'adj_plan_regional': 'float64',
            'adj_plan_growth_rate': 'float64',
            'execution_consolidated': 'float64',
            'execution_regional': 'float64',
            'growth_rate_regional': 'float64',
            'growth_rate_federal_district': 'float64',
            'growth_rate_russia': 'float64',
            'object_name': 'string',
            'okato': 'string',
            'oktmo': 'string',
            'object_level': 'string'
        }
        print("[Normalize] Income normalization complete!", flush=True)
        return df.astype(column_types)
    
    def normalize_expense(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full normalization pipeline for expense data"""
        print(f"[Normalize] Starting expense normalization for {len(df)} rows...", flush=True)

        print("[Normalize] Fixing expense levels...", flush=True)
        df = self.fix_expense_levels(df)
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

        df = self.normalize_regions(df)

        print("[Normalize] Reordering columns...", flush=True)
        columns_order = [
            "year", "month", "expense_level", "expense_part", "plan",
            "adj_plan_consolidated", "adj_plan_regional", "adj_plan_growth_rate",
            "execution_consolidated", "execution_regional", "growth_rate_regional",
            "growth_rate_federal_district", "growth_rate_russia",
            "object_name", "okato", "oktmo", "object_level"
        ]
        df = df[columns_order]
        
        print("[Normalize] Applying column types...", flush=True)
        column_types = {
            'year': 'int16',
            'month': 'int8',
            'expense_level': 'int8',
            'expense_part': 'string',
            'plan': 'float64',
            'adj_plan_consolidated': 'float64',
            'adj_plan_regional': 'float64',
            'adj_plan_growth_rate': 'float64',
            'execution_consolidated': 'float64',
            'execution_regional': 'float64',
            'growth_rate_regional': 'float64',
            'growth_rate_federal_district': 'float64',
            'growth_rate_russia': 'float64',
            'object_name': 'string',
            'okato': 'string',
            'oktmo': 'string',
            'object_level': 'string'
        }
        print("[Normalize] Expense normalization complete!", flush=True)
        return df.astype(column_types)
    
    def fix_expense_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix expense_level=0 for total expense rows. Can be applied to existing data."""
        df = df.copy()
        df.loc[df["expense_part"] == "Расходы бюджета - ИТОГО", "expense_level"] = 0
        return df

