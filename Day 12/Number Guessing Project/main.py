from random import randint
from art import logo

EASY_LEVEL_TURNS = 10
DIFFICULT_LEVEL_TURNS = 5

def check_answers(user_guess, actual_answer, turns):
    if user_guess > actual_answer:
        print("Too high")
        return turns -1
    elif user_guess < actual_answer:
        print("Too low")
        return turns -1
    else:
        print(f"Congratulations! You have the right answer -> {actual_answer} ")




def set_difficulty():
    level = input("Choose difficulty.Type 'easy' or 'difficult': ")
    if level =="easy":
        return EASY_LEVEL_TURNS
    else:
        return DIFFICULT_LEVEL_TURNS

def game():
    print(logo)
    print("Welcome to the number guessing game !")
    print("I'm thinking a number between 1 and 100 : ")
    answer = randint(a=1,b=100)
    print(f"Heyyy , the correct answer is {answer} ")

    turns = set_difficulty()

    guess = 0
    while guess != answer:
        print(f"You have still {turns} attempts to make the right guess :| ")
        guess = int(input("Take a guess: "))
        turns = check_answers(guess, answer, turns)
        if turns == 0:
            print("Game Over.Press to start again.")
            return
        elif guess != answer:
            print("Guess again.")

game()