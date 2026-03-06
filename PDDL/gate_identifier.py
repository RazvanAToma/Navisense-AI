"""
gate_identifier.py
Pairs green and red buoys by proximity.
Each buoy can only be used once.
Gates with separation > MAX_GATE_DISTANCE are invalid.
"""

import math

MAX_GATE_DISTANCE = 10.0  # meters (1 unit = 1 meter)


def identify_gates(world_model):
    """
    Takes the world model (dict of buoy_name -> {x, y, source}).
    Returns a list of gates in order of proximity to boat_position (or origin).
    Each gate: {id, green, red, distance, green_source, red_source}
    """
    greens = {k: v for k, v in world_model.items() if 'green' in k}
    reds   = {k: v for k, v in world_model.items() if 'red'   in k}

    used_reds = set()
    gates     = []

    # Sort greens by distance from boat so we tackle nearest gate first
    boat = world_model.get('boat_position', {'x': 0, 'y': 0})

    def dist(a, b):
        return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

    sorted_greens = sorted(greens.items(), key=lambda kv: dist(kv[1], boat))

    for g_name, g_data in sorted_greens:
        best_red  = None
        best_dist = float('inf')

        for r_name, r_data in reds.items():
            if r_name in used_reds:
                continue
            d = dist(g_data, r_data)
            if d < best_dist and d <= MAX_GATE_DISTANCE:
                best_dist = d
                best_red  = (r_name, r_data)

        if best_red:
            r_name, r_data = best_red
            used_reds.add(r_name)
            gates.append({
                'green':        g_data,
                'red':          r_data,
                'separation':   round(best_dist, 2),
                'green_source': g_data['source'],
                'red_source':   r_data['source'],
            })
            print(f"  [gate_identifier] Paired {g_name} + {r_name} "
                  f"(separation {round(best_dist,2)}m) "
                  f"[{g_data['source']} / {r_data['source']}]")
        else:
            print(f"  [gate_identifier] WARNING: {g_name} has no red partner "
                  f"within {MAX_GATE_DISTANCE}m — skipping")

    return gates
