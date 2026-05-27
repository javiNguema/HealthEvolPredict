import ollama
import sqlite3
import pandas as pd
import re

class GenericDataChatbot:
    def __init__(self):
        self.model_name = "qwen2.5-coder:3b"

    def execute_and_reply(self, user_question: str, df: pd.DataFrame) -> str:
        """
        Dumps the active DataFrame into a temporary in-memory SQL structure,
        asks the local LLM for a query, and runs it.
        """
        # CRITICAL GUARD: Stop execution instantly before spinning up Ollama or allocating RAM
        if df is None or df.empty:
            return "No data has been loaded into the system yet. Please upload a CSV or Excel file via the main interface before using the chatbot helper."

        # 1. Dynamically read the columns to define the schema on the fly
        columns_info = ", ".join([f"{col} ({str(df[col].dtype)})" for col in df.columns])
        
        system_prompt = f"""
                            You are an expert biomedical data analysis assistant. Your only task is to translate the user's question into a valid SQL query (compatible with SQLite) based strictly on a table named 'active_data'.

                            The table 'active_data' contains the following columns:
                            {columns_info}

                            Critical Instructions:
                            1. Respond in plain text, paragraphs, or bullet points.
                            2. DO NOT use markdown code blocks (like ```sql ... ```).
                            3. DO NOT add introductions, explanations, or comments.
                            4. Always target the table named 'active_data'.

                            User Question: {user_question}
                            SQL:
                        """

        # 2. Call the local LLM to get the SQL string (Only runs if data verification passes)
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=system_prompt,
                options={"temperature": 0.0}
            )
            sql_query = response['response'].strip()
            sql_query = re.sub(r"```sql|```", "", sql_query).strip()
        except Exception as e:
            return f"Error connecting to local Ollama instance: {str(e)}"

        # 3. Spin up an ephemeral, temporary in-memory SQLite instance
        try:
            conn = sqlite3.connect(":memory:")
            # Dump the current dataframe into SQL
            df.to_sql("active_data", conn, index=False, if_exists="replace")
            
            # Execute the query
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            # Extract returned headers dynamically
            headers = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()

            if not results:
                return f"Executed Query: `{sql_query}`\n\nNo matching records were found."

            # 4. Format the dynamic data output cleanly for display
            reply = f"*Automated response generated based on current active workspace records:*\n\n"
            for row in results[:15]:  # Limit output rows to avoid blowing up the UI view
                row_data = ", ".join([f"*{h}*: {val}" for h, val in zip(headers, row)])
                reply += f"• {row_data}\n"
                
            if len(results) > 15:
                reply += f"\n*(Showing top 15 of {len(results)} rows found)*"
                
            return reply

        except Exception as e:
            return f"Error executing auto-generated SQL query.\n\n*Attempted SQL:*\n*Error Detail:* {str(e)}"