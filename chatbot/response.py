from chatbot.queries import parse_response, search_id_to_QAwiki, search_item_to_QAwiki
import pdb
import random
from chatbot.utils import parse_similar_question, save_answer, search_cached_answer, similar_query, valid_question

def respond_to(input_text, previous_question = None):
    user_message = str(input_text)
    if (user_message.lower() == 'no one of them'):
        return {
            "answer" :              'Sorry we cant help you',
            "analogous_questions":  [],
            "general_questions":    [],
            'posibles_entities':    []
        }
    elif (user_message.lower() == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return {
            "answer" :              response,
            "analogous_questions":  [],
            "general_questions":    [],
            'posibles_entities':    []
        }
    elif (user_message.lower() == 'it does not help me'):
        # enviar mail a qawiki porque no hay preguntas similares que le sirvan
        return {
            "answer" :              'We contacted to support, sorry for the inconvenience.',
            "analogous_questions":  [],
            "general_questions":    [],
            'posibles_entities':    []
        }
    elif previous_question != None:
        response_QAwiki_id, similar_questions = search_id_to_QAwiki(previous_question)
        response = similar_query(user_message, similar_questions)
        if response['final_answer'] != "":
            return {
                    "answer":               response['final_answer'],
                    "analogous_questions":  [],
                    "general_questions":    [],
                    'posibles_entities':    []
                }
        else:
            return {
                "answer" :              'There is no information using similar questions we have an answer',
                "analogous_questions":  [],
                "general_questions":    [],
                'posibles_entities':    []
            }

    elif not valid_question(user_message):
        return {
            "answer" :              'Sorry, the question must start with "what", "which", "where", "when", "how", "is", "did", "do", "in", "who", "on" ,"kim", "from", "has", "was" or "are',
            "analogous_questions":  [],
            "general_questions":    [],
            'posibles_entities':    []
        }
    else:
        cached_response = search_cached_answer(user_message)
        if cached_response == None:
            response_QAwiki_id, similar_questions = search_id_to_QAwiki(user_message)
            if response_QAwiki_id == None:
                posibles_entities = parse_similar_question(user_message)
                if len(posibles_entities['entities_original_question']) > 0:
                    return {
                        "answer" :              "",
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'posibles_entities':    posibles_entities['entities_original_question']
                }
                else:
                    # aca enviar mail a qawiki pidiendo que agreguen la pregunta
                    return {
                        "answer" :              "There is not information about what you search",
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'posibles_entities':    []
                    }
            
            else:
                response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
                if response_QAwiki_query["query"] == None:
                    return {
                        "answer" :              "There is not result for what you search",
                        "analogous_questions":  [],
                        "general_questions":    [],
                        'posibles_entities':    []
                    }
                response = parse_response(user_message, response_QAwiki_query["query"], response_QAwiki_query["analogous_questions"], response_QAwiki_query["general_questions"])
                if (response["answer"]) != 'Wikidata error. Please contact the administrator':
                    save_answer(response["answer"], user_message, previous_question, response["analogous_questions"], response["general_questions"])
                return {
                    "answer" :              response["answer"],
                    "analogous_questions":  response["analogous_questions"],
                    "general_questions":    response["general_questions"],
                    "posibles_entities":    response["posibles_entities"]
                }
        else:
            return {
                    "answer" :              cached_response['answer'],
                    "analogous_questions":  cached_response['analogous_questions'],
                    "general_questions":    cached_response['general_questions'],
                    "posibles_entities":    []
                }
