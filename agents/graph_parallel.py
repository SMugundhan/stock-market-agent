from langgraph . graph import StateGraph, END

from core . state import StockAnalysisState

from agents . orchestrator import orchestrator_node

from agents . price_agent import price_agent_node

from agents . price_agent_quick import price_agent_quick_node

from agents . news_agent import news_agent_node

from agents . risk_agent import risk_agent_node

from agents . analyst_agent import analyst_agent_node

from agents . report_agent  import report_agent_node

def build_parallel_graph ():

    graph = StateGraph ( StockAnalysisState )

    graph . add_node ( "orchestrator", orchestrator_node )

    graph  . add_node ( "price_agent", price_agent_node )

    graph  . add_node ( "news_agent", news_agent_node )

    graph  . add_node ( "risk_agent", risk_agent_node )

    graph  . add_node ( "analyst_agent", analyst_agent_node )

    graph  . add_node ( "report_agent", report_agent_node )

    graph . add_node ( "price_agent_quick", price_agent_quick_node )

    graph . set_entry_point ( "orchestrator" )

    
    # FAN OUT : orchestrator triggers all 3 simultaneously

    graph . add_edge ( "orchestrator", "price_agent" )

    graph . add_edge ( "orchestrator", "news_agent" )

    graph . add_edge ( "orchestrator", "risk_agent" )
    # Because these nodes are now 'async def' functions,
    # LangGraph's async execution engine runs them CONCURRENTLY
    # using its internal asyncio.gather()-style mechanism

    # FAN IN : async waits for all 3 to complete
    graph.add_edge("price_agent",  "analyst_agent")
    
    graph.add_edge("news_agent",   "analyst_agent")
    
    graph.add_edge("risk_agent",   "analyst_agent")

    #--------------------------------------------------
    graph.add_edge("analyst_agent", "report_agent")
    
    graph.add_edge("report_agent",  END)

    return graph.compile()