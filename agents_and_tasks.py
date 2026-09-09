"""Backward-compatible imports for the MVC banking controller."""

from controllers.banking_controller import build_crew, handle_banking_request
from services.llm_service import MODEL_NAME, build_llm

run_banking_request = handle_banking_request

__all__ = ["MODEL_NAME", "build_crew", "build_llm", "run_banking_request"]
