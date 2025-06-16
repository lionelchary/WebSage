from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables
load_dotenv()

# Initialize the OpenAI model
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Configure Firecrawl MCP server parameters
server_params = StdioServerParameters(
    command="npx",
    env={
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY"),
    },
    args=["firecrawl-mcp"]
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can scrape websites, crawl pages, and extract data using Firecrawl tools. Think step by step and use the appropriate tools to help the user."
                }
            ]

            print("Available Tools -", *[tool.name for tool in tools])
            print("-" * 60)
            
            # Start the conversation loop
            while True:
                user_input = input("\n🗣️  You: ")
                # If the user wants to quit, break the loop
                if user_input.lower() in ["quit", "exit", "q", "exit"]:
                    print("👋 Goodbye!")
                    break
                # If the user input is empty, skip to the next iteration
                if not user_input.strip():
                    continue
                # Add user input to conversation history
                messages.append({"role": "user", "content": user_input[:175000]})

                try:
                    agent_response = await agent.ainvoke({"messages": messages})

                    ai_message = agent_response["messages"][-1].content
                    print(f"\n🤖 Agent: {ai_message}")
                except Exception as e:
                    print("Error:", e)


if __name__ == "__main__":
    asyncio.run(main())