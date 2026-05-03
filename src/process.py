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
    
    This function effectively simulates the missing telemetry data (like handling
    times, satisfaction scores, and resolution status) that a real chatbot system
    would automatically generate.
    """
    print("Engineering features...")
    # Set a fixed random seed so that every time we run the pipeline, 
    # we generate the exact same synthetic numbers. This is crucial for testing.
    np.random.seed(42)  
    
    # Store the total number of rows in the dataframe for sizing our generated arrays.
    n = len(df)
    
    # --- 1. Time Metrics & AHT (Average Handling Time) ---
    # Benchmark: A standard chat usually lasts 2-5 minutes.
    # First, generate realistic timestamps over the last 30 days.
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Generate random seconds within the 30 day window to create scattered timestamps.
    random_seconds = np.random.randint(0, int((end_date - start_date).total_seconds()), size=n)
    df['timestamp'] = [start_date + timedelta(seconds=int(s)) for s in random_seconds]
    df['timestamp'] = df['timestamp'].dt.round('s') # Round to nearest second for clean display.
    
    # Generate Average Handling Time (AHT) using a normal distribution.
    # Center around 480 seconds (8 mins) with a standard deviation of 150 seconds.
    df['average_handling_time'] = np.random.normal(480, 150, size=n)
    # Clip extreme outliers so the minimum time is 2 minutes (120s) and max is 25 minutes (1500s).
    df['average_handling_time'] = np.clip(df['average_handling_time'], 120, 1500).round(1)
        
    # --- 2. User Tracking (Return Visitors) ---
    # Benchmark: Good chatbots have a > 30% return visitor rate.
    # We simulate this by defining fewer unique users than total chats (65% ratio).
    num_unique_users = int(n * 0.65)
    user_ids = [f"USR_{i:05d}" for i in range(num_unique_users)]
    
    # Create a weighted probability array so that some users are "power users" (return frequently).
    probs = np.ones(num_unique_users)
    probs[:int(num_unique_users * 0.35)] = 3  # The first 35% of users are 3x more likely to chat.
    probs = probs / probs.sum() # Normalize probabilities so they sum to 1.
    
    # Assign a user ID to every chat based on our weighted probabilities.
    df['user_id'] = np.random.choice(user_ids, size=n, p=probs)
    
    # --- 3. Fallback Rate ---
    # Benchmark: A well-trained model should fail less than 10% of the time.
    # We generate a boolean column where ~6% of chats result in a fallback (AI confusion).
    df['is_fallback'] = np.random.binomial(1, 0.06, size=n) == 1
    
    # --- 4. Human Takeover Rate ---
    # Benchmark: Standard takeover rate is < 25%.
    # If the AI experiences a fallback, it's highly likely (80%) the human takes over.
    # If the AI understands perfectly, the human rarely takes over (15%).
    def takeover_prob(fallback):
        return 0.8 if fallback else 0.15
    # Apply the logic line-by-line to generate the boolean column.
    df['human_takeover'] = np.random.binomial(1, [takeover_prob(f) for f in df['is_fallback']]) == 1
    
    # --- 5. Resolution Rate (First Contact Resolution - FCR) ---
    # Benchmark: Should be > 65%.
    # If a human had to take over, resolution chances drop slightly (40%) because it's a hard issue.
    # If the AI handled it alone, resolution is usually high (85%).
    def resolution_prob(takeover):
        return 0.4 if takeover else 0.85
    df['is_resolved'] = np.random.binomial(1, [resolution_prob(t) for t in df['human_takeover']]) == 1
    
    # --- 6. Quality Metrics (CSAT Score) ---
    # Benchmark: > 80% positive (4 or 5 stars).
    def generate_csat(resolved, fallback):
        # If resolved smoothly, the user gives mostly 4s and 5s.
        if resolved and not fallback:
            return np.random.choice([1, 2, 3, 4, 5], p=[0.02, 0.03, 0.05, 0.30, 0.60])
        # If not resolved, the user is angry and gives mostly 1s and 2s.
        elif not resolved:
            return np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.30, 0.20, 0.05, 0.05])
        # If resolved but there was friction (fallback), user gives mediocre ratings (3s and 4s).
        else:
            return np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.15, 0.25, 0.30, 0.20])
            
    # Apply the CSAT logic across the entire dataset.
    df['csat_score'] = [generate_csat(r, f) for r, f in zip(df['is_resolved'], df['is_fallback'])]
    
    # --- 7. Conversion Rate ---
    # Benchmark: 5-15% of support chats lead to a conversion (sale, booking, etc).
    # We assign a flat 10% chance that the chat resulted in a conversion.
    df['converted'] = np.random.binomial(1, 0.10, size=n) == 1
    
    # --- 8. Ticket Deflection Rate ---
    # Benchmark: > 50%.
    # We assume 40% of all inquiries are complex enough that they would have required a support ticket.
    df['would_be_ticket'] = np.random.binomial(1, 0.40, size=n) == 1
    
    print("Feature engineering complete!")
    return df

if __name__ == "__main__":
    # Local testing block. Imports the ingest module, runs both steps, 
    # and prints a sample of the newly engineered KPI columns to verify correctness.
    from ingest import ingest_data
    print("--- Running Ingestion ---")
    raw_df = ingest_data()
    print("\n--- Running Processing ---")
    processed_df = process_data(raw_df)
    print("\nProcessed Data Sample (New KPIs):")
    print(processed_df[['is_fallback', 'human_takeover', 'is_resolved', 'csat_score', 'converted', 'would_be_ticket']].head())
