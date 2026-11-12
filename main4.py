from turtle import Turtle,Screen
import random



t = Turtle()

colors = ["red", "yellow","purple","green","orange","blue"]
directions = [0, 90, 180, 270]

t.shape("turtle")
t.pensize(10)
t.speed(25)

for _ in range(200):
    t.color(random.choice(colors))
    t.forward(25)
    t.setheading(random.choice(directions))








screen = Screen()
screen.colormode(1)
screen.exitonclick()
