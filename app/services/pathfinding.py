# app/services/pathfinding.py
import heapq
import math
from typing import List, Dict, Tuple, Optional, cast
from sqlalchemy.orm import Session
from app.models.waypoint import Waypoint, WaypointType
from app.models.connection import Connection
from app.models.room import Room
from app.models.floor import Floor

class PathNode:
    """Yo'l topish uchun node struktura"""
    def __init__(self, waypoint_id: str, floor_id: int, x: int, y: int, 
                 g_score: float, f_score: float, parent: Optional['PathNode'] = None):
        self.waypoint_id = waypoint_id
        self.floor_id = floor_id
        self.x = x
        self.y = y
        self.g_score = g_score  # Boshlanishdan bu node gacha masofa
        self.f_score = f_score  # g_score + heuristic (taxminiy masofa maqsadgacha)
        self.parent = parent
    
    def __lt__(self, other):
        return self.f_score < other.f_score
    
    def __eq__(self, other):
        return self.waypoint_id == other.waypoint_id

class PathFinder:
    """A* algoritmi bilan yo'l topish"""
    
    def __init__(self, db: Session):
        self.db = db
        self.graph: Optional[Dict[str, List[Tuple[str, float]]]] = None
        self.waypoints_dict: Dict[str, Waypoint] = {}
    
    def build_graph(self):
        """Grafni qurish - barcha waypoints va connections"""
        if self.graph is not None:
            return
        
        # Barcha waypoints va connections ni olish
        waypoints = self.db.query(Waypoint).all()
        connections = self.db.query(Connection).all()
        
        # Graph yaratish: {waypoint_id: [(neighbor_id, distance), ...]}
        self.graph = {cast(str, wp.id): [] for wp in waypoints}
        self.waypoints_dict = {cast(str, wp.id): wp for wp in waypoints}
        
        # Bog'lanishlarni qo'shish (ikki tomonlama)
        for conn in connections:
            from_id = cast(str, conn.from_waypoint_id)
            to_id = cast(str, conn.to_waypoint_id)
            if from_id not in self.graph or to_id not in self.graph:
                # Skip invalid links to avoid KeyError
                continue
            self.graph[from_id].append((to_id, float(conn.distance)))
            self.graph[to_id].append((from_id, float(conn.distance)))
        
        # Zinalar va liftlar uchun qavat o'tishlarini qo'shish
        for wp in waypoints:
            if wp.type in [WaypointType.STAIRS, WaypointType.ELEVATOR]:
                connects_to = cast(Optional[str], wp.connects_to_waypoint)
                if connects_to:
                    if connects_to not in self.graph:
                        continue
                    # Qavat o'tish - qo'shimcha vaqt/masofa
                    floor_change_cost = 50 if wp.type == WaypointType.STAIRS else 30
                    wp_id = cast(str, wp.id)
                    self.graph[wp_id].append((connects_to, floor_change_cost))
                    # Legacy linklarni ham ikki tomonlama deb hisoblaymiz
                    if connects_to in self.graph:
                        self.graph[connects_to].append((wp_id, floor_change_cost))
    
    def heuristic(self, wp1_id: str, wp2_id: str) -> float:
        """Heuristic funksiya - Euclidean distance + qavat o'zgarishi"""
        wp1 = self.waypoints_dict.get(wp1_id)
        wp2 = self.waypoints_dict.get(wp2_id)
        
        if wp1 is None or wp2 is None:
            return float('inf')
        
        # Bir xil qavatda bo'lsa - oddiy Euclidean distance
        wp1_floor = cast(int, wp1.floor_id)
        wp2_floor = cast(int, wp2.floor_id)
        wp1_x = cast(int, wp1.x)
        wp1_y = cast(int, wp1.y)
        wp2_x = cast(int, wp2.x)
        wp2_y = cast(int, wp2.y)

        if wp1_floor == wp2_floor:
            return math.sqrt((wp2_x - wp1_x)**2 + (wp2_y - wp1_y)**2)
        
        # Turli qavatlarda bo'lsa - taxminiy masofa + qavat o'zgarishi
        floor_diff = abs(wp2_floor - wp1_floor)
        base_distance = math.sqrt((wp2_x - wp1_x)**2 + (wp2_y - wp1_y)**2)
        return base_distance + (floor_diff * 100)  # Har bir qavat uchun 100 unit qo'shamiz
    
    def reconstruct_path(self, end_node: PathNode) -> List[Dict]:
        """Yo'lni qayta qurish"""
        path = []
        current = end_node
        
        while current is not None:
            wp = self.waypoints_dict[current.waypoint_id]
            path.append({
                'waypoint_id': current.waypoint_id,
                'floor_id': current.floor_id,
                'x': current.x,
                'y': current.y,
                'type': wp.type.value,
                'label': cast(Optional[str], wp.label)
            })
            current = current.parent
        
        path.reverse()
        return path
    
    def find_path(self, start_id: str, end_id: str) -> Tuple[List[Dict], float]:
        """
        A* algoritmi bilan yo'l topish
        Returns: (path, total_distance)
        """
        self.build_graph()
        
        if start_id not in self.graph or end_id not in self.graph:
            return [], float('inf')
        
        if start_id == end_id:
            start_wp = self.waypoints_dict[start_id]
            return [{
                'waypoint_id': start_id,
                'floor_id': cast(int, start_wp.floor_id),
                'x': cast(int, start_wp.x),
                'y': cast(int, start_wp.y),
                'type': start_wp.type.value,
                'label': cast(Optional[str], start_wp.label)
            }], 0.0
        
        # A* algoritmi
        start_wp = self.waypoints_dict[start_id]
        start_node = PathNode(
            start_id,
            cast(int, start_wp.floor_id),
            cast(int, start_wp.x),
            cast(int, start_wp.y),
            g_score=0,
            f_score=self.heuristic(start_id, end_id)
        )
        
        open_set = [start_node]  # Priority queue
        closed_set = set()
        g_scores = {start_id: 0}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if current.waypoint_id == end_id:
                path = self.reconstruct_path(current)
                return path, current.g_score
            
            if current.waypoint_id in closed_set:
                continue
            
            closed_set.add(current.waypoint_id)
            
            # Qo'shnilarni tekshirish
            for neighbor_id, distance in self.graph[current.waypoint_id]:
                if neighbor_id not in self.waypoints_dict:
                    continue
                if neighbor_id in closed_set:
                    continue
                
                tentative_g_score = current.g_score + distance
                
                if neighbor_id not in g_scores or tentative_g_score < g_scores[neighbor_id]:
                    g_scores[neighbor_id] = tentative_g_score
                    neighbor_wp = self.waypoints_dict[neighbor_id]
                    f_score = tentative_g_score + self.heuristic(neighbor_id, end_id)
                    
                    neighbor_node = PathNode(
                        neighbor_id,
                        cast(int, neighbor_wp.floor_id), 
                        cast(int, neighbor_wp.x),
                        cast(int, neighbor_wp.y),
                        g_score=tentative_g_score,
                        f_score=f_score,
                        parent=current
                    )
                    heapq.heappush(open_set, neighbor_node)
        
        return [], float('inf')  # Yo'l topilmadi
    
    def add_instructions(self, path: List[Dict]) -> List[Dict]:
        """Yo'lga yo'riqnomalar qo'shish"""
        if len(path) <= 1:
            return path
        
        for i, step in enumerate(path):
            if i == 0:
                step['instruction'] = "Boshlanish nuqtasi"
                continue
            if i == len(path) - 1:
                step['instruction'] = "Maqsadga yetdingiz"
                continue

            prev_step = path[i-1]
            next_step = path[i+1]

            # Qavat o'zgarishi: zinaga/liftga yetganda oldindan ko'rsatma berish
            if step['type'] in ['stairs', 'elevator'] and next_step['floor_id'] != step['floor_id']:
                direction = "yuqoriga" if next_step['floor_id'] > step['floor_id'] else "pastga"
                if step['type'] == 'stairs':
                    step['instruction'] = f"Zina orqali {direction} chiqing"
                else:
                    step['instruction'] = f"Liftda {direction} chiqing"
                continue

            # Yo'nalishni hisoblash
            angle1 = math.atan2(step['y'] - prev_step['y'], step['x'] - prev_step['x'])
            angle2 = math.atan2(next_step['y'] - step['y'], next_step['x'] - step['x'])
            angle_diff = math.degrees(angle2 - angle1) % 360

            if angle_diff < 45 or angle_diff > 315:
                instruction = "To'g'ri davom eting"
            elif 45 <= angle_diff < 135:
                instruction = "Chapga buriling"
            elif 225 < angle_diff <= 315:
                instruction = "O'ngga buriling"
            else:
                instruction = "Orqaga buriling"

            # Qavatlararo o'tishdan keyin koridorga chiqishni ko'rsatish
            if prev_step['type'] in ['stairs', 'elevator'] and i >= 2:
                prev_prev = path[i-2]
                if prev_prev['floor_id'] != prev_step['floor_id']:
                    if instruction == "To'g'ri davom eting":
                        instruction = "Kalidorga chiqib to'g'ri davom eting"
                    elif instruction == "O'ngga buriling":
                        instruction = "Kalidorga chiqib o'ngga buriling"
                    elif instruction == "Chapga buriling":
                        instruction = "Kalidorga chiqib chapga buriling"

            step['instruction'] = instruction
        
        # Ketma-ket takrorlangan "To'g'ri davom eting"larni qisqartirish
        last_instruction = None
        for step in path:
            instr = step.get('instruction')
            if instr == "To'g'ri davom eting" and instr == last_instruction:
                step['instruction'] = None
            elif instr:
                last_instruction = instr

        return path
    
    def find_nearest_waypoint_to_room(self, room_id: int) -> Optional[str]:
        """Xonaga eng yaqin waypoint topish"""
        room = self.db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return None
        
        # Agar xonaga waypoint biriktirilgan bo'lsa
        room_waypoint_id = cast(Optional[str], room.waypoint_id)
        if room_waypoint_id:
            return room_waypoint_id
        
        # Agar floor_id yo'q bo'lsa
        room_floor_id = cast(Optional[int], room.floor_id)
        if not room_floor_id:
            return None
        
        # Bir xil qavatdagi ROOM waypointlarni olish
        room_waypoints = self.db.query(Waypoint).filter(
            Waypoint.floor_id == room_floor_id,
            Waypoint.type == WaypointType.ROOM
        ).all()
        if not room_waypoints:
            return None

        # Label bo'yicha aniq moslik bo'lsa, shuni ishlatamiz
        room_label = (room.name or "").strip().lower()
        label_matches = [
            wp for wp in room_waypoints
            if (wp.label or "").strip().lower() == room_label
        ]
        candidates = label_matches if label_matches else room_waypoints

        # Xona koordinatasi yo'q bo'lgani uchun, floor markaziga eng yaqin waypointni olamiz
        floor = self.db.query(Floor).filter(Floor.id == room_floor_id).first()
        floor_width = cast(Optional[int], floor.image_width) if floor else None
        floor_height = cast(Optional[int], floor.image_height) if floor else None
        if floor and floor_width and floor_height:
            target_x = floor_width / 2
            target_y = floor_height / 2
        else:
            target_x = sum(cast(int, wp.x) for wp in candidates) / len(candidates)
            target_y = sum(cast(int, wp.y) for wp in candidates) / len(candidates)

        nearest = min(
            candidates,
            key=lambda wp: math.hypot(cast(int, wp.x) - target_x, cast(int, wp.y) - target_y)
        )
        return cast(str, nearest.id)
