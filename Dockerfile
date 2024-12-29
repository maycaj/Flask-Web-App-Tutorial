FROM python:3.8-slim
WORKDIR /Flask-Web-App-Tutorial
COPY . .
RUN pip install -r requirements.txt openai gunicorn
ENV PYTHONPATH=/Flask-Web-App-Tutorial
ENV PORT=8080
ENV CLOUD_RUN=1
EXPOSE 8080
CMD exec gunicorn --bind :$PORT main:app