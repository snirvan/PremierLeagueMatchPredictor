#!/usr/bin/env python3
"""
Remove BZ column and any columns that appear after it in the dataset.
This script cleans up unwanted columns from the matches dataset.
"""

import pandas as pd
import os
from datetime import datetime

def remove_bz_and_after_columns(csv_file):
    """Remove BZ column and any columns after it"""
    print(f"📂 Loading {csv_file}...")
    
    # Load the dataset
    df = pd.read_csv(csv_file)
    
    print(f"📊 Original dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Check if BZ column exists
    if 'BZ' not in df.columns:
        print("ℹ️  BZ column not found in dataset")
        return
    
    # Find the position of BZ column
    bz_index = df.columns.get_loc('BZ')
    print(f"🔍 Found BZ column at position {bz_index}")
    
    # Get columns to remove (BZ and everything after it)
    columns_to_remove = df.columns[bz_index:].tolist()
    print(f"🗑️  Removing {len(columns_to_remove)} columns:")
    for i, col in enumerate(columns_to_remove):
        print(f"  {i+1}. {col}")
    
    # Create backup
    backup_file = f"{csv_file}.backup_remove_bz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    df.to_csv(backup_file, index=False)
    print(f"💾 Backup created: {backup_file}")
    
    # Remove the columns
    df_cleaned = df.drop(columns=columns_to_remove)
    
    print(f"✨ Cleaned dataset: {df_cleaned.shape[0]} rows, {df_cleaned.shape[1]} columns")
    
    # Save the cleaned dataset
    df_cleaned.to_csv(csv_file, index=False)
    print(f"✅ Updated {csv_file}")
    
    print(f"\n📋 Remaining columns ({len(df_cleaned.columns)}):")
    for i, col in enumerate(df_cleaned.columns, 1):
        print(f"  {i:3d}. {col}")

def main():
    """Main execution function"""
    print("🚀 Starting BZ column removal process\n")
    
    # Target file
    target_file = "matches_features_with_balance.csv"
    
    if not os.path.exists(target_file):
        print(f"❌ Error: {target_file} not found!")
        return
    
    # Remove BZ and subsequent columns
    remove_bz_and_after_columns(target_file)
    
    print("\n✅ BZ column removal completed!")

if __name__ == "__main__":
    main()
