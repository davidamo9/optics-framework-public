import asyncio
import inspect
from typing import Any, Dict, Optional, Union
from playwright.async_api import async_playwright, Page, Browser
from playwright.sync_api import sync_playwright, Page as SyncPage, Browser as SyncBrowser
from optics_framework.common.utils import SpecialKey, strip_sensitive_prefix
from optics_framework.common.driver_interface import DriverInterface
from optics_framework.common.config_handler import ConfigHandler
from optics_framework.common.logging_config import internal_logger
from optics_framework.common.eventSDK import EventSDK
from optics_framework.engines.drivers.playwright_driver_manager import set_playwright_driver
from optics_framework.engines.drivers.playwright_UI_helper import UIHelper


class Playwright(DriverInterface):
    _instance = None
    DEPENDENCY_TYPE = "driver_sources"
    NAME = "playwright"
    ACTION_NOT_SUPPORTED = "Action not supported in Playwright."

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Playwright, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.driver: Optional[Union[Page, SyncPage]] = None
        self.browser: Optional[Union[Browser, SyncBrowser]] = None
        self.playwright = None
        self.sync_playwright = None
        self.ui_helper = None

        config_handler = ConfigHandler.get_instance()
        config: Optional[Dict[str, Any]] = config_handler.get_dependency_config(self.DEPENDENCY_TYPE, self.NAME)

        if not config:
            internal_logger.error(f"No configuration found for {self.DEPENDENCY_TYPE}: {self.NAME}")
            raise ValueError("Playwright driver not enabled in config")

        self.capabilities = config.get("capabilities", {})
        if not self.capabilities:
            internal_logger.error("No capabilities found in config")
            raise ValueError("Playwright capabilities not found in config")

        self.remote_url: str = config.get("url", "")
        self.browser_url = self.capabilities.get("browserURL", "about:blank")
        self.browser_name = self.capabilities.get("browserName", "chromium")

        # Debug logging for config values
        internal_logger.debug(f"Playwright config loaded - browserURL: {self.browser_url}, browserName: {self.browser_name}")
        internal_logger.debug(f"Full capabilities: {self.capabilities}")

        self.eventSDK = EventSDK.get_instance()
        self.initialized = True

    def _is_async_context(self) -> bool:
        """Check if we're running inside an asyncio event loop."""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False


    def _init_sync_driver(self):
        """Initialize sync playwright driver for library usage."""
        if not self.sync_playwright:
            self.sync_playwright = sync_playwright()
            self.sync_playwright.start()
            browser_name = self.browser_name.lower()

            if self.remote_url:
                if browser_name == "chromium":
                    self.browser = self.sync_playwright.chromium.connect(self.remote_url)
                elif browser_name == "firefox":
                    self.browser = self.sync_playwright.firefox.connect(self.remote_url)
                elif browser_name == "webkit":
                    self.browser = self.sync_playwright.webkit.connect(self.remote_url)
                else:
                    raise ValueError(f"Unsupported browser: {browser_name}")
            else:
                if browser_name == "chromium":
                    self.browser = self.sync_playwright.chromium.launch(headless=False)
                elif browser_name == "firefox":
                    self.browser = self.sync_playwright.firefox.launch(headless=False)
                elif browser_name == "webkit":
                    self.browser = self.sync_playwright.webkit.launch(headless=False)
                else:
                    raise ValueError(f"Unsupported browser: {browser_name}")

            context = self.browser.new_context()
            self.driver = context.new_page()
            set_playwright_driver(self.driver)
            self.ui_helper = UIHelper()

    async def start_session(self, event_name: Optional[str] = None) -> Page:
        self.playwright = await async_playwright().start()
        browser_name = self.browser_name.lower()

        try:
            if self.remote_url:
                internal_logger.info(f"Connecting to remote Playwright server: {self.remote_url}")
                if browser_name == "chromium":
                    self.browser = await self.playwright.chromium.connect(self.remote_url)
                elif browser_name == "firefox":
                    self.browser = await self.playwright.firefox.connect(self.remote_url)
                elif browser_name == "webkit":
                    self.browser = await self.playwright.webkit.connect(self.remote_url)
                else:
                    raise ValueError(f"Unsupported browser: {browser_name}")
            else:
                internal_logger.info(f"Launching local Playwright browser: {browser_name}")
                if browser_name == "chromium":
                    self.browser = await self.playwright.chromium.launch(headless=False)
                elif browser_name == "firefox":
                    self.browser = await self.playwright.firefox.launch(headless=False)
                elif browser_name == "webkit":
                    self.browser = await self.playwright.webkit.launch(headless=False)
                else:
                    raise ValueError(f"Unsupported browser: {browser_name}")

            context = await self.browser.new_context()
            self.driver = await context.new_page()
            await self.driver.goto(self.browser_url)
            set_playwright_driver(self.driver)
            self.ui_helper = UIHelper()

            if event_name:
                self.eventSDK.capture_event(event_name)

            internal_logger.debug(f"Started Playwright session with browser: {browser_name}")
            return self.driver

        except Exception as e:
            internal_logger.error(f"Failed to start Playwright session: {e}")
            raise

    def launch_app(self, event_name: Optional[str] = None) -> None:
        """Launch the app using the Playwright driver."""
        if self.driver is None:
            if self._is_async_context():
                # In async context, we need to call start_session synchronously
                # Create new event loop in thread to avoid "cannot be called from running loop"
                import concurrent.futures

                def run_async_start_session():
                    return asyncio.run(self.start_session(event_name))

                # Run in thread pool to avoid event loop conflict
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_start_session)
                    future.result()  # Wait for completion and get result
            else:
                # Sync context, use sync driver initialization
                self._init_sync_driver()


    def launch_other_app(self, app_name: str, event_name: Optional[str] = None) -> None:
        if self.driver is None:
            if self._is_async_context():
                # In async context, we need to call start_session synchronously
                import concurrent.futures

                def run_async_start_session():
                    return asyncio.run(self.start_session(event_name))

                # Run in thread pool to avoid event loop conflict
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_start_session)
                    future.result()  # Wait for completion
            else:
                # Sync context, use sync driver initialization
                self._init_sync_driver()

        try:
            self.driver.goto(app_name)
            if event_name:
                self.eventSDK.capture_event(event_name)
            internal_logger.debug(f"Launched other app: {app_name}")
        except Exception as e:
            internal_logger.error(f"Failed to launch other app: {e}")
            raise

    def terminate(self, event_name: Optional[str] = None) -> None:
        if self.driver:
            try:
                self.driver.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
                if self.sync_playwright:
                    self.sync_playwright.stop()
                if event_name:
                    self.eventSDK.capture_event(event_name)
                internal_logger.debug("Playwright session terminated.")
            except Exception as e:
                internal_logger.error(f"Error during termination: {e}")
            finally:
                self.driver = None
                self.browser = None
                self.playwright = None
                self.sync_playwright = None

    def press_element(self, element, repeat: int = 1, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()

            for _ in range(repeat):
                # Handle both sync and async element clicks
                click_result = element.click()

                # Check if click() returned a coroutine (async)
                if inspect.iscoroutine(click_result):
                    internal_logger.debug("Detected async click, running in thread...")
                    import concurrent.futures

                    def run_async_click():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(click_result)
                        finally:
                            loop.close()

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async_click)
                        future.result(timeout=10)  # 10s timeout
                # If it's not a coroutine, it was a sync operation and already completed

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to press element: {e}")
            raise

    def press_coordinates(self, coor_x: int, coor_y: int, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()
            self.driver.mouse.click(coor_x, coor_y)

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
            internal_logger.debug(f"Clicked at coordinates ({coor_x}, {coor_y}) with event: {event_name}")
        except Exception as e:
            internal_logger.error(f"Failed to click at coordinates ({coor_x}, {coor_y}): {e}")
            raise

    def press_percentage_coordinates(self, percentage_x: float, percentage_y: float, repeat: int = 1, event_name: Optional[str] = None) -> None:
        try:
            viewport = self.driver.viewport_size
            abs_x = int(viewport['width'] * percentage_x / 100)
            abs_y = int(viewport['height'] * percentage_y / 100)
            for _ in range(repeat):
                self.press_coordinates(abs_x, abs_y, event_name)
            internal_logger.debug(f"Clicked at percentage coordinates ({percentage_x}%, {percentage_y}%) {repeat} times")
        except Exception as e:
            internal_logger.error(f"Failed to click using percentage coordinates: {e}")
            raise

    def enter_text(self, text: str, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()
            self.driver.keyboard.type(strip_sensitive_prefix(text))

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to enter text: {e}")
            raise

    def enter_text_element(self, element, text: str, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()

            # Handle both sync and async element fill
            fill_result = element.fill(strip_sensitive_prefix(text))

            # Check if fill() returned a coroutine (async)
            if inspect.iscoroutine(fill_result):
                internal_logger.debug("Detected async fill, running in thread...")
                import concurrent.futures

                def run_async_fill():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(fill_result)
                    finally:
                        loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_fill)
                    future.result(timeout=10)  # 10s timeout
            # If it's not a coroutine, it was a sync operation and already completed

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to enter text into element: {e}")
            raise

    def enter_text_using_keyboard(self, input_value: Union[str, SpecialKey], event_name: Optional[str] = None):
        key_map = {
            SpecialKey.ENTER: "Enter",
            SpecialKey.TAB: "Tab",
            SpecialKey.BACKSPACE: "Backspace",
            SpecialKey.SPACE: "Space",
            SpecialKey.ESCAPE: "Escape",
        }

        try:
            timestamp = self.eventSDK.get_current_time_for_events()

            if isinstance(input_value, SpecialKey):
                self.driver.keyboard.press(key_map[input_value])
            else:
                self.driver.keyboard.type(strip_sensitive_prefix(input_value))

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to enter input using keyboard: {e}")
            raise

    def press_keycode(self, keycode: Union[str, int], event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()
            self.driver.keyboard.press(str(keycode))

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to press keycode {keycode}: {e}")
            raise

    def clear_text(self, event_name: Optional[str] = None) -> None:
        self._raise_action_not_supported()

    def clear_text_element(self, element, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()
            element.fill("")

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
        except Exception as e:
            internal_logger.error(f"Failed to clear element text: {e}")
            raise

    def swipe(self, x_coor: int, y_coor: int, direction: str, swipe_length: int, event_name: Optional[str] = None) -> None:
        self._raise_action_not_supported()

    def swipe_percentage(self, x_percentage: float, y_percentage: float, direction: str, swipe_percentage: float, event_name: Optional[str] = None) -> None:
        self._raise_action_not_supported()

    def swipe_element(self, element, direction: str, swipe_length: int, event_name: Optional[str] = None) -> None:
        self._raise_action_not_supported()

    def scroll(self, direction: str, duration: int = 1000, event_name: Optional[str] = None) -> None:
        try:
            timestamp = self.eventSDK.get_current_time_for_events()

            if direction == "down":
                self.driver.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                self.driver.evaluate("window.scrollBy(0, -window.innerHeight)")
            elif direction == "left":
                self.driver.evaluate("window.scrollBy(-window.innerWidth, 0)")
            elif direction == "right":
                self.driver.evaluate("window.scrollBy(window.innerWidth, 0)")
            else:
                raise ValueError(f"Unsupported scroll direction: {direction}")

            if event_name:
                self.eventSDK.capture_event_with_time_input(event_name, timestamp)
            internal_logger.debug(f"Scrolled {direction} with event: {event_name}")
        except Exception as e:
            internal_logger.error(f"Failed to scroll {direction}: {e}")
            raise

    def get_text_element(self, element) -> str:
        # Handle both sync and async element inner_text
        inner_text_result = element.inner_text()

        # Check if inner_text() returned a coroutine (async)
        if inspect.iscoroutine(inner_text_result):
            internal_logger.debug("Detected async inner_text, running in thread...")
            import concurrent.futures

            def run_async_inner_text():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(inner_text_result)
                finally:
                    loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_inner_text)
                return future.result(timeout=10)  # 10s timeout
        else:
            # It was a sync operation, return the result
            return inner_text_result

    def take_screenshot(self, path: Optional[str] = None) -> bytes:
        try:
            return self.driver.screenshot(path=path)
        except Exception as e:
            internal_logger.error(f"Failed to take screenshot: {e}")
            raise

    def wait_until_element_visible(self, locator: str, timeout: int = 5000) -> bool:
        try:
            self.driver.locator(locator).wait_for(state="visible", timeout=timeout)
            return True
        except Exception as e:
            internal_logger.warning(f"Element not visible within timeout: {locator} — {e}")
            return False

    def _raise_action_not_supported(self) -> None:
        internal_logger.warning(self.ACTION_NOT_SUPPORTED)
        raise NotImplementedError(self.ACTION_NOT_SUPPORTED)

    def get_app_version(self) -> str:
        self._raise_action_not_supported()
