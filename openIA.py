import constants as keys
import openai
import pdb

def search_in_chatgpt(sparql_of_similar_question, similar_question, original_question):
    try:

        openai.api_key = keys.API_OPENIA_KEY
        response_chatgpt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": sparql_of_similar_question[0] + ' es la query sparql para "' + similar_question + '" adaptala para "' + original_question + '"'}
            ]
        )

        print(f"Respuesta de OpenIA: {response_chatgpt}")

        return response_chatgpt['choices'][0]['message']['content'], None
    except Exception as e:
        print(f"Respuesta de OpenIA: {e}")
        return None, str(e)