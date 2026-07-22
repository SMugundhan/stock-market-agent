# agents/llm_orchestrator.py

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
# These message types represent the conversation history
# that the LLM sees when it's deciding what tool to call next

from core.config import config
from agents.tools import (
    get_stock_price,
    get_stock_news,
    calculate_risk,
    get_full_analysis
)

# Initialize LLM and bind tools to it
llm = ChatGroq(
    api_key=config.GROQ_API_KEY,
    model_name=config.MODEL_NAME
)

# .bind_tools() tells the LLM "these are the tools available to you"
# The LLM will see each tool's name and description and can
# autonomously decide which ones to call
llm_with_tools = llm.bind_tools([
    get_stock_price,
    get_stock_news,
    calculate_risk,
    get_full_analysis
])


async def run_llm_orchestrator(user_query: str, session_id: str = "default") -> str:
    """
    LLM-driven orchestrator — the LLM decides which tools to call.

    This is fundamentally different from our rule-based orchestrator:
    - No hardcoded if/else logic
    - LLM reads the query and autonomously selects tools
    - LLM can handle queries we never explicitly programmed for
    """

    print(f"\n🤖 LLM Orchestrator received: '{user_query}'")

    # System prompt — defines the LLM's role and behavior
    system_prompt = """You are an intelligent stock market analysis assistant.
You have access to tools that can fetch real-time stock data.

Your job:
1. Understand what the user is asking
2. Choose the RIGHT tools for their specific question
   - Simple price question → use get_stock_price only
   - News/sentiment question → use get_stock_news only
   - Risk question → use calculate_risk only
   - Full analysis request → use get_full_analysis
3. Call tools with correct ticker symbols
4. Synthesize tool results into a clear, helpful answer

Always extract the ticker symbol from the user's query.
Common mappings: Apple=AAPL, Tesla=TSLA, Google=GOOGL, Microsoft=MSFT
"""

    # Build conversation — starts with system context + user's question
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
        # HumanMessage = what the user said
    ]

    # ── ReAct Loop ────────────────────────────────────────
    # The LLM keeps going until it decides it has enough info
    max_iterations = 5
    # Safety limit — prevents infinite loops if LLM keeps calling tools

    for iteration in range(max_iterations):
        print(f"\n🔄 Iteration {iteration + 1}")

        # Ask LLM what to do next
        response = await llm_with_tools.ainvoke(messages)
        # response could be:
        # A) A tool call decision: "call get_stock_price with ticker='AAPL'"
        # B) A final text answer: "Based on the data, AAPL is..."

        messages.append(response)
        # Add LLM's response to conversation history
        # This builds the context for the next iteration

        # Check if LLM wants to call any tools
        if not response.tool_calls:
            # No tool calls = LLM has decided it has enough info
            # and is giving a final text answer
            print(f"✅ LLM finished — providing final answer")
            return response.content

        # LLM wants to call one or more tools
        for tool_call in response.tool_calls:
            # tool_calls is a list because LLM can call multiple tools
            # in a single response

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            # tool_call_id is a unique identifier that links the
            # tool call request to its result in the conversation

            print(f"🔧 LLM calling tool: {tool_name}({tool_args})")

            # Find and execute the tool the LLM requested
            tool_map = {
                "get_stock_price":  get_stock_price,
                "get_stock_news":   get_stock_news,
                "calculate_risk":   calculate_risk,
                "get_full_analysis": get_full_analysis
            }

            tool_fn = tool_map.get(tool_name)

            if tool_fn:
                try:
                    tool_result = await tool_fn.aiinvoke(tool_args)
                    # .invoke() executes the actual tool function
                    print(f"📊 Tool result: {str(tool_result)[:100]}...")
                except Exception as e:
                    tool_result = f"Tool failed: {str(e)}"
                    print(f"❌ Tool error: {e}")
            else:
                tool_result = f"Unknown tool: {tool_name}"

            # Add tool result to conversation so LLM can see it
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call_id
                # Linking result back to the specific tool call request
                # LLM needs this to understand which result belongs to which call
            ))

    # If we hit max_iterations without a final answer
    return "Analysis incomplete — maximum iterations reached."