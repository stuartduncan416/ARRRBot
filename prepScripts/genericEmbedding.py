import argparse                
import openai                  
import pandas as pd            
import pickle                 
import time                    
import os                     
from openai import OpenAI    
import time  

# Set the OpenAI model to be used for embedding generation
EMBEDDING_MODEL = "text-embedding-3-large"

# Initialize the OpenAI client with an API key
client = OpenAI(
    api_key="YOUR OPEN AI KEY HERE",  # Replace with your own key
)

# Function to get the embedding for a given text using OpenAI's embedding API
# Includes retry logic for rate limits, API errors, and network issues
def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    try:
        # Make API call to get embedding
        result = client.embeddings.create(
            model=model,
            input=text
        )
        return result.data[0].embedding

    # Handle rate limit errors by waiting and retrying
    except openai.RateLimitError as e:
        retry_time = e.retry_after if hasattr(e, 'retry_after') else 30
        print(f"Rate limit exceeded. Retrying in {retry_time} seconds...")
        time.sleep(retry_time)
        return get_embedding(text)

    # Handle general API errors
    except openai.APIError as e:
        retry_time = e.retry_after if hasattr(e, 'retry_after') else 30
        print(f"API error occurred. Retrying in {retry_time} seconds...")
        time.sleep(retry_time)
        return get_embedding(text)

    # Handle connection-related errors
    except openai.APIConnectionError as e:
        retry_time = 10
        print(f"Service is unavailable. Retrying in {retry_time} seconds...")
        time.sleep(retry_time)
        return get_embedding(text)

    # Handle request timeout errors
    except openai.APITimeoutError as e:
        retry_time = 10
        print(f"Request timed out: {e}. Retrying in {retry_time} seconds...")
        time.sleep(retry_time)
        return get_embedding(text)

    # Handle OS-related errors (e.g., network down)
    except OSError as e:
        retry_time = 10
        print(f"Connection error occurred: {e}. Retrying in {retry_time} seconds...")
        time.sleep(retry_time)
        raise e  # Raise after retry attempt to stop infinite loop if persistent

# Compute embeddings for all rows in a DataFrame
# Returns a dictionary mapping each index to its corresponding embedding vector
def compute_doc_embeddings(df: pd.DataFrame) -> dict[tuple[str, str], list[float]]:
    return {
        idx: get_embedding(r.articleText) for idx, r in df.iterrows()
    }


if __name__ == "__main__":

    start_time = time.time()  

    # Setup command line arguments
    parser = argparse.ArgumentParser(description="Generate document embeddings from CSV.")
    parser.add_argument("-i", "--input", required=True, help="Input CSV file (e.g., newsplit.csv)")
    args = parser.parse_args()

    # Extract input filename from arguments
    input_csv = args.input

    # Derive base name for output files
    base_name = os.path.splitext(os.path.basename(input_csv))[0]
    original_pkl = f"{base_name}.pkl"                # Save original CSV data
    merged_pkl = f"embeddings_{base_name}.pkl"       # Save data with embeddings

    # Read the input CSV into a pandas DataFrame
    print(f"Reading {input_csv}...")
    df = pd.read_csv(input_csv)

    # Save the original DataFrame as a pickle file for faster future loading
    with open(original_pkl, "wb") as f:
        pickle.dump(df, f)
    print(f"Saved {original_pkl}")

    # Generate embeddings for each article in the dataset
    print("Generating embeddings...")
    document_embeddings = compute_doc_embeddings(df)

    # Convert the dictionary of embeddings to a DataFrame and align it for merging
    embedDf = pd.DataFrame(document_embeddings).T
    embedDf.index.name = df.index.name  # Ensure index names match to allow merging

    # Merge the embeddings with the original DataFrame
    mergedDf = pd.merge(df, embedDf, left_index=True, right_index=True)

    # Drop columns that are no longer needed for the merged output
    mergedDf = mergedDf.drop(columns=['numTokens', 'articleText'], errors='ignore')

    # Save the merged DataFrame with embeddings to a pickle file
    with open(merged_pkl, "wb") as f:
        pickle.dump(mergedDf, f)
    print(f"Saved {merged_pkl}")

    # End timer and print runtime
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nTotal runtime: {elapsed_time:.2f} seconds")