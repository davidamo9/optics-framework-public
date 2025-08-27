#!/usr/bin/env python3
"""
Quick test to verify Playwright config loading and URL navigation.
"""
import sys
import os

# Add the framework to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_loading():
    """Test that Playwright config is loaded correctly."""

    # Set the config path to point to our playwright sample
    os.environ['OPTICS_CONFIG_PATH'] = os.path.join(
        os.path.dirname(__file__),
        '../optics_framework/samples/playwright/config.yaml'
    )

    from optics_framework.engines.drivers.playwright import Playwright

    try:
        # Create Playwright driver instance
        print("Creating Playwright driver...")
        driver = Playwright()

        # Check what URL was loaded from config
        print(f"Browser URL from config: {driver.browser_url}")
        print(f"Browser name from config: {driver.browser_name}")
        print(f"Remote URL from config: {driver.remote_url}")

        # Try to launch the app
        print(f"Attempting to launch app at {driver.browser_url}...")
        driver.launch_app("test_config")

        # Get current URL
        if driver.driver:
            current_url = driver.driver.url
            print(f"Current browser URL: {current_url}")

            # Check if we're at the expected URL
            if "google.com" in current_url:
                print("✓ Successfully navigated to Google!")
            elif current_url == "about:blank":
                print("❌ Still at about:blank - URL navigation failed")
            else:
                print(f"? Navigated to unexpected URL: {current_url}")

        # Clean up
        driver.terminate()
        print("✓ Test completed successfully")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Playwright Config Test ===\n")
    test_config_loading()
