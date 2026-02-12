"""Agent RAG conversationnel avec feedback naturel"""

import os
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import PERSIST_DIR, COLLECTION_NAME, EMBED_MODEL, LLM_MODEL, RETRIEVAL_K, EXPERTISE_DOMAIN
from feedback_manager import FeedbackManager


class RAGAgent:
    def __init__(self):
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=PERSIST_DIR,
        )
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        self.feedback_manager = FeedbackManager()
    
    def _retrieve_documents(self, query: str, exclude_sources: List[tuple] = None) -> List[Dict]:
        """Récupère les documents, en excluant optionnellement certaines sources"""
        # Récupérer plus de docs pour avoir des alternatives
        docs = self.vectorstore.similarity_search(query, k=RETRIEVAL_K * 2)
        
        # Filtrer si nécessaire
        if exclude_sources:
            filtered_docs = [
                doc for doc in docs
                if (doc.metadata.get('source'), doc.metadata.get('slide')) not in exclude_sources
            ]
            docs = filtered_docs[:RETRIEVAL_K] if filtered_docs else docs[:RETRIEVAL_K]
        else:
            docs = docs[:RETRIEVAL_K]
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "slide": doc.metadata.get("slide", "unknown")
            }
            for doc in docs
        ]
    
    def _build_context(self, docs: List[Dict]) -> str:
        """Construit le contexte à partir des documents"""
        return "\n\n---\n\n".join([
            f"[{doc['source']} | Slide {doc['slide']}]\n{doc['content']}"
            for doc in docs
        ])
    
    def query(self, question: str, conversation_history: List = None, session_id: str = None) -> Dict:
        """
        Interroge l'agent avec historique de conversation
        
        Args:
            question: Question actuelle
            conversation_history: Liste des messages précédents (HumanMessage, AIMessage)
            session_id: ID de session pour tracking
        """
        if conversation_history is None:
            conversation_history = []
        
        # Analyser l'historique pour identifier les sources à éviter
        exclude_sources = set()
        if conversation_history:
            # Regarder les 3 derniers échanges pour éviter la répétition
            for msg in conversation_history[-6:]:
                if hasattr(msg, 'additional_kwargs') and 'sources' in msg.additional_kwargs:
                    for doc in msg.additional_kwargs['sources']:
                        exclude_sources.add((doc['source'], doc['slide']))
        
        
        docs = self._retrieve_documents(question, exclude_sources if exclude_sources else None)
        context = self._build_context(docs)
        
        # l'historique pour le LLM
        messages = [
            SystemMessage(content=(
                f"Tu es un assistant expert en {EXPERTISE_DOMAIN}.\n\n"
                
                "CONTEXTE DE CONVERSATION:\n"
                "- Tu participes à une conversation continue avec l'utilisateur\n"
                "- L'utilisateur peut poser des questions de suivi sur le même sujet\n"
                "- TOUJOURS regarder l'historique de la conversation pour comprendre le contexte\n"
                "- Si la question fait référence à quelque chose mentionné avant, utilise ce contexte\n\n"
                
                "INSTRUCTIONS DE RÉPONSE:\n"
                "1. REGARDE L'HISTORIQUE pour comprendre de quoi on parle\n"
                "2. ANALYSE le contexte de la question de l'utilisateur (son rôle, sa situation, son besoin)\n"
                "3. UTILISE PRIORITAIREMENT les documents PowerPoint fournis comme base de ta réponse\n"
                "4. ENRICHIS ta réponse avec ton expertise pour donner des conseils pratiques et spécifiques\n"
                "5. ADAPTE ta réponse au contexte et à la situation de l'utilisateur\n"
                "6. CITE TOUJOURS les sources des documents (fichier + numéro de slide) pour les informations tirées des PPT\n\n"
                
                "STRUCTURE DE RÉPONSE:\n"
                "- Si les documents contiennent des informations pertinentes: Base ta réponse dessus et enrichis avec ton expertise\n"
                "- Si les documents sont partiels: Combine les infos des documents avec tes connaissances pour une réponse complète\n"
                "- Si les documents ne couvrent pas le sujet: Donne une réponse experte basée sur les bonnes pratiques\n\n"
                
                "IMPORTANT:\n"
                "- Ne dis JAMAIS 'je ne peux pas répondre' ou 'les documents ne contiennent pas'\n"
                "- Sois SPÉCIFIQUE au contexte de l'utilisateur (son métier, sa situation)\n"
                "- Donne des réponses ACTIONNABLES et PRATIQUES\n"
                "- Cite les sources quand tu utilises les documents\n"
                "- GARDE LE FIL de la conversation - ne change pas de sujet sans raison\n"
            ))
        ]
        
        
        messages.extend(conversation_history)
        
        # Ajouter la question actuelle avec le contexte
        user_message = f"Contexte des documents:\n{context}\n\n{question}"
        messages.append(HumanMessage(content=user_message))
        
        
        response = self.llm.invoke(messages)
        answer = response.content
        
        
        ai_message = AIMessage(
            content=answer,
            additional_kwargs={'sources': docs}
        )
        
        return {
            "answer": answer,
            "sources": docs,
            "ai_message": ai_message,
            "session_id": session_id
        }
    
    def save_feedback(self, question: str, response: str, feedback_text: str, 
                     feedback_type: str, documents_used: List[Dict], session_id: str):
        """Sauvegarde le feedback utilisateur"""
        self.feedback_manager.add_feedback(
            question=question,
            response=response,
            feedback=feedback_type,
            feedback_detail=feedback_text,
            documents_used=documents_used,
            session_id=session_id
        )