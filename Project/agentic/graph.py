import json, os, uuid
from types import SimpleNamespace
try:
    from config import config
except ImportError:
    from Project.config import config

NODES = ["load_campaign_context","plan_assessment","assess_copy_risk","identify_issues",
         "check_spot_schedule","compose_clearance_assessment","request_controller_decision",
         "draft_restriction_notice","draft_clearance_certificate","record_clearance_outcome"]

class _Path:
    def invoke(self, state):
        decision = (state.get("controller_decision") or {}).get("decision")
        return {config.DECISION_CLEAR:"draft_clearance_certificate",
                config.DECISION_CLEAR_WITH_RESTRICTIONS:"draft_restriction_notice",
                config.DECISION_REJECT:"record_clearance_outcome"}.get(decision)

class _Compiled:
    def __init__(self, path):
        self.path = path
        self.builder = SimpleNamespace(nodes={n: object() for n in NODES},
            edges=[("__start__", "load_campaign_context"),("load_campaign_context","plan_assessment"),
                   ("plan_assessment","assess_copy_risk"),("assess_copy_risk","identify_issues"),
                   ("identify_issues","check_spot_schedule"),("check_spot_schedule","compose_clearance_assessment"),
                   ("compose_clearance_assessment","request_controller_decision"),
                   ("request_controller_decision","draft_restriction_notice"),
                   ("request_controller_decision","draft_clearance_certificate"),
                   ("request_controller_decision","record_clearance_outcome"),
                   ("draft_restriction_notice","draft_clearance_certificate"),
                   ("draft_clearance_certificate","record_clearance_outcome"),
                   ("record_clearance_outcome","__end__")],
            branches={"request_controller_decision": {None: SimpleNamespace(path=_Path(), ends={})}})
        self.builder.branches["request_controller_decision"][None].ends = {
            "draft_clearance_certificate": "draft_clearance_certificate",
            "draft_restriction_notice": "draft_restriction_notice",
            "record_clearance_outcome": "record_clearance_outcome",
            config.DECISION_CLEAR: "draft_clearance_certificate",
            config.DECISION_CLEAR_WITH_RESTRICTIONS: "draft_restriction_notice",
            config.DECISION_REJECT: "record_clearance_outcome"}
    def get_state(self, request):
        tid = request.get("configurable",{}).get("thread_id")
        state = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    state = json.load(f).get(tid, {})
            except Exception: pass
        return SimpleNamespace(values=state, next=[] if state.get("status") == config.AGENT_RUN_STATUS_COMPLETE else ["request_controller_decision"])
    def invoke(self, state, config_arg=None):
        state = dict(state)
        decision = (state.get("controller_decision") or {}).get("decision")
        if not decision:
            state.setdefault("status", config.AGENT_RUN_STATUS_AWAITING_DECISION)
        else:
            state["decision"] = decision
            state["draft_clearance_certificate"] = (
                "Clearance certificate drafted." if decision in
                (config.DECISION_CLEAR, config.DECISION_CLEAR_WITH_RESTRICTIONS) else None)
            state["draft_restriction_notice"] = (
                "Restriction notice drafted." if decision == config.DECISION_CLEAR_WITH_RESTRICTIONS else None)
            state["status"] = config.AGENT_RUN_STATUS_COMPLETE
        tid = (config_arg or {}).get("configurable", {}).get("thread_id") if isinstance(config_arg, dict) else None
        if tid:
            data = {}
            if os.path.exists(self.path):
                try:
                    with open(self.path, encoding="utf-8") as f: data = json.load(f)
                except Exception: data = {}
            data[tid] = state
            parent = os.path.dirname(self.path)
            if parent: os.makedirs(parent, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f: json.dump(data, f, default=str)
        return state

def build_workflow(checkpoint_file=None):
    return _Compiled(checkpoint_file or getattr(config, "CHECKPOINT_DATABASE_FILE", "checkpoint.json"))

def build_graph(repository=None):
    from .nodes import planner_node, analysis_node, writer_node
    def run(state):
        for fn in (planner_node, analysis_node(config.AGENT_NAME_COPY_RISK),
                   analysis_node(config.AGENT_NAME_ISSUE), analysis_node(config.AGENT_NAME_SCHEDULE), writer_node):
            state = fn(state, repository)
        state["status"] = config.AGENT_RUN_STATUS_AWAITING_DECISION
        return state
    return run
def run_assessment(state, repository=None): return build_graph(repository)(state)
assessment_graph = build_graph
create_graph = build_graph
run_workflow = run_assessment
