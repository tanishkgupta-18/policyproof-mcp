"""
PolicyProof MCP Server
A production-ready FastMCP server exposing tools for insurance policy evidence retrieval.
Compatible with AgenticOrg and standard MCP clients over HTTP/SSE transport.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from starlette.responses import JSONResponse

# MCP Server SDK compatibility (supports mcp 2.x and 1.x)
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

try:
    from mcp.server.sse import TransportSecuritySettings
except ImportError:
    TransportSecuritySettings = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("policyproof-mcp")

# Path to the structured local test evidence store
EVIDENCE_FILE_PATH = Path(__file__).parent / "evidence" / "policies.json"


def load_evidence_store() -> List[Dict[str, Any]]:
    """Loads policy evidence from the structured JSON store."""
    if not EVIDENCE_FILE_PATH.exists():
        logger.warning(f"Evidence file not found at {EVIDENCE_FILE_PATH}")
        return []
    try:
        with open(EVIDENCE_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("policies", [])
    except Exception as e:
        logger.error(f"Failed to load evidence file: {e}")
        return []


def search_evidence_records(policy_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Searches matching policy evidence records based on policy_id and query keywords.
    Returns strictly factual evidence records without synthesis or recommendations.
    """
    normalized_policy_id = policy_id.strip().lower()
    normalized_query = query.strip().lower()
    query_tokens = [q for q in normalized_query.split() if q]

    policies = load_evidence_store()
    target_policy = None

    for policy in policies:
        if str(policy.get("policy_id", "")).strip().lower() == normalized_policy_id:
            target_policy = policy
            break

    if not target_policy:
        logger.info(f"No policy found matching policy_id='{policy_id}'")
        return []

    raw_evidence = target_policy.get("evidence", [])
    if not query_tokens:
        # Return all evidence records for the given policy if no query keywords provided
        return [
            {
                "source": item.get("source", ""),
                "page": item.get("page", 0),
                "excerpt": item.get("excerpt", ""),
                "source_url": item.get("source_url", "")
            }
            for item in raw_evidence
        ]

    # Keyword matching against excerpt and source
    results: List[Dict[str, Any]] = []
    for item in raw_evidence:
        source_text = item.get("source", "").lower()
        excerpt_text = item.get("excerpt", "").lower()
        combined_text = f"{source_text} {excerpt_text}"

        # Match if any token is present in the record
        if any(token in combined_text for token in query_tokens):
            results.append({
                "source": item.get("source", ""),
                "page": item.get("page", 0),
                "excerpt": item.get("excerpt", ""),
                "source_url": item.get("source_url", "")
            })

    return results


# Initialize the MCP Server
mcp = FastMCP("PolicyProof MCP")


@mcp.tool()
def health_check() -> Dict[str, str]:
    """
    Performs a health check for the PolicyProof MCP server.
    Returns the server status and service name.
    """
    return {
        "status": "ok",
        "service": "PolicyProof MCP"
    }


@mcp.tool()
def search_policy_evidence(policy_id: str, query: str) -> Dict[str, Any]:
    """
    Searches the policy evidence store for citations, pages, and excerpts matching
    a specific policy ID and query terms.

    Returns factual evidence excerpts only. Does NOT evaluate claims, decide policy
    superiority, or make recommendations.
    """
    results = search_evidence_records(policy_id=policy_id, query=query)
    return {
        "policy_id": policy_id,
        "query": query,
        "results": results
    }


# Add an HTTP monitoring health endpoint for Render, Railway, or load balancer health checks
@mcp.custom_route("/health", methods=["GET"])
async def http_health_endpoint(request):
    """HTTP Health Check endpoint for cloud deployment monitoring."""
    return JSONResponse({
        "status": "ok",
        "service": "PolicyProof MCP",
        "version": "1.0.0"
    })


# Configure Host header and DNS-rebinding security settings for local development and Render deployment
ALLOWED_HOSTS = [
    "localhost",
    "localhost:*",
    "127.0.0.1",
    "127.0.0.1:*",
    "[::1]",
    "[::1]:*",
    "0.0.0.0",
    "0.0.0.0:*",
    "policyproof-mcp.onrender.com",
    "policyproof-mcp.onrender.com:*",
]

# Allow additional hosts from environment variable if configured
env_allowed_hosts = os.environ.get("ALLOWED_HOSTS")
if env_allowed_hosts:
    for h in env_allowed_hosts.split(","):
        h = h.strip()
        if h and h not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(h)
            if not h.endswith(":*"):
                ALLOWED_HOSTS.append(f"{h}:*")

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:*",
    "http://127.0.0.1",
    "http://127.0.0.1:*",
    "http://[::1]:*",
    "https://policyproof-mcp.onrender.com",
    "https://policyproof-mcp.onrender.com:*",
    "http://policyproof-mcp.onrender.com",
]

env_allowed_origins = os.environ.get("ALLOWED_ORIGINS")
if env_allowed_origins:
    for orig in env_allowed_origins.split(","):
        orig = orig.strip()
        if orig and orig not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(orig)

if TransportSecuritySettings is not None:
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=ALLOWED_HOSTS,
        allowed_origins=ALLOWED_ORIGINS,
    )
    # Export ASGI Starlette application for SSE transport with configured security settings
    app = mcp.sse_app(transport_security=transport_security)
else:
    app = mcp.sse_app()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info(f"Starting PolicyProof MCP server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)
