from optics_framework.common.elementsource_interface import ElementSourceInterface
from optics_framework.engines.drivers.playwright_driver_manager import get_playwright_driver
from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils
from typing import Tuple, Union, Optional
import time


class PlaywrightFindElement(ElementSourceInterface):
    """
    Playwright Find Element Class - Direct element location using Playwright's locator API
    """

    def __init__(self):
        """
        Initialize the Playwright Find Element Class.
        """
        self.driver = None

    def _get_playwright_driver(self):
        self.driver = get_playwright_driver()
        return self.driver

    def _safe_locator_exists(self, locator):
        """Safely check if locator has elements, handling both sync and async contexts."""
        try:
            # Try to use wait_for with a very short timeout to check existence
            locator.wait_for(state="attached", timeout=100)  # 100ms timeout
            return True
        except Exception:
            # Element doesn't exist or timeout
            return False

    def _safe_get_nth_element(self, locator, index):
        """Safely get nth element from locator."""
        try:
            nth_locator = locator.nth(index)
            # Check if this specific element exists
            if self._safe_locator_exists(nth_locator):
                return nth_locator
            return None
        except Exception as e:
            internal_logger.warning(f"Error getting nth element at index {index}: {e}")
            return None

    def capture(self) -> bytes:
        """
        Capture the current screen state as a screenshot.

        Returns:
            bytes: Screenshot as bytes
        """
        driver = self._get_playwright_driver()
        try:
            screenshot_bytes = driver.screenshot()
            return screenshot_bytes
        except Exception as e:
            internal_logger.error(f"Failed to capture screenshot: {e}")
            raise

    def get_page_source(self) -> str:
        """
        Get the HTML page source of the current page.

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
        Get all interactive elements from the current page.

        Returns:
            list: A list of interactive elements found on the page.
        """
        internal_logger.exception('PlaywrightFindElement does not support getting interactive elements. Please use PlaywrightPageSource for this functionality.')
        raise NotImplementedError('PlaywrightFindElement does not support getting interactive elements. Please use PlaywrightPageSource for this functionality.')

    def locate(self, element: str, index: Optional[int] = None) -> Union[object, None]:
        """
        Find the specified element on the current page using Playwright locators.

        Args:
            element: The element to find on the page (XPath, CSS selector, text, etc.)
            index: Optional index for multiple matching elements

        Returns:
            Playwright Locator object if found, None otherwise.
        """
        driver = self._get_playwright_driver()
        element_type = utils.determine_element_type(element)

        try:
            if element_type == 'Image':
                # Playwright doesn't support direct image-based element location
                internal_logger.debug('PlaywrightFindElement does not support finding images.')
                return None
            elif element_type == 'XPath':
                # Use XPath locator
                locator = driver.locator(f"xpath={element}")
                if index is not None:
                    # Get specific index if multiple elements match
                    nth_element = self._safe_get_nth_element(locator, index)
                    if nth_element is None:
                        internal_logger.warning(f"Element at index {index} not found for XPath {element}")
                    return nth_element
                else:
                    # Return first element if it exists
                    if self._safe_locator_exists(locator):
                        return locator.first
                    return None
            elif element_type == 'Text':
                # Use text-based locator
                locator = driver.locator(f"text={element}")
                if index is not None:
                    nth_element = self._safe_get_nth_element(locator, index)
                    if nth_element is None:
                        internal_logger.warning(f"Element at index {index} not found for text '{element}'")
                    return nth_element
                else:
                    if self._safe_locator_exists(locator):
                        return locator.first
                    return None
            else:
                # Try as CSS selector or other Playwright selector
                locator = driver.locator(element)
                if index is not None:
                    nth_element = self._safe_get_nth_element(locator, index)
                    if nth_element is None:
                        internal_logger.warning(f"Element at index {index} not found for selector '{element}'")
                    return nth_element
                else:
                    if self._safe_locator_exists(locator):
                        return locator.first
                    return None
        except Exception as e:
            internal_logger.error(f'Error finding element: {element} - {e}')
            return None

    def assert_elements(self, elements, timeout=10, rule="any") -> Tuple[bool, str]:
        """
        Assert that elements are present based on the specified rule.

        Args:
            elements (list): List of elements to locate.
            timeout (int): Maximum time to wait for elements.
            rule (str): Rule to apply ("any" or "all").

        Returns:
            tuple: (bool, timestamp) - True if assertion passes, timestamp when found
        """
        if rule not in ["any", "all"]:
            raise ValueError("Invalid rule. Use 'any' or 'all'.")

        start_time = time.time()
        found = dict.fromkeys(elements, False)

        while time.time() - start_time < timeout:
            for el in elements:
                if not found[el] and self.locate(el):
                    timestamp = utils.get_timestamp()
                    found[el] = True
                    if rule == "any":
                        return True, timestamp

            if rule == "all" and all(found.values()):
                return True, utils.get_timestamp()

            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

        missing_elements = [el for el, ok in found.items() if not ok]
        internal_logger.error(
            f"Elements not found based on rule '{rule}': {missing_elements}"
        )
        raise TimeoutError(
            f"Timeout reached: Elements not found based on rule '{rule}': {elements}"
        )
