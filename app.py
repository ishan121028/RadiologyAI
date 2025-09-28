#!/usr/bin/env python3

"""
CriticalAlert AI - Real-time Emergency Radiology Alert System

Main application following exact Pathway patterns - similar to demo-question-answering/app.py
but specialized for radiology report processing and critical alert generation.
"""

import logging
import os

import pathway as pw
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, InstanceOf
from pathway.xpacks.llm.servers import QASummaryRestServer

# Import Pathway's built-in RAG components
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DEBUG_UPDATE_STREAM = _env_flag("PW_DEBUG_UPDATE_STREAM", False)


class App(BaseModel):
    """
    CriticalAlert AI Application
    
    Follows the exact same pattern as demo-question-answering/app.py
    The YAML instantiates the critical_alert_answerer which contains the RadiologyDocumentStore
    """
    
    # Use Pathway's built-in BaseRAGQuestionAnswerer
    question_answerer: InstanceOf[BaseRAGQuestionAnswerer]
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 49000
    
    # Caching and persistence (same as other apps)
    with_cache: bool = True
    terminate_on_error: bool = False
    debug_update_stream: bool = DEBUG_UPDATE_STREAM
    
    def run(self) -> None:
        """
        Run the CriticalAlert AI application
        
        This is where the actual Pathway computation graph gets set up
        Similar to QASummaryRestServer.run() in existing examples
        """
        
        # Use Pathway's built-in QASummaryRestServer - exactly like demo-question-answering
        server = QASummaryRestServer(self.host, self.port, self.question_answerer)
        
        logging.info("🚀 CriticalAlert AI Server Starting...")
        logging.info(f"📡 Server: http://{self.host}:{self.port}")
        logging.info("📋 Standard Pathway RAG endpoints:")
        logging.info("  POST /v1/pw_ai_answer - Medical query answering")
        logging.info("  POST /v1/pw_ai_retrieve - Document retrieval")
        logging.info("  POST /v1/statistics - Processing statistics")
        logging.info("🔄 Using LandingAI parser for medical document processing...")
        
        # Run with standard Pathway server (should eliminate crashes)
        server.run(
            with_cache=self.with_cache,
            terminate_on_error=self.terminate_on_error,
            cache_backend=pw.persistence.Backend.filesystem("Cache"),
        )

    @classmethod
    def from_config(cls, config: dict) -> "App":
        """Instantiate App from YAML config while honoring debug overrides."""

        config = dict(config)
        debug_override = config.pop("debug_update_stream", None)
        instance = cls(**config)
        if debug_override is not None:
            instance.debug_update_stream = bool(debug_override)
        return instance

    model_config = ConfigDict(extra="forbid")


if __name__ == "__main__":
    # EXACT same pattern as demo-question-answering/app.py
    with open("app.yaml") as f:
        config = pw.load_yaml(f)
    app = App.from_config(config)
    app.run()
