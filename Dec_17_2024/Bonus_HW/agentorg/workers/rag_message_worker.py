import logging

from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI

from agentorg.workers.worker import BaseWorker, register_worker
from agentorg.workers.message_worker import MessageWorker
from agentorg.workers.rag_worker import RAGWorker
from agentorg.utils.graph_state import MessageState
from agentorg.utils.model_config import MODEL


logger = logging.getLogger(__name__)


@register_worker
class RagMsgWorker(BaseWorker):

    description = "A combination of RAG and Message Workers"

    def __init__(self):
        super().__init__()
        self.action_graph = self._create_action_graph()
        self.llm = ChatOpenAI(model=MODEL["model_type_or_path"], timeout=30000)
     
    def _create_action_graph(self):
        workflow = StateGraph(MessageState)
        # Add nodes for each worker
        rag_wkr = RAGWorker()
        msg_wkr = MessageWorker()
        workflow.add_node("rag_worker", rag_wkr.execute)
        workflow.add_node("message_worker", msg_wkr.execute)
        # Add edges
        workflow.add_edge(START, "rag_worker")
        workflow.add_edge("rag_worker", "message_worker")
        return workflow

    def execute(self, msg_state: MessageState):
        graph = self.action_graph.compile()
        result = graph.invoke(msg_state)
        return result
