from turtle import Turtle,Screen
import random


n = Turtle()

colors = ["red", "yellow","purple","green","orange","blue"]
n.speed("fastest")
n.pensize(3)

def draw_spiral_graph(size_of_gap):
    for _ in range(int(360 / size_of_gap )):
        n.circle(100)
        n.color(random.choice(colors))
        n.setheading(n.heading() + size_of_gap)
        n.circle(100)

draw_spiral_graph(5)

screen = Screen()
screen.exitonclick()