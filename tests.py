from config import *
from base import *
from robot import *

def print_messages():
    for i in e.keys():
        print(ANSI.GREEN.value + f"{i} received messages:" + ANSI.RESET.value)
        for message in e[i].kb.received_messages["please_help"]:
            print(ANSI.GREEN.value + f"  timestep: {message.timestep}, type: {message.mtype}, position: {message.content}, countdown: {message.countdown}" + ANSI.RESET.value)

        print(ANSI.YELLOW.value + f"{i} read messages:" + ANSI.RESET.value)
        for message in e[i].kb.read_messages["please_help"]:
            print(ANSI.YELLOW.value + f"  timestep: {message.timestep}, type: {message.mtype}, position: {message.content}, countdown: {message.countdown}" + ANSI.RESET.value)
    print("==============================")

def test_read_messages():
    for i in e.keys():
        e[i].read_message()

timestep = 0
map = Grid()

e = {"salt": Robot(grid=map, team=Team.RED, position=[1,0], direction=Dir.SOUTH, deposit=[0,0], timestep=timestep), 
     "pepper": Robot(grid=map, team=Team.RED, position=[2,0], direction=Dir.SOUTH, deposit=[0,0], timestep=timestep), 
     "butter": Robot(grid=map, team=Team.RED, position=[3,4], direction=Dir.SOUTH, deposit=[0,0], timestep=timestep)}

for i in e.keys():
    map.add_robot(e[i], tuple(e[i].pos))

e["salt"].partner = e["pepper"]
e["pepper"].partner = e["salt"]

message = Message(timestep=timestep, mtype="please_help", content=(2,2))

e["salt"].send_to_partner(message)

print_messages()
test_read_messages()
print_messages()
