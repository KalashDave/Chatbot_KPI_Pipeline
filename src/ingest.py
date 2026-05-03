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
    # Load environment variables from the .env file into the system environment.
    # This is necessary to securely access the HF_TOKEN without hardcoding it.
    load_dotenv()
    
    # Retrieve the Hugging Face access token from the environment variables.
    hf_token = os.getenv("HF_TOKEN")
    
    # Ensure the token exists before proceeding, otherwise raise an error 
    # to prevent silent failures during the dataset download.
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment variables. Please check your .env file.")
    
    # Authenticate with the Hugging Face Hub using the retrieved token.
    print("Logging into Hugging Face...")
    login(token=hf_token)
    
    print("Downloading 'bitext/Bitext-customer-support-llm-chatbot-training-dataset'...")
    # Load the specific dataset from Hugging Face.
    # We specify split="train" because this dataset only contains a training split,
    # which we will use as our primary dummy data source.
    dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
    
    # Print the total number of records successfully downloaded.
    print(f"Dataset downloaded! Number of records: {len(dataset)}")
    
    # Convert the Hugging Face Dataset object into a pandas DataFrame.
    # Pandas is required for the downstream feature engineering and KPI calculations.
    df = dataset.to_pandas()
    
    # Print the shape (rows, columns) of the resulting DataFrame to confirm conversion.
    print(f"Successfully converted to Pandas DataFrame. Shape: {df.shape}")
    
    # Return the raw DataFrame to be used by the processing script.
    return df

if __name__ == "__main__":
    # The following block only runs if this script is executed directly (e.g., `python src/ingest.py`).
    # It serves as a local test to verify the ingestion pipeline works correctly.
    df = ingest_data()
    print("\nSample Data:")
    # Print the first 3 rows of the DataFrame to quickly inspect the ingested data.
    print(df.head(3))
