from flask import Flask, request, render_template, redirect, session, jsonify
from flask_cors import CORS  # CORS 라이브러리 임포트
from dotenv import load_dotenv
import openai
import pandas as pd
import os
import sqlite3
import logging

load_dotenv()
app = Flask(__name__)

CORS(app, supports_credentials=True)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#Setting log file
# 로그 설정
logging.basicConfig(filename='app.log', level=logging.DEBUG)

#Setting secret key for Session
app.secret_key = 'dlwndud124@'

#Setting options for DB(SQLAlchemy)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Basic db class
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.String, nullable=False)
    bot_response = db.Column(db.String, nullable=False)
    sources = db.Column(db.String, nullable=True)

#Extracting userdata
user_df = pd.read_csv("/home/ubuntu/chat_stat_question/users.csv")
users = dict(zip(user_df['username'],user_df['password']))

#.env로부터 API KEY 획득
openai.api_key = os.getenv('OPENAI_API_KEY')

#기본 파라미터 설정
MODEL = 'gpt-3.5-turbo'
TEMPERATURE = 0.0
MAX_TOKENS = 4096


# Basic function
# 기본 함수: context의 메시지가 최대 길이를 초과했는지 확인하는 코드
def check_tokens(items):
    cnt = 0

    if items is None:
        return cnt

    for item in items:
        cnt += len(item['content'])

    return cnt

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/summary')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login() :
    if request.method == 'POST' :
        username = request.form['username']
        password = int(request.form['password'])

        if username in users and users[username] == password :
            session['username'] = username
	
            return redirect('/summary') 
        else:
            return '''
            <script>
                alert("올바른 ID와 비밀번호를 입력해주세요.");
                window.location.href = '/login';
            </script>
            '''
    else :
        return render_template('login.html')


@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'username' not in session:
        return redirect('/login')

    name = session.get('username')
    if request.method == 'POST':
        # JSON 데이터 접근
        data = request.get_json()

        # Checking messages
        message = data['question'][-1]

        full_message = message
        context = []
        if len(context) == 0:
            context.append({"role": "system", "content": "You are a helpful elementary school teacher."})
            context.append({"role": "user", "content": "You are going to provide feedback with specific explanation and easy words."})
            context.append({"role": "user", "content": full_message})
        else :
            context.append({"role": "user", "content": full_message})

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=context,
            temperature=TEMPERATURE
        )

        answer = response['choices'][0]['message']['content']

        # 데이터베이스에 저장
        chat_history_entry = ChatHistory(user_message=message, bot_response=answer, sources=name)
        db.session.add(chat_history_entry)
        db.session.commit()


        #대화 목록에 추가
        context.append({'role': 'assistant', 'content': answer})

        return {'response' : answer }

    else :
        return render_template('summary.html')
    

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    if 'username' not in session:
        return redirect('/login')

    name = session.get('username')
    if request.method == 'POST':
        # JSON 데이터 접근
        data = request.get_json()

        # Checking messages
        message = data['question'][-1]

        full_message = message
        context = []
        if len(context) == 0:
            context.append({"role": "system", "content": "You are a helpful elementary school teacher."})
            context.append({"role": "user", "content": "You are going to provide feedback with specific explanation and easy words."})
            context.append({"role": "user", "content": full_message})
        else :
            context.append({"role": "user", "content": full_message})

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=context,
            temperature=TEMPERATURE
        )

        answer = response['choices'][0]['message']['content']

        # 데이터베이스에 저장
        chat_history_entry = ChatHistory(user_message=message, bot_response=answer, sources=name)
        db.session.add(chat_history_entry)
        db.session.commit()


        #대화 목록에 추가
        context.append({'role': 'assistant', 'content': answer})

        return {'response' : answer }

    else :
        return render_template('compare.html')

    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/history')
def get_history():
    history = ChatHistory.summary.all()
    return render_template('history.html', chat_history=history)


#@app.route('/history')
#def history():
#    with sqlite3.connect(DATABASE) as conn:
#        cursor = conn.cursor()
#        cursor.execute("SELECT * FROM ChatHistory")
#        chat_history = cursor.fetchall()
#    return render_template('history.html', chat_history=chat_history)


if __name__ == '__main__':
    app.run(debug=True)
