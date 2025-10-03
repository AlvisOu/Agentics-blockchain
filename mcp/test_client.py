import asyncio
from fastmcp import Client

async def main():
    # Point the client to your local MCP server script
    client = Client("./smart_contract_server.py")

    async with client:
        # Quick sanity check
        await client.ping()
        print("Connected to MCP server")

        # List available tools exposed by smartcontract_fastmcp.py
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Example: check contract status
        status = await client.call_tool("contract_status", {})
        print("Contract status:", status)

        deposit_res = await client.call_tool("pay_deposit", {})
        print("Deposit:", deposit_res)

        # Example: tenant pays rent for month 1
        result = await client.call_tool("pay_rent", {"month": 1})
        print("Pay rent tx:", result)


asyncio.run(main())
