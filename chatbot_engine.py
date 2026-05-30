import ollama
import sqlite3
import pandas as pd
import re

class GenericDataChatbot:
    def __init__(self):
        self.model_name = "qwen2.5-coder:3b"

    def execute_and_reply(self, user_question: str, df: pd.DataFrame, history: list = None) -> str: # type: ignore
        """
        Translates user question to SQL with conversational memory, 
        executes it, and synthesizes a natural response.
        """
        if df is None or df.empty:
            return "No data has been loaded into the system yet."

        if history is None:
            history = []

        # 1. Format the history into a readable string block for the LLM
        formatted_history = ""
        # We take the last 6 messages to avoid overflowing the LLM context window
        for msg in history[-6:]:
            formatted_history += f"{msg['role']}: {msg['text']}\n"

        # 2. Schema Info
        columns_info = ", ".join([f"{col} ({str(df[col].dtype)})" for col in df.columns])
        
        # 3. Step 1: SQL Generation Prompt (Now includes Chat History)
        sql_generation_prompt = f"""
        You are an expert biomedical data analysis assistant. Your task is to translate the user's question into a valid SQLite query based strictly on a table named 'active_data'.

        The table 'active_data' contains the following columns:
        {columns_info}

        Here is the recent conversation history for context. Use this to understand pronouns like "them", "it", or follow-up constraints:
        {formatted_history}

        Current User Question: {user_question}
        
        Critical Instructions:
        1. Respond ONLY with the raw SQL code. No markdown formatting.
        2. Always target the table named 'active_data'.
        
        SQL:
        """

        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=sql_generation_prompt,
                options={"temperature": 0.0}
            )
            sql_query = response['response'].strip()
            sql_query = re.sub(r"```sql|```", "", sql_query).strip()
        except Exception as e:
            return f"Error connecting to local Ollama instance: {str(e)}"

        # 4. Database Execution
        try:
            conn = sqlite3.connect(":memory:")
            df.to_sql("active_data", conn, index=False, if_exists="replace")
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()

            if not results:
                return f"I checked the records using the query `{sql_query}`, but no matching entries were found."
        except Exception as e:
            return f"I ran into an issue running the generated query.\n\n*SQL:* `{sql_query}`\n*Error:* {str(e)}"

        # 5. Step 2: Human-style Response Prompt (Now includes Chat History)
        formatted_rows = [", ".join([f"{h}: {val}" for h, val in zip(headers, row)]) for row in results[:15]]
        data_context = "\n".join([f"- {r}" for r in formatted_rows])

        synthesis_prompt = f"""
        You are a conversational biomedical data analysis chatbot. 
        Answer the user's current question naturally using the provided conversation history and the raw database results.

        Recent Conversation History:
        {formatted_history}

        Current User Question: "{user_question}"
        
        Database Results for this question:
        {data_context}
        
        Instructions:
        - Provide a friendly, conversational, and natural response answering the user.
        - Treat this as a continuation of the conversation history.
        - Do not mention SQL or table names.
        """

        try:
            human_response = ollama.generate(
                model=self.model_name,
                prompt=synthesis_prompt,
                options={"temperature": 0.7}
            )
            return human_response['response'].strip()
        except Exception as e:
            return f"I extracted the data, but failed to summarize it natively: {results[:3]}"