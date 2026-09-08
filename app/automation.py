from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class StudentTask:
    full_name: str
    university_id: str
    national_id: str
    program_name: str
    section_name: str


class AutomationManager:
    def __init__(self, driver_path: str | None = None):
        self.driver_path = driver_path

    def build_driver(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        if self.driver_path:
            return webdriver.Chrome(executable_path=self.driver_path, options=options)
        return webdriver.Chrome(options=options)

    def run_commands(self, student: StudentTask, commands: list[dict[str, Any]], lecture_url: str):
        driver = self.build_driver()
        try:
            driver.get(lecture_url)
            wait = WebDriverWait(driver, 20)

            for command in commands:
                selector_type = command["selector_type"]
                selector_value = command["selector_value"]
                value_template = command.get("value_template")
                command_type = command["command_type"]

                if command_type == "open_url":
                    driver.get(selector_value)
                    continue

                by = self._map_by(selector_type)
                wait.until(EC.presence_of_element_located((by, selector_value)))

                if command_type == "fill":
                    rendered = self._render_value(value_template, student)
                    element = driver.find_element(by, selector_value)
                    element.clear()
                    element.send_keys(rendered)
                elif command_type == "click":
                    driver.find_element(by, selector_value).click()
                elif command_type == "wait":
                    import time
                    time.sleep(float(command.get("wait_seconds", 0) or 0))

        finally:
            driver.quit()

    def _map_by(self, selector_type: str):
        mapping = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
        }
        return mapping.get(selector_type.lower(), By.CSS_SELECTOR)

    def _render_value(self, value_template: str | None, student: StudentTask):
        values = {
            "full_name": student.full_name,
            "university_id": student.university_id,
            "national_id": student.national_id,
            "program_name": student.program_name,
            "section_name": student.section_name,
        }
        if not value_template:
            return ""

        for key, value in values.items():
            value_template = value_template.replace(f"{{{key}}}", str(value))
        return value_template
