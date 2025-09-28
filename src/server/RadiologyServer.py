from pathway.xpacks.llm.servers import QARestServer
from src.intelligence.critical_alert_answerer import RadiologyQuestionAnswerer

class RadiologyRestServer(QARestServer):
    """
    Creates a REST Server for answering queries to a given instance of ``BaseQuestionAnswerer``.
    It exposes four endpoints:
    - ``/v1/retrieve`` which is answered using ``retrieve`` method,
    - ``/v1/statistics`` which is answered using ``statistics`` method,
    - ``/v1/pw_list_documents`` which is answered using ``list_documents`` method,
    - ``/v1/pw_ai_answer`` which is answered using ``answer_query`` method,
    - ``/v2/list_documents`` which is answered using ``list_documents`` method,
    - ``/v2/answer`` which is answered using ``answer_query`` method,

    Args:
        host: host on which server will run
        port: port on which server will run
        rag_question_answerer: instance of ``BaseQuestionAnswerer`` which is used
            to answer queries received in the endpoints.
        rest_kwargs: optional kwargs to be passed to ``pw.io.http.rest_connector``
    """

    def __init__(
        self,
        host: str,
        port: int,
        rag_question_answerer: RadiologyQuestionAnswerer,
        **rest_kwargs,
    ):
        super().__init__(host, port, **rest_kwargs)

        self.serve(
            "/v1/retrieve",
            rag_question_answerer.RetrieveQuerySchema,
            rag_question_answerer.retrieve,
            **rest_kwargs,
        )
        self.serve(
            "/v1/statistics",
            rag_question_answerer.StatisticsQuerySchema,
            rag_question_answerer.statistics,
            **rest_kwargs,
        )

        self.serve(
            "/v1/pw_list_documents",
            rag_question_answerer.InputsQuerySchema,
            rag_question_answerer.list_documents,
            **rest_kwargs,
        )
        self.serve(
            "/v1/pw_ai_answer",
            rag_question_answerer.AnswerQuerySchema,
            rag_question_answerer.answer_query,
            **rest_kwargs,
        )
        self.serve(
            "/v2/list_documents",
            rag_question_answerer.InputsQuerySchema,
            rag_question_answerer.list_documents,
            **rest_kwargs,
        )
        self.serve(
            "/v2/answer",
            rag_question_answerer.AnswerQuerySchema,
            rag_question_answerer.answer_query,
            **rest_kwargs,
        )

        # Custom patient tools are only available through MCP, not REST
        # This avoids potential conflicts with double delegation
        # MCP: http://localhost:8123/mcp
        # Tools: search_patient_by_id, query_patient_extraction