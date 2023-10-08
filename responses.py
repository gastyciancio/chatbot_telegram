from queries import search

def respond_to(input_text):
    user_message = str(input_text).lower()

    response = search(user_message)

    return response