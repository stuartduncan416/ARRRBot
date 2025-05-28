import numpy as np
from openai import OpenAI, OpenAIError
import pandas as pd
import tiktoken
from app import app
from app.utils import benchmark
import pickle
import os

# Load configuration values from the Flask app's config
EMBEDDING_MODEL = app.config['EMBEDDING_MODEL']
SEPARATOR = app.config['SEPARATOR']
ENCODING = app.config['ENCODING']

# Initialize OpenAI client using API key from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Get tokenizer encoding and separator length for later token-based operations
encoding = tiktoken.get_encoding(ENCODING)
separator_len = len(encoding.encode(SEPARATOR))

def get_embedding(text, model: str = EMBEDDING_MODEL):
    """
    Send a text string to the OpenAI API to get its embedding vector.
    """
    result = client.embeddings.create(
        model=model,
        input=text,
    )
    return result.data[0].embedding

def load_embeddings(fname):
    """
    Load a pickled DataFrame containing document embeddings and return as a dictionary.
    Assumes the DataFrame contains a 'uniqueId' index and numerical columns for the embedding.
    """
    with open(fname, "rb") as f:
        f.seek(0)
        df = pickle.load(f)

    # Remove extra columns that are not needed for similarity calculations
    df = df.drop('title', axis=1)
    df = df.drop('articleLink', axis=1)

    # Identify columns that represent the embedding dimensions
    dim_cols = [col for col in df.columns if col != "uniqueId"]

    # Use 'uniqueId' as dictionary key and convert row vectors to lists
    df.set_index(["uniqueId"], inplace=True)
    embeddings_dict = df[dim_cols].apply(lambda row: row.tolist(), axis=1).to_dict()

    return embeddings_dict

@benchmark("setupChat")
def setupChat():
    """
    Load the article content and associated document embeddings.
    Returns the embeddings dictionary used to find relevant sections.
    """
    # Load articles from a pickle file
    with open(app.config['ARTICLES_FILE'], "rb") as f:
        f.seek(0)
        df = pickle.load(f)

    # Ensure DataFrame is indexed properly for lookups
    df.set_index(["uniqueId"], inplace=True)

    # Load corresponding document embeddings
    document_embeddings = load_embeddings(app.config['EMBEDDINGS_FILE'])

    return document_embeddings

def vector_similarity(x, y):
    """
    Compute cosine similarity (dot product) between two vectors.
    OpenAI embeddings are normalized, so cosine similarity == dot product.
    """
    return np.dot(np.array(x), np.array(y))

def order_document_sections_by_query_similarity(query, contexts):
    """
    Rank all document sections by their similarity to the user query.
    Returns a list of (similarity score, document ID) tuples, sorted high to low.
    """
    query_embedding = get_embedding(query)

    document_similarities = sorted([
        (vector_similarity(query_embedding, doc_embedding), doc_index) 
        for doc_index, doc_embedding in contexts.items()
    ], reverse=True)

    return document_similarities

@benchmark("construct_prompt")
def construct_prompt(previousChat, previousChatNew, question, context_embeddings, df, justQuestions):
    """
    Construct a prompt for the chatbot using the most relevant sections of documents.
    Adds a system message with context, followed by prior conversation history and the user query.
    Returns the prompt, context string, and unique source URLs.
    """

    messages = []

    # Concatenate last three user questions to improve context matching
    lastThreeQuestions = ' '.join(justQuestions[-3:])

    # Get ranked list of relevant sections
    most_relevant_document_sections = order_document_sections_by_query_similarity(lastThreeQuestions, context_embeddings)

    chosen_sections = []
    chosen_sections_len = 0
    chosen_sections_indexes = []
    chosenSectionLinks = []

    for docItem in most_relevant_document_sections:

        # Ensure the document section exists in DataFrame
        if docItem[1] in df.index:
            document_section = df.loc[docItem[1]]

            # Skip sections that are just questions (less useful for context)
            if str(document_section.articleText).endswith("?"):
                continue
            else:
                # Accumulate token count with separator length
                chosen_sections_len += int(document_section.numTokens) + separator_len

            # Stop if total length exceeds token limit
            if chosen_sections_len > 2000:
                break

            # Add section content and metadata
            chosen_sections.append(SEPARATOR + document_section.articleText.replace("\n", " "))
            chosenSectionLinks.append((document_section.articleLink, document_section.title))
            chosen_sections_indexes.append(str(docItem[1]))
        
    # Remove duplicate URLs while preserving order
    uniqueLinks = list(dict.fromkeys(chosenSectionLinks))

    # System-level instruction for the assistant
    header = """Answer the question based on the context below. If the answer is not contained in the context tags below, answer only 'Sorry I don't know the answer to that question.' and nothing else. Don't mention the context is in your answers. Your answer should be about 50 words and should be expert-level writing."""

    # Embed the chosen context into tags
    context = '<context> """\n{}"""\n </context>'.format("".join(chosen_sections))
    systemMessage = "{} {}".format(header, context)

    messages.append({"role": "system", "content": systemMessage})

    # Add prior conversation turns to the message history
    for item in previousChatNew:
        messages.append(item)

    # Format the current question
    questionNew = "\n Question: {} \n".format(question)
    messages.append({"role": "user", "content": questionNew})

    return (messages, context, uniqueLinks)

@benchmark("answer_query_with_context")
def answer_query_with_context(previousChat, previousChatNew, query, justQuestions, df, document_embeddings, show_prompt: bool = False):
    """
    Main function to answer a user query using context-aware information retrieval.
    Builds the prompt, queries OpenAI, and appends source links to the response.
    """
    uniqueLinks = []
    answerWithSource = ""

    # Generate prompt and get context for the query
    prompt, context, uniqueLinks = construct_prompt(previousChat, previousChatNew, query, document_embeddings, df, justQuestions)

    # Make a call to OpenAI's chat completion API
    response = client.chat.completions.create(
        model=app.config['COMPLETION_MODEL'],
        messages=prompt,
        max_tokens=app.config['MAX_TOKENS'],
        temperature=app.config['TEMPERATURE']
    )

    # If a confident answer is given, append source links
    if response.choices[0].message.content.strip(" \n") != "Sorry I don't know the answer to that question.":
        answerWithSource = response.choices[0].message.content.strip(" \n") + "<span class = 'sources'> Sources: "
        counter = 0
        for link, title in uniqueLinks[:5]:
            answerWithSource += f'<a href="{link}" target="_blank" class="source-link" title="{title}">{title}</a>'
        answerWithSource += "</span>"
    else:
        answerWithSource = response.choices[0].message.content.strip(" \n")

    # Return the plain answer, answer with sources, the context used, and the prompt
    return (response.choices[0].message.content.strip(" \n"), answerWithSource, context, prompt, uniqueLinks)