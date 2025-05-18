import osmnx as ox
import networkx as nx
import numpy as np
from geopy.distance import geodesic
from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session
from models.truck import Truck
from models.container import Container
from models.truck_route import TruckRoute
from models.route_stop import RouteStop
from schemas.route import TruckRouteCreate, RouteStopCreate
import crud.truck as truck_crud
import crud.container as container_crud
import crud.truck_route as route_crud
from datetime import datetime

class RoutePlanningService:
    def __init__(self):
        # Cache for network graphs to avoid repeated downloads
        self._graph_cache = {}
        
    def _get_road_network(self, center_lat: float, center_lng: float, radius: int = 5000):
        """Get or create a cached road network for the area"""
        cache_key = f"{center_lat:.4f}_{center_lng:.4f}_{radius}"
        if cache_key not in self._graph_cache:
            self._graph_cache[cache_key] = ox.graph_from_point(
                (center_lat, center_lng), 
                dist=radius, 
                network_type='drive'
            )
        return self._graph_cache[cache_key]
    
    def _calculate_route_metrics(self, truck: Truck, ordered_stops: List[Container]) -> Dict[str, Any]:
        """Calculate estimated distance, duration, and emissions for a route"""
        total_distance = 0
        coords = [(truck.location_lat, truck.location_lng)]
        
        # Add all container coordinates
        for container in ordered_stops:
            coords.append((container.location_lat, container.location_lng))
        
        # Calculate distances between consecutive points
        for i in range(len(coords) - 1):
            distance = geodesic(coords[i], coords[i+1]).kilometers
            total_distance += distance
        
        # Calculate metrics
        estimated_duration = total_distance / (truck.average_speed or 40)  # Default speed 40 km/h
        estimated_emissions = total_distance * (truck.emission_per_km or 0.8)  # Default emissions
        estimated_cost = total_distance * (truck.cost_per_km or 1.5)  # Default cost
        
        return {
            "distance_km": round(total_distance, 2),
            "duration_hours": round(estimated_duration, 2),
            "emissions_kg": round(estimated_emissions, 2),
            "cost": round(estimated_cost, 2)
        }
    
    def _optimize_route(self, 
                        truck: Truck, 
                        containers: List[Container], 
                        optimization_method: str = "distance") -> List[Container]:
        """Optimize container visit order based on the selected method"""
        start_point = (truck.location_lat, truck.location_lng)
        
        if optimization_method == "nearest_neighbor":
            # Simple nearest neighbor algorithm
            remaining = containers.copy()
            ordered = []
            current = start_point
            
            while remaining:
                # Find nearest container to current position
                distances = [(i, geodesic(current, (c.location_lat, c.location_lng)).kilometers) 
                           for i, c in enumerate(remaining)]
                nearest_idx, _ = min(distances, key=lambda x: x[1])
                
                # Add to ordered list
                nearest = remaining.pop(nearest_idx)
                ordered.append(nearest)
                current = (nearest.location_lat, nearest.location_lng)
                
            return ordered
        
        elif optimization_method == "capacity_optimized":
            # Prioritize containers based on fill level
            return sorted(containers, key=lambda x: x.current_fill, reverse=True)
        
        else:  # default to distance optimization
            # Use nearest neighbor
            return self._optimize_route(truck, containers, "nearest_neighbor")
    
    def create_optimized_route(self, 
                              db: Session,
                              truck_id: int,
                              container_ids: List[int],
                              optimization_method: str = "distance") -> TruckRoute:
        """Create an optimized route for a truck to visit containers"""
        # Get truck and containers
        truck = truck_crud.get_truck(db, truck_id)
        containers = [container_crud.get_container(db, container_id) 
                     for container_id in container_ids if container_crud.get_container(db, container_id)]
        
        # Optimize route
        ordered_containers = self._optimize_route(truck, containers, optimization_method)
        
        # Calculate route metrics
        metrics = self._calculate_route_metrics(truck, ordered_containers)
        
        # Create route record
        route_data = TruckRouteCreate(
            truck_id=truck_id,
            start_time=datetime.utcnow(),
            status="planned",
            total_distance_km=metrics["distance_km"],    # Changed from estimated_distance
            total_emissions=metrics["emissions_kg"],     # Changed from estimated_emissions 
            total_cost=metrics["cost"],                  # Changed from estimated_cost
            # Remove estimated_duration and scheduled_start as they don't exist in the model
        )
        
        # Create route stops
        stops = []
        for i, container in enumerate(ordered_containers):
            stop = RouteStopCreate(
                container_id=container.id,
                stop_number=i + 1,
                status="pending",
                estimated_fill_level=container.current_fill
            )
            stops.append(stop)
        
        # Create route with stops
        return route_crud.create_route(db, route_data, stops)
    
    def get_route_details(self, db: Session, route_id: int) -> Dict[str, Any]:
        """Get detailed information about a route including all stops"""
        route = route_crud.get_route_by_id(db, route_id)
        if not route:
            return None
            
        stops = route_crud.get_stops_by_route(db, route_id)
        truck = truck_crud.get_truck(db, route.truck_id)
        
        # Format detailed response
        stop_details = []
        for stop in stops:
            container = container_crud.get_container(db, stop.container_id)
            stop_details.append({
                "stop_id": stop.id,
                "stop_number": stop.stop_number,
                "status": stop.status,
                "container_id": container.id,
                "container_type": container.container_type,
                "location": {
                    "lat": container.location_lat,
                    "lng": container.location_lng,
                    "address": container.address
                },
                "estimated_fill_level": stop.estimated_fill_level
            })
        
        return {
            "route_id": route.id,
            "status": route.status,
            "truck": {
                "id": truck.id,
                "name": truck.name,
                "capacity_white": truck.capacity_white,
                "capacity_green": truck.capacity_green,
                "capacity_brown": truck.capacity_brown
            },
            "metrics": {
                "total_distance_km": route.total_distance_km,
                "total_emissions": route.total_emissions,
                "total_cost": route.total_cost,
                # Optionally add these as None if you want to keep the keys for compatibility
                "estimated_duration": None,
                "actual_distance": None,
                "actual_duration": None
            },
            "schedule": {
                "start_time": route.start_time,
                "end_time": route.end_time,
                # Optionally add these as None if you want to keep the keys for compatibility
                "scheduled_start": None,
                "actual_start": None,
                "actual_end": None
            },
            "stops": stop_details
        }

    def calculate_priority(container):
        # Fixed calculation
        return container.current_fill / container.capacity

route_planning_service = RoutePlanningService()