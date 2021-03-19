from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

import random


class CivAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.ems_ablt = random.randrange(10)  # Capacité à émettre des signaux
        # Capacité à recevoir des signaux
        self.rcpt_ablt = random.randrange(10)
        # Type de civilisation : Pacifique ou Aggressive
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = random.randrange(10)  # Niveau technologique

    def step(self):
        print("Agent {} initialized".format(self.unique_id),
              "Emission ability : {}".format(self.ems_ablt),
              "Reception ability : {}".format(self.rcpt_ablt),
              "Tech lvl : {}".format(self.tech_lvl),
              "Type : {}".format(self.type))


class CivModel(Model):
    """A model with some number of agents."""

    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)  # Créer une timeline

        for i in range(self.num_agents):

            agent = CivAgent(i, self)
            self.schedule.add(agent)  # ajoute N agent à la timeline
            # positionne aléatoirement l'agent sur la grille
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        self.schedule.step()
