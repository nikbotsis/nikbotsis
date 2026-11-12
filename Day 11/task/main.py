import random
from art import logo

def deal_card():

    cards = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10 ]
    card = random.choice(cards)
    return card

def calculate_score(cards):
    if sum(cards) == 21 and len(cards) == 2:
        return 0

    if 11 in cards and sum(cards) > 21:
        cards.remove(11)
        cards.append(1)
    return sum(cards)

def compare(u_score, c_score):
    if u_score == c_score:
        return "Draw !!!"

    elif c_score == 0:
        return "Lose, opponent has Blackjack !"

    elif u_score == 0:
        return "Win, you have Blackjack !"

    elif u_score > 21:
        return "You lost ,you've over 21 !"

    elif u_score > c_score:
        return "You win,you've passed CPU !"

    else:
        return "You Lose Bro :("


def play_game():
    print(logo)
    user_cards = []
    computer_cards = []
    user_score = -1
    computer_score = -1
    is_game_over = False

    for _ in range(2):
        user_cards.append(deal_card())
        computer_cards.append(deal_card())


    while not is_game_over:
        user_score = calculate_score(user_cards)
        computer_score = calculate_score(computer_cards)
        print(f"user cards: {user_cards},user's current score: {user_score}")
        print(f"computer cards: {computer_cards}, computer's current score: {computer_score}")

        if user_score == 0 or computer_score == 0 or user_score > 21:
            is_game_over = True
        else:
            user_should_deal = input("Type 'y' to get another card ,type 'n' to pass")
            if user_should_deal == "y":
                user_cards.append(deal_card())
            else:
                is_game_over = True

    while computer_score != 0 and computer_score <17:
        computer_cards.append(deal_card())
        computer_score = calculate_score(computer_cards)


    print(f"The computer's final score is: {computer_score},and the computer's final hand is: {computer_cards}")
    print(f"The user's final score is: {user_score},and the user's final hand is: {user_cards}")
    print(compare(user_score, computer_score))


while input("Do you want to play  BlackJack ? Type 'y' to play , type 'n' to stop !" ) == "y":
    print("\n" * 20)
    play_game()

