from queries import search
import pdb
import random

def respond_to(input_text):
    user_message = str(input_text)

    if (user_message == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return {
            "answer" : response,
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": []
        }
    elif ('it does not help me for' in user_message):
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
    elif '_similar_to_question_' in user_message:

        similar_question = user_message.split('_similar_to_question_')[0]
        original_question = user_message.split('_similar_to_question_')[1]
        # Agregar alias a la pregunta en QAWiki
        response = search(similar_question)
        return response
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