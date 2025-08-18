python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

python main.py

# 또는 FastAPI 서버 실행
uvicorn app.main:app --reload
