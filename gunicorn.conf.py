import multiprocessing

bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
loglevel = "info"
accesslog = "-"
capture_output = True
enable_stdio_inheritance = True
timeout = 120
