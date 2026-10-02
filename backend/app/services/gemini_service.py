"""
Google Gemini Service for MAHA-GR (महाराष्ट्र शासन निर्णय AI).
Provides:
- Supported Gemini Flash LLM generation strictly grounded in retrieved official GR evidence.
- Marathi-first prompt engineering preserving eligibility conditions, numerical values, and exceptions.
- Clear distinction between official source text and explanatory guidance.
- Insufficient-evidence detection and disclaimer of legal authority.
- Integration with dedicated EmbeddingService.
"""
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.embedding_service import EmbeddingService

_is_configured = False


def setup_gemini():
    global _is_configured
    if _is_configured:
        return
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _is_configured = True
            logger.info("Google Gemini AI client configured successfully.")
        except Exception as e:
            logger.error(f"Error configuring Google Gemini: {e}")


class GeminiService:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Delegates to dedicated EmbeddingService for document chunk embedding."""
        return EmbeddingService.get_document_embedding(text)

    @staticmethod
    def get_query_embedding(query: str) -> List[float]:
        """Delegates to dedicated EmbeddingService for retrieval query embedding."""
        return EmbeddingService.get_query_embedding(query)

    @classmethod
    def generate_grounded_answer(
        cls,
        query: str,
        context_passages: List[Dict[str, Any]],
        language: str = "mr",
        insufficient_evidence: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generates an answer strictly grounded in retrieved Maharashtra GR passages.
        Enforces evidence-based facts in the requested language (Marathi/Hindi/English).
        Preserves eligibility conditions, exceptions, and disclaims legal authority.
        """
        setup_gemini()

        # If retrieval is deemed insufficient, return an honest message without hallucinating
        if insufficient_evidence or not context_passages:
            return cls._get_insufficient_evidence_message(query, language)

        # Format context blocks
        formatted_context = ""
        for idx, item in enumerate(context_passages, 1):
            formatted_context += (
                f"\n--- [अधिकृत शासन निर्णय पुरावा {idx} / Official Evidence {idx}] ---\n"
                f"दस्तऐवज (Document): {item.get('document_title', 'Maharashtra GR')}\n"
                f"शासन निर्णय क्रमांक (GR Number): {item.get('gr_number') or 'N/A'}\n"
                f"विभाग (Department): {item.get('department') or 'General'}\n"
                f"पृष्ठ क्रमांक (Page): {item.get('page') or 'N/A'}\n"
                f"विभाग/कलम (Section): {item.get('section') or 'N/A'}\n"
                f"अधिकृत मजकूर (Official Text):\n{item.get('text', '').strip()}\n"
            )

        prompts_by_language = {
            "mr": {
                "role": (
                    "तुम्ही महाराष्ट्र शासन निर्णयांचे (MAHA-GR) अधिकृत आणि विश्वासू AI विश्लेषक आहात.\n"
                    "खाली दिलेल्या अधिकृत शासन निर्णय पुराव्यांच्या आधारे विचारलेल्या प्रश्नाचे मुद्देसूद आणि स्पष्ट उत्तर मराठीत द्या."
                ),
                "rules": (
                    "कडक नियम (Strict Grounding Rules):\n"
                    "१. फक्त आणि फक्त वर दिलेल्या अधिकृत पुराव्यांमधील माहितीवर आधारित उत्तर द्या. मनाने कोणतीही माहिती, आकडेवारी किंवा तारीख जोडू नका.\n"
                    "२. शासन निर्णयातील पात्रता (Eligibility), अटी व शर्ती (Conditions), आणि अपवाद (Exceptions) जसेच्या तसे अचूक मांडा.\n"
                    "३. प्रशासकीय भाषा कठीण असल्यास नागरिकांना समजेल अशा सुलभ भाषेत स्पष्टीकरण द्या, परंतु मूळ शासन नियमाचा अर्थ बदलू नये.\n"
                    "४. जर पुराव्यांमध्ये विचारलेल्या प्रश्नाचे संपूर्ण उत्तर नसेल, तर तसे प्रामाणिकपणे स्पष्ट लिहा.\n"
                    "५. हे उत्तर केवळ माहितीसाठी असून कायदेशीर सल्ला नाही असा स्पष्ट संदेश उत्तराच्या शेवटी असावा."
                ),
                "disclaimer": "सूचना: हे उत्तर उपलब्ध शासन निर्णयांच्या आधारे स्वयंचलित तयार केले असून हा अधिकृत कायदेशीर सल्ला नाही. कृपया मूळ शासन निर्णय तपासा.",
            },
            "hi": {
                "role": (
                    "आप महाराष्ट्र शासन निर्णयों (MAHA-GR) के आधिकारिक और विश्वसनीय एआई सहायक हैं।\n"
                    "नीचे दिए गए आधिकारिक साक्ष्यों के आधार पर पूछे गए प्रश्न का स्पष्ट और सटीक उत्तर हिंदी में दें।"
                ),
                "rules": (
                    "सख्त नियम (Strict Grounding Rules):\n"
                    "१. केवल ऊपर दिए गए आधिकारिक साक्ष्यों पर आधारित उत्तर दें। बिना प्रमाण के कोई भी जानकारी न जोड़ें।\n"
                    "२. शासन आदेश में दी गई पात्रता (Eligibility), शर्तें और अपवाद (Exceptions) को बिना बदले सही ढंग से प्रस्तुत करें।\n"
                    "३. यदि उपलब्ध साक्ष्य में पूरा उत्तर नहीं है, तो स्पष्ट रूप से बताएं कि जानकारी अपूर्ण है।\n"
                    "४. यह केवल सूचनात्मक सहायता है और कानूनी सलाह नहीं है।"
                ),
                "disclaimer": "सूचना: यह उत्तर केवल सूचनात्मक उद्देश्य के लिए है और कोई आधिकारिक कानूनी सलाह नहीं है। कृपया मूल जी.आर. देखें।",
            },
            "en": {
                "role": (
                    "You are the official MAHA-GR assistant specializing in Maharashtra Government Resolutions.\n"
                    "Answer the user's question clearly and comprehensively in English, strictly grounded in the provided official evidence."
                ),
                "rules": (
                    "Strict Grounding Rules:\n"
                    "1. Rely ONLY on the provided official evidence. Do not extrapolate, assume, or hallucinate dates, rules, or schemes.\n"
                    "2. Faithfully preserve all eligibility criteria, restrictions, and exceptions exactly as stated in the resolutions.\n"
                    "3. Clearly distinguish official government directives from explanatory context.\n"
                    "4. If the retrieved evidence is insufficient to answer the question completely, clearly state what information is missing.\n"
                    "5. Conclude with a clear disclaimer that this is informational and not formal legal advice."
                ),
                "disclaimer": "Notice: This response is generated for informational purposes based on available government resolutions and does not constitute formal legal counsel. Please verify with the official signed GR.",
            },
        }

        lang_cfg = prompts_by_language.get(language, prompts_by_language["mr"])

        full_prompt = f"""{lang_cfg['role']}

{lang_cfg['rules']}

{formatted_context}

नागरिकाचा प्रश्न / User Query:
"{query}"

कृपया वरील पुराव्यांच्या आधारे स्पष्ट आणि वस्तुनिष्ठ उत्तर लिहा:
"""

        if not settings.GEMINI_API_KEY or not _is_configured:
            return cls._generate_mock_grounded_answer(query, context_passages, language, lang_cfg["disclaimer"])

        candidate_models = []
        if getattr(cls, "_working_model_name", None):
            candidate_models.append(cls._working_model_name)
        if settings.GEMINI_MODEL and settings.GEMINI_MODEL not in candidate_models:
            candidate_models.append(settings.GEMINI_MODEL)
        for fallback in ["models/gemini-flash-lite-latest", "models/gemini-flash-latest", "models/gemini-3.8-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        answer_text = None
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name=model_name)
                response = model.generate_content(full_prompt)
                if response and response.text:
                    answer_text = response.text
                    cls._working_model_name = model_name
                    logger.info(f"Generated grounded answer using Gemini model: {model_name}")
                    break
            except Exception as e:
                logger.warning(f"Gemini model '{model_name}' invocation failed: {e}. Trying next candidate...")
                continue

        if not answer_text:
            return cls._generate_mock_grounded_answer(query, context_passages, language, lang_cfg["disclaimer"])

        # Ensure disclaimer is included if not present
        if lang_cfg["disclaimer"] not in answer_text:
            answer_text += f"\n\n---\n*{lang_cfg['disclaimer']}*"

        return answer_text

    @staticmethod
    def _get_insufficient_evidence_message(query: str, language: str) -> str:
        """Returns honest message when retrieved evidence does not support an answer."""
        if language == "mr":
            return (
                f"शासन निर्णय भांडारामध्ये '{query}' या विषयाबाबत पुरेसा अधिकृत पुरावा उपलब्ध नाही.\n\n"
                f"सध्या प्रणालीत समाविष्ट असलेल्या शासन निर्णयांमध्ये या प्रश्नाशी थेट संबंधित तरतुदी किंवा निकष आढळले नाहीत. "
                f"मनाने खोटी किंवा काल्पनिक माहिती देणे टाळण्यासाठी हे उत्तर मर्यादित ठेवण्यात आले आहे.\n\n"
                f"कृपया संबंधित विभागाचा अचूक शासन निर्णय (GR) अपलोड करा किंवा आपल्या प्रश्नाचे शब्द बदलून पुन्हा प्रयत्न करा."
            )
        elif language == "hi":
            return (
                f"प्रणाली में उपलब्ध शासन निर्णयों में '{query}' के संबंध में पर्याप्त साक्ष्य उपलब्ध नहीं है।\n\n"
                f"गलत या काल्पनिक जानकारी से बचने के लिए उत्तर नहीं दिया जा रहा है। "
                f"कृपया संबंधित आधिकारिक जी.आर. अपलोड करें या अन्य शब्दों के साथ पुनः प्रयास करें।"
            )
        else:
            return (
                f"Insufficient evidence was found in the indexed Maharashtra Government Resolutions regarding '{query}'.\n\n"
                f"To prevent hallucination of administrative rules or figures, no speculative answer is provided. "
                f"Please ensure the relevant GR is uploaded to the repository, or refine your search query."
            )

    @staticmethod
    def _generate_mock_grounded_answer(
        query: str,
        passages: List[Dict[str, Any]],
        language: str,
        disclaimer: str,
    ) -> str:
        """High-fidelity mock answer for local development and CI testing."""
        first_doc = passages[0] if passages else {}
        doc_title = first_doc.get("document_title", "महाराष्ट्र शासन निर्णय")
        gr_num = first_doc.get("gr_number") or "उपलब्ध शासन निर्णय"
        page_num = first_doc.get("page") or 1
        excerpt = first_doc.get("text", "")[:250].strip()

        if language == "mr":
            return (
                f"'{doc_title}' (शासन निर्णय क्रमांक: {gr_num}) मधील अधिकृत तरतुदींनुसार:\n\n"
                f"१. **अधिकृत तरतूद**: {excerpt}...\n"
                f"२. **पात्रता व अटी**: प्रस्तुत निर्णयातील पृष्ठ {page_num} वर नमूद केलेल्या निकषांनुसार सदर आदेश लागू राहील.\n\n"
                f"---\n*{disclaimer}*"
            )
        elif language == "hi":
            return (
                f"'{doc_title}' (जी.आर. क्रमांक: {gr_num}) के अनुसार:\n\n"
                f"१. **आधिकारिक प्रावधान**: {excerpt}...\n"
                f"२. **शर्तें**: पृष्ठ संख्या {page_num} पर दिए गए निर्देशों के अनुसार प्रक्रिया पूर्ण की जानी चाहिए।\n\n"
                f"---\n*{disclaimer}*"
            )
        else:
            return (
                f"Based on the official resolution '{doc_title}' (GR No: {gr_num}):\n\n"
                f"1. **Official Provision**: {excerpt}...\n"
                f"2. **Conditions & Eligibility**: Subject to the stipulations detailed on Page {page_num} of the source document.\n\n"
                f"---\n*{disclaimer}*"
            )
