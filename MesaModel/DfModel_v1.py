
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

import random
from collections import OrderedDict


class CivAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.emission = random.randrange(2)  # Capacité à émettre des signaux
        # Capacité à recevoir des signaux
        self.reception = random.randrange(2)
        # Type de civilisation : Pacifique ou Aggressive
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = random.randrange(10)  # Niveau technologique
        # Positions des agents qui ne sont déclarés qu'après les dimensions de la grid
        self.x, self.y = None, None
        self.pos = None

    def step(self):
        print("Agent {} initialized".format(self.unique_id),
              #"Emission ability : {}".format(self.emission),
              #"Reception ability : {}".format(self.reception),
              #"Tech lvl : {}".format(self.tech_lvl),
              "Type :", "Aggressive" if self.type else "Pacifique")


class CivModel(Model):
    """A model with some number of agents."""

    def __init__(self, N, width=500, height=500):
        self.nb_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)  # Créer une timeline

        for i in range(self.nb_agents):

            agent = CivAgent(i, self)
            self.schedule.add(agent)  # ajoute N agent à la timeline
            # positionne aléatoirement l'agent sur la grille
            agent.x = self.random.randrange(self.grid.width)
            agent.y = self.random.randrange(self.grid.height)
            agent.pos = agent.x, agent.y
            self.grid.place_agent(agent, agent.pos)

    def random_connect(self):
        """Renvoie une liste de pair d'agent, dans l'ordre si random=False"""
        random_id = random.sample(
            [k for k in range(self.nb_agents)], self.nb_agents)
        n_l = [k for k in range(self.nb_agents)]
        connection = list(zip(n_l, random_id))
        return connection

    def contact(self):
        """Première aspect de la logique utilisé, random_connect crée une 
            liste de tuple qui relie deux CivAgent entre eux cette fonction compare leur 
            self.type (0 pour Pacifique (P) et 1 pour aggressif (A)) et leur niveau technologique
            (self.tech_lvl) si besoin."""

        #print(self.schedule._agents[2])
        #print(list(self.schedule._agents))
        r_l = self.random_connect()
        #print(r_l)
        for a, b in r_l:
            #print(a)

            # Si l'agent a deja ete remove, continue
            if a in list(self.schedule._agents) and b in list(self.schedule._agents):
                agent_a = self.schedule._agents[a]
                agent_b = self.schedule._agents[b]
            else:
                continue

            if agent_a.type < agent_b.type:  # Si b A et a P
                self.schedule.remove(agent_a)  # remove a
                print("Agent", a, "destroyed by Agent", b)
            elif agent_a.type > agent_b.type:  # Si b P et a A
                self.schedule.remove(agent_b)  # remove b
                print("Agent", b, "destroyed by Agent", a)
            elif agent_a.type == 1 and agent_b.type == 1:  # Si b A et a A, regarde le tech_lvl
                print("Agents", a, "and", b, "are both aggresive")
                if agent_a.tech_lvl == agent_b.tech_lvl:  # btech == atech <=> b P et a P
                    print(a, "and", b, "have the same technological level, nothing appends")
                    continue
                elif agent_a.tech_lvl < agent_b.tech_lvl:
                    self.schedule.remove(agent_a)
                    print("Agent", b ,"stronger than Agent", a)
                    print("Agent", a, "destroyed by Agent", b)
                else:
                    self.schedule.remove(agent_b)
                    print("Agent", a ,"stronger than Agent", b)
                    print("Agent", b, "destroyed by Agent", a)
            else:
                continue
        # Renvoie la liste des agents ayant survécu
        survivors = [index for index in list(self.schedule._agents)]
        print("Survivors:", survivors)
        return survivors

    def step(self):
        self.schedule.step()
        self.contact()
