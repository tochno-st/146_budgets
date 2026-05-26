import os
import glob
import zipfile
import pandas as pd
from pathlib import Path
from typing import Optional
from .config import Config


class StorageManager:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._s3_client = None
    
    @property
    def s3_client(self):
        if self._s3_client is None and self.config.s3_bucket:
            import boto3
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                endpoint_url=self.config.s3_endpoint_url,
                region_name=self.config.s3_region
            )
        return self._s3_client
    
    def load_existing(self, filepath: str) -> Optional[pd.DataFrame]:
        """Load existing parquet file if exists"""
        if os.path.exists(filepath):
            return pd.read_parquet(filepath)
        return None
    
    def load_latest_file(self, directory: str, data_type: str, project_code: str) -> Optional[pd.DataFrame]:
        """Find and load the latest parquet file matching the pattern"""
        pattern = os.path.join(directory, f"data_budget_{data_type}_{project_code}_v*.parquet")
        files = glob.glob(pattern)
        
        if not files:
            return None
        
        # Sort by modification time to get the latest
        latest_file = max(files, key=os.path.getmtime)
        print(f"Loading existing data from: {latest_file}")
        return pd.read_parquet(latest_file)
    
    def save_local(self, df: pd.DataFrame, base_path: str, formats: list = None):
        """Save dataframe to local files in multiple formats"""
        if formats is None:
            formats = ["parquet", "csv", "xlsx"]
        
        Path(base_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Excel has a maximum row limit of 1,048,576
        EXCEL_MAX_ROWS = 1_048_576
        
        saved_files = []
        for fmt in formats:
            filepath = f"{base_path}.{fmt}"
            if fmt == "parquet":
                df.to_parquet(filepath, index=False)
            elif fmt == "csv":
                df.to_csv(filepath, index=False)
            elif fmt == "xlsx":
                if len(df) > EXCEL_MAX_ROWS:
                    # Split by year and save to zip archive
                    zip_path = self._save_excel_split_by_year(df, base_path)
                    saved_files.append(zip_path)
                    print(f"Saved: {zip_path}")
                    continue
                df.to_excel(filepath, index=False)
            saved_files.append(filepath)
            print(f"Saved: {filepath}")
        return saved_files
    
    def _save_excel_split_by_year(self, df: pd.DataFrame, base_path: str) -> str:
        """Split DataFrame by year and save as separate Excel files in a zip archive"""
        import tempfile
        
        base_name = Path(base_path).name
        zip_path = f"{base_path}_xlsx.zip"
        
        print(f"DataFrame has {len(df):,} rows, splitting by year for Excel export...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            excel_files = []
            
            for year in sorted(df["year"].unique()):
                year_df = df[df["year"] == year]
                excel_filename = f"{base_name}_{year}.xlsx"
                excel_path = os.path.join(temp_dir, excel_filename)
                year_df.to_excel(excel_path, index=False)
                excel_files.append((excel_path, excel_filename))
                print(f"  Created: {excel_filename} ({len(year_df):,} rows)")
            
            # Create zip archive with all Excel files
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for excel_path, excel_filename in excel_files:
                    zf.write(excel_path, excel_filename)
        
        return zip_path
    
    def create_zip_files(self, saved_files: list) -> list:
        """Create separate zip files for each format (parquet, csv, xlsx)"""
        zip_files = []
        for filepath in saved_files:
            path = Path(filepath)
            fmt = path.suffix.lstrip(".")  # Get format without dot
            base_name = path.stem  # Get filename without extension
            zip_name = f"{base_name}_{fmt}.zip"
            zip_path = path.parent / zip_name
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(filepath, path.name)
            
            zip_files.append(str(zip_path))
            print(f"Created zip: {zip_path}")
        
        return zip_files
    
    def upload_to_s3(self, local_path: str, s3_folder: str, version: str = None):
        """Upload file to S3 bucket"""
        if not self.s3_client:
            print("S3 not configured, skipping upload")
            return None
        
        filename = os.path.basename(local_path)
        if version:
            s3_key = f"{s3_folder}/{version}/{filename}"
        else:
            s3_key = f"{s3_folder}/{filename}"
        
        self.s3_client.upload_file(local_path, self.config.s3_bucket, s3_key)
        print(f"Uploaded to S3: s3://{self.config.s3_bucket}/{s3_key}")
        return s3_key
    
    def merge_data(self, old_df: Optional[pd.DataFrame], new_df: pd.DataFrame,
                   subset: Optional[list] = None) -> pd.DataFrame:
        """Merge old and new dataframes, removing duplicates"""
        if old_df is None:
            return new_df.sort_values(["year", "month"]).drop_duplicates(subset=subset)
        return pd.concat([old_df, new_df]).sort_values(["year", "month"]).drop_duplicates(subset=subset)
    
    def get_existing_dates(self, df: pd.DataFrame) -> list:
        """Get list of existing year-month combinations"""
        if df is None:
            return []
        return [f"{row['year']}-{row['month']:02d}" 
                for _, row in df.drop_duplicates(["year", "month"])[["year", "month"]].iterrows()]

