import requests
import re
import json
from typing import Optional, Dict, Callable
import defusedxml.ElementTree as ET
from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils

class AIActionHandler:
    def __init__(self, keyword_map:  Optional[Dict[str, Callable]] = None):
        self.ollama_model = "gemma3:4b"
        self.keyword_map = keyword_map or {}

    def set_keyword_map(self, keyword_map: Dict[str, Callable]):
        self.keyword_map = keyword_map

    def handle_action(self, instruction: str = None, xml_file: str = None, xml_string: str = None, screenshot_path: str = None) -> str:
        xml_text = self.extract_visible_elements(xml_file) if xml_file else xml_string
        if not xml_text:
            raise ValueError("Either xml_file or xml_string must be provided.")
        if not screenshot_path:
            raise ValueError("screenshot_path is not provided for popup handling.")
        prompt = self.build_prompt(instruction=instruction, xml_text=xml_text)
        response = self.query_ollama(prompt, model=self.ollama_model)
        internal_logger.debug(f"[Prompt Sent to LLM]\n{prompt}")
        internal_logger.debug(f"[LLM Response]\n{response}")
        utils.save_llm_log(prompt, response, agent_name="ai_action")
        return self.extract_json_from_llm_response(response)

    def extract_json_from_llm_response(self, raw_response: str):
        # Step 1: Strip surrounding triple backticks and optional "json" label
        cleaned = re.sub(r"^```json\n|```$", "", raw_response.strip())

        # Step 2: Parse as JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")

    def query_ollama(self, prompt, model="gemma3:4b"):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=15)
        if response.ok:
            return response.json()['response']
        else:
            raise Exception(f"Request failed: {response.status_code} - {response.text}")

    def extract_xml_text(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        lines = []
        for elem in root.iter():
            attribs = elem.attrib
            line = f"Element: class='{attribs.get('class', '')}', resource-id='{attribs.get('resource-id', '')}', content-desc='{attribs.get('content-desc', '')}', text='{attribs.get('text', '')}'"
            lines.append(line)
        return "\n".join(lines)

    def extract_visible_elements(xml_file, include_invisible=False):
        """
        Extracts relevant UI elements from Appium page source for LLM input.

        Args:
            xml_file (str): Path to the XML page source.
            include_invisible (bool): Whether to include elements with displayed='false'.

        Returns:
            str: Formatted string of UI elements for LLM consumption.
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()

        cleaned_lines = []

        for elem in root.iter():
            attrib = elem.attrib

            # Skip invisible elements unless explicitly allowed
            if not include_invisible and attrib.get('displayed') == 'false':
                continue

            # Skip layout/container-only elements with no meaningful info
            if not attrib.get('text') and not attrib.get('resource-id') and not attrib.get('content-desc'):
                continue

            # Optional: Skip elements that are not clickable or interactable
            # if attrib.get('clickable') != 'true':
            #     continue

            cleaned = {
                'class': attrib.get('class', ''),
                'text': attrib.get('text', ''),
                'resource_id': attrib.get('resource-id', ''),
                'content_desc': attrib.get('content-desc', ''),
                'bounds': attrib.get('bounds', ''),
                'clickable': attrib.get('clickable', 'false'),
                'enabled': attrib.get('enabled', 'false'),
            }

            line = (
                f"[{cleaned['class']}] "
                f"text='{cleaned['text']}', "
                f"id='{cleaned['resource_id']}', "
                f"desc='{cleaned['content_desc']}', "
                f"bounds={cleaned['bounds']}, "
                f"clickable={cleaned['clickable']}, "
                f"enabled={cleaned['enabled']}"
            )
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def build_prompt(self, instruction: str, xml_text: str) -> str:
        return f"""
    You are an intelligent assistant helping automate mobile app testing.

    The user gave the following instruction:
    "{instruction}"

    Here is the current mobile app screen, represented as an Appium XML page source:
    {xml_text}

    Your task is to analyze the page source, understand the user's intent, and recommend the best action(s) to perform next. You must extract both:
    1. The action (e.g., press_element, enter_text, swipe)
    2. The target element (from the page source) that matches the user's intent

    Guidelines:
    - Use `"press_element"` if the user wants to tap a button or UI element.
    - Use `"enter_text"` only if the target is a visible input field.
    - Use `"swipe"` if navigation or content scrolling is required.
    - You can match elements based on `text`, `content-desc`, `resource-id`, `label`, `value`, or other attributes found in the XML.
    - Ensure the selected target is present in the page source and relevant to the instruction.
    - If the instruction includes positions like "first", "second", "third", etc., treat it as a request to press the N-th clickable option from a list or group.

    The output must be a valid JSON array of dictionaries, each with:
    - "action": one of the above action names
    - "target": a dictionary containing required arguments for that action
    - "reason": a brief explanation of why this action is recommended

    Do not include "action" inside the "target" dictionary.
    Be accurate and concise. Do not return anything outside the JSON array.
    """.strip()

    def perform_ai_action(self, instruction: str, xml_file: str = None, xml_string: str = None, screenshot_path: str = None) -> str:
        """
        Perform an AI-driven action based on the provided instruction and XML context.

        :param instruction: The user instruction to be processed.
        :param xml_file: Path to the XML file representing the current app screen.
        :param xml_string: String representation of the XML if not using a file.
        :param screenshot_path: Path to the screenshot for context.
        :return: JSON response from the LLM with recommended actions.
        """
        try:
            suggestion =  self.handle_action(instruction, xml_file, xml_string, screenshot_path)
            internal_logger.info(f"[PopupHandler Suggestion] {suggestion}")

            for step in suggestion:
                action = step.get("action")
                target = step.get("target", {})

                if action and action in self.keyword_map:
                    element_value = next((v for k, v in target.items() if "element" or "text" in k.lower()), None)
                    self.keyword_map[action](element_value)
                else:
                    internal_logger.warning(f"Action '{action}' not found in keyword map.")
        except Exception as e:
            internal_logger.error(f"AIHander failed: {e}", exc_info=True)
