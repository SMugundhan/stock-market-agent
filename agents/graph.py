from langgraph.graph import StateGraph, END

# StateGraph = the main class for the graph, which contains the states and transitions

# END = a special state that represents the end of the graph

from core.state import StockAnalysisState #import our shared state definition

from agents.price_agent import price_agent_node

from agents.analyst_agent import analyst_agent_node

from agents.news_agent import news_agent_node

from agents.risk_agent import risk_agent_node

from agents.orchestrator import orchestrator_node

from agents.error_handler import error_handler_node

from agents.routing import route_after_analyst, route_after_orchestrator

from agents. report_agent import report_agent_node

from agents. price_agent_quick import price_agent_quick_node

def build_graph ():

    """ This function builds and returns the state graph for our stock analysis agent.      
    graph flow : START -> Price Agent -> Analyst Agent -> END
    """ 
    # Step 1 : Create the graph with our state definition

    graph = StateGraph ( StockAnalysisState )

    # Step 2 : add nodes to the graph

    graph . add_node ( "orchestrator", orchestrator_node )

    graph . add_node ( "price_agent" , price_agent_node )

    graph . add_node ( "price_agent_quick", price_agent_quick_node )

    graph . add_node ( "news_agent" , news_agent_node )

    graph . add_node ( "risk_agent", risk_agent_node )

    graph . add_node ( "analyst_agent" , analyst_agent_node )
    
    graph . add_node ( "report_agent", report_agent_node )

    graph . add_node ( "error_handler", error_handler_node )

    # Step 3 : Set the entry point of the graph to be the price agent

    graph . set_entry_point ( "orchestrator" )

    # Conditional edge after orchestrator

    graph . add_conditional_edges ( 'orchestrator', route_after_orchestrator, { "price_agent" : "price_agent", "price_agent_quick" : "price_agent_quick" , "error_handler" : "error_handler" } )
    # Price agent -> normal route, error handler -> error route
    # When route_after_orchestrator() returns "price_agent"
    # → LangGraph goes to price_agent node
    # When it returns "error_handler"
    # → LangGraph goes to error_handler node

    # Step 4 : Connect the nodes with edges to define the flow

    # full pipeline

    graph . add_edge ( "price_agent" , "news_agent" )

    graph . add_edge ( "news_agent", "risk_agent" )

    graph . add_edge ( "risk_agent" , "analyst_agent" )

    # quick Pipeline------------------

    graph . add_edge ( "price_agent_quick", "report_agent" )

    # Conditional edge after analyst

    graph . add_conditional_edges ( "analyst_agent", route_after_analyst, { "report_agent" : "report_agent", "retry_analyst" : "analyst_agent" } )
    # from analyst -> Routing if success END else loop

    # Step 5 : Connect the last node to END to signify the end of the graph

    graph . add_edge ( "report_agent", END )

    graph . add_edge ( "error_handler", END ) # after analyst agent finishes, we are done

    # Step 6 : Compile the graph

    compiled_graph = graph . compile ( )

    return compiled_graph