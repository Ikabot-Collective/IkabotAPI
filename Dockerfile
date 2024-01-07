FROM python:3

# Creating Application Source Code Directory
RUN mkdir -p /usr/src/app

# Setting Home Directory for containers
WORKDIR /usr/src/app

# Installing python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install
RUN python -m playwright install-deps

# Copying src code to Container
COPY . /usr/src/app

# Application Environment variables
#ENV APP_ENV development
ENV PORT 5000

# Exposing Ports
EXPOSE $PORT

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-c", "gunicorn.conf.py", "run:app"]