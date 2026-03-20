"""
identifier.py
Pairs green and red buoys by proximity (max 10m).
Also identifies speedgate components (gate + beacon + yellow buoy).
Returns a list of identified tasks in order of distance from boat.
"""

import math

MAX_GATE_DISTANCE = 10.0  # meters


def dist(a, b):
    return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)


def identify_tasks(world_model):
    """
    Returns a list of tasks identified from the world model.
    Each task: {
        'type':           'gate' | 'speedgate',
        'green':          {...},
        'red':            {...},
        'beacon':         {...} or None,
        'yellow':         {...} or None,
        'green_source':   'detected' | 'estimated',
        'red_source':     'detected' | 'estimated',
        'beacon_source':  'detected' | 'estimated' | None,
        'yellow_source':  'detected' | 'estimated' | None,
    }
    """
    greens  = {k: v for k, v in world_model.items() if 'green'  in k}
    reds    = {k: v for k, v in world_model.items() if 'red'    in k}
    beacons = {k: v for k, v in world_model.items() if 'beacon' in k}
    yellows = {k: v for k, v in world_model.items() if 'yellow' in k}

    boat    = world_model.get('boat_position', {'x': 0, 'y': 0})
    used_reds    = set()
    used_beacons = set()
    used_yellows = set()
    tasks = []

    sorted_greens = sorted(greens.items(), key=lambda kv: dist(kv[1], boat))

    for g_name, g_data in sorted_greens:
        # Find nearest red within 10m
        best_red  = None
        best_dist = float('inf')
        for r_name, r_data in reds.items():
            if r_name in used_reds:
                continue
            d = dist(g_data, r_data)
            if d < best_dist and d <= MAX_GATE_DISTANCE:
                best_dist = d
                best_red  = (r_name, r_data)

        if not best_red:
            print(f"  [identifier] WARNING: {g_name} has no red partner "
                  f"within {MAX_GATE_DISTANCE}m — skipping")
            continue

        r_name, r_data = best_red
        used_reds.add(r_name)

        # Gate center
        gate_center = {
            'x': (g_data['x'] + r_data['x']) / 2,
            'y': (g_data['y'] + r_data['y']) / 2,
        }

        # Check if there's a beacon + yellow nearby → speedgate
        nearest_beacon = None
        for b_name, b_data in beacons.items():
            if b_name in used_beacons:
                continue
            nearest_beacon = (b_name, b_data)
            break

        nearest_yellow = None
        for y_name, y_data in yellows.items():
            if y_name in used_yellows:
                continue
            nearest_yellow = (y_name, y_data)
            break

        if nearest_beacon and nearest_yellow:
            b_name, b_data = nearest_beacon
            y_name, y_data = nearest_yellow
            used_beacons.add(b_name)
            used_yellows.add(y_name)
            task_type = 'speedgate'
            print(f"  [identifier] Speedgate: {g_name}+{r_name} "
                  f"(gate sep {round(best_dist,2)}m) + {b_name} + {y_name}")
        else:
            b_data = None
            y_data = None
            task_type = 'gate'
            print(f"  [identifier] Gate: {g_name}+{r_name} "
                  f"(sep {round(best_dist,2)}m) "
                  f"[{g_data['source']}/{r_data['source']}]")

        tasks.append({
            'type':          task_type,
            'green':         g_data,
            'red':           r_data,
            'gate_center':   gate_center,
            'beacon':        b_data,
            'yellow':        y_data,
            'green_source':  g_data['source'],
            'red_source':    r_data['source'],
            'beacon_source': b_data['source'] if b_data else None,
            'yellow_source': y_data['source'] if y_data else None,
        })

    return tasks
