import random
from art import logo
from art import vs
from game_data import data

def format_data(account):
    """ Takes the account data and returns the printable format"""
    account_name = account["name"]
    account_descr = account["description"]
    account_country = account["country"]
    return f"{account_name},a {account_descr} from {account_country}"

def check_answer(user_guess ,a_followers, b_followers):
    """Takes user's guess and then compares the followers between the accounts and returns if they got it right"""
    if a_followers > b_followers:
        return user_guess == "a"
    else:
        return user_guess == "b"



print(logo)
score=0
game_should_continue = True
account_b = random.choice(data)

while game_should_continue:
    #Generate a random account from the game data
    account_a = account_b
    account_b = random.choice(data)
    if account_a == account_b:
        account_b = random.choice(data)

    print(f"Compare A: {format_data(account_a)}")
    print(vs)
    print(f"Compare B: {format_data(account_b)}")

    guess = input("Who has more followers?Type 'a' or 'b': ").lower()

    #Clear the screem
    print("\n"*20)
    print(logo)

    a_follower_count = account_a["follower_count"]
    b_follower_count = account_b["follower_count"]
    is_correct = check_answer(guess, a_follower_count, b_follower_count)


    if is_correct:
        score += 1
        print(f"You are right.Current score is {score}")
    else:
        print(f"Ops..That's wrong.Final score is {score}")
        game_should_continue = False
