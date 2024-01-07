import psutil


def clean_up_driver_processes(driver_name="chromedriver"):
    """
    Terminate lingering driver processes to prepare for a new run of the web application.

    Parameters:
    - driver_name (str, optional): The name of the driver process to terminate (e.g., "geckodriver", "chromedriver", "IEDriverServer").
      Defaults to "chromedriver" if not provided.

    This function identifies and terminates any active processes whose names match the specified driver_name.
    It is particularly useful in the Selenium context to ensure a clean environment before restarting the web application.
    """
    for proc in psutil.process_iter():
        if proc.name() == driver_name:
            proc.kill()
