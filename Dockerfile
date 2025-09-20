FROM python:3.13

EXPOSE 8080
WORKDIR /app

COPY . ./

run pip install -r requirements.txt
ENTRYPOINT ["streamlit", "run", "main_page.py", "--server.port=8080", "--server.address=0.0.0.0"]