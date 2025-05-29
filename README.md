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

### Prepare the Document Embeddings

The embedding script [genericEmbedding.py](https://github.com/stuartduncan416/chatbot/blob/main/prepScripts/genericEmbedding.py), prepares the article data from the data gathering script for text comparison. 

1. Install the required dependencies if needed:\
`pip install pandas` (which should already be installed)\
`pip install openai`
2. Add your OpenAI key to [genericEmbedding.py](https://github.com/stuartduncan416/chatbot/blob/main/prepScripts/genericEmbedding.py) 
3. Run the script specifying the CSV file you created with the article data script as an input file\
`python genericEmbedding.py -i yourArticles.csv`

If run successfully, two pickle files should be saved in the directory you ran the script from: yourArticles.pkl and embeddings_yourArticles.pkl

### Flask Application Setup

The Flask application developed for this project encompassed the core functionality of the chatbot prototype, including the user interface, the construction of conversational prompts, and the integration with OpenAI’s API. The process below outlines how to setup the application on a PythonAnywhere hosting account. 

1. Login into your PythonAnywhere account
2. Open a bash console
3. Create a directory for your chatbot application using this command in the bash console:\
`mkdir myChatbot`
4. On version of the Flask project downloaded to your computer edit the file paths for the embeddings within the [config.py](https://github.com/stuartduncan416/chatbot/blob/main/chatbotTool/config.py). Assuming your static files would live in a static directory of the root directory of your project file (something like /home/yourusername/myChatbot/static/) this section of code would look as follows:
```
# File paths
ARTICLES_FILE = "static/yourArticles.pkl"
EMBEDDINGS_FILE = "static/embeddings_yourArticles.pkl"
```
5. Create a .env file, similar to this [sample file](https://github.com/stuartduncan416/chatbot/blob/main/chatbotTool/SAMPLE.env) and place this in the root directory of your Flask project on your local computer
6. Edit the values in this .env file to match your OpenAI key and your desired password for your chatbot. Note that OpenAI API key is not contained in quotes in this file, but your password is
7. Returning to your bash console in the PythonAnywhere dashboard, create a virtual environment for your project, using the following command:\
`mkvirtualenv --python=/usr/bin/python3.8 chatbotEnv`
8. Your virtual environment should be now be running, and you should see the name of your virtual environment at the beginning of the console prompt
9. Within your virtual environment install the following Python libraries:\
`pip install numpy`\
`pip install pandas`\
`pip install tiktoken`\
`pip install flask`\
`pip install -U Flask-WTF`\
`pip install openai`\
`pip install python-dotenv`\
`pip install Flask-Session`
10. In your Flask project root directory create a directory called : flask_session You could do this with the following command :\
`mkdir -p /home/yourusername/myChatbot/flask_session`
11. In your Flask project root directory also create a directory called : static You could do this with the following command :\
`mkdir -p /home/yourusername/myChatbot/static`
12. Using your FTP client, upload your two pickle files to this static directory
13. On the PythonAnywhere dashboard create a web app
14. Select a manual installation
15. Select Python 3.8 as your Python version
16. On the configuration page for your web app change the following settings:
  - In the virtualenv section, enter the name of your virtualenv, in this case : chatbotEnv
  - Set the working directory to your project root directory, in this case : /home/yourusername/myChatbot/
  - Set the static files URL to /static/ and the static directory to your specfied static directory in this case: /home/yourusername/myChatbot/static/
  - Open the WSGI configuration file by clicking on it in the code section, erase everything in it and put it code similar to this:\
```
import sys
import os
from dotenv import load_dotenv
project_folder = os.path.expanduser('~/myChatbot')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

path = '/home/yourusername/myChatbot/'

if path not in sys.path:
   sys.path.insert(0, path)

from chatbot import app as application
```
17. Reload your web app, by clicking on the green reload button at the top of web app configuration page
18. If everything has worked, you should be able to visit the url of your web application, and see the working chatbot. You will be able to login with the password specified in your .env file

    
    









