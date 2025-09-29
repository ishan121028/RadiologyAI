from pathway.xpacks.llm.servers import QARestServer
from src.intelligence.critical_alert_answerer import RadiologyQuestionAnswerer

class RadiologyRestServer(QARestServer):
    """
    Creates a REST Server for radiology document processing and patient queries.
    
    Inherits all standard endpoints from QARestServer:
    - ``/v1/retrieve`` - document retrieval
    - ``/v1/statistics`` - system statistics  
    - ``/v1/pw_list_documents`` - document listing
    - ``/v1/pw_ai_answer`` - question answering
    - ``/v2/list_documents`` - document listing (v2)
    - ``/v2/answer`` - question answering (v2)
    
    Adds patient-specific endpoints:
    - ``/v1/search_patient_by_id`` - search by patient ID
    - ``/v1/query_patient_extraction`` - query patient extraction data

    Args:
        host: host on which server will run
        port: port on which server will run
        rag_question_answerer: instance of ``RadiologyQuestionAnswerer`` which is used
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
        # QARestServer already registers all standard endpoints (retrieve, statistics, etc.)
        super().__init__(host, port, rag_question_answerer, **rest_kwargs)

        # Only register our custom patient-specific endpoints
        self.serve(
            "/v1/search_patient_by_id",
            rag_question_answerer.PatientSearchSchema,
            rag_question_answerer.search_patient_by_id,
            **rest_kwargs,
        )
        self.serve(
            "/v1/query_patient_extraction",
            rag_question_answerer.PatientQuerySchema,
            rag_question_answerer.query_patient_extraction,
            **rest_kwargs,
        )


