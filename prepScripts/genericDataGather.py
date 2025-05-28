import pandas as pd
import argparse
from newspaper import Article
from transformers import GPT2TokenizerFast
import time

# Load the GPT2 tokenizer to count tokens in text (used later to limit or filter text length)
tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

def scrapeArticleText(links):
    """
    Given a list of article URLs, this function downloads and parses each article,
    extracting the title and full text, then returns a DataFrame with the results.
    """
    articleDf = pd.DataFrame(columns=["title", "articleText"])

    for link in links:
        article = Article(link)
        article.download()  # Fetch the article HTML
        article.parse()     # Extract and structure the article content

        rowDict = {
            "title": article.title,
            "articleText": article.text,
            "articleLink": link
        }
        # Append the new row to the dataframe
        articleDf = pd.concat([articleDf, pd.DataFrame([rowDict])], ignore_index=True)

    return articleDf

def splitByParagraph(articlesDf):
    """
    Splits the article text into paragraphs, filters out short and empty ones,
    and counts tokens in each paragraph. Long paragraphs are truncated to 500 tokens.
    """
    # Split the text of each article into a list of paragraphs by newline
    articlesDf = articlesDf.assign(articleText=articlesDf['articleText'].str.split('\n')).explode('articleText')

    # Remove any empty strings or whitespace-only paragraphs
    articlesDf = articlesDf[articlesDf['articleText'].str.strip() != '']

    # Drop rows with missing values and reset the index
    articlesDf = articlesDf.reset_index(drop=True).dropna()

    # Count the number of tokens in each paragraph
    articlesDf['numTokens'] = articlesDf['articleText'].apply(count_tokens)

    # Truncate paragraphs longer than 500 tokens
    articlesDf.loc[articlesDf['numTokens'] > 500, 'articleText'] = \
        articlesDf.loc[articlesDf['numTokens'] > 500, 'articleText'].apply(lambda x: reduceLong(x))

    # Remove very short paragraphs (fewer than 5 tokens)
    rows_to_drop = articlesDf[articlesDf['numTokens'] < 5].index
    articlesDf.drop(rows_to_drop, inplace=True)

    # Reset index again after filtering
    articlesDf = articlesDf.reset_index(drop=True)

    return articlesDf

def count_tokens(text):
    """
    Returns the number of tokens in a given text using the GPT2 tokenizer.
    """
    tokens = tokenizer.encode(text)
    return len(tokens)

def reduceLong(text):
    """
    Truncates a text to the first 500 tokens to ensure length consistency.
    """
    tokens = tokenizer.encode(text)
    reduced_tokens = tokens[:500]
    return tokenizer.decode(reduced_tokens)

def main():
 
    start_time = time.time()  

    # Setup command line arguments
    parser = argparse.ArgumentParser(description='Scrape articles and split into paragraphs.')
    parser.add_argument('-i', '--input', required=True, help='Input CSV file with article links')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file for split paragraphs')
    args = parser.parse_args()

    # Read the list of article links from the input file (assumes no header row)
    df = pd.read_csv(args.input, header=None)
    linkList = df[0].tolist()

    # Scrape and process articles 
    allArticles = scrapeArticleText(linkList)
    
    # Split article text into individual paragraphs and process
    articlesSplitByParagraphDf = splitByParagraph(allArticles)

    # Set the row index as a unique ID and save the result to a CSV file
    articlesSplitByParagraphDf.index.name = 'uniqueId'
    articlesSplitByParagraphDf.to_csv(args.output)

    # End timer and print runtime
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nTotal runtime: {elapsed_time:.2f} seconds")


if __name__ == '__main__':
    main()