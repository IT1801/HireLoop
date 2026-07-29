from langgraph.graph import StateGraph, END, START
from src.components.graphs.state import HireLoopState
from src.components.graphs.edges import check_responses
from src.components.agents.jd_generator import generate_jd_node, approve_jd_node
from src.components.agents.job_poster import generate_post_node, approve_post_node, wait_for_apps_node
from src.components.agents.application_collecter import application_collector
from src.components.agents.resume_screener import resume_screener
from src.components.agents.calender_checker import calendar_checker
from src.components.agents.scheduler_email import draft_schedule_emails, approve_schedule_emails, scheduler_email
from src.components.agents.result_email import result_preparer, result_email
from src.components.checkpointer.setup import get_checkpointer

def build_graph():
    """
    Constructs and compiles the HireLoop LangGraph.
    """
    workflow = StateGraph(HireLoopState)

    # Add Nodes
    workflow.add_node("generate_jd", generate_jd_node)
    workflow.add_node("approve_jd", approve_jd_node)
    workflow.add_node("generate_post", generate_post_node)
    workflow.add_node("approve_post", approve_post_node)
    workflow.add_node("wait_for_apps", wait_for_apps_node)
    workflow.add_node("application_collector", application_collector)
    workflow.add_node("resume_screener", resume_screener)
    workflow.add_node("calendar_checker", calendar_checker)
    workflow.add_node("draft_schedule_emails", draft_schedule_emails)
    workflow.add_node("approve_schedule_emails", approve_schedule_emails)
    workflow.add_node("scheduler_email", scheduler_email)
    workflow.add_node("result_preparer", result_preparer)
    workflow.add_node("result_email", result_email)

    # Define Edges
    workflow.add_edge(START, "generate_jd")
    workflow.add_edge("generate_jd", "approve_jd")
    workflow.add_edge("approve_jd", "generate_post")
    workflow.add_edge("generate_post", "approve_post")
    workflow.add_edge("approve_post", "wait_for_apps")
    workflow.add_edge("wait_for_apps", "application_collector")
    
    # Conditional edge to loop back if not enough responses
    workflow.add_conditional_edges(
        "application_collector",
        check_responses,
        {
            "jd_generator": "generate_jd",
            "resume_screener": "resume_screener"
        }
    )
    
    workflow.add_edge("resume_screener", "calendar_checker")
    workflow.add_edge("calendar_checker", "draft_schedule_emails")
    workflow.add_edge("draft_schedule_emails", "approve_schedule_emails")
    workflow.add_edge("approve_schedule_emails", "scheduler_email")
    workflow.add_edge("scheduler_email", "result_preparer")
    workflow.add_edge("result_preparer", "result_email")
    workflow.add_edge("result_email", END)

    # Compile with checkpointer
    checkpointer = get_checkpointer()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
