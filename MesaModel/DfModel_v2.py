
from mesa import Agent, Model
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

import random
from collections import OrderedDict

emission_range = 5
reception_range = 5
technological_range = 10

class CivAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.emission = random.randrange(emission_range)  # Capacité à émettre des signaux
        # Capacité à recevoir des signaux
        self.reception = random.randrange(reception_range)
        # Type de civilisation : Pacifique ou Aggressive
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = random.randrange(technological_range)  # Niveau technologique
        # Positions des agents qui ne sont déclarés qu'après les dimensions de la grid
        self.x, self.y = None, None
        self.pos = None

    def step(self):
        print("Agent", self.unique_id, " initialized",
              "Emission ability : ", self.emission,
              "Reception ability : ", self.reception,
              "Tech lvl : {}".format(self.tech_lvl),
              "Type :", "Aggressive" if self.type else "Pacifique")


class CivModel(Model):
    """A model with some number of agents."""

    def __init__(self, N, width=500, height=500):
        self.nb_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = BaseScheduler(self)  # Créer une timeline

        for i in range(self.nb_agents):

            agent = CivAgent(i, self)
            self.schedule.add(agent)  # ajoute N agent à la timeline
            # positionne aléatoirement l'agent sur la grille
            agent.x = self.random.randrange(self.grid.width)
            agent.y = self.random.randrange(self.grid.height)
            agent.pos = agent.x, agent.y
            self.grid.place_agent(agent, agent.pos)

    def random_connect(self, seed=0):
        """Renvoie une liste de pair d'agent dans l'orde aléatoire"""
        #random.seed(0) # Pas bien !
        random_id = random.sample(
            [k for k in range(self.nb_agents)], self.nb_agents)
        n_l = [k for k in range(self.nb_agents)]
        connection = list(zip(n_l, random_id))
        print(connection)
        return connection

    def detect(self, agentA, agentB, both=True):
        """Renvoie si oui ou non l'agent a detect l'agent b
            Fonctionnement du système émission/réception:
            Plus un agent émet de signaux, plus il est repérable. Le niveau de reception
            définit la capacité d'un agent à détecter des signaux.
            Par conséquent plus le niveau d'emission d'un agent est haut plus il
            est facilement reperable par des agents dont le niveau de reception est bas.
            """
        if agentA.reception == 0:
            return False
            print("Agent", self.schedule._agents, "ne peut rien reperer") # Cas ou reception = 0, L'agent ne peut rien reperer
        else:
            # Créé une liste par compréhension dont les élement sont les niveaux d'emissions reperables par l'agent A, 
            # si l'agent B a un niveau d'emission appartement à cette liste alors A peut reperer B
            spotable_agents = [k for k in range(emission_range-1, emission_range-agentA.reception-1, -1)]
            print("Agent", agentA.unique_id, "R"+str(agentA.reception), "Agent", agentB.unique_id, "E"+str(agentB.emission), "l'agent peut reperer ceux dont l'emission est : ", spotable_agents)
            return agentB.emission in spotable_agents # renvoie vrai si l'agentB peut etre repere par A ou faux sinon


    def contact(self):
        """Première aspect de la logique utilisé, random_connect crée une 
            liste de tuple qui relie deux CivAgent entre eux cette fonction compare leur 
            self.type (0 pour Pacifique (P) et 1 pour aggressif (A)) et leur niveau technologique
            (self.tech_lvl) si besoin."""

        #print(self.schedule._agents[2])
        #print(list(self.schedule._agents))
        r_l = self.random_connect(0)
        #print(r_l)
        for a, b in r_l:
            #print(a)

            # Si l'agent n'appartient déjà plus à self.schedule (qu'il a donc déjà été remove), passe à la prochaine itération
            if a in list(self.schedule._agents) and b in list(self.schedule._agents):
                agent_a = self.schedule._agents[a]
                agent_b = self.schedule._agents[b]

                if a == b: # Si A est B, passe
                    print("Meme agent")
                    continue
                elif not self.detect(agent_a, agent_b): # Si A ne detect pas B, vérifie que B ne detect pas A puis passe
                    print("Agent", a, "ne rentre pas en contact avec Agent", b, ": AR", agent_a.reception, "/ BE", agent_b.emission)
                    continue
                    if not self.detect(agent_b, agent_a):
                        print("Agent", b, "ne rentre pas en contact avec Agent", a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
                        continue
                    else:
                        print("Mais Agent", b, "rentre en contact avec Agent", a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
            else:
                continue

            print("Agents", a, b, "entre en contact !",
                "Agents restant", list(self.schedule._agents))
            if agent_a.type < agent_b.type:  # Si b Aggressif et a Pacifist
                self.schedule.remove(agent_a)  # remove a
                print("Agent", a, "destroyed by Agent", b)
            elif agent_a.type > agent_b.type:  # Si b Pacifist et a Aggressif
                self.schedule.remove(agent_b)  # remove b
                print("Agent", b, "destroyed by Agent", a)
            elif agent_a.type == 1 and agent_b.type == 1:  # Si b Aggressif et a Aggressif, regarde le tech_lvl
                print("Agents", a, "and", b, "are both aggresive")
                if agent_a.tech_lvl == agent_b.tech_lvl:  # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
                    print(a, "and", b, "have the same technological level, nothing appends")
                    continue
                elif agent_a.tech_lvl < agent_b.tech_lvl:# Si B a un meilleur NT que A, B détruit A
                    self.schedule.remove(agent_a)
                    print("Agent", b ,"stronger than Agent", a)
                    print("Agent", a, "destroyed by Agent", b)
                else:
                    self.schedule.remove(agent_b) # Same mais inverse
                    print("Agent", a ,"stronger than Agent", b)
                    print("Agent", b, "destroyed by Agent", a)
            else:
                # Cas où les deux agents sont pacifistes et la chaine de suspicion s'engrange, à implémenter
                print("Agent", a, "and", b, "are both pacifists -> chaine de suspicion (a implémenté, ne fait rien pour l'instant)")
                if agent_a.tech_lvl == agent_b.tech_lvl:  # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
                    print(a, "and", b, "have the same technological level, nothing appends")
                    continue
                elif agent_a.tech_lvl < agent_b.tech_lvl:# Si B a un meilleur NT que A, B détruit A
                    self.schedule.remove(agent_a)
                    print("Agent", b ,"stronger than Agent", a)
                    print("Agent", a, "destroyed by Agent", b)
                else:
                    self.schedule.remove(agent_b) # Same mais inverse
                    print("Agent", a ,"stronger than Agent", b)
                    print("Agent", b, "destroyed by Agent", a)
                    
        # Renvoie la liste des agents ayant survécu
        survivors = [index for index in list(self.schedule._agents)]
        print("Survivors:")
        #affiche les agents restant
        self.schedule.step()
        return survivors

    def step(self):
        #self.schedule.step()
        self.contact()

def main():
    empty_model = CivModel(5)
    empty_model.schedule.step()
    for i in range(5):
        print("Tour : " + str(i))
        empty_model.step()
        print("Nombre d'agents restant", len(empty_model.schedule._agents))
    empty_model.step

if __name__ == "__main__":
    main()