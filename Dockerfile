FROM python:3.10

# Creating Application Source Code Directory
RUN mkdir -p /usr/src/app

# Setting Home Directory
WORKDIR /usr/src/app

# Installing python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install
RUN python -m playwright install-deps

# Copying src code to Container
COPY . /usr/src/app

# Exposing Ports
EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-c", "gunicorn.conf.py", "run:app"]