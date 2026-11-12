import random
from turtle  import Turtle,Screen

nikos = Turtle()
colors = ["red","blue", "brown", "purple","cyan","green"]

def draw_shape(num_sides):
    angle = 360 / num_sides
    for _ in range(num_sides):
        nikos.forward(100)
        nikos.right(angle)
for shape_side_n in range(3,11):
    nikos.color(random.choice(colors))
    draw_shape(shape_side_n)





screen = Screen()
screen.exitonclick()