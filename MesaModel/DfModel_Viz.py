from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

from DfModel import CivModel

# Grid design
def agent_portrayal(agent):
	portrayal = {"Shape": "circle",
				 "Color": "red", 
				 "Filled": "true",
				 "Layer": 0,
				 "r": 0.5}
	return portrayal 

# Grid dimension
WIDTH, HEIGHT = 500, 500

# Grid squaring
nb_square_x, nb_square_y = 10, 10
grid = CanvasGrid(agent_portrayal, nb_square_x, nb_square_y, WIDTH, HEIGHT) # Initialize grid


server = ModularServer(CivModel, # Initialize Server for Model "CivModel"
					   [grid], 	 # Print grids
					   "Dark Forest Model", # Title
					   {"N":5, "width":10, "height":10}) # Declare CivModel arguments

server.port = 8521 # Set port
server.launch() 
