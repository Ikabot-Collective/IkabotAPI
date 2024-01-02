FROM python:3

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--access-logfile", "logfile.txt", "-b", "0.0.0.0:5000", "app:app"]