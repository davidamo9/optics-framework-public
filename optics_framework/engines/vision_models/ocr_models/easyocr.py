from typing import List, Tuple, Optional
import easyocr
import cv2
from optics_framework.common.text_interface import TextInterface
from optics_framework.common import utils
from optics_framework.common.logging_config import internal_logger




class EasyOCRHelper(TextInterface):
    """
    Helper class for Optical Character Recognition (OCR) using EasyOCR.

    This class uses EasyOCR to detect text in images and optionally locate
    specific reference text.
    """

    def __init__(self, language: str = "en"):
        """
        Initializes the EasyOCR reader.

        :param language: Language code for OCR (default: "en").
        :type language: str

        :raises RuntimeError: If EasyOCR fails to initialize.
        """
        try:
            self.reader = easyocr.Reader([language])
            # internal_logger.debug(f"EasyOCR initialized with language: {language}")
        except Exception as e:
            internal_logger.error(f"Failed to initialize EasyOCR: {e}")
            raise RuntimeError("EasyOCR initialization failed.") from e

    def find_element(
        self, input_data, text, index=None
    ) -> tuple[bool, tuple[int, int], tuple[tuple[int, int], tuple[int, int]]] | None:
        """
        Locate multiple instances of a specific text in the given frame using OCR and return the center coordinates
        of the text at the given index with bounding box coordinates.

        Parameters:
        - input_data (np.array): Image data of the frame.
        - text (str): The text to locate in the frame.
        - index (int): The index of the match to retrieve.

        Returns:
        - bool: True if the text is found, False otherwise.
        - tuple: (x, y) coordinates of the center of the indexed text in the frame or (None, None) if out of bounds.
        - tuple: Bounding box coordinates of the detected text.
        """
        _, ocr_results = self.detect_text(input_data)

        detected_texts = []

        # Iterate over each detected text
        if ocr_results is not None:
            for bbox, detected_text, confidence in ocr_results:
                detected_text = detected_text.strip()
                if text in detected_text:
                    top_left_ocr = bbox[0]  # (x1, y1)
                    bottom_right_ocr = bbox[2]  # (x3, y3)

                    x_top_left, y_top_left = int(top_left_ocr[0]), int(top_left_ocr[1])
                    x_bottom_right, y_bottom_right = (
                        int(bottom_right_ocr[0]),
                        int(bottom_right_ocr[1]),
                    )

                    # Create the (x,y) tuples for cv2.rectangle
                    pt1 = (x_top_left, y_top_left)
                    pt2 = (x_bottom_right, y_bottom_right)

                    w = x_bottom_right - x_top_left
                    h = y_bottom_right - y_top_left

                    # Calculate the center coordinates
                    center_x = x_top_left + w // 2
                    center_y = y_top_left + h // 2

                    detected_texts.append((True, (center_x, center_y), (pt1, pt2)))

                    # Draw bounding box around the detected text
                    cv2.rectangle(input_data, pt1, pt2, (0, 255, 0), 2)
                    cv2.circle(input_data, (center_x, center_y), 5, (0, 0, 255), -1)

        if not detected_texts:
            return None
        if index is not None:
            # Return the requested index
            if 0 <= index < len(detected_texts):
                return detected_texts[index]
            return None

        utils.save_screenshot(
            input_data, "annotated_frame"
        )
        return detected_texts[0]

    def detect_text(self, input_data) -> Optional[Tuple[str, List[Tuple[List[List[int]], str, float]]]]:
        """
        Detects text in the given image using EasyOCR.

        :param input_data: Image data (numpy array).
        :return: List of tuples (bounding box, text, confidence) or None.
        """
        gray_image = cv2.cvtColor(input_data, cv2.COLOR_BGR2GRAY)
        results = self.reader.readtext(gray_image)
        if not results:
            return None
        detected_text = ' '.join(result[1] for result in results)
        return detected_text, results

    def element_exist(self, input_data, reference_data):
        return super().element_exist(input_data, reference_data)
