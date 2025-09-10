from .load_model import GeminiLLM,read_from_db,template
from .memory_manager import SessionMemoryManager
from typing import Optional,Dict

class SessionAwareRAG:

  def __init__(self):
    self.db = read_from_db()
    self.llm = GeminiLLM()
    self.template = template
    self.memory_manager = SessionMemoryManager()

    self.enhanced_template = """Bạn là trợ lý AI thông minh của Học viện Công nghệ Bưu chính Viễn thông.

{conversation_context}Thông tin từ cơ sở dữ liệu:
{rag_context}

Câu hỏi hiện tại: {question}

Hướng dẫn:
- Dựa vào lịch sử cuộc trò chuyện và thông tin cơ sở dữ liệu để trả lời
- Nếu có liên quan đến câu hỏi trước đó, hãy tham khảo ngữ cảnh
- Trả lời bằng tiếng Việt, rõ ràng và hữu ích
- Nếu không biết thông tin, hãy thừa nhận và đề xuất cách khác

Trả lời:"""

  def process_query_with_session(self,
                                   query:str,
                                   user_id:str,
                                   session_id:Optional[str]=None)->Dict[str,str]:

      try:
        if session_id is None or not self.memory_manager.session_exists(user_id,session_id):
          session_id = self.memory_manager.create_new_session(user_id)
          print(f"Created new session: {session_id}")
        else:
          print(f"Using existing session: {session_id}")

        self.memory_manager.add_message_to_session(user_id,session_id,'user',query)

        conversation_context = self.memory_manager.build_conversation_context(user_id,session_id)

        if self.db is None:
          raise Exception("Vector database not loaded")

        docs = self.db.similarity_search(query,k=3)
        rag_context = "\n".join([doc.page_content for doc in docs])

        formatted_prompt = self.enhanced_template.format(
          conversation_context=conversation_context + "\n" if conversation_context else "",
          rag_context=rag_context,
          question=query
        )

        ai_response = self.llm.generate(formatted_prompt)

        self.memory_manager.add_message_to_session(user_id,session_id,'assistant',ai_response)

        return {
          "success":True,
          "response":ai_response,
          "session_id":session_id,
          "user_id":user_id
        }
      except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print(error_msg)

        return{
          "success":False,
          "response":error_msg,
          "session_id":session_id,
          "user_id":user_id,
          "error":str(e)
        }

  def get_session_history(self,user_id:str,session_id:str)->Dict[str,str]:
      history = self.memory_manager.get_session_history(user_id,session_id)

      return{
        "session_id":session_id,
        "user_id":user_id,
        "messages_cnt":len(history),
        "messages":history
      }
  def get_user_sessions_list(self,user_id:str)->Dict[str,str]:
      return self.memory_manager.get_user_sessions(user_id)

def create_rag_chain():
  return SessionAwareRAG()