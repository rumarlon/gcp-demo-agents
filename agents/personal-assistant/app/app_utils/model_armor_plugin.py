# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from typing import Any, Optional

from google.adk.plugins import BasePlugin
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1

logger = logging.getLogger(__name__)


class ModelArmorPlugin(BasePlugin):
    """ADK Security Plugin integrating Google Cloud Model Armor.

    Sanitizes user prompts before LLM inference and inspects model responses
    for security risks (prompt injection, jailbreaks, PII/SDP leakage, CSAM, malicious URLs).
    """

    def __init__(
        self,
        name: str = "model_armor_plugin",
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        template_id: Optional[str] = None,
        strict_mode: bool = False,
    ):
        super().__init__(name=name)

        self.project_id = project_id or os.getenv(
            "MODEL_ARMOR_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT")
        )
        self.location = location or os.getenv("MODEL_ARMOR_LOCATION", "us")
        self.template_id = template_id or os.getenv("MODEL_ARMOR_TEMPLATE_ID")
        self.strict_mode = (
            strict_mode
            or os.getenv("MODEL_ARMOR_STRICT_MODE", "false").lower() == "true"
        )

        self._client: Optional[modelarmor_v1.ModelArmorClient] = None

    @property
    def client(self) -> Optional[modelarmor_v1.ModelArmorClient]:
        """Lazy-initializes ModelArmorClient."""
        if self._client is None and self.template_id:
            try:
                endpoint = f"modelarmor.{self.location}.rep.googleapis.com"
                self._client = modelarmor_v1.ModelArmorClient(
                    transport="rest",
                    client_options=ClientOptions(api_endpoint=endpoint),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize ModelArmorClient: {e}. Model Armor screening will be bypassed."
                )
        return self._client

    @property
    def template_name(self) -> Optional[str]:
        if self.project_id and self.location and self.template_id:
            return f"projects/{self.project_id}/locations/{self.location}/templates/{self.template_id}"
        return None

    async def before_model_callback(
        self, agent: Any, llm_request: Any, **kwargs: Any
    ) -> Optional[Any]:
        """Sanitizes user prompt turns using Model Armor before sending to LLM."""
        if not self.template_name or not self.client:
            logger.debug(
                "Model Armor template not configured. Skipping prompt sanitization."
            )
            return None

        # Extract last user message
        if not llm_request.contents:
            return None

        last_content = llm_request.contents[-1]
        if getattr(last_content, "role", None) != "user":
            return None

        user_text_parts = [
            part.text
            for part in getattr(last_content, "parts", [])
            if hasattr(part, "text") and part.text
        ]
        if not user_text_parts:
            return None

        prompt_text = " ".join(user_text_parts)

        try:
            req = modelarmor_v1.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=modelarmor_v1.DataItem(
                    text=prompt_text,
                ),
            )
            res = self.client.sanitize_user_prompt(request=req)

            # Check for filter match / risk detection
            sanitization_result = res.sanitization_result
            filter_match_state = getattr(
                sanitization_result, "filter_match_state", None
            )

            if filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:
                logger.warning(
                    f"Model Armor flagged risk in user prompt: {sanitization_result}"
                )
                if self.strict_mode:
                    raise ValueError(
                        "Input query blocked by Google Cloud Model Armor security policy."
                    )

        except Exception as e:
            if self.strict_mode:
                raise
            logger.warning(f"Model Armor prompt screening warning: {e}")

        return None

    async def after_model_callback(
        self, agent: Any, llm_response: Any, **kwargs: Any
    ) -> Optional[Any]:
        """Inspects model response output for security or sensitivity violations."""
        if not self.template_name or not self.client or not llm_response:
            return None

        response_text = getattr(llm_response, "text", None)
        if not response_text:
            return None

        try:
            req = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=modelarmor_v1.DataItem(text=response_text),
            )
            res = self.client.sanitize_model_response(request=req)

            sanitization_result = res.sanitization_result
            if (
                getattr(sanitization_result, "filter_match_state", None)
                == modelarmor_v1.FilterMatchState.MATCH_FOUND
            ):
                logger.warning(
                    f"Model Armor flagged risk in model response: {sanitization_result}"
                )

        except Exception as e:
            logger.warning(f"Model Armor response screening warning: {e}")

        return None
