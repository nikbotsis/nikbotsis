###This code will not work in repl.it as there is no access to the colorgram package here.###
##We talk about this in the video tutorials##
#import colorgram


#rgb_colors = []
#colors = colorgram.extract('image.jpg', 30)
#for color in colors:
    #rgb_colors.append(color.rgb)

#print(rgb_colors)


import turtle as turtle_module
import random


turtle_module.colormode(255)
tim = turtle_module.Turtle()
tim.speed("fastest")
tim.penup()
tim.hideturtle()
color_list =[(245,243,238),(246, 242, 244),(202, 164, 110),(240, 245, 241),(236, 239, 243),(149, 75, 50),(222, 201, 136), (53, 93, 123)]


tim.setheading(225)
tim.forward(250)
tim.setheading(0)
number_of_dots = 100


for dot_count in range(1,number_of_dots + 1):
    tim.dot(20,random.choice(color_list) )
    tim.forward(50)

    if dot_count % 10 == 0:
        tim.setheading(90)
        tim.forward(50)
        tim.setheading(180)
        tim.forward(500)
        tim.setheading(0)


screen = turtle_module.Screen()
screen.exitonclick()