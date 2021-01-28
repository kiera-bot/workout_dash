FROM python:3.8
WORKDIR /app
ADD . /app
EXPOSE 8080
RUN pip install -r requirements.txt
CMD ["python", "main.py", "--peloton_username", "YOUR_USERNAME", "--peloton_password", "YOUR_PASSWORD"]