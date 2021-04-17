from mesa import Agent, Model
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from tkinter import *
import random
import math
#from collections import OrderedDict

##### TKINTER PARAMETERS & INITIALIZATION #####

H = 500
W = 500

#

window = Tk()
canvas = Canvas(window, width=W, height=H, bg='black')
canvas.pack()

###############################################

##### IMPORTANT PARAMETERS #####

# AGENT PARAMETERS
emission_range = 5
reception_range = 5
technological_range = 10

# UNIVERS PARAMETER
univers_scale = 500
opacity_factor = 1
threshold = 0.001
nb_clusters = 3
clusters_scale = 100

################################
# random.seed(0)


class CivAgent(Agent):

    def __init__(self, unique_id, model):

        super().__init__(unique_id, model)

        # Caracteristic
        self.emission = random.randrange(emission_range)
        self.reception = random.randrange(reception_range)
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = random.randrange(technological_range)

        # Coordinates
        self.x = None
        self.y = None
        self.z = None  # for 3D

    def step(self):

        print("Agent", self.unique_id, " initialized",
              "Emission ability : ", self.emission,
              "Reception ability : ", self.reception,
              "Tech lvl : ", self.tech_lvl,
              "Type :", "Aggressive" if self.type else "Pacifique")

    def activate_suspicion(self, agent_id):
        self.suspicious = 1, agent_id


class CivModel(Model):

    def __init__(self, N):

        self.nb_agents = N  # Nombre d'agents
        self.schedule = BaseScheduler(self)  # Timeline basic

        # Initializations spatials des agents
        positions = self.spawn_clusters()
        #print(positions, len(positions))

        for i in range(self.nb_agents):
            # positionne aléatoirement l'agent sur la grille
            agent = CivAgent(i, self)
            agent.x, agent.y, agent.z = positions[i]
            self.schedule.add(agent)  # ajoute les agents à la timeline

        # Calcules les distances entre les agents
        self.distances_log = self.calculate_distance()

    def spawn_clusters(self):
        """Répartis les civilisations en clusters de densité égale 
           dans l'univers (peut être assimiler à des galaxies)"""
        coords = []

        for i in range(nb_clusters):
            clx, cly, clz = random.randint(0, univers_scale), random.randint(
                0, univers_scale), random.randint(0, univers_scale)  # Créer un point de cluster

            # Créé un nombres de groupe d'agent équivalent à celui des clusters
            rd_nb_civ = int(self.nb_agents/nb_clusters)+1
            # Répartis aléatoiremnt les civilisations autour de ce clusters dans un radius donné.
            for j in range(rd_nb_civ):
                r = clusters_scale
                pl_x, pl_y, pl_z = random.randint(max(
                    0, clx-r), min(univers_scale, clx+r)), random.randint(max(0, cly-r), min(univers_scale, cly+r)), random.randint(max(0, clz-r), min(univers_scale, clz+r))
                coords.append((pl_x, pl_y, pl_z))
        return coords

    def random_connect(self, methodeTheo=False, seed=0):
        """Renvoie une liste de pair d'agent dans l'orde aléatoire"""
        # random.seed(0) # Pas bien !
        random_id = random.sample(
            [k for k in range(len(list(self.schedule._agents)))], len(list(self.schedule._agents)))
        n_l = list(range(len(list(self.schedule._agents))))
        connection = list(zip(n_l, random_id))
        # print(connection)
        return connection

    def sort_dict(self, dic, first_term=False):
        sorted_dict = {}
        if first_term:
            for i in range(self.nb_agents):
                sorted_dict.update({k: v for k,
                                    v in sorted(dic.items(), key=lambda item: item[1]) if i is k[0]})
        else:
            sorted_dict = {k: v for k, v in sorted(
                dic.items(), key=lambda item: item[1])}
        return sorted_dict

    def nn_connect(self):
        """Connect chaque agent avec les autres en partant du plus proches"""
        distances_dict = self.calculate_distance()
        for i in range(self.nb_agents):
            order_of_connection = self.sort_dict(distances_dict)
        # print(order_of_connection)
        return order_of_connection.keys()

    def calculate_distance(self):
        """Créé un dictionnaire dont les keys sont la pair d'agent en question la la value la distance les séparant"""
        distances_log = {}
        for i in self.schedule._agents:
            #print(distances_log, len(distances_log))
            if i in self.schedule._agents.keys():
                agentA = self.schedule._agents[i]
                for j in range(i+1, len(self.schedule._agents)):
                    if j in self.schedule._agents.keys():
                        agentB = self.schedule._agents[j]
                        d = math.sqrt((agentA.x-agentB.x)**2 +
                                      (agentA.y-agentB.y)**2 + (agentA.z-agentB.z)**2)
                        distances_log[(i, j)] = d
        return distances_log

    def detect_distance_check(self, distance, opacity_factor, threshold):
        """Utilise la fonction exp(-kx) pour simuler la difficulté des civilisations 
            à communiquer par rapport à la distance qui les sépare"""
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
            a = self.detect_distance_check(self.distances_log[(min(agentA.unique_id, agentB.unique_id), max(
                agentA.unique_id, agentB.unique_id))], opacity_factor, threshold)
            print(self.distances_log[(min(agentA.unique_id, agentB.unique_id), max(
                agentA.unique_id, agentB.unique_id))], a, threshold)
            if not a >= threshold:
                print("Trop loin...")

            # max(Reception) + 1, merci Théo
            return agentA.reception + agentB.emission >= reception_range+1 and a >= threshold

    def remove_store(self, agent_id, storage):
        storage.append(self.schedule._agents[agent_id])
        self.schedule.remove(agent_id, storage)
        return storage

    def contact(self):
        """Première aspect de la logique utilisé, random_connect crée une
            liste de tuple qui relie deux CivAgent entre eux cette fonction compare leur
            self.type (0 pour Pacifique (P) et 1 pour aggressif (A)) et leur niveau technologique
            (self.tech_lvl) si besoin."""

        # print(self.schedule._agents[2])
        # print(list(self.schedule._agents))
        r_l = self.nn_connect()
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

            print("Agents", a, b, "entre en contact !",)
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
        self.schedule.step()
        return survivors

    def step(self):
        # self.schedule.step()
        self.calculate_distance()
        self.contact()


def main():
    N = 100
    model = CivModel(N)
    # print(model.nn_connect())
    model.step()
    draw(canvas, model.schedule._agents, 'white')

    for i in range(1000):
        print("Tour : ", i)
        model.step()
        print("Nombre d'agents restant", len(model.schedule._agents))

    draw(canvas, model.schedule._agents, 'green')
    model.schedule.step()
    window.mainloop()  # Visualize!


def draw(canvas, agents_list, color):
    for agent in agents_list.values():
        canvas.create_oval(agent.x, agent.y, agent.x +
                           10, agent.y+10, fill=color)


if __name__ == "__main__":
    main()
