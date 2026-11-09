from .agents import call_model
try:
    from config import config
except ImportError:
    from Project.config import config
def planner_node(state, repository=None):
    state["analyses"]=dict(state.get("analyses",{})); state["analyses"]["planner"]=call_model(config.AGENT_NAME_PLANNER,"Plan assessment",repository,state.get("run_id")); return state
def analysis_node(agent_name):
    def node(state,repository=None):
        state["analyses"]=dict(state.get("analyses",{})); state["analyses"][agent_name]=call_model(agent_name,"Assess campaign",repository,state.get("run_id")); return state
    return node
def writer_node(state,repository=None):
    # The writer is the fifth pre-decision call.  It deliberately produces a
    # deterministic draft when Gemini is unavailable, just like the analysts.
    state["analyses"]=dict(state.get("analyses",{}))
    state["analyses"]["writer"]=call_model(config.AGENT_NAME_WRITER,"Draft clearance assessment",repository,state.get("run_id"))
    state["result"]={"decision":state.get("decision",config.DECISION_CLEAR_WITH_RESTRICTIONS),"analyses":state.get("analyses",{})}; return state