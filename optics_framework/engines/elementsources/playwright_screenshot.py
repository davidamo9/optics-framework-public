from optics_framework.common.elementsource_interface import ElementSourceInterface
from optics_framework.engines.drivers.playwright_driver_manager import get_playwright_driver
from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils
import numpy as np
import cv2
from typing import Tuple, Optional
import time


class PlaywrightScreenshot(ElementSourceInterface):
    """
    Playwright Screenshot Class - Screenshot capture for computer vision-based element detection
    """

    def __init__(self):
        """
        Initialize the Playwright Screenshot Class.
        """
        self.driver = None

    def _get_playwright_driver(self):
        self.driver = get_playwright_driver()
        return self.driver

    def capture(self) -> np.ndarray:
        """
        Capture the current screen state as a screenshot.

        Returns:
            np.ndarray: Screenshot as numpy array for computer vision processing
        """
        driver = self._get_playwright_driver()
        try:
            # Get screenshot as bytes
            screenshot_bytes = driver.screenshot()

            # Convert bytes to numpy array
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if screenshot is None:
                raise ValueError("Failed to decode screenshot")

            return screenshot
        except Exception as e:
            internal_logger.error(f"Failed to capture screenshot: {e}")
            raise

    def get_page_source(self) -> str:
        """
        Get the HTML page source (not typically used for screenshot-based detection).

        Returns:
            str: The HTML page source.
        """
        driver = self._get_playwright_driver()
        try:
            page_source = driver.content()
            return page_source
        except Exception as e:
            internal_logger.error(f"Failed to get page source: {e}")
            raise

    def get_interactive_elements(self):
        """
        Screenshot-based element source doesn't support getting interactive elements.
        Use PlaywrightPageSource for this functionality.
        """
        internal_logger.exception('PlaywrightScreenshot does not support getting interactive elements. Please use PlaywrightPageSource for this functionality.')
        raise NotImplementedError('PlaywrightScreenshot does not support getting interactive elements. Please use PlaywrightPageSource for this functionality.')

    def locate(self, element: str, index: Optional[int] = None) -> Optional[Tuple[int, int]]:
        """
        Screenshot-based element location is handled by vision models, not directly here.
        This method is typically called by TextDetectionStrategy or ImageDetectionStrategy.

        Args:
            element: The element to find (usually handled by vision models)
            index: Optional index for multiple elements

        Returns:
            None (vision models handle the actual element detection)
        """
        internal_logger.warning('PlaywrightScreenshot.locate() should be used with vision models (TextDetectionStrategy/ImageDetectionStrategy)')
        return None

    def assert_elements(self, elements, timeout=30, rule='any') -> Tuple[bool, str]:
        """
        Screenshot-based element assertion is handled by vision models.
        This is typically called by TextDetectionStrategy or ImageDetectionStrategy.

        Args:
            elements (list): List of elements to assert
            timeout (int): Maximum time to wait for elements
            rule (str): Rule to apply ("any" or "all")

        Returns:
            tuple: (False, timestamp) - Always returns False as vision models handle assertions
        """
        internal_logger.warning('PlaywrightScreenshot.assert_elements() should be used with vision models (TextDetectionStrategy/ImageDetectionStrategy)')
        timestamp = utils.get_timestamp()
        return False, timestamp

    def capture_stream(self, timeout: int = 30):
        """
        Capture a stream of screenshots for continuous monitoring.
        Used by screenshot streaming strategies.

        Args:
            timeout: Maximum time to capture screenshots

        Yields:
            np.ndarray: Screenshot frames
        """
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                screenshot = self.capture()
                yield screenshot
                time.sleep(0.1)  # Small delay between captures
            except Exception as e:
                internal_logger.error(f"Error in screenshot stream: {e}")
                break
