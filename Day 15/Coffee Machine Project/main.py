MENU = {
    "espresso": {
        "ingredients": {
            "water": 50,
            "coffee": 18,
        },
        "cost": 1.5,
    },
    "latte": {
        "ingredients": {
            "water": 200,
            "milk": 150,
            "coffee": 24,
        },
        "cost": 2.5,
    },
    "cappuccino": {
        "ingredients": {
            "water": 250,
            "milk": 100,
            "coffee": 24,
        },
        "cost": 3.0,
    }
}

resources = {
    "water": 300,
    "milk": 200,
    "coffee": 100,
}
profit = 0

#1.Print Report

#2.Check resources sufficient
def is_resources_sufficient(order_ingredients):
    """Returns True when it can make the order , returns False when it cannot"""
    for item in order_ingredients:
        if order_ingredients[item] > resources[item]:
            print(f"Sorry,there is not enough {item}.")
            return False
        return True



#3. Process coins
def payment_system():
    print("Insert coins please:")
    total = int(input("How many quarters?")) * 0.25
    total += int(input("How many dimes?")) * 0.1
    total += int(input("How many nickles?")) * 0.05
    total += int(input("How many peenies?")) *0.01
    return total

#4. Check transaction successful
def transaction_successful(money_received, drink_cost):
    if money_received >= drink_cost:
        change = round(money_received - drink_cost , 2)
        print(f"Your change is {change}.Thank you very much!")
        global profit
        profit += drink_cost
        return True
    else:
        print("Sorry the money is not enough.Refund is happening right now ...")
        return False


#5. Make Coffee
def coffee_maker(drink_name , order_ingredients):
    for item in order_ingredients:
        resources[item] -= order_ingredients[item]
    print(f"Your {drink_name} is ready️️ ️☕️.Enjoy!")

is_on = True

while is_on:
    choice = input("What would you like? (espresso/latte/cappuccino): ")
    if choice == "off":
        is_on = False
    elif choice == "report":
        print(f"Water: {resources['water']}ml")
        print(f"Milk: {resources['milk']}ml")
        print(f"Coffee: {resources['coffee']}g")
        print(f"Money: ${profit}")
    else:
        drink = MENU[choice]
        if is_resources_sufficient(drink["ingredients"]):
            payment = payment_system()
            if transaction_successful(payment, drink["cost"]):
                coffee_maker(choice, drink["ingredients"])