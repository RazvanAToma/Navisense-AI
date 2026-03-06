"""
problem_generator.py
Generates a PDDL problem file from identified gates.
detected  → fact added to :init (planner can use it directly)
estimated → fact NOT added (planner must search/confirm first)
"""


def generate_problem(gates, output_path='PDDL/problem.pddl'):
    gate_ids = [f"gate{i+1}" for i in range(len(gates))]

    objects_str = ' '.join(gate_ids) + ' - gate'

    init_facts = []
    for i, gate in enumerate(gates):
        gid = gate_ids[i]

        if gate['green_source'] == 'detected':
            init_facts.append(f'(green_confirmed {gid})')

        if gate['red_source'] == 'detected':
            init_facts.append(f'(red_confirmed {gid})')

    init_str = '\n    '.join(init_facts) if init_facts else '; nothing confirmed yet'

    goal_facts = [f'(gate_passed {gid})' for gid in gate_ids]
    goal_str   = '\n      '.join(goal_facts)

    problem = f"""(define (problem roboboat-gates)
  (:domain maritime-autonomy)

  (:objects
    {objects_str}
  )

  (:init
    {init_str}
  )

  (:goal
    (and
      {goal_str}
    )
  )

)
"""
    with open(output_path, 'w') as f:
        f.write(problem)

    print(f"  [problem_generator] Written: {output_path}")
    print(f"  [problem_generator] Gates: {gate_ids}")
    print(f"  [problem_generator] Init facts: {init_facts if init_facts else 'none'}")

    return output_path
