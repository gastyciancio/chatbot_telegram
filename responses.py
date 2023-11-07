from queries import search
from similar_query import similar_query
import pdb
import random
from utils import search_with_sparql_of_similar_question

def respond_to(input_text, previous_question = None, context = None):
    user_message = str(input_text)

    if (user_message == 'No one of them'):
        return {
            "answer" : 'Sorry we cant help you',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": [],
            'posibles_entities': []
        }
    elif (user_message == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return {
            "answer" : response,
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": [],
            'posibles_entities': []
        }
    elif (user_message == 'it does not help me'):
        # enviar mail a qawiki porque no hay preguntas similares que le sirvan
        return {
            "answer" : 'We contacted to support, sorry for the inconvenience.',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": [],
            'posibles_entities': []
        }
    elif context.user_data.get('sparql_of_similar_question') != None:
        response = search_with_sparql_of_similar_question(context, user_message)

        return {
                "answer": response['answer'],
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": [],
                'posibles_entities': []
            }
    elif previous_question != None:
        # Agregar alias a la pregunta en QAWiki
        print(previous_question)

        response_similar_query = similar_query(user_message, previous_question) 

        if response_similar_query == None:
            return {
                "answer" : 'An unexpected error happened on OpenIA',
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": [],
                'posibles_entities': []
            }
        else:
            context.user_data['sparql_of_similar_question'] = response_similar_query['sparql_of_similar_question']
            context.user_data['entity_similar_question_in_chatgpt'] = response_similar_query['similar_question_response']['entity_similar_question_in_chatgpt']
            return {
                "answer": 'answer',
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": [],
                'posibles_entities': response_similar_query['similar_question_response']['entities_similar_question']
            }
    elif not valid_question(user_message):
        return {
            "answer" : 'Sorry, the question must start with "when", "how", "what" or "which"',
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": [],
            'posibles_entities': []
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