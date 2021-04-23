from mesa import Agent, Model
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from tkinter import *
import random
import math
import matplotlib.pyplot as plt
#from collections import OrderedDict

##### TKINTER PARAMETERS & INITIALIZATION #####

H = 500
W = 500

#window = Tk()
#canvas = Canvas(window, width=W, height=H, bg='black')
#canvas.pack()

###############################################

##### IMPORTANT PARAMETERS #####

# AGENT PARAMETERS
emission_range = 5
reception_range = 5
technocontactal_range = 3  # From Type 0 to Type 3 (Cf. Kardashev Scale)
suspicion_cooldown = 3

# UNIVERS PARAMETER
univers_scale = 1000
opacity_factor = 1
threshold = 0.01
nb_clusters = 5
clusters_scale = 100

# DRAKE EQUATION PARAMETERS : E = R*fg*ne*fl*fi*fc*L
R = 1  # 1 - 3 # average galactic rate of star production
fg = 0.1  # 0.1 #fraction of 'good' and stable dwarves accompanied by planets
ne = 0.1  # 0.1 - 5 # number of candidates planets per system
fl = 0.1  # 0.1 - 1.0 / 10e-8 # fraction of said planets upon which life arises
fi = 0.1  # 0.01 - 1.0 / 10e-8 # fraction of the latter upon which intelligence evolves
fc = 0.5  # 0.01 - 1.0 # fraction of intelligent species which devellop detectable tech
L = 10**6  # arbitrary # the average lifespan of such a technocontactal culture
global E
# the expected number of populated site in a galaxy
E = round(R*fg*ne*fl*fi*fc*L)

################################
# random.seed(0)


class CivAgent(Agent):

    def __init__(self, unique_id, model):

        super().__init__(unique_id, model)

        # Caracteristic
        self.emission = random.randrange(emission_range)
        self.reception = random.randrange(reception_range)
        self.type = bool(random.getrandbits(1))
        self.tech_lvl = round(random.uniform(0, technocontactal_range), 2)

        # Coordinates
        self.x = None
        self.y = None
        self.z = None  # for 3D

    def step(self):

        print("Agent", self.unique_id, "->",
              " E:", self.emission,
              " R:", self.reception,
              " T:", self.tech_lvl,
              " Type:", "A" if self.type else "P",
              " at:", self.x, self.y, self.z)


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

        # Timeline
        self.timeline = 0
        self.connection_logs = {}  # connections effectuées
        self.removed_agents = {}  # agents enlevés (list unique id)

        # Chaîne de suspicion
        self.suspicions = {} # key : (agent1, agent2), value : suspicion_cooldown

### Utilitaires ###############################################################

    def remove_store(self, agent_id):
        """We use this function instead of the mesa remove() implemented method. It allows storing after supression"""
        self.removed_agents[self.timeline] = []
        self.removed_agents[self.timeline].append(
            self.schedule._agents[agent_id])
        self.schedule.remove(self.schedule._agents[agent_id])

    def restitute_old_state(self, time):
        """Permet de revenir à l'état du model à l'étape 'time'"""
        old_state = self.schedule._agents
        to_add = [v for k, v in self.removed_agents.items() if k >= time]

        # A remplacer
        n = []
        for i in to_add:
            n += i
        to_add = n

        # print(to_add)
        for agent in to_add:
            old_state[agent.unique_id] = agent
        # print(old_state.keys())

        return old_state

###############################################################################

### Localisation ##############################################################

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

    def sort_dict(self, dic, first_term=False):
        """Tri le dictionnaire de distance de la valeur la plus grande à la plus faible"""
        sorted_dict = {}
        if first_term:
            for i in range(self.nb_agents):
                sorted_dict.update({k: v for k,
                                    v in sorted(dic.items(), key=lambda item: item[1]) if i is k[0]})
        else:
            sorted_dict = {k: v for k, v in sorted(
                dic.items(), key=lambda item: item[1])}
        return sorted_dict

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

###############################################################################

### Connection inter-agents ###################################################

    def random_connect(self, methodeTheo=False, seed=0):
        """Renvoie une liste de pair d'agent dans l'orde aléatoire"""
        # random.seed(0) # Pas bien !
        random_id = random.sample(
            [k for k in range(len(list(self.schedule._agents)))], len(list(self.schedule._agents)))
        n_l = list(range(len(list(self.schedule._agents))))
        connection = list(zip(n_l, random_id))
        # print(connection)
        return connection

    def nn_connect(self):
        """Connect chaque agent avec les autres en partant du plus proches"""
        distances_dict = self.calculate_distance()
        for i in range(self.nb_agents):
            order_of_connection = self.sort_dict(distances_dict)
        # print(order_of_connection)
        return order_of_connection.keys()

###############################################################################

### Detection #################################################################

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

            if not a >= threshold:
                print("Trop loin...")
                print(self.distances_log[(min(agentA.unique_id, agentB.unique_id), max(
                    agentA.unique_id, agentB.unique_id))], a, threshold)
                return a >= threshold
            # max(Reception) + 1
            return agentA.reception + agentB.emission >= reception_range+1

###############################################################################

### Logique ###################################################################
    
    def contact(self, a, b):
        """Logique de contact entre deux agents a et b, soit deux agents, cette fonction compare leur
            self.type (0 pour Pacifique (P) et 1 pour aggressif (A)) et leur niveau technologique
            (self.tech_lvl) si besoin"""

        if a in list(self.schedule._agents) and b in list(self.schedule._agents):
            agent_a = self.schedule._agents[a]
            agent_b = self.schedule._agents[b]

            if a == b:
                print("Meme agent")
                return
            # Si A ne detect pas B, vérifie que B ne detect pas A puis passe
            elif not self.detect(agent_a, agent_b):
                print("Agent", a, "ne rentre pas en contact avec Agent",
                      b, ": AR", agent_a.reception, "/ BE", agent_b.emission)
                return

                if not self.detect(agent_b, agent_a):
                    print("Agent", b, "ne rentre pas en contact avec Agent",
                          a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
                    return
                else:
                    print("Mais Agent", b, "rentre en contact avec Agent",
                          a, ": BR", agent_b.reception, "/ AE", agent_a.emission)
        else:
            return

        print("Agents", a, b, "entre en contact !",)
        if agent_a.type < agent_b.type:  # Si b Aggressif et a Pacifist
            self.remove_store(a)
            # self.schedule.remove(agent_a)  # remove a
            print("Agent", a, "destroyed by Agent", b)
        elif agent_a.type > agent_b.type:  # Si b Pacifist et a Aggressif
            self.remove_store(b)
            # self.schedule.remove(agent_b)  # remove b
            print("Agent", b, "destroyed by Agent", a)
        elif agent_a.type == 1 and agent_b.type == 1:  # Si b Aggressif et a Aggressif, regarde le tech_lvl
            print("Agents", a, "and", b, "are both aggresive")
            # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
            if agent_a.tech_lvl == agent_b.tech_lvl:
                print(a, "and", b,
                      "have the same technological level, nothing appends")
                return
            elif agent_a.tech_lvl < agent_b.tech_lvl:  # Si B a un meilleur NT que A, B détruit A
                self.remove_store(a)
                # self.schedule.remove(agent_a)
                print("Agent", b, "stronger than Agent", a)
                print("Agent", a, "destroyed by Agent", b)
            else:
                self.remove_store(b)
                # self.schedule.remove(agent_b)  # Same mais inverse
                print("Agent", a, "stronger than Agent", b)
                print("Agent", b, "destroyed by Agent", a)
        else:
            # Cas où les deux agents sont pacifistes et la chaine de suspicion s'engrange, à implémenter
            print("Agent", a, "and", b,
                  "are both pacifists -> chaine de suspicion (implémenté)----------------------")
            if (a,b) not in self.suspicions:
                self.suspicions[(a,b)] = suspicion_cooldown
                print(self.suspicions)
            # Niv technologique B == Niv technologique A <=> b Pacifist et a Pacifist, donc passe
            if agent_a.tech_lvl == agent_b.tech_lvl:
                print(a, "and", b,
                      "have the same technocontactal level, nothing appends")
                return
            elif agent_a.tech_lvl < agent_b.tech_lvl:  # Si B a un meilleur NT que A, B détruit A
                self.remove_store(a)
                # self.schedule.remove(agent_a)
                print("Agent", b, "stronger than Agent", a)
                print("Agent", a, "destroyed by Agent", b)
            else:
                self.remove_store(b)
                # self.schedule.remove(agent_b)  # Same mais inverse
                print("Agent", a, "stronger than Agent", b)
                print("Agent", b, "destroyed by Agent", a)

    def step(self):
        """Agissement du model à chaque étape"""

        # Compte le nombre de tour
        print("Tour :", self.timeline)
        self.timeline += 1

        # Connecte les agents
        r_l = self.random_connect()
        # Add the ongoing connection to the log (so it can be reused afterwards)
        self.connection_logs[self.timeline] = r_l
        print(r_l)

        #Logique de contact et de 
        self.resolve_suspicious()
        for a, b in r_l:
            self.contact(a, b)

        # Renvoie la liste des agents ayant survécu
        print("Survivors:")
        # affiche les agents restant
        self.schedule.step()
        print("Nombre d'agents restant", len(self.schedule._agents))

    def resolve_suspicious(self):
        for agentA, agentB in self.suspicions.keys():
            if self.suspicions[(agentA, agentB)] == 0:
                self.contact(agentA, agentB)
                print("Argh, ils ont craqué !", agentA, agentB)
                continue
            self.suspicions[(agentA, agentB)] -= 1
            print("Les agents", agentA, "et", agentB, "se méfient")
        print(self.suspicions)

        # delete toutes les chaines terminées
        to_del = list(self.suspicions.items())
        for k, v in to_del:
            if v <= 0:
                del self.suspicions[k]
        print(self.suspicions)


###############################################################################

### Plotting Graphs ###########################################################
    
    def plot_agents_positions(self, color):
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')

        for agent in self.schedule._agents.values():
            ax.scatter(agent.x, agent.y, agent.z, color=color, marker='o')

        plt.show()

    def plot_agents_type(self):
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        types = [int(a.type) for a in self.schedule._agents.values()]

        return axs.hist(types, bins=2)

    def plot_agents_tech(self):
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        tech = [a.tech_lvl for a in self.schedule._agents.values()]

        return axs.hist(tech, bins=technocontactal_range)

    def plot_agents_ems(self):
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        ems = [a.emission for a in self.schedule._agents.values()]

        return axs.hist(ems, bins=emission_range)

    def plot_agents_rec(self):
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        rec = [a.reception for a in self.schedule._agents.values()]

        return axs.hist(rec, bins=reception_range)

###############################################################################


def main():
    model = CivModel(E)

    for i in range(5):
        model.step()


if __name__ == "__main__":
    main()