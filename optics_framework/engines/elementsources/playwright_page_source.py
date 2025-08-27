from optics_framework.common.elementsource_interface import ElementSourceInterface
from optics_framework.engines.drivers.playwright_driver_manager import get_playwright_driver
from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils
from optics_framework.engines.drivers.playwright_UI_helper import UIHelper
from lxml import html
from typing import Tuple, Union, Optional
import time


class PlaywrightPageSource(ElementSourceInterface):
    """
    Playwright Page Source Class - Element location using HTML page source parsing
    """

    def __init__(self):
        """
        Initialize the Playwright Page Source Class.
        """
        self.driver = None
        self.ui_helper = UIHelper()
        self.tree = None
        self.root = None

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

    def get_page_source(self) -> Tuple[str, str]:
        """
        Get the HTML page source of the current page.

        Returns:
            tuple: (page_source, timestamp)
        """
        timestamp = utils.get_timestamp()

        driver = self._get_playwright_driver()
        page_source = driver.content()

        # Parse HTML content with lxml
        self.tree = html.fromstring(page_source)

        internal_logger.debug('\n\n========== PAGE SOURCE FETCHED ==========\n')
        internal_logger.debug(f'Page source fetched at: {timestamp}')
        internal_logger.debug('\n==========================================\n')
        return page_source, timestamp

    def get_interactive_elements(self):
        """
        Get all interactive elements from the current page using UIHelper.

        Returns:
            list: A list of interactive elements found on the page.
        """
        return self.ui_helper.get_interactive_elements()

    def locate(self, element: str, index: Optional[int] = None) -> Union[object, None]:
        """
        Locate a UI element on the current page using HTML page source parsing.

        Args:
            element (str): The element identifier to locate (text, XPath, CSS selector)
            index (int, optional): Index for multiple matching elements

        Returns:
            Playwright Locator object if found, None otherwise
        """
        driver = self._get_playwright_driver()
        element_type = utils.determine_element_type(element)

        if element_type == 'Image':
            # Image-based search is not supported in page source mode
            internal_logger.debug('PlaywrightPageSource does not support finding images.')
            return None
        else:
            if element_type == 'Text':
                if index is not None:
                    xpath = self.find_xpath_from_text_index(element, index)
                else:
                    xpath = self.find_xpath_from_text(element)

                if xpath:
                    try:
                        # Convert to Playwright locator
                        locator = driver.locator(f"xpath={xpath}")
                        if self._safe_locator_exists(locator):
                            return locator.first
                        return None
                    except Exception as e:
                        internal_logger.error(f"Error finding element by text: {e}")
                        return None
                return None
            elif element_type == 'XPath':
                # For XPath, we can use it directly with Playwright
                try:
                    locator = driver.locator(f"xpath={element}")
                    if index is not None:
                        nth_element = self._safe_get_nth_element(locator, index)
                        return nth_element
                    else:
                        if self._safe_locator_exists(locator):
                            return locator.first
                        return None
                except Exception as e:
                    internal_logger.error(f"Error finding element by xpath: {e}")
                    return None
            else:
                # Try as CSS selector
                try:
                    locator = driver.locator(element)
                    if index is not None:
                        nth_element = self._safe_get_nth_element(locator, index)
                        return nth_element
                    else:
                        if self._safe_locator_exists(locator):
                            return locator.first
                        return None
                except Exception as e:
                    internal_logger.error(f"Error finding element by selector: {e}")
                    return None

    def locate_using_index(self, element, index, strategy=None) -> Union[object, None]:
        """
        Locate element using index-based strategy (similar to Appium implementation).

        Args:
            element: Element to locate
            index: Index for multiple elements
            strategy: Optional strategy hint

        Returns:
            Playwright Locator object if found, None otherwise
        """
        # For now, delegate to the main locate method with index
        return self.locate(element, index)

    def assert_elements(self, elements, timeout=30, rule='any') -> Tuple[bool, str]:
        """
        Assert the presence of elements on the current page.

        Args:
            elements (list): List of elements to assert on the page.
            timeout (int): Maximum time to wait for the elements to appear.
            rule (str): Rule to apply ("any" or "all").

        Returns:
            tuple: (bool, timestamp) - True if elements are found, timestamp when found
        """
        if rule not in ["any", "all"]:
            raise ValueError("Invalid rule. Use 'any' or 'all'.")

        start_time = time.time()

        while time.time() - start_time < timeout:
            texts = [el for el in elements if utils.determine_element_type(el) == 'Text']
            xpaths = [el for el in elements if utils.determine_element_type(el) == 'XPath']
            other_selectors = [el for el in elements if utils.determine_element_type(el) not in ['Text', 'XPath', 'Image']]

            _, timestamp = self.get_page_source()  # Refresh page source

            # Check text-based elements
            text_found = self.ui_text_search(texts, rule) if texts else (rule == "all")

            # Check XPath-based elements
            xpath_found = True
            if xpaths:
                xpath_results = []
                for xpath in xpaths:
                    try:
                        driver = self._get_playwright_driver()
                        locator = driver.locator(f"xpath={xpath}")
                        xpath_results.append(self._safe_locator_exists(locator))
                    except Exception:
                        xpath_results.append(False)
                xpath_found = (all(xpath_results) if rule == "all" else any(xpath_results))
            elif rule == "all":
                xpath_found = True

            # Check other selector-based elements
            selector_found = True
            if other_selectors:
                selector_results = []
                for selector in other_selectors:
                    try:
                        driver = self._get_playwright_driver()
                        locator = driver.locator(selector)
                        selector_results.append(self._safe_locator_exists(locator))
                    except Exception:
                        selector_results.append(False)
                selector_found = (all(selector_results) if rule == "all" else any(selector_results))
            elif rule == "all":
                selector_found = True

            # Rule evaluation
            if rule == "any":
                if text_found or xpath_found or selector_found:
                    return True, timestamp
            elif rule == "all":
                if text_found and xpath_found and selector_found:
                    return True, timestamp

            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

        # Timeout reached
        internal_logger.warning(f"Timeout reached. Rule: {rule}, Elements: {elements}")
        raise TimeoutError(
            f"Timeout reached: Elements not found based on rule '{rule}': {elements}"
        )

    def find_xpath_from_text(self, text: str) -> Optional[str]:
        """
        Find the XPath of an element based on the text content.

        Args:
            text (str): The text content to search for in the HTML tree.

        Returns:
            str: The XPath of the element containing the text, or None if not found.
        """
        if not self.tree:
            self.get_page_source()

        # Search for text in various HTML attributes and content
        # Try text content first
        elements = self.tree.xpath(f"//*[contains(text(), '{text}')]")
        if elements:
            return self.tree.getpath(elements[0])

        # Try common attributes
        attributes = ['value', 'placeholder', 'title', 'alt', 'aria-label']
        for attr in attributes:
            elements = self.tree.xpath(f"//*[@{attr} and contains(@{attr}, '{text}')]")
            if elements:
                return self.tree.getpath(elements[0])

        return None

    def find_xpath_from_text_index(self, text: str, index: int, strategy=None) -> Optional[str]:
        """
        Find XPath for text with specific index.

        Args:
            text: Text to search for
            index: Index of the element (0-based)
            strategy: Optional strategy hint

        Returns:
            XPath string if found, None otherwise
        """
        if not self.tree:
            self.get_page_source()

        # Find all elements containing the text
        elements = self.tree.xpath(f"//*[contains(text(), '{text}')]")

        # If no direct text match, try attributes
        if not elements:
            attributes = ['value', 'placeholder', 'title', 'alt', 'aria-label']
            for attr in attributes:
                elements = self.tree.xpath(f"//*[@{attr} and contains(@{attr}, '{text}')]")
                if elements:
                    break

        if elements and index < len(elements):
            return self.tree.getpath(elements[index])

        return None

    def ui_text_search(self, texts, rule='any') -> bool:
        """
        Checks if any or all given texts exist in the HTML tree.

        Args:
            texts (list): List of text strings to search for.
            rule (str): Rule for matching ('any' or 'all').

        Returns:
            bool: True if the condition is met, otherwise False.
        """
        if not self.tree:
            self.get_page_source()

        found_texts = set()

        for text in texts:
            internal_logger.debug(f'Searching for text: {text}')

            # Search in text content
            elements = self.tree.xpath(f"//*[contains(text(), '{text}')]")
            if elements:
                found_texts.add(text)
                if rule == 'any':
                    return True
                continue

            # Search in common HTML attributes
            attributes = ['value', 'placeholder', 'title', 'alt', 'aria-label', 'data-testid']
            for attr in attributes:
                elements = self.tree.xpath(f"//*[@{attr} and contains(@{attr}, '{text}')]")
                if elements:
                    internal_logger.debug(f"Match found using {attr} for '{text}'")
                    found_texts.add(text)
                    break

            if rule == 'any' and text in found_texts:
                return True

        return len(found_texts) == len(texts) if rule == 'all' else False
