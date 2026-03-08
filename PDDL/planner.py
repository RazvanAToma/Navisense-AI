"""
planner.py
Lightweight STRIPS planner — pure Python, no external dependencies.
Supports: :strips :typing :negative-preconditions
"""

from itertools import product
from collections import deque
import re


# ── PARSER ─────────────────────────────────────────────────────

def tokenize(text):
    text = re.sub(r';[^\n]*', '', text)
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
        tokens.pop(0)
        return lst
    return token

def parse_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read().lower()
    tokens = tokenize(text)
    results = []
    while tokens:
        results.append(parse_sexp(tokens))
    return results[0] if len(results) == 1 else results


# ── DOMAIN ─────────────────────────────────────────────────────

class Domain:
    def __init__(self, path):
        tree    = parse_file(path)
        self.actions = []
        for section in tree[2:]:
            if section[0] == ':action':
                self.actions.append(self._parse_action(section))

    def _parse_action(self, tokens):
        action = {'name': tokens[1], 'params': [], 'pre': [], 'eff': []}
        i = 2
        while i < len(tokens):
            key = tokens[i]
            if   key == ':parameters':  action['params'] = self._parse_params(tokens[i+1]); i += 2
            elif key == ':precondition': action['pre']    = tokens[i+1]; i += 2
            elif key == ':effect':       action['eff']    = tokens[i+1]; i += 2
            else: i += 1
        return action

    def _parse_params(self, lst):
        return [lst[i] for i in range(len(lst)) if lst[i] != '-' and (i == 0 or lst[i-1] != '-')]


# ── PROBLEM ────────────────────────────────────────────────────

class Problem:
    def __init__(self, path):
        tree         = parse_file(path)
        self.objects = {}
        self.init    = set()
        self.goal    = []
        for section in tree[2:]:
            tag = section[0]
            if tag == ':objects':
                self._parse_objects(section[1:])
            elif tag == ':init':
                for fact in section[1:]:
                    self.init.add(tuple(fact))
            elif tag == ':goal':
                self.goal = section[1]

    def _parse_objects(self, tokens):
        i, pending = 0, []
        while i < len(tokens):
            if tokens[i] == '-':
                for o in pending: self.objects[o] = tokens[i+1]
                pending = []; i += 2
            else:
                pending.append(tokens[i]); i += 1


# ── STATE LOGIC ────────────────────────────────────────────────

def eval_cond(cond, state, b):
    if not cond or isinstance(cond, str): return True
    h = cond[0]
    if h == 'and': return all(eval_cond(c, state, b) for c in cond[1:])
    if h == 'not': return not eval_cond(cond[1], state, b)
    return tuple(b.get(t, t) for t in cond) in state

def apply_eff(eff, state, b):
    state = set(state)
    if not eff or isinstance(eff, str): return state
    h = eff[0]
    if h == 'and':
        for e in eff[1:]: state = apply_eff(e, state, b)
        return state
    if h == 'not':
        state.discard(tuple(b.get(t, t) for t in eff[1]))
        return state
    state.add(tuple(b.get(t, t) for t in eff))
    return state

def goal_met(goal, state):
    if not goal or isinstance(goal, str): return True
    h = goal[0]
    if h == 'and': return all(goal_met(g, state) for g in goal[1:])
    if h == 'not': return tuple(goal[1]) not in state
    return tuple(goal) in state


# ── PLANNER ────────────────────────────────────────────────────

def plan(domain_path, problem_path):
    domain  = Domain(domain_path)
    problem = Problem(problem_path)
    objects = list(problem.objects.keys())

    # Ground all actions
    grounded = []
    for action in domain.actions:
        params = action['params']
        if not params:
            grounded.append((action['name'], {}, action['pre'], action['eff']))
            continue
        for combo in product(objects, repeat=len(params)):
            binding = dict(zip(params, combo))
            name    = f"{action['name']}({','.join(combo)})"
            grounded.append((name, binding, action['pre'], action['eff']))

    init  = frozenset(problem.init)
    queue = deque([(init, [])])
    seen  = {init}

    while queue:
        state, history = queue.popleft()
        if goal_met(problem.goal, state):
            return history
        for (name, binding, pre, eff) in grounded:
            if eval_cond(pre, state, binding):
                new_state = frozenset(apply_eff(eff, state, binding))
                if new_state not in seen:
                    seen.add(new_state)
                    queue.append((new_state, history + [name]))

    return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python planner.py domain.pddl problem.pddl")
        sys.exit(1)
    result = plan(sys.argv[1], sys.argv[2])
    if result:
        print("Plan found:")
        for step in result: print(f"  {step}")
    else:
        print("No plan found.")
