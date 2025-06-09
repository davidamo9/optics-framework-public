import requests
import re
import json
import defusedxml.ElementTree as ET
from optics_framework.common.logging_config import internal_logger
from optics_framework.common import utils

class PopupHandler:
    def __init__(self, ollama_model="gemma3:4b"):
        self.ollama_model = ollama_model

    def handle_popup(self, xml_file: str = None, xml_string: str = None, screenshot_path: str = None) -> str:
        xml_text = self.extract_xml_text(xml_file) if xml_file else xml_string
        if not xml_text:
            raise ValueError("Either xml_file or xml_string must be provided.")
        if not screenshot_path:
            raise ValueError("screenshot_path is not provided for popup handling.")
        prompt = self.build_prompt(xml_text)
        response = self.query_ollama(prompt, model=self.ollama_model)
        internal_logger.debug(f"[Prompt Sent to LLM]\n{prompt}")
        internal_logger.debug(f"[LLM Response]\n{response}")
        utils.save_llm_log(prompt, response, agent_name="popup_handler")
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

    def build_prompt(self, xml_text):
        return f"""
    You are an intelligent assistant analyzing an Appium XML page source representing a mobile app screen.

    Here is the extracted page structure:
    {xml_text}

    Based on the elements and their attributes, suggest the next best action the user should perform on this screen. Your suggestion can include:
    - Action name (e.g., press_element, enter_text, swipe)
    - Target (element name or description)
    - Reason for choosing this action

    Rules for your suggestions:
    - Only use `"enter_text"` if an actual text input field is clearly visible.
    - If the user must tap a button or option (e.g., "Continue", "Use without account"), use `"press_element"` with the button text.


    The output must be a valid JSON array of dictionaries, each with:
    - "action": one of the above action names
    - "target": a dictionary containing required arguments for that action
    - "reason": a brief explanation of why this action is recommended

    """.strip()
