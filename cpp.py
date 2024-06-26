import os
import csv
import gzip
import argparse
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from urllib.request import urlretrieve
from matplotlib.animation import FuncAnimation

def createGraph(ville, pays, speed_dic):
    """
    ### Paramètres
    - ville : str
        - [Nom de la ville]
    - pays : str
        - [Nom du pays]
    - speed_dic : dict
        - [Dictionnaire des vitesses]
    ### Opérations
    - Crée un graphe des routes à partir de la ville et du pays, en mode non simplifié.
    ### Retour
    - M : NetworkX graph
        - [Graphe non orienté]
    """
    lieu=ville+', '+pays
    M=ox.convert.to_undirected(ox.graph_from_place(lieu, network_type="drive_service", simplify=False))
    #On ajoute les longueurs des arêtes
    M=ox.distance.add_edge_lengths(M)
    #On ajoute les limitations de vitesses
    M=ox.routing.add_edge_speeds(M, speed_dic, 20)
    #Pour ensuite ajouter les temps de trajet.
    M=ox.routing.add_edge_travel_times(M)
    return M

def to_eularian(G) :
    """
    ### Paramètres
    - G : NetworkX graph
        - [Graphe non orienté]
    ### Opérations
    - Transforme le graphe en graphe eulérien
    ### Retour
    - weighted_edges : List
        - [Liste des arêtes pondérées]
    """
    weighted_edges = list(G.edges(keys=True, data=True))
    tmp=[]
    for i in range(len(weighted_edges)):
        tmp.append((weighted_edges[i][0],weighted_edges[i][1],weighted_edges[i][3]['travel_time']))
    weighted_edges = tmp
    
    G = nx.eulerize(G)
    return weighted_edges

def create_correspondance_dict(weighted_edges) :
    """
    ### Paramètres
    - weighted_edges : List
        - [Liste des arêtes pondérées]
    ### Opérations
    - Pour chaque arête, crée sa contrepartie en base 0 et l'ajoute au dictionnaire de correspondance
    - Crée une nouvelle liste d'arêtes pondérées avec les nouvelles arêtes
    ### Retour
    - correspondance : Dict
        - [Dictionnaire de correspondance]
    - new_edges : List
        - [Nouvelle liste des arêtes pondérées]
    """
    correspondance = {}
    new_edges = []
    i = 0
    for (u,v,w) in weighted_edges:
        if (u not in correspondance):
            correspondance[u] = i
            i += 1
        if (v not in correspondance):
            correspondance[v] = i
            i += 1
        new_edges.append((correspondance[u],correspondance[v],w))
    return correspondance, new_edges

def file_operations(nodes, new_edges) :
    """
    ### Paramètres
    - nodes : int
        - [Nombre de noeuds]
    - new_edges : List
        - [Nouvelle liste des arêtes pondérées]
    ### Opérations
    - Ecrit dans un fichier texte les données du graphe sous la forme :
        - [Nombre de noeuds]
        - [Nombre d'arêtes]
        - Puis pour chaque arête :
        - [noeud_de_départ noeud_de_fin poids]
    """
    f = open("./media/graph.txt", "w")
    f.write(str(nodes)+"\n"+str(len(new_edges))+"\n")
    for (u,v,w) in new_edges:
        f.write(str(u)+" "+str(v)+" "+str(w)+"\n")
    f.close()

def read_result(correspondance) :
    """
    ### Paramètres
    - correspondance : Dict
        - [Dictionnaire de correspondance]
    ### Opérations
    - Lit le fichier texte contenant les résultats du calcul du chinese postman problem
    ### Retour
    - path : List
        - [Liste des noeuds du chemin optimal]
    """
    read2 = []
    path = []
    with open("./media/results.txt", "r") as f:
        read2 = f.read().splitlines()
    for line in read2[0].split(" "):
        if (line != "") :
            for (key, value) in correspondance.items():
                if (value == int(line)):
                    path.append(key)
                    break
    return path

def multiplePathAnimation(graph,pathList):
    """
    ### Paramètres
    - graph : NetworkX graph
        - [Graphe non orienté]
    - pathList : List
        - [list de routes osmnx]
    ### Opérations
    - Crée, affiche et sauvegarde une animation des chemins donnés en paramètres
    """

    def getNthValueFromEachTab(tab,n):
        res=[]
        for i in range(len(tab)):
            if n<len(tab[i]):
                res.append(tab[i][n])
            else:
                res.append(tab[i][-1])
        return res
    
    def initAnim():
        return line, scatter_list
    
    # Fonction d'animation
    def animate(i):
        xCoord=getNthValueFromEachTab(lons,i)
        yCoord=getNthValueFromEachTab(lats,i)
        if (len(pathList)>=3):
            for _ in range(n):
                if i<len(lons[2]):
                    line.set_data(lons[2][:i], lats[2][:i])
                if i==len(lons[2]):
                    line.set_data(lons[2], lats[2])
        for j in range(n):
            scatter_list[j].set_offsets((xCoord[j], yCoord[j]))
        
        return line, scatter_list
    
    listOfColors=['red','orange', 'yellow','green','blue','purple','brown','black']
    n=len(pathList)
    cNodes=[[] for _ in range(n)]
    for i in range(n):
        for point in pathList[i]:
            cNodes[i].append((graph._node[point]['x'],graph._node[point]['y']))
    # Configuration de la figure
    fig, ax = plt.subplots(figsize=(10, 10))
    # Tracé du graphe
    ox.plot_graph(graph, ax=ax, edge_color='#cecece', node_color='#cecece', node_size=0.5 ,show=False, close=False)
    # Extraction des coordonnées du chemin
    route_nodes = graph.nodes(data=True)
    lats=[]
    lons=[]
    for path in pathList:
        lats.append([route_nodes[node]['y'] for node in path])
        lons.append([route_nodes[node]['x'] for node in path])  
    
    # Tracé du chemin
    for i in range(n):
        nColor=i
        while i>(len(listOfColors)-1):
            nColor-=len(listOfColors)
        ax.plot(lons[i], lats[i], color=listOfColors[nColor], linewidth=2, alpha=0.7)
    # Initialisation de la ligne de l'animation
    """__________________________Animation____________________________________"""
    xCoord=getNthValueFromEachTab(lons,0)
    yCoord=getNthValueFromEachTab(lats,0)
    scatter_list=[]
    # Plot the first scatter plot (starting nodes = initial car locations = hospital locations)
    for i in range(n):
        scatter_list.append(ax.scatter(xCoord[i],yCoord[i], s=20, marker='o', c=listOfColors[i], label=f'Facteur {i+1}', alpha=0.7))

    line, = ax.plot([], [], color='#2dffe0', linewidth=2, alpha=0.7)

    plt.legend(frameon=False)

    # Création de l'animation
    ani = FuncAnimation(fig, animate, init_func=initAnim, frames=max(len(lons[i]) for i in range(n)), interval=100) #
    print("Saving animation...")
    ani.save('./media/route_animation.mp4', dpi=200)
    plt.show()
    
    plt.close()

def dividePath(graph, path, n):
    #A voir comment on récupère les données
    egdeWeight=[]
    for i in range(len(path)-1):
        x=graph.get_edge_data(path[i],path[i+1])
        for key in x:
            egdeWeight.append(x[key]['travel_time'])
    #Début de la fonction
    sumPath=sum(egdeWeight)
    maxWeight=(sumPath/n)*1.05
    minWeight=(sumPath/n)*0.95
    if int(len(path)/n)<len(path)/n:
            len_path=int(len(path)/n)+1
    else:
        len_path=int(len(path)/n)
    paths=[]
    sums=[]
    end=0
    for i in range(n):
        beginning=end
        end=(i+1)*len_path+1
        if end>len(path):
            end=len(path)
        else:
            while sum(egdeWeight[beginning:end-1])>maxWeight or sum(egdeWeight[beginning:end-1])>sumPath/n:
                end-=1
            while sum(egdeWeight[beginning:end-1])<minWeight:
                end+=1
        paths.append(path[beginning:end])
        sums.append(sum(egdeWeight[beginning:end-1]))
    return paths
    

def get_departement(ville, pays):
    departements = {"Ain": "01", "Aisne": "02", "Allier": "03", "Alpes-de-Haute-Provence": "04", "Hautes-Alpes": "05",
    "Alpes-Maritimes": "06", "Ardèche": "07","Ardennes": "08","Ariège": "09","Aube": "10","Aude": "11","Aveyron": "12",
    "Bouches-du-Rhône": "13","Calvados": "14","Cantal": "15","Charente": "16","Charente-Maritime": "17","Cher": "18",
    "Corrèze": "19","Côte-d'Or": "21","Côtes-d'Armor": "22","Creuse": "23","Dordogne": "24","Doubs": "25","Drôme": "26",
    "Eure": "27","Eure-et-Loir": "28","Finistère": "29", "Corse-du-Sud": "2A","Haute-Corse": "2B","Gard": "30","Haute-Garonne": "31",
    "Gers": "32","Gironde": "33","Hérault": "34","Ille-et-Vilaine": "35","Indre": "36","Indre-et-Loire": "37","Isère": "38",
    "Jura": "39","Landes": "40","Loir-et-Cher": "41","Loire": "42","Haute-Loire": "43","Loire-Atlantique": "44","Loiret": "45",
    "Lot": "46","Lot-et-Garonne": "47","Lozère": "48","Maine-et-Loire": "49","Manche": "50","Marne": "51","Haute-Marne": "52",
    "Mayenne": "53","Meurthe-et-Moselle": "54","Meuse": "55","Morbihan": "56","Moselle": "57","Nièvre": "58","Nord": "59",
    "Oise": "60","Orne": "61","Pas-de-Calais": "62","Puy-de-Dôme": "63","Pyrénées-Atlantiques": "64","Hautes-Pyrénées": "65",
    "Pyrénées-Orientales": "66","Bas-Rhin": "67","Haut-Rhin": "68","Rhône": "69","Haute-Saône": "70","Saône-et-Loire": "71",
    "Sarthe": "72","Savoie": "73","Haute-Savoie": "74","Paris": "75","Seine-Maritime": "76","Seine-et-Marne": "77",
    "Yvelines": "78","Deux-Sèvres": "79","Somme": "80","Tarn": "81","Tarn-et-Garonne": "82","Var": "83","Vaucluse": "84",
    "Vendée": "85","Vienne": "86","Haute-Vienne": "87","Vosges": "88","Yonne": "89","Territoire de Belfort": "90",
    "Essonne": "91","Hauts-de-Seine": "92","Seine-Saint-Denis": "93","Val-de-Marne": "94","Val-d'Oise": "95","Guadeloupe": "971",
    "Martinique": "972","Guyane": "973","La Réunion": "974","Mayotte": "976"}
    place=ox.geocode_to_gdf(f"{ville}, {pays}")
    department=place['display_name'][0].split(',')[2]
    return departements[department[1:]]

def get_numberOfHousePerStreet(place,departement):
    rues = {}
    with gzip.open(f"./media/adresses-{departement}.csv.gz", "rt") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if row[7] == place:
                if row[4] in rues:
                    rues[row[4]] += 1
                else:
                    rues[row[4]] = 1
    return rues

def get_letterPerStreetDivided(graph,paths,Streets):
    division=[]
    pdn="Pas de nom"
    print(Streets)
    f=0
    notVisited={street:True for street in Streets}
    notVisited[pdn]=True
    postman=[0 for _ in range(len(paths))]
    for path in paths:
        division.append([])
        visited={street:False for street in Streets}
        visited[pdn]=False
        for i in range(len(path)-1):
            x=graph.get_edge_data(path[i],path[i+1])
            for key in x:
                #print(x[key].keys())
            #affiche tous les segments de rue pour un certain nom
                if ('name' in x[key]):
                    
                    streetName=x[key]['name']
                    if streetName in Streets and not (visited[streetName]):
                        division[f].append((streetName,Streets[streetName]))
                        visited[streetName]=True
                        notVisited[streetName]=False
                else:
                    if not visited[pdn]:
                        division[f].append((pdn,1))
                        visited['Pas de nom']=True
                    postman[f]+=1
        print("Done for this one")
        f+=1
        
    letters=0
    sp=sum(postman)
    #On trouve le nombre de lettre des rues qui n'ont pas été marqué comme distribué
    for street in Streets.keys():
        if notVisited[street]:
            letters+=Streets[street]
    #On les répartis selon le nombre de segments sans nom croisé
    t=0
    for i in range(len(postman)):
        if postman[i]!=0:
            for l in range(len(division[i])):
                if division[i][l][0]==pdn:
                    print(division[i][l], round(letters*(postman[i]/sp)))
                    t+=round(letters*(postman[i]/sp))
                    division[i][l]=(pdn,round(letters*(postman[i]/sp)))
    print(t, letters)
    print(division)
    totaux = [sum([lettre for _, lettre in facteur]) for facteur in division]

    with open("media/charts", "w") as f:
        for i in range(len(division)):
            f.write(f"{i}\n")
            f.write(f"0|100\n")
            timecode = 0
            addlettres = 0
            for _, lettres in division[i]:
                if lettres > 50:
                    timediff = (6 / len(division[i]) * timecode) / 3
                    for _ in range(3):
                        addlettres += lettres / 3
                        f.write(f"{(6 / len(division[i]) * timecode)}|{((totaux[i] - addlettres) / totaux[i]) * 100}\n")
                        timecode += timediff / 3
                else:
                    addlettres += lettres
                    f.write(f"{(6 / len(division[i]) * timecode)}|{((totaux[i] - addlettres) / totaux[i]) * 100}\n")
                timecode += 1
            f.write("6|0\n")

    return division

def main(city, nf) :
    place = input("Enter the city name: ") if city == '' else city
    nombre_facteurs = int(input("Enter the number of postmen: ")) if nf == 0 else nf
    
    speed_dic={'motorway':130,'trunk':90, 'primary':80, 'secondary':50, 'tertiary': 50,'unclassified':50,'residential':30,'living_street':30,'service':10,'parking':20,'road':50}

    print("Creating graph...")

    G = createGraph(place, "France", speed_dic)
    weighted_edges = to_eularian(G)

    print("Graph created and converted to Eularian path.")

    correspondance, new_edges = create_correspondance_dict(weighted_edges)
    nodes = len(G.nodes)

    print("Writing file...")

    file_operations(nodes, new_edges)

    print("Executing cpp...")

    os.system("./chinese-postman-problem/chinese -f ./media/graph.txt")

    print("Reading result...")

    path = read_result(correspondance)

    departement = get_departement(place, "France")
    urlretrieve(f"https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{departement}.csv.gz", f"./media/adresses-{departement}.csv.gz")
    rues = get_numberOfHousePerStreet(place,departement)
    
    print("Dividing path...")
    paths=dividePath(G, path, nombre_facteurs)
    
    get_letterPerStreetDivided(G,paths,rues)
    
    print("Creating animation...")
    #multiplePathAnimation(G,paths)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process city name and number of postmen.')
    parser.add_argument('city', type=str, nargs='?', default='', help='The name of the city')
    parser.add_argument('postmen', type=int, nargs='?', default=0, help='The number of postmen')

    args = parser.parse_args()
    main(args.city, args.postmen)
