"""Interface conversationnelle pour l'agent RAG"""

import sys
import uuid
from langchain_core.messages import HumanMessage
from rag_agent import RAGAgent


def main():
    agent = RAGAgent()
    
    if len(sys.argv) > 1:

        question = " ".join(sys.argv[1:])
        result = agent.query(question)
        print("\n" + result["answer"])
        print(f"\n📚 Sources: {len(result['sources'])} documents")
        return
    

    print("🤖 RAG Agent - Mode Conversation")
    print("Posez vos questions et guidez-moi avec vos feedbacks naturels")
    print("\nCommandes spéciales:")
    print("  • 'ok' ou 'bien' ou 'parfait' → Confirme que la réponse est bonne")
    print("  • 'new' → Nouvelle conversation")
    print("  • 'quit' → Quitter\n")
    
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    conversation_history = []
    current_question = None
    current_answer = None
    current_sources = None
    
    while True:
        user_input = input("\n💬 Vous: ").strip()
        
        if user_input.lower() in ['quit', 'q', 'exit']:
            print("Au revoir!")
            break
        
        # Commandes de confirmation (réponse satisfaisante)
        if user_input.lower() in ['ok', 'bien', 'parfait', 'good', 'great', 'merci', 'thanks']:
            if current_answer:
                agent.save_feedback(
                    question=current_question,
                    response=current_answer,
                    feedback_text=user_input,
                    feedback_type="positive",
                    documents_used=current_sources,
                    session_id=session_id
                )
                print(" Parfait ! Posez une autre question ou tapez 'quit'")
            continue
        
        if user_input.lower() == 'new':
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            conversation_history = []
            current_question = None
            current_answer = None
            print("Nouvelle conversation démarrée")
            continue
        
        if not user_input:
            continue
        
        # Déterminer le type d'entrée utilisateur
        # 3 types: NOUVELLE QUESTION | SUITE DE CONVERSATION | FEEDBACK
        
        user_lower = user_input.lower()
        
        # Mots-clés de NOUVELLE question (changement de sujet)
        new_topic_keywords = [
            'maintenant', 'passons à', 'autre chose', 'changer de sujet',
            'nouvelle question', 'autre question', 'parlons de'
        ]
        
        # Mots-clés de SUITE de conversation (même sujet)
        continuation_keywords = [
            'comment', 'pourquoi', 'et si', 'mais', 'donc', 'alors',
            'concrètement', 'pratiquement', 'en détail', 'précise',
            'exemple', 'plus d\'info', 'développe', 'continue',
            'ensuite', 'après', 'du coup'
        ]
        
        # Mots-clés de FEEDBACK négatif
        feedback_keywords = [
            'non', 'pas bon', 'incorrect', 'faux', 'erreur',
            'mieux', 'améliore', 'change', 'refais', 'plutôt'
        ]
        
        # DÉCISION
        if current_answer is None:
            # Pas de contexte → forcément nouvelle question
            is_new_question = True
            is_continuation = False
        
        elif any(user_lower.startswith(kw) for kw in feedback_keywords):
            # Commence par feedback → c'est un feedback
            is_new_question = False
            is_continuation = False
        
        elif any(kw in user_lower for kw in new_topic_keywords):
            # Mots-clés de changement de sujet → nouvelle question
            is_new_question = True
            is_continuation = False
        
        elif any(kw in user_lower for kw in continuation_keywords):
            # Mots-clés de continuation → suite de conversation
            is_new_question = False
            is_continuation = True
        
        elif user_input.endswith('?') and len(user_input.split()) > 3:
            # Question avec contexte → probablement une suite
            is_new_question = False
            is_continuation = True
        
        else:
            # Par défaut: si court et vague, c'est probablement feedback
            is_new_question = False
            is_continuation = len(user_input.split()) > 5
        
        if is_new_question:
            # NOUVELLE QUESTION (nouveau sujet)
            print("\n [Nouvelle question détectée]")
            current_question = user_input
            
            result = agent.query(
                question=current_question,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            current_answer = result["answer"]
            current_sources = result["sources"]
            
            # Ajouter à l'historique
            conversation_history.append(HumanMessage(content=current_question))
            conversation_history.append(result["ai_message"])
            
            print(f"\n🤖 Agent: {current_answer}")
            print(f"\n📚 Sources: {len(current_sources)} documents")
            for i, src in enumerate(current_sources[:3], 1):
                filename = src['source'].split('/')[-1]
                print(f"   {i}. {filename} | Slide {src['slide']}")
            
            print("\n Satisfait ? Tapez 'ok' pour confirmer ou donnez un feedback pour améliorer")
        
        elif is_continuation:
            # SUITE DE CONVERSATION (même sujet, approfondir)
            print("\n💬 [Suite de la conversation]")
            
            # Ne pas changer current_question, c'est une continuation
            # On ajoute la question de suivi à l'historique
            
            result = agent.query(
                question=user_input,  # La question de suivi
                conversation_history=conversation_history,  # Garde tout l'historique
                session_id=session_id
            )
            
            current_answer = result["answer"]
            current_sources = result["sources"]
            
            # Ajouter à l'historique
            conversation_history.append(HumanMessage(content=user_input))
            conversation_history.append(result["ai_message"])
            
            print(f"\n🤖 Agent: {current_answer}")
            print(f"\n📚 Sources: {len(current_sources)} documents")
            for i, src in enumerate(current_sources[:3], 1):
                filename = src['source'].split('/')[-1]
                print(f"   {i}. {filename} | Slide {src['slide']}")
            
            print("\n💡 Satisfait ? Tapez 'ok' pour confirmer ou continuez à discuter")
        
        else:
            # FEEDBACK/CORRECTION
            print("\n [Feedback détecté - Amélioration de la réponse...]")
            
            # Sauvegarder le feedback précédent
            if current_answer:
                agent.save_feedback(
                    question=current_question,
                    response=current_answer,
                    feedback_text=user_input,
                    feedback_type="correction",
                    documents_used=current_sources,
                    session_id=session_id
                )
            
            # L'utilisateur guide la réponse
            follow_up = f"{current_question}\n\nIndication: {user_input}"
            
            result = agent.query(
                question=follow_up,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            current_answer = result["answer"]
            current_sources = result["sources"]
            
            # Mettre à jour l'historique
            conversation_history.append(HumanMessage(content=user_input))
            conversation_history.append(result["ai_message"])
            
            print(f"\n🤖 Agent: {current_answer}")
            print(f"\n📚 Sources: {len(current_sources)} documents")
            for i, src in enumerate(current_sources[:3], 1):
                filename = src['source'].split('/')[-1]
                print(f"   {i}. {filename} | Slide {src['slide']}")
            
            print("\n Satisfait ? Tapez 'ok' pour confirmer ou continuez à guider")


if __name__ == "__main__":
    main()