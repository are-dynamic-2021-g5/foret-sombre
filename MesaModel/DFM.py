from mesa import Agent, Model
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from tkinter import *

import random
import math

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)

##### TKINTER PARAMETERS & INITIALIZATION #####

root = Tk()
root.title("The Dark Forest Theory - Interface")
root.geometry("1000x500")
root.configure(bg='white')

##### IMPORTANT PARAMETERS #####

# MODEL
I = 10

# AGENT PARAMETERS
emission_range = 5
reception_range = 5
technocontactal_range = 3  # From Type 0 to Type 3 (Cf. Kardashev Scale)
suspicion_cooldown = 5

# UNIVERS PARAMETER
univers_scale = 10000
opacity_factor = 1
threshold = 0.1
nb_clusters = 1
clusters_scale = univers_scale/nb_clusters # Modifiable à souhait

# DRAKE EQUATION PARAMETERS : E = R*fg*ne*fl*fi*fc*L
R = 2  # 1 - 3 # average galactic rate of star production
fg = 0.1  # 0.1 #fraction of 'good' and stable dwarves accompanied by planets
ne = 0.1  # 0.1 - 5 # number of candidates planets per system
fl = 0.1  # 0.1 - 1.0 / 10e-8 # fraction of said planets upon which life arises
fi = 0.1  # 0.01 - 1.0 / 10e-8 # fraction of the latter upon which intelligence evolves
fc = 0.5  # 0.01 - 1.0 # fraction of intelligent species which devellop detectable tech
L = 10**6  # arbitrary # the average lifespan of such a technocontactal culture
# the expected number of populated site in a galaxy
E = round(R*fg*ne*fl*fi*fc*L) + 1

################################

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
        self.connection_logs = {}  # connections effectuées dict[tour[int] : list[connections]]
        self.removed_agents = {}  # agents enlevés dict[tour[int] : list[agents]]

        # Chaîne de suspicion
        self.suspicions = {} # key : (agent1, agent2), value : suspicion_cooldown

        # Historique
        self.historique = {} # dict[tour[int], list[agents]]
        self.historique[0] = list(self.schedule._agents.values())

### Utilitaires ###############################################################

    def remove_store(self, agent_id):
        """We use this function instead of the mesa remove() implemented method. It allows storing after supression"""
        self.removed_agents[self.timeline] = []
        self.removed_agents[self.timeline].append(
            self.schedule._agents[agent_id])
        self.schedule.remove(self.schedule._agents[agent_id])

    def restitute_agents(self, time):
        """Permet de revenir à l'état du model à l'étape 'time'"""
        old_state = self.schedule._agents
        to_add = [v for k, v in self.removed_agents.items() if k >= time]

        # list[list]->list[int]
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
        distances_log = {} #key (a, b), value float(distance)
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

        # Update historique
        self.historique[self.timeline] = list(self.schedule._agents.values())
        #print("Historique à time =", self.timeline, [i.unique_id for liste in self.historique.values() for i in liste])

        # Compte le nombre de tour
        print("Tour :", self.timeline)
        self.timeline += 1

        # Connecte les agents
        r_l = self.random_connect()
        # Add the ongoing connection to the log (so it can be reused afterwards)
        self.connection_logs[self.timeline] = r_l
        print("Liste des connections", r_l)

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
                print("Séquence suspicion terminer : ", agentA, agentB)
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

### Indicateurs ###############################################################
    
    def distance_moyenne(self, time):
        agent_ids = [a.unique_id for a in self.historique[time]]
        sum_dist = 0

        for a, b in list(self.distances_log.keys()):
            #print(1)
            if a in agent_ids and b in agent_ids:
                #print(2)
                sum_dist += self.distances_log[(a, b)]

        return sum_dist/((len(agent_ids)*(len(agent_ids)+1))/2)

    def ratio_P(self, time):
        agents = self.historique[time]
        tot_P = 0
        for i in agents:
            if i.type == 0:
                tot_P += 1

        return tot_P/len(agents)

    def ratio_A(self, time):
        return 1-self.ratio_P(time)

    def ems_moyen(self, time):
        agents = self.historique[time]
        sum_ems = 0
        n = 0
        for i in agents:
            sum_ems += i.emission
            n += 1

        return sum_ems/n
        
    def rec_moyen(self, time):
        agent_ids = self.historique[time]
        sum_ems = 0
        n = 0
        for i in agent_ids:
            sum_ems += i.reception
            n += 1

        return sum_ems/n

    def tech_moyen(self, time):
        agent_ids = self.historique[time]
        sum_ems = 0
        n = 0
        for i in agent_ids:
            sum_ems += i.tech_lvl
            n += 1

        return sum_ems/n

    def nb_agent_alive(self, time):
        return len(self.historique[time])

    def nb_agent_dead(self, time):
        return self.nb_agents-len(self.historique[time])

    def nb_contact(self, time):
        return len(self.connection_logs[time+1])

    def plot_ind(self, f):
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        x = [k for k in range(self.timeline)]
        y = [f(i) for i in range(self.timeline)]
        axs.plot(x, y)
        axs.set_ylabel(f.__name__)
        axs.set_xlabel('étapes')

###############################################################################

def tkinter_setup(model):

    ### TKINTER PARAMETERS & INITIALIZATION #####

    # Functions
    # slider func
    def update(s):
        
        to_plot = model.historique[slider.get()]
        #print("Historique à time=", slider.get(), [i.unique_id for i in to_plot])
        ax.clear()
        ax.axis('off')

        for a in to_plot:
            ax.scatter(a.x, a.y, a.z, color='w')

        plot.draw()  
        
        # Labels update
        nb_agents_var.set("Nombre de civilisation "+str(len(to_plot)))
        nb_morts_var.set("Nombre de civilisation mortes "+str(model.nb_agent_dead(slider.get())))        
        ems_moyen_var.set("Niveau moyen d'émission "+str(round(model.ems_moyen(slider.get()), 2)))
        rec_moyen_var.set("Niveau moyen de réception "+str(round(model.rec_moyen(slider.get()), 2)))
        tech_moyen_var.set("Niveau technologique moyen "+ str(round(model.tech_moyen(slider.get()), 2)))
        P_ratio_var.set("Ratio Pacifique : "+ str(round(model.ratio_P(slider.get()), 2)))
        A_ratio_var.set("Ratio Aggressif : "+ str(round(model.ratio_A(slider.get()), 2)))
        nb_contact_var.set("Nombre de contact : "+ str(model.nb_contact(slider.get())))
        distance_moyenne_var.set("Distance moyenne : "+ str(int(model.distance_moyenne(slider.get()))))
    # Get slider values
    def get_sliders_value():
        global R, fg, ne, fl, fi, fc, L, E
        R = R_scale.get()  
        fg = fg_scale.get()  
        ne = ne_scale.get() 
        fl = fl_scale.get()   
        fi = fi_scale.get() 
        fc = fc_scale.get() 
        L = L_scale.get()

        # the expected number of populated site in a galaxy
        E = round(R*fg*ne*fl*fi*fc*L) + 1

    def quit_all():

        root.quit()
        exit()

    # Frames
    plot_frame = Frame(root, bg='black')
    button_frame = Frame(root, bg='white')
    label_frame = Frame(root, bg='white', padx=10)
    #settings_frame = Frame(root, bg='white', padx=10, pady=10)

    # Widgets
    quitter_button = Button(button_frame, bg='white', text='Quitter', command=quit_all)
    start_button = Button(button_frame, bg='white', text='Start', command=main)
    apply_button = Button(button_frame, bg='white', text='Apply', command=get_sliders_value)
    """
    R_scale = Scale(settings_frame, bg='white', label='R', from_=0.1, to=5, resolution=0.1, orient=HORIZONTAL)
    fg_scale = Scale(settings_frame, bg='white', label='fg', from_=0.1, to=0.1, resolution=0.1, orient=HORIZONTAL)
    ne_scale = Scale(settings_frame, bg='white', label='ne', from_=0.1, to=5, resolution=0.1, orient=HORIZONTAL)
    fl_scale = Scale(settings_frame, bg='white', label='fl', from_=0.1, to=1, resolution=0.1, orient=HORIZONTAL)
    fi_scale = Scale(settings_frame, bg='white', label='fi', from_=0.01, to=1, resolution=0.01, orient=HORIZONTAL)
    fc_scale = Scale(settings_frame, bg='white', label='fc', from_=0.01, to=1, resolution=0.01, orient=HORIZONTAL)
    L_scale = Scale(settings_frame, bg='white', label='L', from_=1000000, to=5000000000, resolution=1000000, orient=HORIZONTAL)
    """
    slider = Scale(root, bg='white', from_=0, to=I-1, orient=HORIZONTAL, state='active', tickinterval=round(I/4), command=update)

    # Labels
    # Static labels
    nb_init_agents = Label(label_frame, bg='white', text="Nombre initial de civilisation "+ str(model.nb_agents))
    #drkeq_label = Label(settings_frame, bg='white', text="Équation de Drake :")
    # Dynamic Var
    nb_agents_var = StringVar()
    nb_morts_var = StringVar()
    ems_moyen_var = StringVar()
    rec_moyen_var = StringVar()
    tech_moyen_var = StringVar()
    P_ratio_var = StringVar()
    A_ratio_var = StringVar()
    nb_contact_var = StringVar()
    distance_moyenne_var = StringVar()

    # Dynamic labels
    nb_morts_label = Label(label_frame, bg='white', padx=10, textvariable=nb_morts_var)    
    nb_agents_label = Label(label_frame, bg='white', padx=10, textvariable=nb_agents_var)
    ems_moyen_label = Label(label_frame, bg='white', padx=10, textvariable=ems_moyen_var)
    rec_moyen_label = Label(label_frame, bg='white', padx=10, textvariable=rec_moyen_var)
    tech_moyen_label = Label(label_frame, bg='white', padx=10, textvariable=tech_moyen_var)
    P_ratio_label = Label(label_frame, bg='white', padx=10, textvariable=P_ratio_var)
    A_ratio_label = Label(label_frame, bg='white', padx=10, textvariable=A_ratio_var)
    nb_contact_label = Label(label_frame, bg='white', padx=10, textvariable=nb_contact_var)
    distance_moyenne_label = Label(label_frame, bg='white', padx=10, textvariable=distance_moyenne_var)
    # Grid configuration
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Grid layout
    # Frames
    plot_frame.grid(row=0, column=0, rowspan=3, sticky='nsew')
    button_frame.grid(row=0, column=1, sticky='nsew')
    label_frame.grid(row=1, column=1, sticky='new')
    #settings_frame.grid(row=0, column=2, rowspan=2, sticky='nsew')

    # Widgets
    start_button.grid(row=0, column=1, sticky='nsew')
    quitter_button.grid(row=0, column=0, sticky='nsew')
    apply_button.grid(row=0, column=2, sticky='nsew')

    slider.grid(row=3, column=0, sticky='nsew')
    """
    R_scale.grid(row=1, column=0, sticky='nsew')
    fg_scale.grid(row=2, column=0, sticky='nsew')
    ne_scale.grid(row=3, column=0, sticky='nsew')
    fl_scale.grid(row=4, column=0, sticky='nsew')
    fi_scale.grid(row=5, column=0, sticky='nsew')
    fc_scale.grid(row=6, column=0, sticky='nsew')
    L_scale.grid(row=7, column=0, sticky='nsew')
    """
    # Labels
    nb_init_agents.grid(row=1, column=0, sticky='ne')
    nb_agents_label.grid(row=2, column=0, sticky='ne')
    nb_morts_label.grid(row=3, column=0, sticky='ne')
    ems_moyen_label.grid(row=4, column=0, sticky='ne')
    rec_moyen_label.grid(row=5, column=0, sticky='ne')
    tech_moyen_label.grid(row=6, column=0, sticky='ne')
    P_ratio_label.grid(row=7, column=0, sticky='ne')
    A_ratio_label.grid(row=8, column=0, sticky='ne')
    nb_contact_label.grid(row=9, column=0, sticky='ne')
    distance_moyenne_label.grid(row=10, column=0, sticky='ne')
    #drkeq_label.grid(row=0, column=0, sticky='nsew')

    # 3D graph
    plt.style.use("dark_background")
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.axis('off')
    plot = FigureCanvasTkAgg(fig, master=plot_frame)
    plot.get_tk_widget().pack()

    update('s')

    ###############################################

def plot_lot(model, f, nb_mod, nb_step, mn=True):

        Y=[]
        x = [k for k in range(nb_step)]

        fig, axs = plt.subplots(1, 1)
        axs.set_ylabel(f.__name__)
        axs.set_xlabel('étapes')

        for i in range(nb_mod):
            M = model(E)
            for i in range (nb_step):
                M.step()
       
            y = [f(M, i) for i in range(nb_step)]
            Y.append(y)
            axs.plot(x, y, color='black')

        if mn:
            mean = [0 for i in range(nb_step)]
            for l in Y:
                for j in range(len(l)):
                    mean[j] += l[j]

            for i in range(len(mean)):
                mean[i] /= nb_mod
        
            axs.plot(x, mean, color='red', linewidth=5)


def main():

    model = CivModel(1000)

    ### MAIN LOGIC ####
        
    for i in range(I):
        model.step()

    ###################

    print(R, fg, ne, fl, fi, fc, L, E)

    tkinter_setup(model)

    root.mainloop()

if __name__ == "__main__":
    main()