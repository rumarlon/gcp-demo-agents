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

import os
import google.auth
import pytest


def has_gcp_credentials() -> bool:
    """Returns True if valid GCP credentials or ADC can be loaded."""
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    ):
        return True
    try:
        credentials, _ = google.auth.default()
        return credentials is not None
    except Exception:
        return False


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Automatically skip integration tests if GCP credentials are missing."""
    if not has_gcp_credentials():
        pytest.skip("Skipping integration test: GCP credentials not configured")
