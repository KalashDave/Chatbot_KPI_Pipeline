"""
Script to pull data from Hugging Face
"""

import os
import pandas as pd
from dotenv import load_dotenv
from datasets import load_dataset
from huggingface_hub import login

def ingest_data() -> pd.DataFrame:
    """
    Loads the Bitext customer support dataset from Hugging Face
    and returns it as a pandas DataFrame.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the HF token
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment variables. Please check your .env file.")
    
    # Login to Hugging Face
    print("Logging into Hugging Face...")
    login(token=hf_token)
    
    print("Downloading 'bitext/Bitext-customer-support-llm-chatbot-training-dataset'...")
    # Load the dataset (using 'train' split as per the plan)
    dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
    
    print(f"Dataset downloaded! Number of records: {len(dataset)}")
    
    # Convert to pandas DataFrame
    df = dataset.to_pandas()
    print(f"Successfully converted to Pandas DataFrame. Shape: {df.shape}")
    
    return df

if __name__ == "__main__":
    # Test the ingestion function when the script is run directly
    df = ingest_data()
    print("\nSample Data:")
    print(df.head(3))
