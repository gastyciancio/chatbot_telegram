from chatbot.queries import parse_response, search_id_to_QAwiki, search_item_to_QAwiki
import pdb
import random
from chatbot.utils import parse_similar_question, save_answer, save_response_as_template_chatbot, search_cached_answer, search_id_to_templates_alias, search_question_template_en, send_email_to_qawiki, valid_question

def respond_to(input_text, context):
    user_message = str(input_text)
    if (user_message.lower() == 'it was helpful'):
        save_response_as_template_chatbot(context)
        return return_response( random.choice(["Okay, see you later!", "I'm glad it helped you", "See u till next time!"]), [], [], False)
    if (user_message.lower() == 'it was not helpful'):
        context.user_data['posibles_alias'] = []
        response = random.choice(["Sorry we didn't help you.", "Okay, sorry for the inconvenient", "Sorry, we suggest you to ask different"])
        return return_response(response, [], [], False)
    elif (user_message.lower() == 'bye'):
        response = random.choice(["Bye.", "Okay, see you later!", "Goodbye.", "Hope I helped you!"])
        return return_response(response, [], [], False)
    elif not valid_question(user_message):
        if context.user_data.get('context_question') == None:
            return return_response('Sorry, the question must start with "What", "Which", "Where", "When", "How", "Is", "Did", "Do", "In", "Who", "On", "From", "Has", "Was" or "Are', [], [], False)
        else: 
            context_question = context.user_data.get('context_question')
            context_question_template_en = context.user_data.get('context_question_template_en')
            response, used_similar_mentions = parse_similar_question(user_message, context, [context_question], context_question, context_question_template_en )
            if response != "" and response != None:
                context.user_data["posible_response"] = response
                context.user_data["posible_question"] = user_message
                return return_response(response, [], [], True)
            else:
                send_email_to_qawiki(user_message, 'There was no answer for a question, even using similar question')
                return return_response('There is no information we have an answer', [], [], False)
    else:
        cached_response = search_cached_answer(user_message)
        if cached_response == None:
            response_QAwiki_id, similar_questions = search_id_to_QAwiki(user_message)
            response_QAwiki_id = search_id_to_templates_alias(user_message, response_QAwiki_id)
            print(response_QAwiki_id)
            if response_QAwiki_id == None:
                response, used_similar_mentions = parse_similar_question(user_message, context, similar_questions, None, None)
                if response != "" and response != None:
                    context.user_data["posible_response"] = response
                    context.user_data["posible_question"] = user_message

                    if len(used_similar_mentions) > 0:
                        context.user_data['context_question_template_en'] = used_similar_mentions[0]
                        context.user_data['context_question'] = user_message
                    return return_response(response, [], [], True)
                else:
                    send_email_to_qawiki(user_message, 'There was no answer for a question, even using similar question')
                    return return_response('There is no information we have an answer', [], [], False)
            else:
                response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
                if response_QAwiki_query["query"] == None:
                    send_email_to_qawiki(user_message, 'There was no SPARQL query in the question with id' + response_QAwiki_id)
                    return return_response('There is not result for what you search', [], [], False)
                response = parse_response(user_message, response_QAwiki_query["query"], response_QAwiki_query["analogous_questions"], response_QAwiki_query["general_questions"])
                if (response["answer"]) != 'Unexpected error. Please contact the administrator':
                    response_search_question_template_en = search_question_template_en(user_message)
                    save_answer(user_message, response["answer"], response["analogous_questions"], response["general_questions"], response_search_question_template_en)
                    
                    context.user_data['context_question'] = user_message
                    context.user_data['context_question_template_en'] = response_search_question_template_en
                else:
                    send_email_to_qawiki(user_message, 'There was an error using the sparql given for the question on QAWiki with id' + response_QAwiki_id)
                return return_response(response["answer"], response["analogous_questions"], response["general_questions"], False)
        else:
            context.user_data['context_question'] = user_message
            context.user_data['context_question_template_en'] = cached_response['question_template_en']
            return return_response(cached_response['answer'], cached_response['analogous_questions'], cached_response['general_questions'],False)
           
def return_response(answer, analogous_questions, general_questions, ask_for_add_alias):
     return {
        "answer" :              answer,
        "analogous_questions":  analogous_questions,
        "general_questions":    general_questions,
        'ask_for_add_alias':    ask_for_add_alias
    }
