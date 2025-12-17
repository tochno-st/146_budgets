import os
import argparse
from datetime import datetime
from typing import Optional
from pathlib import Path

from .config import Config
from .storage import StorageManager
from .income import IncomeLoader
from .expense import ExpenseLoader


class BudgetUpdater:
    def __init__(self, config: Optional[Config] = None, data_dir: str = "data"):
        self.config = config or Config()
        self.config.data_dir = data_dir
        self.storage = StorageManager(self.config)
        self.income_loader = IncomeLoader(self.config)
        self.expense_loader = ExpenseLoader(self.config)
    
    def _get_version(self) -> str:
        return datetime.now().strftime("%Y%m%d")
    
    def update_income(self, date_from: str = None, date_to: str = None,
                      input_file: str = None, output_dir: str = None,
                      s3_folder: str = None, version: str = None) -> dict:
        """Update income data"""
        if output_dir is None:
            output_dir = os.path.join(self.config.data_dir, "processed")
        
        if input_file:
            old_df = self.storage.load_existing(input_file)
        else:
            default_path = os.path.join(output_dir, f"{self.config.income_filename}.parquet")
            old_df = self.storage.load_existing(default_path)
        
        existing_dates = self.storage.get_existing_dates(old_df)
        
        new_df = self.income_loader.download(date_from, date_to, existing_dates)
        
        if new_df.empty:
            print("No new income data to add")
            return {"status": "no_update", "files": []}
        
        merged_df = self.storage.merge_data(old_df, new_df)
        
        base_path = os.path.join(output_dir, self.config.income_filename)
        saved_files = self.storage.save_local(merged_df, base_path)
        
        # Create zip files for each format
        zip_files = self.storage.create_zip_files(saved_files)
        
        if s3_folder:
            ver = version or self._get_version()
            for f in zip_files:
                self.storage.upload_to_s3(f, s3_folder, ver)
        
        return {
            "status": "updated",
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
        
        if input_file:
            old_df = self.storage.load_existing(input_file)
        else:
            default_path = os.path.join(output_dir, f"{self.config.expense_filename}.parquet")
            old_df = self.storage.load_existing(default_path)
        
        existing_dates = self.storage.get_existing_dates(old_df)
        
        new_df = self.expense_loader.download(date_from, date_to, existing_dates)
        
        if new_df.empty:
            print("No new expense data to add")
            return {"status": "no_update", "files": []}
        
        merged_df = self.storage.merge_data(old_df, new_df)
        
        base_path = os.path.join(output_dir, self.config.expense_filename)
        saved_files = self.storage.save_local(merged_df, base_path)
        
        # Create zip files for each format
        zip_files = self.storage.create_zip_files(saved_files)
        
        if s3_folder:
            ver = version or self._get_version()
            for f in zip_files:
                self.storage.upload_to_s3(f, s3_folder, ver)
        
        return {
            "status": "updated",
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

