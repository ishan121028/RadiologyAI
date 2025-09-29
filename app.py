#!/usr/bin/env python3
import logging
import os

import pathway as pw
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, InstanceOf
from pathway.xpacks.llm.servers import QASummaryRestServer
from src.server.RadiologyServer import RadiologyRestServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.mcp_server import PathwayMcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()
pw.set_license_key(os.getenv("PATHWAY_LICENSE_KEY"))

def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DEBUG_UPDATE_STREAM = _env_flag("PW_DEBUG_UPDATE_STREAM", False)


class App(BaseModel):
    """
    Radiology AI Application
    
    Follows the exact same pattern as demo-question-answering/app.py
    The YAML instantiates the question_answerer which contains the RadiologyDocumentStore
    """
    
    question_answerer: InstanceOf[BaseRAGQuestionAnswerer]
    mcp_server: InstanceOf[PathwayMcp] = None
    
    # Server configuration
    host: str
    port: int
    
    with_cache: bool = True
    terminate_on_error: bool = False
    debug_update_stream: bool = DEBUG_UPDATE_STREAM
    
    def run(self) -> None:
        """
        Run the Radiology AI application
        
        This is where the actual Pathway computation graph gets set up
        Similar to QASummaryRestServer.run() in existing examples
        """

        server = RadiologyRestServer(self.host, self.port, self.question_answerer)
        if self.mcp_server:
            logging.info(f"MCP Server: http://{self.mcp_server.host}:{self.mcp_server.port}/mcp/")

        server.run(
            with_cache=self.with_cache,
            terminate_on_error=self.terminate_on_error,
            cache_backend=pw.persistence.Backend.filesystem("Cache")
        )

    @classmethod
    def from_config(cls, config: dict) -> "App":
        """Instantiate App from YAML config while honoring debug overrides."""

        config = dict(config)
        instance = cls(**config)
        return instance

    model_config = ConfigDict(extra="forbid")


if __name__ == "__main__":
    with open("app.yaml") as f:
        config = pw.load_yaml(f)
    app = App.from_config(config)
    app.run()
