from chatbot.queries import add_alias_to_question_in_qawiki, parse_response, search_id_to_QAwiki, search_item_to_QAwiki
import pdb
import random
from chatbot.utils import parse_similar_question, save_answer, search_cached_answer, send_email_to_qawiki, valid_question

def respond_to(input_text, context):
    user_message = str(input_text)
    if (user_message.lower() == 'add alias to question'):
        ids = context.user_data.get('ids_for_alias')
        alias = context.user_data.get('alias')
        responses = []
        for id in ids:
            responses.append(add_alias_to_question_in_qawiki(id, alias))
        context.user_data['ids_for_alias'] = []
        context.user_data['alias'] = None
        answer = ""
        for response in responses:
            answer = answer + response
        return {
            "answer" :              answer,
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    if (user_message.lower() == 'not add alias to question'):
        context.user_data['alias'] = None
        context.user_data['ids_for_alias'] = []
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
       
        return {
            "answer" :              response,
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    if (user_message.lower() == 'no one of them'):
        return {
            "answer" :              'Sorry we cant help you',
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    elif (user_message.lower() == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return {
            "answer" :              response,
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    elif not valid_question(user_message):
        return {
            "answer" :              'Sorry, the question must start with "what", "which", "where", "when", "how", "is", "did", "do", "in", "who", "on" ,"kim", "from", "has", "was" or "are',
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    else:
        cached_response = search_cached_answer(user_message)
        if cached_response == None:
            response_QAwiki_id, similar_questions = search_id_to_QAwiki(user_message, True)
            if response_QAwiki_id == None:
                response = parse_similar_question(user_message, context, similar_questions)
                if response != "":
                    context.user_data['alias'] = user_message
                    save_answer(user_message, response, [], [])
                    return {
                        "answer" :              response,
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'ask_for_add_alias':    True
                }
                else:
                    send_email_to_qawiki(user_message, 'There was no answer for a question, even using similar question on QAWiki')
                    return {
                        "answer" :              "There is no information using similar questions we have an answer",
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'ask_for_add_alias':    False
                    }
            else:
                response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
                if response_QAwiki_query["query"] == None:
                    send_email_to_qawiki(user_message, 'There was no SPARQL query in the question with id' + response_QAwiki_id)
                    return {
                        "answer" :              "There is not result for what you search",
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'ask_for_add_alias':    False
                    }
                response = parse_response(user_message, response_QAwiki_query["query"], response_QAwiki_query["analogous_questions"], response_QAwiki_query["general_questions"])
                if (response["answer"]) != 'Wikidata error. Please contact the administrator':
                    save_answer(user_message, response["answer"], response["analogous_questions"], response["general_questions"])
                else:
                    send_email_to_qawiki(user_message, 'There was an error using the sparql given for the question on QAWiki with id' + response_QAwiki_id)
                return {
                    "answer" :              response["answer"],
                    "analogous_questions":  response["analogous_questions"],
                    "general_questions":    response["general_questions"],
                    'ask_for_add_alias':    False
                }
        else:
            return {
                    "answer" :              cached_response['answer'],
                    "analogous_questions":  cached_response['analogous_questions'],
                    "general_questions":    cached_response['general_questions'],
                    'ask_for_add_alias':    False
                }
