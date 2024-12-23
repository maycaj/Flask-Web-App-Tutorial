FROM python:3.8-slim
WORKDIR /Flask-Web-App-Tutorial
COPY . .
RUN pip install -r requirements.txt
ENV PYTHONPATH=/Flask-Web-App-Tutorial
EXPOSE 8080
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
CMD ["python", "website/main.py"]