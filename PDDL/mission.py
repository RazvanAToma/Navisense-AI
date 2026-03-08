"""
mission.py  —  NaviSense PDDL Mission Runner
============================================
Pipeline:
  1. WORLD_MODEL   — set by GUI / sensors
  2. identifier    — geometry: pairs buoys, identifies gate vs speedgate
  3. problem_gen   — builds PDDL problem from identified tasks
  4. planner       — finds optimal action sequence (pure Python BFS)
  5. executor      — maps actions → node scripts → runs them in order

To add a new task type:
  - Add new actions to domain.pddl
  - Add new identifier logic in identifier.py
  - Add new node scripts in nodes/
  - Register them in ACTION_TO_NODE below
"""

import subprocess
from identifier        import identify_tasks
from problem_generator import generate_problem
from planner           import plan

# ══════════════════════════════════════════════════════════════
# ACTION → NODE MAPPING
# Maps planner action names (from domain.pddl) to node scripts.
# None = internal planner action, no script needed.
# ══════════════════════════════════════════════════════════════
ACTION_TO_NODE = {
    'search_for_green':  'PDDL/nodes/search_pattern.py',
    'search_for_red':    'PDDL/nodes/search_pattern.py',
    'search_for_beacon': 'PDDL/nodes/search_pattern.py',
    'search_for_yellow': 'PDDL/nodes/search_pattern.py',
    'identify_gate':     None,
    'align_to_gate':     'PDDL/nodes/moving_to_point.py',
    'pass_through_gate': 'PDDL/nodes/pass_through_gates.py',
    'enter_speedgate':   'PDDL/nodes/pass_through_gates.py',
    'run_speedgate':     'PDDL/nodes/drive_speedgate.py',
}

# ══════════════════════════════════════════════════════════════
# WORLD MODEL
# source: "estimated" = placed in GUI, approximate position
# source: "detected"  = confirmed by YOLO/LiDAR, reliable
# ══════════════════════════════════════════════════════════════
WORLD_MODEL = {
    'boat_position':  {'x': 0,  'y': 0,  'source': 'detected'},

    'green_buoy_1':   {'x': 10, 'y': 20, 'source': 'estimated'},
    'red_buoy_1':     {'x': 10, 'y': 24, 'source': 'estimated'},

    'green_buoy_2':   {'x': 20, 'y': 20, 'source': 'estimated'},
    'red_buoy_2':     {'x': 20, 'y': 24, 'source': 'estimated'},
    'beacon_1':       {'x': 25, 'y': 22, 'source': 'estimated'},
    'yellow_buoy_1':  {'x': 35, 'y': 22, 'source': 'estimated'},
}

# ══════════════════════════════════════════════════════════════
# STEP 1 — IDENTIFY TASKS
# ══════════════════════════════════════════════════════════════
print("\n── Step 1: Identifying tasks from world model...")
tasks = identify_tasks(WORLD_MODEL)

if not tasks:
    print("No valid tasks identified. Aborting.")
    exit(1)

print(f"  Identified {len(tasks)} task(s):")
for i, t in enumerate(tasks):
    print(f"    task{i+1}: {t['type']}")

# ══════════════════════════════════════════════════════════════
# STEP 2 — GENERATE PDDL PROBLEM
# ══════════════════════════════════════════════════════════════
print("\n── Step 2: Generating PDDL problem...")
generate_problem(tasks, output_path='PDDL/problem.pddl')

# ══════════════════════════════════════════════════════════════
# STEP 3 — PLAN
# ══════════════════════════════════════════════════════════════
print("\n── Step 3: Planning...")
sequence = plan('PDDL/domain.pddl', 'PDDL/problem.pddl')

if not sequence:
    print("Planner found no solution. Aborting.")
    exit(1)

print(f"\n  Plan ({len(sequence)} steps):")
for step in sequence:
    print(f"    {step}")

# ══════════════════════════════════════════════════════════════
# STEP 4 — EXECUTE
# ══════════════════════════════════════════════════════════════
print("\n── Step 4: Executing...\n")

# Build a target lookup so nodes know where to go
# Maps task index → relevant positions
task_targets = {}
for i, task in enumerate(tasks):
    task_targets[f'task{i+1}'] = {
        'gate_center':  task['gate_center'],
        'green':        task['green'],
        'red':          task['red'],
        'beacon':       task.get('beacon'),
        'yellow':       task.get('yellow'),
    }

for step in sequence:
    action_name = step.split('(')[0].strip()
    script      = ACTION_TO_NODE.get(action_name)

    # Extract which task this step is for
    task_id = step.split('(')[1].rstrip(')') if '(' in step else None
    target  = task_targets.get(task_id, {})

    if script is None:
        print(f"   [skip] {step}")
        continue

    # Print target info for this step
    if action_name in ('search_for_green',):
        pos = target.get('green', {})
        print(f">> {step}")
        print(f"   Target: search around x={pos.get('x')}, y={pos.get('y')}")
    elif action_name in ('search_for_red',):
        pos = target.get('red', {})
        print(f">> {step}")
        print(f"   Target: search around x={pos.get('x')}, y={pos.get('y')}")
    elif action_name in ('search_for_beacon',):
        pos = target.get('beacon', {})
        print(f">> {step}")
        print(f"   Target: search around x={pos.get('x')}, y={pos.get('y')}")
    elif action_name in ('search_for_yellow',):
        pos = target.get('yellow', {})
        print(f">> {step}")
        print(f"   Target: search around x={pos.get('x')}, y={pos.get('y')}")
    elif action_name in ('align_to_gate', 'pass_through_gate', 'enter_speedgate'):
        pos = target.get('gate_center', {})
        print(f">> {step}")
        print(f"   Target: gate center x={pos.get('x')}, y={pos.get('y')}")
    elif action_name == 'run_speedgate':
        gc = target.get('gate_center', {})
        bc = target.get('beacon',      {})
        yc = target.get('yellow',      {})
        print(f">> {step}")
        print(f"   Gate:   x={gc.get('x')}, y={gc.get('y')}")
        print(f"   Beacon: x={bc.get('x')}, y={bc.get('y')}")
        print(f"   Yellow: x={yc.get('x')}, y={yc.get('y')}")
    else:
        print(f">> {step}")

    subprocess.run(['python', script], check=True)
    print(f"   done\n")

print("── Mission complete.")