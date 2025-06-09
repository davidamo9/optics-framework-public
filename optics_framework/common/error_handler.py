from typing import Optional, Dict, Callable
from optics_framework.common.llm_agents.manager import get_llm_agent_manager
from optics_framework.common.logging_config import internal_logger
from optics_framework.common.llm_agents.popup_handler import PopupHandler

class ErrorHandler:
    def __init__(self, keyword_map:  Optional[Dict[str, Callable]] = None):
        self.event_manager = get_llm_agent_manager().event_manager
        self.popup_handler = PopupHandler()
        self.keyword_map = keyword_map or {}


    def set_keyword_map(self, keyword_map: Dict[str, Callable]):
        self.keyword_map = keyword_map

    def classify_failure(self, error_code: str) -> str:
        if error_code.startswith("E0201") or error_code.startswith("X0201"):
            return "screen_popup"
        elif error_code.startswith("E0401") or error_code.startswith("X0401"):
            return "keyword_execution"
        elif error_code.startswith("E0101"):
            return "driver_issue"
        else:
            return "general_error"

    def handle_error(self, error_code: str, error_message: str, context_info=None):
        # session = SessionManager().get_session(self.session_id) if self.session_id else None

        failure_type = self.classify_failure(error_code)
        # entity_type = context_info.get("entity_type", "system") if context_info else "system"
        # entity_id = context_info.get("entity_id", "unknown") if context_info else "unknown"
        screenshot_path = context_info.get("screenshot_path") if context_info else None
        page_source = context_info.get("page_source") if context_info else None

        #TODO: use event trigger
        # event = Event(
        #     entity_type=entity_type,
        #     entity_id=entity_id,
        #     name=f"Failure {error_code}",
        #     status=EventStatus.FAIL,
        #     message=f"{error_code}: {error_message}",
        #     extra={
        #         "page_source": context_info.get("page_source") if context_info else None,
        #         "screenshot_path": context_info.get("screenshot_path") if context_info else None
        #     }
        # )
        # Trigger LLM suggestion for screen popups
        if failure_type == "screen_popup" and page_source:
            try:
                suggestions = self.popup_handler.handle_popup(xml_string=page_source, screenshot_path=screenshot_path)
                internal_logger.info(f"[PopupHandler Suggestion] {suggestions}")

                for step in suggestions:
                    action = step.get("action")
                    target = step.get("target", {})

                    if action and action in self.keyword_map:
                        self.keyword_map[action](target["element_name"])
                        return True
                    else:
                        internal_logger.warning(f"Action '{action}' not found in keyword map.")
            except Exception as e:
                internal_logger.error(f"PopupHandler failed: {e}", exc_info=True)
        internal_logger.warning(f"Handling error {error_code}: {error_message}")
        return False
