import sys
import osmnx as ox
import pandas as pd
import networkx as nx
import math
import json
from random import randint

### Compute the distance between two nodes
def distance(p1, p2):
  return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def distance(p1, p2):
  return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def get_time_to_travel(src,dest,street_graph):    
    dist =  nx.shortest_path_length(street_graph, int(src), int(dest), weight='length')
    time_it_takes = int(dist / 10 )# Considering that the speed in the streets is approximately 36 km/h or 10 m/s
    return(time_it_takes)

def create_clusters_df(street_graph, computing_infra_csv_path):
    col_names = names=["id", "long", "lat"]
    df_computing_infra = pd.read_csv(computing_infra_csv_path,names = col_names)
    max = int(len(street_graph.nodes)/len(df_computing_infra))+1    
    streets_nearest_busstop_map = {}
    clusters = {}

    for i in range(len(df_computing_infra)):
        clusters[i] = []
        
    for node in street_graph:
        min_dist = 9999999.0
        current_best_cluster = 0
        coord_street = [ street_graph.nodes[node]['x'],street_graph.nodes[node]['y']]
        for i in df_computing_infra.index:
            coord_computing_node = [df_computing_infra['long'][i],df_computing_infra['lat'][i]]
            dist = distance(coord_street, coord_computing_node) 
            if dist < min_dist and len(clusters[i]) < max:
                min_dist = dist
                current_best_cluster = i
        clusters[current_best_cluster].append(node)
        streets_nearest_busstop_map[node] = f'bus_stop_{current_best_cluster}'        
    return (streets_nearest_busstop_map)

# Build the graph of streets
def build_street_graph(place): 
    area = ox.geocode_to_gdf(place)
    graph_streets = ox.graph_from_place(place, network_type='drive')
    return(graph_streets)

def build_computing_infra_df(place):
    graph_bus_stops = ox.geometries_from_place(place, tags={'highway':'bus_stop'})
    return 0
    
def generate_path(street_graph,offset,n_hops):
    path = []
    cont = 0
    best_dest = []
    for node in street_graph.nodes:
        if cont < offset:
            cont= cont+1
            continue
        candidatos_dist =  nx.descendants_at_distance(street_graph, node, n_hops)
        if (len(candidatos_dist))>1:
            cords_source = [ street_graph.nodes[node]['x'],street_graph.nodes[node]['y']]
            dest_offset = randint(1, len(candidatos_dist))
            count_dest = 1
            max_dist = -1
            for dest in candidatos_dist:  
                cords_dest = [ street_graph.nodes[dest]['x'],street_graph.nodes[dest]['y']]
                dist = distance(cords_source,cords_dest)
                if dist > max_dist:
                    max_dist = dist
                    best_dest = dest
                    path = nx.shortest_path(street_graph, source=node, target=best_dest)
            break        
    return(path)

def create_parent_graph(graph,src, dest,time,parent_graph,street):
    if dest == src:
        return
    if time < 0 : 
        return
    if street not in parent_graph:
        parent_graph[street] = []
    key = int(src)
    edges =  graph.in_edges(key)
    for edge in edges:
        adj_node = f'{edge[0]}'
        visit_time = time - get_time_to_travel(adj_node,src,graph) 
        if visit_time >=0 :
            depedent_street = f'{adj_node}_{src}_{visit_time}_{time}'
            if  depedent_street not in parent_graph[street]:
                parent_graph[street].append(depedent_street)
                create_parent_graph(graph,adj_node, src,visit_time,parent_graph, depedent_street)



def build_parent_graph(graph,path):    
    parent_graph = {}
    visited = {}
    current_time = 0
    # First we init the dependencies with the nodes in the path
    for i in range(1, len(path)):
        src  =path[i-1]
        dest = path[i]
        time_to_travel =  get_time_to_travel(src,dest,graph)
        parent_graph[f'{path[i-1]}_{path[i]}_{current_time}_{current_time+time_to_travel}']=[]
        current_time+=time_to_travel
    current_time = 0
    time_to_travel =  get_time_to_travel(path[0],path[1],graph)

    for i in range(2,len(path)):
        current_time +=time_to_travel
        dest = f'{path[i]}'
        src = f'{path[i-1]}'
        previous =  f'{path[i-2]}'
        time_to_travel_previous = get_time_to_travel(previous,src,graph) 
        time_to_travel = get_time_to_travel(src,dest,graph)
        street =f'{src}_{dest}_{current_time}_{time_to_travel+current_time}'
        parent_graph[f'{src}_{dest}_{current_time}_{time_to_travel+current_time}'].append(f'{previous}_{src}_{current_time-time_to_travel_previous}_{current_time}')
        create_parent_graph(graph,src, dest,current_time,parent_graph,street)

    return (parent_graph)
    


def print_parent_graph(graph):
    for node in graph:
        print(node)
    for son in graph:
        for parent in graph[parent]:
            print(parent,son)


def print_path(path,graph):
    for node in path:
        print(graph.in_edges(node))
        print(graph.out_edges(node))

def build_networkx_from_dag(dag):
    digraph = nx.DiGraph()
    for son in dag:
        for parent in dag[node]:
            digraph.add_edge(parent,son)
    return(digraph)

def generate_workload(place,index,amount_requests,n_hops,path_computing_infra,output_path):
    req_generated = 0
    while (req_generated < amount_requests):
        try:
            street_graph = build_street_graph(place)    
            offset = randint(0, len(street_graph.nodes))
            path_ex =  generate_path(street_graph,offset,n_hops)
            print('Route: ',path_ex)
            dag = build_parent_graph(street_graph,path_ex)    
            if len(dag) == 0: continue
            dict_busstops = create_clusters_df(street_graph,path_computing_infra)
            digraph = nx.DiGraph()
            for son in dag:
                for parent in dag[son]:
                    digraph.add_edge(parent,son)
            topological_sorted_dag = list(nx.topological_sort(digraph))
            tasks_list = []
            req_name = f"req-{index}"
            for node in topological_sorted_dag:
                key = int(node.split('_')[0])
                parents_formated = []
                for parent in dag[node]:
                    parents_formated.append(f'{req_name}-{parent}')
                item = {
                    "name" : f"{req_name}-{node}",
                    "flopsAmount": 13.5e8,
                    "machine" : f'{dict_busstops[key]}',
                    "parents" : parents_formated
                }
                tasks_list.append(item)
                
            # Data to be written
            dictionary = {
                "name": req_name,
                "schemaVersion": "1.0",
                "tasks": tasks_list,
                "path": path_ex
            }     
            # Serializing json
            json_object = json.dumps(dictionary, indent=4)
             
            # Writing to sample.json
            with open(f"{output_path}/req_{index}.json", "w") as outfile:
                outfile.write(json_object)
            index+=1
            req_generated+=1
            print('request',index)
        except Exception as e: 
            print(e)
            generate_workload(place,index,amount_requests-req_generated,n_hops,path_computing_infra,output_path)
            break
        


place = sys.argv[1]
index = int(sys.argv[2])
amount_requests =  int( sys.argv[3])
n_hops =  int( sys.argv[4])
path_computing_infra =  sys.argv[5]
output_path =  sys.argv[6]





generate_workload(place,index,amount_requests,n_hops,path_computing_infra,output_path)
