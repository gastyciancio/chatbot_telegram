from queries import search
from similar_query import similar_query
import pdb
import random

def respond_to(input_text, previous_question = None):
    user_message = str(input_text)

    if (user_message == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return {
            "answer" : response,
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": []
        }
    elif (user_message == 'it does not help me'):
        # enviar mail a qawiki porque no hay preguntas similares que le sirvan
        return {
            "answer" : 'We contacted to support, sorry for the inconvenience.',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": []
        }
    elif not valid_question(user_message):
        return {
            "answer" : 'Sorry, the question must start with "when", "how", "what" or "which"',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": []
        }
    elif previous_question != None:
        # Agregar alias a la pregunta en QAWiki
        # Buscar la query para la pregunta original usando la pregunta similar
        print(previous_question)
        response = similar_query(user_message) 
        return {
            "answer" : 'En desarrollo',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": []
        }
    else:
        response = search(user_message)
        return response

def valid_question(text):
    words_needed = ["what", "which", "where", "when", "how"]
    start_with = False

    for word in words_needed:
        if text.startswith(word):
            start_with = True
            break
    return start_with