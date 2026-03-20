TASK_RULES = {
    "gate": {
        "rules": "gate = one green buoy + one red buoy, max 10m apart. Gates wider than 10m are invalid.",
        "required_types": ["green_buoy", "red_buoy"],
    },
    "towergate": {
        "rules": "towergate = one green tower + one red tower, max 15m apart. Towergates wider than 15m are invalid.",
        "required_types": ["green_tower", "red_tower"],
    },
    "speedgate": {
        "rules": "speedgate = gate (green+red buoy) + beacon (green or red) + yellow buoy. Use ONLY DriveSpeedgate — it handles everything atomically. Do NOT use PassThroughGate for speedgate. Beacon color determines direction: green_beacon = CCW around yellow buoy, red_beacon = CW around yellow buoy.",
        "required_types": ["green_buoy", "red_buoy", "yellow_buoy", "green_beacon", "red_beacon"],
    },
    "waterdelivery": {
        "rules": "waterdelivery = triangle.",
        "required_types": ["triangle"],
    },
}