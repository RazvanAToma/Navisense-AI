"""
problem_generator.py
Generates a PDDL problem file from identified tasks.
detected  → fact added to :init (planner uses it directly)
estimated → fact NOT added (planner must search/confirm first)
"""


def generate_problem(tasks, output_path='problem.pddl'):
    task_ids = [f"task{i+1}" for i in range(len(tasks))]

    objects_str = ' '.join(task_ids) + ' - task'

    init_facts = []
    goal_facts = []

    for i, task in enumerate(tasks):
        tid = task_ids[i]

        # Set task type flag
        if task['type'] == 'speedgate':
            init_facts.append(f'(is_speedgate {tid})')
        else:
            init_facts.append(f'(is_gate {tid})')

        # Add confirmed detections to init
        if task['green_source'] == 'detected':
            init_facts.append(f'(green_confirmed {tid})')
        if task['red_source'] == 'detected':
            init_facts.append(f'(red_confirmed {tid})')
        if task['beacon_source'] == 'detected':
            init_facts.append(f'(beacon_confirmed {tid})')
        if task['yellow_source'] == 'detected':
            init_facts.append(f'(yellow_confirmed {tid})')

        # Goal depends on task type
        if task['type'] == 'speedgate':
            goal_facts.append(f'(speedgate_done {tid})')
        else:
            goal_facts.append(f'(gate_passed {tid})')

    init_str = '\n    '.join(init_facts) if init_facts else '; nothing pre-confirmed'
    goal_str = '\n      '.join(goal_facts)

    problem = f"""(define (problem roboboat-mission)
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

    print(f"  [problem_gen] Written: {output_path}")
    for i, task in enumerate(tasks):
        print(f"  [problem_gen] task{i+1} = {task['type']} "
              f"(green:{task['green_source']} red:{task['red_source']})")

    return output_path
