# mt-whiteboard

```bash
python3 -m venv venv
source venv/bin/activate

conda activate chat-whiteboard

pip install -r requirements.txt
python3 app.py
```

Azure conifg:

```bash
gunicorn app:app --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker
```
