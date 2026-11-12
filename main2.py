from turtle import Turtle, Screen

nik = Turtle()

nik.shape("circle")
nik.color("red")
for _ in range(8):

    nik.forward(50)
    nik.penup()
    nik.forward(25)
    nik.pendown()
    nik.left(50)

screen = Screen()
screen.exitonclick()