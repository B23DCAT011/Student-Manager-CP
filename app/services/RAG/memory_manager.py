import json
import os
import uuid
from datetime import datetime
from typing import List,Dict,Optional

class SessionMemoryManager:
    """Quan ly session memory"""
    def __init__(self,base_path:str="app/services/memory/sessions"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)


    def _get_session_file_path(self,user_id:str,session_id:str)->str:
      return os.path.join(self.base_path,f"user_{user_id}_session_{session_id}.json")

    def create_new_session(self,user_id:str)->str:
      session_id = str(uuid.uuid4())[:8]

      session_data = {
        "session_id":session_id,
        "user_id":user_id,
        "created_at":datetime.now().isoformat(),
        "last_updated":datetime.now().isoformat(),
        "messages":[]
      }

      file_path = self._get_session_file_path(user_id,session_id)

      with open(file_path,'w',encoding='utf-8') as f:
          json.dump(session_data,f,ensure_ascii=False,indent=2)

      print(f"Created new session: {session_id} for user: {user_id}")
      return session_id
    def add_message_to_session(self,user_id:str,session_id:str,role:str,content:str)-> bool:
      file_path = self._get_session_file_path(user_id,session_id)

      if not os.path.exists(file_path):
        print(f"Session file not found: {file_path}")
        return False

      try:
        with open(file_path,'r',encoding='utf-8') as f:
            session_data = json.load(f)

        new_message = {
          "role":role,
          "content":content,
          "timestamp":datetime.now().isoformat()
        }

        session_data['messages'].append(new_message)
        session_data['last_updated'] = datetime.now().isoformat()

        with open(file_path,'w',encoding='utf-8') as f:
           json.dump(session_data,f,ensure_ascii=False,indent=2)

        print(f"Added message to session: {session_id} for user: {user_id}")
        return True
      except Exception as e:
        print(f"Error adding message to session: {e}")
        return False

    def get_session_history(self,user_id:str,session_id:str)->List[Dict[str,str]]:
      file_path = self._get_session_file_path(user_id,session_id)

      if not os.path.exists(file_path):
        print(f"Session file not found: {file_path}")
        return []

      try:
          with open(file_path,'r',encoding='utf-8') as f:
            session_data = json.load(f)
          return session_data.get('messages',[])
      except Exception as e:
          print(f"Error reading session history: {e}")
          return []
    def get_user_sessions(self,user_id:str)->List[Dict[str,str]]:
        sessions = []

        try:
          for filename in os.listdir(self.base_path):
              if filename.startswith(f"user_{user_id}_session_"):
                file_path = os.path.join(self.base_path,filename)

                with open(file_path,'r',encoding='utf-8') as f:
                    session_data = json.load(f)

                session_info = {
                    "session_id":session_data.get("session_id"),
                    "created_at":session_data.get("created_at"),
                    "last_updated":session_data.get("last_updated"),
                    "message_count":len(session_data.get("messages",[])),
                    "last_message":session_data.get("messages",[])[-1] if session_data.get("messages",[]) else None
                }
                sessions.append(session_info)

          sessions.sort(key=lambda x:x['last_updated'],reverse=True)
          return sessions
        except Exception as e:
          print(f"Error retrieving user sessions: {e}")
          return []

    def session_exists(self,user_id:str,session_id:str)->bool:
        file_path = self._get_session_file_path(user_id,session_id)
        return os.path.exists(file_path)

    def build_conversation_history(self,user_id:str,session_id:str,max_messages:int=10)->str:
       history = self.get_session_history(user_id,session_id)

       if not history:
          return ""

       recent_messages = history[-max_messages:] if len(history)>max_messages else history

       context_lines = []
       for msg in recent_messages:
          role_label = "User" if msg['role']=='user' else "Assistant"
          context_lines.append(f"{role_label}: {msg['content']}")

       if context_lines:
          return "Lịch sử cuộc trò chuyện:\n" + "\n".join(context_lines)

       return ""

    def build_conversation_context(self, user_id: str, session_id: str, max_messages: int = 10) -> str:
        """
        Build conversation context for RAG system
        This method is called by enhanced_rag.py
        """
        return self.build_conversation_history(user_id, session_id, max_messages)