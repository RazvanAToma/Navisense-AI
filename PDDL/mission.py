"""
mission.py
Main entry point.

Pipeline:
  1. World model (from GUI / sensors)
  2. Gate identifier  — geometry, pairs buoys by proximity
  3. Problem generator — builds PDDL problem from gates
  4. Planner          — finds optimal action sequence
  5. Executor         — maps actions to node scripts and runs them
"""

import subprocess
from gate_identifier   import identify_gates
from problem_generator import generate_problem
from planner           import plan

# ── 1. NODE REGISTRY ───────────────────────────────────────────
# Maps planner action names → node scripts
# Action names must match what the planner outputs (lowercase, no params)
NODE_REGISTRY = {
    'search_for_green':     'PDDL/nodes/search_pattern.py',
    'move_to_green':        'PDDL/nodes/moving_to_point.py',
    'orbit_for_red':        'PDDL/nodes/orbit_target.py',
    'move_to_red_estimate': 'PDDL/nodes/moving_to_point.py',
    'identify_gate':         None,                        # internal, no script
    'align_to_gate':        'PDDL/nodes/moving_to_point.py',
    'pass_through_gate':    'PDDL/nodes/pass_through_gates.py',
}

# ── 2. WORLD MODEL ─────────────────────────────────────────────
# source: "estimated" = placed in GUI, approximate position
# source: "detected"  = confirmed by YOLO/LiDAR, reliable position
WORLD_MODEL = {
    'boat_position': {'x': 0,  'y': 0,  'source': 'detected'},
    'green_buoy_1':  {'x': 10, 'y': 20, 'source': 'detected'},
    'red_buoy_1':    {'x': 12, 'y': 24, 'source': 'estimated'},
    'green_buoy_2':  {'x': 20, 'y': 20, 'source': 'detected'},
    'red_buoy_2':    {'x': 22, 'y': 24, 'source': 'estimated'},
}

# ── 3. IDENTIFY GATES ──────────────────────────────────────────
print("\n── Step 1: Identifying gates from world model...")
gates = identify_gates(WORLD_MODEL)

if not gates:
    print("No valid gates found. Aborting mission.")
    exit(1)

print(f"  Found {len(gates)} gate(s)")

# ── 4. GENERATE PDDL PROBLEM ───────────────────────────────────
print("\n── Step 2: Generating PDDL problem...")
generate_problem(gates, output_path='PDDL/problem.pddl')

# ── 5. RUN PLANNER ─────────────────────────────────────────────
print("\n── Step 3: Planning...")
action_sequence = plan('PDDL/domain.pddl', 'PDDL/problem.pddl')

if not action_sequence:
    print("Planner found no solution. Aborting mission.")
    exit(1)

print(f"\n  Plan ({len(action_sequence)} steps):")
for step in action_sequence:
    print(f"    {step}")

# ── 6. EXECUTE ─────────────────────────────────────────────────
print("\n── Step 4: Executing...\n")

for step in action_sequence:
    # Extract base action name (strip parameters in parentheses)
    action_name = step.split('(')[0].strip()
    script      = NODE_REGISTRY.get(action_name)

    if script is None:
        print(f"   [skip] {step}  (internal action, no script)")
        continue

    print(f">> {step}")
    subprocess.run(['python', script], check=True)
    print(f"   done\n")

print("── Mission complete.")
