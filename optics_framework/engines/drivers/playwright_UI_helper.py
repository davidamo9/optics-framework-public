from typing import Optional, List
from lxml import html, etree
from playwright.sync_api import Page, ElementHandle

from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils
from optics_framework.engines.drivers.playwright_driver_manager import get_playwright_driver
class UIHelper:
    def __init__(self):
        self.driver: Optional[Page] = None

    def _get_playwright_driver(self) -> Page:
        if self.driver is None:
            self.driver = get_playwright_driver()
        return self.driver

    def get_page_source(self) -> str:
        """
        Fetch the current UI tree (page source) and prettify for storage/debug.
        """
        timestamp = utils.get_timestamp()
        driver = self._get_playwright_driver()
        page_source = driver.content()
        tree = html.fromstring(page_source)
        prettified_html = html.tostring(tree, pretty_print=True, encoding='unicode')

        utils.save_page_source_html(prettified_html, timestamp)
        internal_logger.debug('\n\n========== PAGE SOURCE FETCHED ==========\n')
        internal_logger.debug(f'Page source fetched at: {timestamp}')
        internal_logger.debug('\n==========================================\n')
        return page_source

    def find_html_elements_by_text(self, text: str) -> List[etree.Element]:
        """
        Finds HTML elements by their visible text content.
        Returns a list of lxml elements.
        """
        page_source = self.get_page_source()
        tree = html.fromstring(page_source)
        elements = tree.xpath(f'//*[contains(text(), "{text}")]')
        return elements

    def find_html_elements_by_xpath(self, xpath: str) -> List[etree.Element]:
        """
        Finds HTML elements by XPath.
        Returns a list of lxml elements.
        """
        page_source = self.get_page_source()
        tree = html.fromstring(page_source)
        elements = tree.xpath(xpath)
        return elements

    def get_playwright_element_by_xpath(self, xpath: str, index: int = 0) -> ElementHandle:
        """
        Returns Playwright ElementHandle by XPath.
        """
        driver = self._get_playwright_driver()
        locator = driver.locator(f'xpath={xpath}')
        count = locator.count()
        if count == 0:
            raise ValueError(f"No element found for XPath: {xpath}")
        if index >= count:
            raise IndexError(f"Index {index} is out of bounds for element count {count}")
        return locator.nth(index)

    def get_playwright_element_by_text(self, text: str, index: int = 0) -> ElementHandle:
        """
        Returns Playwright ElementHandle by text using :has-text().
        """
        driver = self._get_playwright_driver()
        locator = driver.locator(f'text="{text}"')
        count = locator.count()
        if count == 0:
            raise ValueError(f"No element found with text: {text}")
        if index >= count:
            raise IndexError(f"Index {index} is out of bounds for element count {count}")
        return locator.nth(index)

    def wait_until_text_visible(self, text: str, timeout: int = 5000) -> bool:
        """
        Wait until an element containing the given text is visible.
        """
        driver = self._get_playwright_driver()
        try:
            driver.locator(f'text="{text}"').first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception as e:
            internal_logger.warning(f"Text '{text}' not visible in timeout: {e}")
            return False

    def wait_until_xpath_visible(self, xpath: str, timeout: int = 5000) -> bool:
        """
        Wait until an element matching the XPath is visible.
        """
        driver = self._get_playwright_driver()
        try:
            driver.locator(f'xpath={xpath}').first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception as e:
            internal_logger.warning(f"XPath '{xpath}' not visible in timeout: {e}")
            return False

    def get_element_bounding_box(self, element: ElementHandle) -> Optional[dict]:
        """
        Returns the bounding box of a Playwright element.
        """
        try:
            box = element.bounding_box()
            if box is None:
                internal_logger.warning("Bounding box is None for the element.")
            return box
        except Exception as e:
            internal_logger.error(f"Error getting bounding box: {e}")
            return None

    def get_element_inner_text(self, element: ElementHandle) -> str:
        """
        Returns the inner text of a Playwright element.
        """
        try:
            return element.inner_text()
        except Exception as e:
            internal_logger.error(f"Failed to get inner text: {e}")
            return ""

    def get_element_attribute(self, element: ElementHandle, attribute: str) -> Optional[str]:
        """
        Returns the value of a given attribute for an element.
        """
        try:
            return element.get_attribute(attribute)
        except Exception as e:
            internal_logger.error(f"Failed to get attribute '{attribute}': {e}")
            return None
