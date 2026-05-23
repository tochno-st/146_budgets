import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    base_url: str = "https://www.iminfin.ru/areas-of-analysis/budget/finansoviy-pasport-subjecta-rf/redirect/copen-imon/Data"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    
    # S3 settings
    s3_bucket: Optional[str] = field(default_factory=lambda: os.getenv("S3_BUCKET"))
    s3_access_key: Optional[str] = field(default_factory=lambda: os.getenv("S3_ACCESS_KEY"))
    s3_secret_key: Optional[str] = field(default_factory=lambda: os.getenv("S3_SECRET_KEY"))
    s3_endpoint_url: Optional[str] = field(default_factory=lambda: os.getenv("S3_ENDPOINT_URL"))
    s3_region: str = field(default_factory=lambda: os.getenv("S3_REGION", "us-east-1"))
    
    # File paths
    data_dir: str = "data"
    project_code: str = "145"
    income_filename_template: str = "data_budget_income_{code}_v{version}"
    expense_filename_template: str = "data_budget_expenses_{code}_v{version}"
    
    # API UUIDs
    income_uuid: str = "77b109a3-1c64-42db-9f58-6d79b42ba198"
    expense_uuid: str = "556b0bd7-00a9-4713-84cc-5b54bcd506c7"
    
    # Normalizer settings
    normalizer_weights: dict = field(default_factory=lambda: {"levenshtein": 0.4, "token_set": 0.6})
    normalizer_approach_weights: dict = field(default_factory=lambda: {"original": 0.3, "stemmed": 0.7})
    normalizer_threshold: int = 70
    
    request_delay: float = 0.5

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds between retries

    # Concurrency settings
    max_workers: int = 10

