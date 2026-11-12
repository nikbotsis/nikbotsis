#age = int(input("How old are you?"))
#if age >= 18:
    #print(f"You can drive at age {age}.")
#else:
    #print(f"You can not drive ,because you are less than {age} years old.")

try:
    print(6 > 5)
except TypeError:
    print("You can't mix integers and strings in a comparison")