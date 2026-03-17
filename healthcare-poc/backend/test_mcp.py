"""Quick test to verify MCP ehr_lookup works via MCPClient through an Agent."""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient


def test_mcp_ehr():
    client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="python", args=["mcp_ehr_server.py"])
        )
    )

    with client:
        tools = client.list_tools_sync()
        print(f"Tools from MCP server: {[t.tool_name for t in tools]}")
        assert any(t.tool_name == "ehr_lookup" for t in tools), "ehr_lookup not found!"
        print("PASS: ehr_lookup tool is registered in MCP server")

        # Test via Agent (the real usage path)
        model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt="You are a clinical assistant. Use ehr_lookup to fetch patient data. Always call the tool.",
        )

        result = agent("[Patient ID: P001] Fetch the EHR record for patient P001")
        print(f"\nAgent response for P001:\n{result}")
        print("\nPASS: MCP ehr_lookup called successfully via Agent")


if __name__ == "__main__":
    test_mcp_ehr()
