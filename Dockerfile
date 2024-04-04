FROM python:3.10-slim

COPY . /ikabotapi/
WORKDIR /ikabotapi

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \ 
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*
RUN python -m playwright install && \
    python -m playwright install-deps

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]