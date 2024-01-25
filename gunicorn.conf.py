import multiprocessing

bind = "0.0.0.0:5005"
workers = multiprocessing.cpu_count() * 2 + 1
loglevel = "info"
accesslog = "-"
capture_output = True
enable_stdio_inheritance = True
timeout = 120
