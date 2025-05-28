from app import app
from flask import render_template, flash, redirect, session, url_for, request, Response
from app.forms import ChatForm, PasswordForm
from chat import setupChat, answer_query_with_context
import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import deque
import pickle
import os

# Embeddings will be initialized after login
document_embeddings = None
df = None

def ensure_loaded():
    global document_embeddings, df
    if document_embeddings is None:
        document_embeddings = setupChat()
    if df is None:
        with open(app.config['ARTICLES_FILE'], "rb") as f:
            f.seek(0)
            loaded_df = pickle.load(f)
            df = loaded_df.set_index(["uniqueId"])

@app.before_request
def check_session():
    """
    Middleware to check session age and reset it if older than 1 hour.
    This ensures inactive users are logged out and session data is cleared.
    """
    last_activity = session.get('last_activity')
    if last_activity and datetime.now(timezone.utc) > last_activity + timedelta(hours=1):
        session.clear()
    session['last_activity'] = datetime.now(timezone.utc)

@app.route('/')
def home():
    """
    Redirects to the password page.
    """
    return redirect(url_for('password'))

@app.route('/password', methods=['GET', 'POST'])
def password():
    """
    Password gate to access the chatbot.
    Loads embeddings and initializes session state upon successful login.
    """
    global document_embeddings  # Access the shared variable to store embeddings

    form = PasswordForm()

    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data

        # Check if password matches the environment variable
        if password == os.getenv("CHAT_PASSWORD"):
            session.clear() 
            session['logged_in'] = True
            document_embeddings = setupChat()
            session['fullChat'] = [] 

            return redirect(url_for('chatRoute'))
        else:
            flash('Invalid password')

    return render_template('index.html', form=form)

@app.route('/chat', methods=['GET', 'POST'])
def chatRoute():
    """
    The main chat route, which handles conversation flow and response rendering.
    Manages session-based chat history and query-response threading.
    """

    ensure_loaded()

    context = "No Context Yet"
    prompt = "No prompt Yet"
    uniqueLinks = []
    followupSuggestions = []

    if session.get('logged_in'):
        # Retrieve session-persistent chat state
        chatHistory = session.get('chatHistory', [])
        previousChat = session.get('previousChat', [])
        previousChatNew = session.get('previousChatNew', [])
        justQuestions = session.get('justQuestions', [])
        fullChat = session.get('fullChat', []) 

        form = ChatForm()

        if form.reset.data:
            # Reset all session-based chat states when Reset is clicked
            session["chatHistory"] = []
            session["previousChat"] = []
            session["previousChatNew"] = []
            session["justQuestions"] = []
            session["fullChat"] = [] 

            # Clear local copies too
            chatHistory = []
            previousChat = []
            previousChatNew = []
            justQuestions = []

            return redirect(url_for('chatRoute'))

        if request.method == 'POST' and form.export.data:
            export_text = "\n".join(fullChat)
            return Response(
                export_text,
                mimetype='text/plain',
                headers={'Content-Disposition': 'attachment;filename=chat_export.txt'}
            )

        if form.validate_on_submit():
            # Get the user's new question
            question = form.questionText.data
            chatHistory.append(question)
            justQuestions.append(question)

            # Get AI-generated answer and sources using contextual retrieval
            answer, answerWithSource, context, prompt, uniqueLinks = answer_query_with_context(
                list(previousChat), list(previousChatNew), question, justQuestions, df, document_embeddings
            )

            answerDisplay = "\n" + answerWithSource + "\n"

            # Store user and assistant turns for the prompt
            questionNew = "\n Question: {} {}\n".format(question, " ")
            previousChatNew.append({'role': 'user', 'content': questionNew})
            previousChatNew.append({'role': 'assistant', 'content': answer})

            # Save a simplified QA history as well
            previousChat.append("Q: " + question)
            previousChat.append("A: " + answer)

            fullChat.append("Q: " + question)       
            fullChat.append("A: " + answer)        

            if answer.strip().lower() != "sorry i don't know the answer to that question.":
                followupSuggestions = get_followup_questions(answer)
            else:
                followupSuggestions = []
                answerWithSource = answer  

            # Clear the form input
            form.questionText.data = None

            # Add answer to chat display history
            chatHistory.append(answerDisplay)

            # Limit stored session history to prevent large cookie sizes
            max_history = 10
            chatHistory = chatHistory[-max_history:]
            previousChat = previousChat[-max_history:]
            previousChatNew = previousChatNew[-max_history:]
            justQuestions = justQuestions[-3:]

            # Save updated state to session
            session["chatHistory"] = chatHistory
            session["previousChat"] = previousChat
            session["previousChatNew"] = previousChatNew

            # added this aswell
            session["justQuestions"] = justQuestions
            session["fullChat"] = fullChat  

        # Render chat page with current state and form
        return render_template(
            'chat.html',
            form=form,
            chatHistory=chatHistory,
            context=context,
            prompt=prompt,
            previousChat=justQuestions,
            previousChatNew=previousChatNew,
            uniqueLinks=uniqueLinks,
            fullChat=fullChat,
            followupSuggestions=followupSuggestions  
        )

    else:
        # Redirect to login if user isn't authenticated
        return redirect(url_for('password'))

def get_followup_questions(answer, model="gpt-4o-mini"):
    """
    Generate suggested follow-up questions based on the assistant's answer.
    """
    try:
        client = app.config.get('OPENAI_CLIENT')
        if not client:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

        prompt = f"""You are a helpful assistant. Based on the following answer, suggest 3 short and relevant follow-up questions a curious user might ask next.

Answer:
\"\"\"
{answer}
\"\"\"

List only the follow-up questions, each on its own line."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )

        suggestions = response.choices[0].message.content.strip().split("\n")
        return [s.lstrip("0123456789. ").strip() for s in suggestions if s.strip()]
    except Exception as e:
        app.logger.error(f"Error generating follow-up questions: {e}")
        return []
