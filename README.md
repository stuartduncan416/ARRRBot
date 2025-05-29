# chatbot
A Flask chatbot application, designed with small newsrooms in mind, that uses the OpenAI API to answer user questions drawing upon information contained in a provided knowledge base of news articles.

The code created as part of this project can be broadly classified into two parts, the scripts that prepare article data for use in the chatbot (contained within the prepScripts directory), and the Flask project files for that chatbot tool itself (contained within the chatbotTool directory). 

# Implementation Details

The video below explains how to deploy the chatbot using the PythonAnywhere hosting service. A concise overview of the process is also included on this page.

This implementation requires the following:
* Python 3.8 or later installed on your local computer
* The preparation scripts and Flask application files from this repository
* An OpenAI account with an active API key
* A PythonAnywhere account (free or paid)
* An FTP client for file transfers

Helpful resources:
* [How To Get An OpenAI API Key](https://youtu.be/SzPE_AE0eEo?si=jf9D8ok9w3QPSQ-c)
* [How to Install Python on Your System](https://realpython.com/installing-python/)
* [PythonAnywhere](https://www.pythonanywhere.com/)
* [How to Use and Setup the FileZilla FTP Client](https://youtu.be/0DpnTp9QeHU?si=0QupsvV_sdMp5yud)
* [Download the FileZilla FTP Client](https://filezilla-project.org/download.php?type=client)

## Implementation Overview

### Prepare Your Article data

The data gatherer script [genericDataGather.py](https://github.com/stuartduncan416/chatbot/blob/main/prepScripts/genericDataGather.py), gathers article data from news websites and outputs a CSV file of your article data to be used for creating embeddings. 

1. Create a text file with one article URL per line, similar to [uniqueLinksSample.csv](https://github.com/stuartduncan416/chatbot/blob/main/prepScripts/uniqueLinksSample.csv)
2. Install the required dependencies if needed:\
`pip install newspaper3k`\
`pip install pandas`\
`pip install transformers`
3. Run the script specifiying the article url text file created in step one, and your desired output CSV filename:\
`python genericDataGather.py -i yourArticleList.txt -o yourArticles.csv`


