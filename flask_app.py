from flask import (
    Flask, request, render_template, redirect, session, jsonify)
from flask_cors import CORS  # CORS 라이브러리 임포트
from dotenv import load_dotenv
import openai
import pandas as pd

load_dotenv()

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

#Setting secret key for Session
app.secret_key = 'dlwndud124@'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

#Setting options for DB(SQLAlchemy)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

CORS(app)

user_df = pd.read_csv("/home/jy9307/mysite/users.csv")
print(user_df)
users = dict(zip(user_df['username'],user_df['password']))

#.env로부터 API KEY 획득
openai.api_key = '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'

#기본 파라미터 설정
MODEL = 'gpt-3.5-turbo'
TEMPERATURE = 0.0
MAX_TOKENS = 4096



# Basic class
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.String, nullable=False)
    bot_response = db.Column(db.String, nullable=False)
    sources = db.Column(db.String, nullable=True)


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
        return redirect('/query')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login() :
    if request.method == 'POST' :
        username = request.form['username']
        password = int(request.form['password'])

        if username in users and users[username] == password :
            session['username'] = username
            return redirect('/query')
        else:
            return '''
            <script>
                alert("올바른 ID와 비밀번호를 입력해주세요.");
                window.location.href = '/login';
            </script>
            '''
    else :
        return render_template('login.html')


@app.route('/query', methods=['GET', 'POST'])
def query() :
    username = session.get('username')

    if request.method == 'POST':
        # JSON 데이터 접근
        data = request.get_json()

        # Checking messages
        message = data['question'][-1]

        # Define beginner
        beginner = """
    너는 통계적 탐구 문제에 대한 질문을 받고 이에 대한 피드백을 줄거야.
    피드백을 주는 기준은 다음과 같아.

    1. 관심 변수가 명확하고 사용 가능한가?
    2. 관심 대상 모집단이 명확한가?
      모집단/표본 상황이 아닌 경우라면, 관심 집단이 명확한가?
    3. 의도가 명확한가? 예를 들어, 질문이 요약/기술, 비교, 연관성 중 어떤 것인지 명확하게 드러나는가?
    4. 해당 데이터를 사용하여 질문에 답변할 수 있는가?
    5. 조사할 가치가 있고 흥미로우며 목적이 있는 질문인가?
    6. 전체 집단에 대한 분석이 가능한 질문인가?

    피드백을 제공할 탐구 문제는 다음과 같아.
"""
        full_message = beginner + message

        context = []
        if len(context) == 0:
            context.append({"role": "system", "content": "You are a helpful elementary school teacher. "})
            context.append({"role": "user", "content": "You are going to provide feedback with specific explanation and easy words."})
            context.append({"role": "user", "content": full_message})
        else:
            context.append({"role": "user", "content": full_message})

        response = openai.ChatCompletion.create(model=MODEL,
                                                    messages=context,
                                                    temperature=TEMPERATURE)

        answer = response['choices'][0]['message']['content']
        # sources = [item['metadata']['source'] for item in response.get('source_documents', [])]
        # sources_str = ', '.join(sources)

        # 데이터베이스에 저장
        chat_history_entry = ChatHistory(user_message=message, bot_response=answer, sources=username)
        db.session.add(chat_history_entry)
        db.session.commit()

        # 대화 목록에 추가
        context.append({'role': 'assistant', 'content': answer})

        return {'response' : answer }



    else :
        return render_template('query.html')



@app.route('/history', methods=['GET'])
def get_history():
    history = ChatHistory.query.all()
    result = []
    for entry in history:
        result.append({
            'id': entry.id,
            'user_message': entry.user_message,
            'bot_response': entry.bot_response,
            'sources': entry.sources
        })
    return jsonify(result)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
