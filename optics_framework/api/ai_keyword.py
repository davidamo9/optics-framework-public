from optics_framework.common.optics_builder import OpticsBuilder
from optics_framework.common.logging_config import internal_logger
from optics_framework.common.strategies import StrategyManager
from optics_framework.common.eventSDK import EventSDK
from optics_framework.common.llm_agents.ai_action import AIActionHandler
from optics_framework.common import utils

class AIKeyword:
    """
    High-Level API for AI-driven intent recognition and action execution.
    """

    def __init__(self, builder: OpticsBuilder, ai_handler: AIActionHandler = None):
        self.element_source = builder.get_element_source()
        self.image_detection = builder.get_image_detection()
        self.text_detection = builder.get_text_detection()
        self.strategy_manager = StrategyManager(
            self.element_source, self.text_detection, self.image_detection)
        self.event_sdk = EventSDK().get_instance()
        self.ai_handler = ai_handler

    def ai_action(
        self,
        instruction: str,
    ) -> bool:
        """
        Executes an AI-driven action based on the provided action name and parameters.

        :param action: The name of the action to be executed.
        :param params: Parameters required for the action execution.
        :param session_id: Optional session ID for tracking.
        :param event_name: Optional event name for logging.
        :return: True if the action was successfully executed, False otherwise.
        """
        internal_logger.debug(f"Executing AI action: {instruction}")
        screenshot_np = self.strategy_manager.capture_screenshot()
        screenshot_path = utils.save_screenshot(screenshot_np, "ai_action_screenshot")
        page_source = self.strategy_manager.capture_pagesource()
        self.ai_handler.perform_ai_action(instruction, xml_string=page_source, screenshot_path=screenshot_path)
