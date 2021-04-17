
from mesa import Agent, Model
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

import random
import math
from collections import OrderedDict

emission_range = 5
reception_range = 5
technological_range = 10
univers_scale = 1000
opacity_factor = 1
threshold = 0.001
# random.seed(0)

class CivAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # Capacité à émettre des signaux
        self.emission = random.randrange(emission_range)
        # Capacité à recevoir des signaux
        self.reception = random.randrange(reception_range)
        # Type de civilisation : Pacifique ou Aggressive
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = random.randrange(technological_range) 
        # Niveau technologique
        # Positions des agents qui ne sont déclarés qu'après les dimensions de la grid
        self.x, self.y, self.z = random.randrange(1000), random.randrange(1000), random.randrange(1000)
        self.pos = self.x, self.y

    def step(self):
        print("Agent", self.unique_id, " initialized",
              "Emission ability : ", self.emission,
              "Reception ability : ", self.reception,
              "Tech lvl : ", self.tech_lvl,
              "Type :", "Aggressive" if self.type else "Pacifique")


class CivModel(Model):
    """A model with some number of agents."""

    def __init__(self, N):
        self.nb_agents = N
        self.schedule = BaseScheduler(self)  # Créer une timeline

        for i in range(self.nb_agents):
            agent = CivAgent(i, self)
            self.schedule.add(agent)  # ajoute N agent à la timeline
            # positionne aléatoirement l'agent sur la grille

        self.distances_log = self.calculate_distance()

    def random_connect(self, methodeTheo=False, seed=0):
        """Renvoie une liste de pair d'agent dans l'orde aléatoire"""
        #random.seed(0) # Pas bien !
        random_id = random.sample(
            [k for k in range(len(list(self.schedule._agents)))], len(list(self.schedule._agents)))
        n_l = list(range(len(list(self.schedule._agents))))
        connection = list(zip(n_l, random_id))
        print(connection)
        return connection

    def calculate_distance(self):
        distances_log = {}
        for i in self.schedule._agents:
            #print(distances_log, len(distances_log))
            if i in self.schedule._agents.keys():
                agentA = self.schedule._agents[i]
                for j in range(i+1, len(self.schedule._agents)):
                    if j in self.schedule._agents.keys():
                        agentB = self.schedule._agents[j]
                        d = math.sqrt((agentA.x-agentB.x)**2+(agentA.y-agentB.y)**2)
                        distances_log[(i, j)] = d
        return distances_log

    def detect_distance_check(self, distance, opacity_factor, threshold):
        d_scaled = distance/univers_scale
        return math.exp(-opacity_factor*d_scaled)

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
            # Cas ou reception = 0, L'agent ne peut rien reperer
            print("Agent", self.schedule._agents, "ne peut rien reperer")
        else:
            a = self.detect_distance_check(self.distances_log[(min(agentA.unique_id, agentB.unique_id), max(agentA.unique_id, agentB.unique_id))], opacity_factor, threshold)
            print(self.distances_log[(min(agentA.unique_id, agentB.unique_id), max(agentA.unique_id, agentB.unique_id))], a, threshold)
            if not a >= threshold:
                print("Trop loin...")
                
            return agentA.reception + agentB.emission >= reception_range+1 and a >= threshold# max(R) + 1

    def contact(self):
        """Première aspect de la logique utilisé, random_connect crée une
            liste de tuple qui relie deux CivAgent entre eux cette fonction compare leur
            self.type (0 pour Pacifique (P) et 1 pour aggressif (A)) et leur niveau technologique
            (self.tech_lvl) si besoin."""

        # print(self.schedule._agents[2])
        # print(list(self.schedule._agents))
        r_l = self.random_connect()
        # print(r_l)
        for a, b in r_l:
            # print(a)

            # Si l'agent n'appartient déjà plus à self.schedule (qu'il a donc déjà été remove), passe à la prochaine itération
            if a in list(self.schedule._agents) and b in list(self.schedule._agents):
                agent_a = self.schedule._agents[a]
                agent_b = self.schedule._agents[b]

                if a == b:  # Si A est B, passe
                    print("Meme agent")
                    continue
                # Si A ne detect pas B, vérifie que B ne detect pas A puis passe
                elif not self.detect(agent_a, agent_b):
                    print("Agent", a, "ne rentre pas en contact avec Agent",
                          b, ": AR", agent_a.reception, "/ BE", agent_b.emission)
                    continue
                    if not self.detect(agent_b, agent_a):
                        print("Agent", b, "ne rentre pas en contact avec Agent",
                              a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
                        continue
                    else:
                        print("Mais Agent", b, "rentre en contact avec Agent",
                              a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
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
                # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
                if agent_a.tech_lvl == agent_b.tech_lvl:
                    print(a, "and", b,
                          "have the same technological level, nothing appends")
                    continue
                elif agent_a.tech_lvl < agent_b.tech_lvl:  # Si B a un meilleur NT que A, B détruit A
                    self.schedule.remove(agent_a)
                    print("Agent", b, "stronger than Agent", a)
                    print("Agent", a, "destroyed by Agent", b)
                else:
                    self.schedule.remove(agent_b)  # Same mais inverse
                    print("Agent", a, "stronger than Agent", b)
                    print("Agent", b, "destroyed by Agent", a)
            else:
                # Cas où les deux agents sont pacifistes et la chaine de suspicion s'engrange, à implémenter
                print("Agent", a, "and", b,
                      "are both pacifists -> chaine de suspicion (a implémenté, ne fait rien pour l'instant)")
                # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
                if agent_a.tech_lvl == agent_b.tech_lvl:
                    print(a, "and", b,
                          "have the same technological level, nothing appends")
                    continue
                elif agent_a.tech_lvl < agent_b.tech_lvl:  # Si B a un meilleur NT que A, B détruit A
                    self.schedule.remove(agent_a)
                    print("Agent", b, "stronger than Agent", a)
                    print("Agent", a, "destroyed by Agent", b)
                else:
                    self.schedule.remove(agent_b)  # Same mais inverse
                    print("Agent", a, "stronger than Agent", b)
                    print("Agent", b, "destroyed by Agent", a)

        # Renvoie la liste des agents ayant survécu
        survivors = [index for index in list(self.schedule._agents)]
        print("Survivors:")
        # affiche les agents restant
        # self.schedule.step()
        return survivors

    def step(self):
        #self.schedule.step()
        self.calculate_distance()
        self.contact()

def main():
    model = CivModel(1000)
    model.step()
    for i in range(100):
        print("Tour : ", i)
        model.step()
        print("Nombre d'agents restant", len(model.schedule._agents))


if __name__ == "__main__":
    main()
