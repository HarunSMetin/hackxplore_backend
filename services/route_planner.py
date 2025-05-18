import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from sqlalchemy.orm import Session
import os
import ast

from models.truck import Truck
from models.container import Container
from models.truck_route import TruckRoute
from models.route_stop import RouteStop

class TruckObj:
    def __init__(self, truck_id, depot_lat, depot_lon, capacity_white, capacity_green, capacity_brown,
                cost_per_km=1.8, emission_per_km=1.0, average_speed=23.0):
        self.truck_id = truck_id
        self.capacity_m3_weiß = capacity_white
        self.capacity_m3_grün = capacity_green
        self.capacity_m3_braun = capacity_brown
        self.cost_per_km = cost_per_km
        self.emission_per_km = emission_per_km
        self.average_speed = average_speed
        self.depot_lat = depot_lat
        self.depot_lon = depot_lon

def get_distance_matrix(containers):
    """Create a distance matrix using Euclidean distances"""
    n = len(containers)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
            else:
                # Calculate Euclidean distance in meters (approximate)
                lat1, lng1 = containers[i].location_lat, containers[i].location_lng
                lat2, lng2 = containers[j].location_lat, containers[j].location_lng
                
                # Simple distance calculation in meters
                distance = (((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5) * 111000
                matrix[i][j] = distance
    
    return matrix

def plan_routes_with_rewards(db: Session, date: datetime, 
                             num_trucks: int = 1, 
                             reward_per_m3: float = 100.0):
    """Plan routes for trucks based on container fill levels"""
    
    # Get all trucks
    trucks_db = db.query(Truck).limit(num_trucks).all()
    if not trucks_db:
        return {"error": "No trucks available"}
    
    # Get all containers
    containers = db.query(Container).all()
    if not containers:
        return {"error": "No containers found"}
    
    # Initialize truck objects
    trucks = []
    for t in trucks_db:
        trucks.append(TruckObj(
            truck_id=t.id,
            depot_lat=t.location_lat,
            depot_lon=t.location_lng,
            capacity_white=t.capacity_white,
            capacity_green=t.capacity_green,
            capacity_brown=t.capacity_brown,
            cost_per_km=t.cost_per_km,
            emission_per_km=t.emission_per_km,
            average_speed=t.average_speed
        ))
    
    # Calculate distance matrix
    distance_matrix = get_distance_matrix(containers)
    
    # Prepare container data
    container_states = []
    for container in containers:
        # Here we would normally get fill levels from sensor readings
        # For simplicity, we'll use current_fill as a percentage of capacity
        fill_level_percent = (container.current_fill / container.capacity) * 100
        fill_volume_m3 = container.capacity * (fill_level_percent / 100) / 1000  # Convert to m3
        
        container_states.append({
            'Container_Id': container.id,
            'Latitude': container.location_lat,
            'Longitude': container.location_lng,
            'Fill_Level': fill_level_percent,
            'Container_Size_m3': container.capacity / 1000,  # Convert to m3
            'Fill_Volume_m3': fill_volume_m3,
            'Container_Type': container.type.lower()  # Assuming type is "white", "green", or "brown"
        })
    
    # Plan routes
    start_time = date.replace(hour=8, minute=0)  # Start at 8 AM
    
    # Map container IDs to matrix indices
    container_idx_map = {container.id: idx for idx, container in enumerate(containers)}
    
    # Assume first container is depot
    depot_idx = 0
    
    # Build demands per node
    demands = [{} for _ in range(len(containers))]
    for state in container_states:
        container_id = state['Container_Id']
        idx = container_idx_map[container_id]
        typ = state['Container_Type'].lower()
        if typ not in demands[idx]:
            demands[idx][typ] = 0
        demands[idx][typ] += state.get('Fill_Volume_m3', 0)
    
    # Set up tracking
    unvisited = set(i for i in range(1, len(containers)) if sum(demands[i].values()) > 0)
    routes = {truck.truck_id: [(depot_idx, start_time)] for truck in trucks}
    truck_loads = {truck.truck_id: {'white': 0.0, 'green': 0.0, 'brown':0.0} for truck in trucks}
    truck_capacities = {
        truck.truck_id: {
            'white': truck.capacity_m3_weiß,
            'green': truck.capacity_m3_grün,
            'brown': truck.capacity_m3_braun
        } for truck in trucks
    }
    cost_per_meter = trucks[0].cost_per_km / 1000  # €/m
    
    # While containers left to visit
    while unvisited:
        progress = False
        for truck in trucks:
            current_route = routes[truck.truck_id]
            current_node, current_time = current_route[-1]
            
            # Find feasible nodes this truck can pick up
            feasible_nodes = []
            for node in unvisited:
                node_demand = demands[node]
                feasible = True
                for typ in node_demand:
                    if truck_loads[truck.truck_id][typ] + node_demand[typ] > truck_capacities[truck.truck_id][typ]:
                        feasible = False
                        break
                if feasible:
                    feasible_nodes.append(node)
            
            if not feasible_nodes:
                # Return to depot if not there
                if current_node != depot_idx:
                    dist_back = distance_matrix[current_node][depot_idx]
                    travel_time_back = timedelta(seconds=(dist_back / (truck.average_speed * 1000 / 3600)))
                    arrival_time = current_time + travel_time_back
                    routes[truck.truck_id].append((depot_idx, arrival_time))
                continue
                
            # Score nodes by profit (reward - cost)
            scores = []
            for node in feasible_nodes:
                node_demand = demands[node]
                reward = sum(node_demand[t] * reward_per_m3 for t in node_demand)
                dist = distance_matrix[current_node][node]
                travel_cost = dist * cost_per_meter
                net_gain = reward - travel_cost
                scores.append((net_gain, node))
            scores.sort(reverse=True)
            best_score, best_node = scores[0]  # greedy
            
            # Travel to this node and collect load
            dist_travel = distance_matrix[current_node][best_node]
            travel_time = timedelta(seconds=(dist_travel / (truck.average_speed * 1000 / 3600)))
            service_time = timedelta(minutes=5)
            
            arrival_time = current_time + travel_time
            departure_time = arrival_time + service_time
            
            routes[truck.truck_id].append((best_node, departure_time))
            
            # Update truck loads
            node_demand = demands[best_node]
            for typ in node_demand:
                truck_loads[truck.truck_id][typ] += node_demand[typ]
            
            # Remove node from unvisited
            unvisited.remove(best_node)
            
            # Update time
            routes[truck.truck_id][-1] = (best_node, departure_time)
            
            progress = True
        
        if not progress:
            break
    
    # Return to depot
    for truck in trucks:
        current_route = routes[truck.truck_id]
        last_node, last_time = current_route[-1]
        if last_node != depot_idx:
            dist_back = distance_matrix[last_node][depot_idx]
            travel_time_back = timedelta(seconds=(dist_back / (truck.average_speed * 1000 / 3600)))
            arrival_time = last_time + travel_time_back
            current_route.append((depot_idx, arrival_time))
    
    # Convert results to DB models
    result_routes = []
    for truck_id, route_data in routes.items():
        truck_db = next((t for t in trucks_db if t.id == truck_id), None)
        if not truck_db:
            continue
            
        # Calculate total distance
        total_dist = 0
        for i in range(1, len(route_data)):
            prev_node, _ = route_data[i-1]
            curr_node, _ = route_data[i]
            total_dist += distance_matrix[prev_node][curr_node]
        
        total_dist_km = total_dist / 1000
        total_cost = total_dist_km * truck_db.cost_per_km
        total_emissions = total_dist_km * truck_db.emission_per_km
        
        # Create route in DB
        db_route = TruckRoute(
            truck_id=truck_id,
            start_time=route_data[0][1],
            end_time=route_data[-1][1],
            total_distance_km=total_dist_km,
            total_cost=total_cost,
            total_emissions=total_emissions,
            status="planned"
        )
        db.add(db_route)
        db.flush()  # Get ID for stops
        
        # Add stops
        for stop_num, (node_idx, time) in enumerate(route_data):
            container_id = containers[node_idx].id
            
            # Calculate collected volumes
            collected_white = 0.0
            collected_green = 0.0
            collected_brown = 0.0
            
            if node_idx != depot_idx and node_idx < len(containers):
                container = containers[node_idx]
                container_type = container.type.lower()
                
                # Calculate fill volume
                fill_level_percent = (container.current_fill / container.capacity) * 100
                fill_volume_m3 = container.capacity * (fill_level_percent / 100) / 1000  # Convert to m3
                
                if container_type == "white":
                    collected_white = fill_volume_m3
                elif container_type == "green":
                    collected_green = fill_volume_m3
                elif container_type == "brown":
                    collected_brown = fill_volume_m3
            
            db_stop = RouteStop(
                route_id=db_route.id,
                container_id=container_id,
                stop_number=stop_num,
                planned_arrival_time=time,
                collected_white_glass_m3=collected_white,
                collected_green_glass_m3=collected_green,
                collected_brown_glass_m3=collected_brown
            )
            db.add(db_stop)
        
        result_routes.append(db_route)
    
    db.commit()
    return result_routes