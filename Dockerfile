FROM python:3.8-slim
WORKDIR /Flask-Web-App-Tutorial
COPY . .
RUN pip install -r requirements.txt
ENV PYTHONPATH=/Flask-Web-App-Tutorial
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-m", "flask", "--app", "website/main.py", "run", "--host=0.0.0.0", "--port=$PORT"]