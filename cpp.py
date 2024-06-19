import os
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def createGraph(ville, pays, speed_dic):
    lieu=ville+', '+pays
    M=ox.convert.to_undirected(ox.graph_from_place(lieu, network_type="drive", simplify=False))
    #On ajoute les longueurs des arêtes
    M=ox.distance.add_edge_lengths(M)
    #On ajoute les limitations de vitesses
    M=ox.routing.add_edge_speeds(M, speed_dic, 20)
    #Pour ensuite ajouter les temps de trajet.
    M=ox.routing.add_edge_travel_times(M)
    return M

def to_eularian(G) :
    # conversion en graphe eulérien
    weighted_edges = list(G.edges(keys=True, data=True))
    tmp=[]
    for i in range(len(weighted_edges)):
        tmp.append((weighted_edges[i][0],weighted_edges[i][1],weighted_edges[i][3]['travel_time']))
    weighted_edges = tmp
    
    G = nx.eulerize(G)
    return weighted_edges

def create_correspondance_dict(weighted_edges) :
    # dic de correpondance pour 0-based graph
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
    # Création du fichier d'edges
    f = open("./media/graph.txt", "w")
    f.write(str(nodes)+"\n"+str(len(new_edges))+"\n")
    for (u,v,w) in new_edges:
        f.write(str(u)+" "+str(v)+" "+str(w)+"\n")
    f.close()

def read_result(correspondance) :
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
        scatter_list, = [ax.scatter(xCoord,yCoord, s=20, marker='o', c='cyan', label=f'Facteur', alpha=.7)]
        
        return line, scatter_list

    listOfColors=['red','orange', 'yellow','green','blue','purple','brown','black']
    n=len(pathList)
    # A adapter et faire marcher
    nodes=list(graph.nodes)
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
    
    # Plot the first scatter plot (starting nodes = initial car locations = hospital locations)
    scatter_list, =[ax.scatter(xCoord,yCoord, s=20, marker='o', c='cyan', label=f'Facteur', alpha=0.7)]

    line, = ax.plot([], [], color='#2dffe0', linewidth=2, alpha=0.7)

    plt.legend(frameon=False)

    # Création de l'animation
    ani = FuncAnimation(fig, animate, init_func=initAnim, frames=max(len(lons[i]) for i in range(n)),  blit=True, interval=100)
    
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
    print(sums, sumPath)
    lens=[len(p) for p in paths]
    print(lens)
    multiplePathAnimation(graph,paths)

def main() :
    place = input("Enter the city name: ")
    nombre_facteurs = int(input("Enter the number of postmen: "))
    
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

    print("Dividing path...")
    dividePath(G, path, nombre_facteurs)

    """
    fig, ax = ox.plot_graph_route(G, path, route_color="y", route_linewidth=6, node_size=1, show=False, close=False)
    plt.show()

    route_nodes = path
    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route_nodes]
    point, = ax.plot([], [], 'ro', markersize=8)

    def init():
        point.set_data([], [])
        return point,

    def animate(i):
        point.set_data(route_coords[i][1], route_coords[i][0])
        return point,

    ani = FuncAnimation(fig, animate, frames=len(route_coords), init_func=init, interval=200, blit=True)

    print("Creating video...")

    ani.save("route_animation.mp4", dpi=500)
    """

if __name__ == "__main__":
    main()