# Global variable to store the playwright driver instance
_driver = None

def set_playwright_driver(driver):
    """Set the global playwright driver instance."""
    global _driver
    _driver = driver

def get_playwright_driver():
    """Retrieve the global playwright driver instance."""
    if _driver is None:
        raise RuntimeError(
            "playwright driver has not been initialized. Call set_driver() after starting the session.")
    return _driver

def quit_playwright_driver():
    """Quit the global playwright driver instance."""
    global _driver
    if _driver is not None:
        _driver.quit()
        _driver = None
