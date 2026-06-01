"""Tool catalog loader and scope enforcement."""

from typing import Any, Dict, List, Optional

from .auth import validate_scope, get_principal_scopes
from .config import config
from .specs import load_tools_spec


class ToolCatalog:
    """Catalog of available tools with scope validation."""

    def __init__(self):
        self.tools = load_tools_spec().get("tools", {})
        self.shared_secret = config.AGENT_SHARED_SECRET

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        return list(self.tools.keys())

    def validate_tool_access(
        self,
        tool_name: str,
        principal: str
    ) -> bool:
        """Check if principal can access tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        
        required_scopes = tool.get("required_scopes", [])
        principal_scopes = get_principal_scopes(principal)
        
        return all(
            validate_scope(scope, principal_scopes)
            for scope in required_scopes
        )

    def get_tools_for_principal(self, principal: str) -> List[Dict[str, Any]]:
        """Get tools accessible to principal."""
        accessible_tools = []
        for tool_name, tool in self.tools.items():
            if self.validate_tool_access(tool_name, principal):
                accessible_tools.append(tool)
        return accessible_tools


# Global tool catalog instance
tool_catalog = ToolCatalog()
