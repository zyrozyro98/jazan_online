from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


class RenderManager:
    """Render API helper for checking the service status before launching the app."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path(__file__).resolve().parent.parent / "render_config.json"

    def load_config(self):
        if not self.config_path.exists():
            return {}
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config: dict[str, Any]):
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def api_request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None):
        config = self.load_config()
        api_key = config.get("api_key", "")
        if not api_key:
            return None, {"error": "api_key_missing"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = endpoint
        if not url.startswith("http"):
            base_url = config.get("api_base_url", "https://api.render.com/v1/services")
            url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")

        try:
            response = requests.request(method=method, url=url, headers=headers, json=payload, timeout=20)
            return response, response.json() if response.content else {}
        except Exception as exc:
            return None, {"error": str(exc)}

    def get_service_status(self):
        config = self.load_config()
        service_id = config.get("service_id", "")
        api_key = config.get("api_key", "")

        if not service_id or not api_key:
            return {
                "can_start": False,
                "status": "not_configured",
                "message": "Render API غير مهيأ. قم بإدخال service_id و api_key داخل render_config.json قبل التشغيل.",
            }

        response, data = self.api_request("GET", f"{service_id}")
        if response is None or response.status_code != 200:
            error_text = data.get("error") or data.get("message") or "فشل في الاتصال بـ Render"
            return {
                "can_start": False,
                "status": "api_error",
                "message": f"تعذر التحقق من خدمة Render: {error_text}",
            }

        raw_status = data.get("status", "unknown")
        service_info = data.get("service", data)
        suspended = bool(service_info.get("suspended", False))

        normalized_status = str(raw_status).lower()
        can_start = normalized_status in {"live", "active", "running", "deployed"} and not suspended

        config["status"] = normalized_status
        config["suspended"] = suspended
        config["enabled"] = can_start
        self.save_config(config)

        if can_start:
            return {
                "can_start": True,
                "status": normalized_status,
                "message": "تم تفعيل الاستخدام بنجاح، ويمكن فتح التطبيق الآن.",
            }

        return {
            "can_start": False,
            "status": normalized_status,
            "message": "الخدمة متوقفة أو غير مفعلة من قبل المطور في Render، لذلك تم منع فتح التطبيق حتى يتم تفعيلها.",
        }
