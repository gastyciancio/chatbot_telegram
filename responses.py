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
            "general_questions": []
        }

    if not valid_question(user_message):
        return {
            "answer" : 'Sorry, the question must start with "when", "how", "what" or "which"',
            "analogous_questions": [],
            "general_questions": []
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