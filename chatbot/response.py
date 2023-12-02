from chatbot.queries import parse_response, search_id_to_QAwiki, search_item_to_QAwiki
import pdb
import random
from chatbot.utils import parse_similar_question, save_answer, search_cached_answer, search_template_chatbot, send_email_to_qawiki, valid_question
from qa_autocomplete.utils import read_json, save_json

CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH = "static/cached_questions/templates_chatbot.json"
CACHED_QUESTIONS_TEMPLATES_PATH = "static/cached_questions/templates.json"
CACHED_PATH = 'static/cached_questions'

def respond_to(input_text, context):
    user_message = str(input_text)
    if (user_message.lower() == 'it was helpful'):
        if 'We had to use similar questions to give you this answer, please help us saying if this answer helped you.' in context.user_data.get('posible_response'):
            context.user_data['posible_response'] = context.user_data.get('posible_response').replace('We had to use similar questions to give you this answer, please help us saying if this answer helped you.', ' ')
        if "We don't have an answer for that question. However we found similar questions that might be useful. " in context.user_data.get('posible_response'):
            context.user_data['posible_response'] = context.user_data.get('posible_response').replace("We don't have an answer for that question. However we found similar questions that might be useful. ", ' ')
        save_answer(context.user_data.get('posible_question'), context.user_data.get('posible_response'), [], [])
        context.user_data['posible_question'] = None
        context.user_data['posible_response'] = None
        template_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
        templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
        questions_template_en = []
        for template_chat in template_chatbot:
            questions_template_en.append(template_chat['question_template_en'].lower())
        for temp in templates:
            if 'question_template_en' in temp:
                questions_template_en.append(temp['question_template_en'].lower())
        for template in context.user_data.get('posibles_alias'):
            if template['question_template_en'].lower() not in questions_template_en:
                template_chatbot.append(template)
        save_json(template_chatbot, CACHED_PATH, 'templates_chatbot.json')
        context.user_data['posibles_alias'] = []
       
        return {
            "answer" :              random.choice(["Okay, see you later!", "I'm glad it helped you", "See u till next time!"]),
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    if (user_message.lower() == 'it was not helpful'):
        context.user_data['posibles_alias'] = []
        response = random.choice(["Sorry we didn't help you.", "Okay, sorry for the inconvenient", "Sorry, we suggest you to ask different"])
       
        return {
            "answer" :              response,
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    if (user_message.lower() == 'no one of them'):
        return {
            "answer" :              "Sorry we can't help you",
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
            "answer" :              'Sorry, the question must start with "What", "Which", "Where", "When", "How", "Is", "Did", "Do", "In", "Who", "On", "From", "Has", "Was" or "Are',
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }
    else:
        cached_response = search_cached_answer(user_message)
        if cached_response == None:
            response_QAwiki_id, similar_questions = search_id_to_QAwiki(user_message)
            if response_QAwiki_id == None:

                search_template_chatbot_response = search_template_chatbot(user_message)
                if search_template_chatbot_response['query'] != None:
                    response = parse_response(user_message, search_template_chatbot_response['query'], [],[])
                    if (response["answer"]) != 'Unexpected error. Please contact the administrator':
                        save_answer(user_message, response["answer"], [],[])
                    else:
                        send_email_to_qawiki(user_message, 'There was an error using the sparql given for the question on chatbot templates for: ' + user_message)
                    return {
                        "answer" :              response["answer"],
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'ask_for_add_alias':    False
                    }
                else:
                    response = parse_similar_question(user_message, context, similar_questions)
                    if response != "":
                        context.user_data["posible_response"] = response
                        context.user_data["posible_question"] = user_message
                       
                        return {
                            "answer" :              response,
                            "analogous_questions":  [],
                            "general_questions":    [],
                            'ask_for_add_alias':    True
                    }
                    else:
                        send_email_to_qawiki(user_message, 'There was no answer for a question, even using similar question')
                        return {
                            "answer" :              "There is no information we have an answer",
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
                if (response["answer"]) != 'Unexpected error. Please contact the administrator':
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
