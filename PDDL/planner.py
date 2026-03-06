"""
Lightweight STRIPS planner — no external dependencies.
Supports: :strips :typing :negative-preconditions
"""

from itertools import product
from collections import deque
import re


# ── PDDL PARSER ────────────────────────────────────────────────

def tokenize(text):
    text = re.sub(r';[^\n]*', '', text)       # strip comments
    text = text.replace('(', ' ( ').replace(')', ' ) ')
    return text.split()

def parse_sexp(tokens):
    if not tokens:
        return []
    token = tokens.pop(0)
    if token == '(':
        lst = []
        while tokens[0] != ')':
            lst.append(parse_sexp(tokens))
        tokens.pop(0)  # remove ')'
        return lst
    return token

def parse_file(path):
    with open(path) as f:
        text = f.read().lower()
    tokens = tokenize(text)
    results = []
    while tokens:
        results.append(parse_sexp(tokens))
    return results[0] if len(results) == 1 else results


# ── DOMAIN LOADER ──────────────────────────────────────────────

class Domain:
    def __init__(self, path):
        tree = parse_file(path)
        assert tree[0] == 'define'

        self.types   = {}   # type -> parent
        self.actions = []

        for section in tree[2:]:
            tag = section[0]
            if tag == ':types':
                self._parse_types(section[1:])
            elif tag == ':action':
                self.actions.append(self._parse_action(section))

    def _parse_types(self, tokens):
        i = 0
        pending = []
        while i < len(tokens):
            if tokens[i] == '-':
                parent = tokens[i+1]
                for t in pending:
                    self.types[t] = parent
                pending = []
                i += 2
            else:
                pending.append(tokens[i])
                i += 1
        for t in pending:
            self.types[t] = 'object'

    def _parse_action(self, tokens):
        action = {'name': tokens[1], 'params': [], 'pre': [], 'eff': []}
        i = 2
        while i < len(tokens):
            key = tokens[i]
            if key == ':parameters':
                action['params'] = self._parse_params(tokens[i+1])
                i += 2
            elif key == ':precondition':
                action['pre'] = tokens[i+1]
                i += 2
            elif key == ':effect':
                action['eff'] = tokens[i+1]
                i += 2
            else:
                i += 1
        return action

    def _parse_params(self, lst):
        params = []
        i = 0
        while i < len(lst):
            if lst[i] == '-':
                i += 2
            else:
                params.append(lst[i])
                i += 1
        return params


# ── PROBLEM LOADER ─────────────────────────────────────────────

class Problem:
    def __init__(self, path):
        tree = parse_file(path)
        assert tree[0] == 'define'

        self.objects = {}   # name -> type
        self.init    = set()
        self.goal    = []

        for section in tree[2:]:
            tag = section[0]
            if tag == ':objects':
                self._parse_objects(section[1:])
            elif tag == ':init':
                for fact in section[1:]:
                    self.init.add(self._fact(fact))
            elif tag == ':goal':
                self.goal = section[1]

    def _parse_objects(self, tokens):
        i = 0
        pending = []
        while i < len(tokens):
            if tokens[i] == '-':
                obj_type = tokens[i+1]
                for o in pending:
                    self.objects[o] = obj_type
                pending = []
                i += 2
            else:
                pending.append(tokens[i])
                i += 1

    def _fact(self, lst):
        return tuple(lst)


# ── STATE EVALUATION ───────────────────────────────────────────

def eval_condition(cond, state, binding):
    if not cond:
        return True
    if isinstance(cond, str):
        return True
    head = cond[0]

    if head == 'and':
        return all(eval_condition(c, state, binding) for c in cond[1:])
    if head == 'not':
        return not eval_condition(cond[1], state, binding)

    # ground the fact
    grounded = tuple(binding.get(t, t) for t in cond)
    return grounded in state

def apply_effect(eff, state, binding):
    state = set(state)
    if not eff:
        return state
    if isinstance(eff, str):
        return state
    head = eff[0]

    if head == 'and':
        for e in eff[1:]:
            state = apply_effect(e, state, binding)
        return state
    if head == 'not':
        grounded = tuple(binding.get(t, t) for t in eff[1])
        state.discard(grounded)
        return state

    grounded = tuple(binding.get(t, t) for t in eff)
    state.add(grounded)
    return state


# ── GROUNDING ─────────────────────────────────────────────────

def ground_actions(domain, problem):
    grounded = []
    for action in domain.actions:
        params = action['params']
        if not params:
            grounded.append((action['name'], {}, action['pre'], action['eff']))
            continue
        # get objects of matching type (simplified: use all objects)
        candidates = list(problem.objects.keys())
        for combo in product(candidates, repeat=len(params)):
            binding = dict(zip(params, combo))
            name = f"{action['name']}({','.join(combo)})"
            grounded.append((name, binding, action['pre'], action['eff']))
    return grounded


# ── BFS PLANNER ────────────────────────────────────────────────

def goal_reached(goal, state):
    if not goal:
        return True
    head = goal[0]
    if head == 'and':
        return all(goal_reached(g, state) for g in goal[1:])
    if head == 'not':
        grounded = tuple(goal[1])
        return grounded not in state
    return tuple(goal) in state

def plan(domain_path, problem_path):
    domain  = Domain(domain_path)
    problem = Problem(problem_path)

    grounded = ground_actions(domain, problem)
    init_state = frozenset(problem.init)

    queue   = deque([(init_state, [])])
    visited = {init_state}

    while queue:
        state, actions_taken = queue.popleft()

        if goal_reached(problem.goal, state):
            return actions_taken

        for (name, binding, pre, eff) in grounded:
            if eval_condition(pre, state, binding):
                new_state = frozenset(apply_effect(eff, state, binding))
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, actions_taken + [name]))

    return None  # no plan found


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python planner.py domain.pddl problem.pddl")
        sys.exit(1)
    result = plan(sys.argv[1], sys.argv[2])
    if result:
        print("Plan found:")
        for step in result:
            print(f"  {step}")
    else:
        print("No plan found.")
