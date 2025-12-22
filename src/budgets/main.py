import os
import re
import glob
import argparse
from datetime import datetime
from typing import Optional
from pathlib import Path

from .config import Config
from .storage import StorageManager
from .income import IncomeLoader
from .expense import ExpenseLoader
from .normalizer import DataNormalizer


class BudgetUpdater:
    def __init__(self, config: Optional[Config] = None, data_dir: str = "data"):
        self.config = config or Config()
        self.config.data_dir = data_dir
        self.storage = StorageManager(self.config)
        self.income_loader = IncomeLoader(self.config)
        self.expense_loader = ExpenseLoader(self.config)
        self.normalizer = DataNormalizer(self.config)
    
    def _get_version(self, output_dir: str = None) -> str:
        """Generate version string with run number if multiple runs per day"""
        base_date = datetime.now().strftime("%Y%m%d")
        
        if output_dir is None:
            output_dir = os.path.join(self.config.data_dir, "processed")
        
        # Check for existing files with today's date to determine run number
        pattern = os.path.join(output_dir, f"*_v{base_date}*.parquet")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return base_date
        
        # Find the highest run number
        max_run = 1
        for f in existing_files:
            # Check for pattern like v20251217(2)
            match = re.search(rf'_v{base_date}\((\d+)\)', f)
            if match:
                run_num = int(match.group(1))
                max_run = max(max_run, run_num)
            else:
                # File without run number exists, so next run is at least (2)
                max_run = max(max_run, 1)
        
        # Return next run number
        return f"{base_date}({max_run + 1})"
    
    def _get_filename(self, data_type: str, version: str) -> str:
        """Generate filename based on template"""
        if data_type == "income":
            template = self.config.income_filename_template
        else:
            template = self.config.expense_filename_template
        
        return template.format(code=self.config.project_code, version=version)
    
    def update_income(self, date_from: str = None, date_to: str = None,
                      input_file: str = None, output_dir: str = None,
                      s3_folder: str = None, version: str = None) -> dict:
        """Update income data"""
        if output_dir is None:
            output_dir = os.path.join(self.config.data_dir, "processed")
        
        # Load existing data
        if input_file:
            old_df = self.storage.load_existing(input_file)
        else:
            # Find latest existing file
            old_df = self.storage.load_latest_file(output_dir, "income", self.config.project_code)
        
        existing_dates = self.storage.get_existing_dates(old_df)
        
        new_df = self.income_loader.download(date_from, date_to, existing_dates)
        
        if new_df.empty:
            print("No new income data to add")
            return {"status": "no_update", "files": []}
        
        merged_df = self.storage.merge_data(old_df, new_df)
        
        # Generate version and filename
        ver = version or self._get_version(output_dir)
        filename = self._get_filename("income", ver)
        base_path = os.path.join(output_dir, filename)
        
        saved_files = self.storage.save_local(merged_df, base_path)
        
        # Create zip files for each format
        zip_files = self.storage.create_zip_files(saved_files)
        
        if s3_folder:
            for f in zip_files:
                self.storage.upload_to_s3(f, s3_folder, ver)
        
        return {
            "status": "updated",
            "version": ver,
            "files": saved_files,
            "zip_files": zip_files,
            "rows_added": len(new_df),
            "total_rows": len(merged_df)
        }
    
    def update_expense(self, date_from: str = None, date_to: str = None,
                       input_file: str = None, output_dir: str = None,
                       s3_folder: str = None, version: str = None) -> dict:
        """Update expense data"""
        if output_dir is None:
            output_dir = os.path.join(self.config.data_dir, "processed")
        
        # Load existing data
        if input_file:
            old_df = self.storage.load_existing(input_file)
        else:
            # Find latest existing file
            old_df = self.storage.load_latest_file(output_dir, "expenses", self.config.project_code)
        
        existing_dates = self.storage.get_existing_dates(old_df)
        
        new_df = self.expense_loader.download(date_from, date_to, existing_dates)
        
        if new_df.empty:
            print("No new expense data to add")
            return {"status": "no_update", "files": []}
        
        merged_df = self.storage.merge_data(old_df, new_df)
        # Apply expense_level fixes to all data (including previously gathered)
        merged_df = self.normalizer.fix_expense_levels(merged_df)
        
        # Generate version and filename
        ver = version or self._get_version(output_dir)
        filename = self._get_filename("expense", ver)
        base_path = os.path.join(output_dir, filename)
        
        saved_files = self.storage.save_local(merged_df, base_path)
        
        # Create zip files for each format
        zip_files = self.storage.create_zip_files(saved_files)
        
        if s3_folder:
            for f in zip_files:
                self.storage.upload_to_s3(f, s3_folder, ver)
        
        return {
            "status": "updated",
            "version": ver,
            "files": saved_files,
            "zip_files": zip_files,
            "rows_added": len(new_df),
            "total_rows": len(merged_df)
        }
    
    def update_all(self, date_from: str = None, date_to: str = None,
                   output_dir: str = None, s3_folder: str = None, 
                   version: str = None) -> dict:
        """Update both income and expense data"""
        ver = version or self._get_version()
        
        income_result = self.update_income(
            date_from=date_from, date_to=date_to,
            output_dir=output_dir, s3_folder=s3_folder, version=ver
        )
        
        expense_result = self.update_expense(
            date_from=date_from, date_to=date_to,
            output_dir=output_dir, s3_folder=s3_folder, version=ver
        )
        
        return {
            "version": ver,
            "income": income_result,
            "expense": expense_result
        }


def main():
    parser = argparse.ArgumentParser(description="Budget data updater")
    parser.add_argument("--type", choices=["income", "expense", "all"], default="all",
                        help="Type of data to update")
    parser.add_argument("--date-from", type=str, help="Start date (YYYY-MM)")
    parser.add_argument("--date-to", type=str, help="End date (YYYY-MM)")
    parser.add_argument("--input", type=str, help="Input parquet file path")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Output directory")
    parser.add_argument("--s3-folder", type=str, help="S3 folder for upload")
    parser.add_argument("--version", type=str, help="Version string for S3 upload")
    parser.add_argument("--data-dir", type=str, default="data", help="Base data directory")
    
    args = parser.parse_args()
    
    updater = BudgetUpdater(data_dir=args.data_dir)
    
    if args.type == "income":
        result = updater.update_income(
            date_from=args.date_from, date_to=args.date_to,
            input_file=args.input, output_dir=args.output_dir,
            s3_folder=args.s3_folder, version=args.version
        )
    elif args.type == "expense":
        result = updater.update_expense(
            date_from=args.date_from, date_to=args.date_to,
            input_file=args.input, output_dir=args.output_dir,
            s3_folder=args.s3_folder, version=args.version
        )
    else:
        result = updater.update_all(
            date_from=args.date_from, date_to=args.date_to,
            output_dir=args.output_dir, s3_folder=args.s3_folder,
            version=args.version
        )
    
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()

