import pandas as pd
from src.preprocessing import run_pipeline_preprocessing

def test_preprocessing_outlier_keep():
    """Verify that outlier_strategy='keep' preserves all rows and returns correct structure."""
    raw_data = pd.DataFrame({
        'CustomerID': [1, 2, 3, 4],
        'Recency': [10, 20, 999, 40],
        'Frequency': [1, 5, 10, 1000],
        'Monetary': [100.0, 500.0, 1000.0, 500000.0]
    })
    
    result = run_pipeline_preprocessing(raw_data, outlier_strategy="keep")
    
    assert len(result["processed_df"]) == len(raw_data)
    assert result["processed_df"].isnull().sum().sum() == 0