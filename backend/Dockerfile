FROM python:3.11-slim

WORKDIR /app

COPY ./app /app/app

RUN pip install fastapi uvicorn pymysql sqlalchemy cryptography email-validator passlib[bcrypt]==1.7.4 bcrypt==3.2.2 python-jose[cryptography]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]