"""
Script to engineer features and calculate KPIs
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw Hugging Face dataframe and adds synthetic
    operational KPIs to it, realistically tuned to match standard benchmarks.
    """
    print("Engineering features...")
    np.random.seed(42)  # For reproducibility
    n = len(df)
    
    # 1. Time Metrics & AHT (Benchmark: 2-5 min)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    random_seconds = np.random.randint(0, int((end_date - start_date).total_seconds()), size=n)
    df['timestamp'] = [start_date + timedelta(seconds=int(s)) for s in random_seconds]
    df['timestamp'] = df['timestamp'].dt.round('s')
    
    # Base AHT around 480 seconds (8 mins). Add variance.
    df['average_handling_time'] = np.random.normal(480, 150, size=n)
    df['average_handling_time'] = np.clip(df['average_handling_time'], 120, 1500).round(1)
        
    # 2. User Tracking (Return Visitor Rate Benchmark: > 30%)
    num_unique_users = int(n * 0.65)
    user_ids = [f"USR_{i:05d}" for i in range(num_unique_users)]
    probs = np.ones(num_unique_users)
    probs[:int(num_unique_users * 0.35)] = 3  # Return visitors are 3x more likely to be picked
    probs = probs / probs.sum()
    df['user_id'] = np.random.choice(user_ids, size=n, p=probs)
    
    # 3. Fallback Rate (Benchmark: < 10%)
    # Realistically ~6%
    df['is_fallback'] = np.random.binomial(1, 0.06, size=n) == 1
    
    # 4. Human Takeover Rate (Benchmark: < 25%)
    # Realistically ~20%. Correlated with fallbacks.
    def takeover_prob(fallback):
        return 0.8 if fallback else 0.15
    df['human_takeover'] = np.random.binomial(1, [takeover_prob(f) for f in df['is_fallback']]) == 1
    
    # 5. Resolution Rate (FCR) (Benchmark: > 65%)
    # Realistically ~75%. Correlated with takeover.
    def resolution_prob(takeover):
        return 0.4 if takeover else 0.85
    df['is_resolved'] = np.random.binomial(1, [resolution_prob(t) for t in df['human_takeover']]) == 1
    
    # 6. Quality Metrics (CSAT Score Benchmark: > 80% positive)
    def generate_csat(resolved, fallback):
        if resolved and not fallback:
            return np.random.choice([1, 2, 3, 4, 5], p=[0.02, 0.03, 0.05, 0.30, 0.60])
        elif not resolved:
            return np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.30, 0.20, 0.05, 0.05])
        else: # resolved but had fallback/friction
            return np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.15, 0.25, 0.30, 0.20])
            
    df['csat_score'] = [generate_csat(r, f) for r, f in zip(df['is_resolved'], df['is_fallback'])]
    
    # 7. Conversion Rate (Benchmark: 5-15%)
    # Let's say ~10%.
    df['converted'] = np.random.binomial(1, 0.10, size=n) == 1
    
    # 8. Ticket Deflection Rate (Benchmark: > 50%)
    # 40% of all inquiries are complex enough to have been a ticket.
    df['would_be_ticket'] = np.random.binomial(1, 0.40, size=n) == 1
    
    print("Feature engineering complete!")
    return df

if __name__ == "__main__":
    from ingest import ingest_data
    print("--- Running Ingestion ---")
    raw_df = ingest_data()
    print("\n--- Running Processing ---")
    processed_df = process_data(raw_df)
    print("\nProcessed Data Sample (New KPIs):")
    print(processed_df[['is_fallback', 'human_takeover', 'is_resolved', 'csat_score', 'converted', 'would_be_ticket']].head())
