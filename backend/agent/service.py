import os
import logging
from openai import OpenAI
from sqlalchemy import text
from fastapi import HTTPException
from agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db_session):
        self.db = db_session
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # Configure Client (Support for Vercel AI Gateway)
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set. Agent will not function.")
            self.client = None
        else:
            # Vercel AI Gateway support
            # Note: vck_ keys often require the gateway URL. 
            # If the user is using a pure Vercel AI SDK key, it might need 'https://gateway.ai.vercel.dev/v1' 
            # but some specific integrations use other URLs.
            base_url = None
            if self.api_key.startswith("vck_"):
                logger.info("Detected Vercel AI Gateway Key.")
                base_url = "https://gateway.ai.vercel.dev/v1"
            
            logger.info(f"Initializing OpenAI Client with {'custom base_url' if base_url else 'defualt base_url'}")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )

    def process_query(self, user_question: str):
        """
        1. Convert User Question -> SQL (using GPT-4o-mini)
        2. Execute SQL (Locally)
        3. Return Results (Raw)
        """
        if not self.api_key:
            raise HTTPException(status_code=503, detail="AI Service unavailable (Missing API Key)")

        # 1. Generate SQL
        try:
            sql_query = self._generate_sql(user_question)
            logger.info(f"Generated SQL: {sql_query}")
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to interpret question.")

        # 2. Execute SQL (Read-Only Safety Check)
        if not self._is_safe_sql(sql_query):
            raise HTTPException(status_code=400, detail="Unsafe query formulation.")

        try:
            result = self.db.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
            
            return {
                "question": user_question,
                "sql": sql_query,
                "result": [dict(zip(columns, row)) for row in rows]
            }

        except Exception as e:
            logger.error(f"SQL Execution Error: {e}")
            raise HTTPException(status_code=400, detail=f"Database query failed: {str(e)}")

    def _generate_sql(self, question: str) -> str:
        """Call OpenAI (or Vercel Gateway) to translate question to SQL"""
        # Vercel Gateway requires specific model names sometimes, but standard usually work.
        # Ensure we use a cheap model.
        response = self.client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0,
            max_tokens=200
        )
        # Clean up response (remove markdown if present)
        sql = response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def _is_safe_sql(self, sql: str) -> bool:
        """Basic safety check"""
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT"]
        upper_sql = sql.upper()
        for term in forbidden:
            if term in upper_sql:
                return False
        return True
