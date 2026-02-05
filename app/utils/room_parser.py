
import re
from typing import Optional, Dict

def parse_room_name(room_name: str) -> Dict[str, Optional[str]]:
    """
    Xona nomini parse qilish
    Format: {qavat}{xona}-{blok}
    Misol: "106-B blok" → {floor: "1", room: "06", building: "B"}
    """
    # Accept:
    # - Any floor number length (>=1) + 2-digit room number => total digits >= 3
    # - Block letter case-insensitive
    # Examples:
    # - "106-B blok" => floor 1, room 06
    # - "1006-b blok" => floor 10, room 06
    pattern = r'^\s*(\d{3,})\s*-\s*([A-Za-z])\s*(?:blok|block)\s*$'
    match = re.match(pattern, room_name.strip(), flags=re.IGNORECASE)
    
    if match:
        full_number = match.group(1)
        floor_num = full_number[:-2]
        room_num = full_number[-2:]
        building = match.group(2).upper()
        
        return {
            'floor_number': int(floor_num) if floor_num.isdigit() else None,
            'room_number': room_num,
            'building': building,
            'floor_name': f"{floor_num}-qavat",
            'full_room': f"{floor_num}{room_num}",
        }
    
    return {
        'floor_number': None,
        'room_number': None,
        'building': None,
        'floor_name': None,
        'full_room': None,
    }

def format_room_name(floor_number: int, room_number: str, building: str) -> str:
    """
    Xona nomini format qilish
    Misol: (1, "06", "B") → "106-B blok"
    """
    return f"{floor_number}{room_number}-{building.upper()} blok"
