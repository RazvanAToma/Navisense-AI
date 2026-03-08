(define (domain maritime-autonomy)

  (:requirements :strips :typing :negative-preconditions)

  (:types task)

  (:predicates
    ; ── object detection status
    (green_confirmed   ?t - task)
    (red_confirmed     ?t - task)
    (beacon_confirmed  ?t - task)
    (yellow_confirmed  ?t - task)

    ; ── task progression
    (gate_identified   ?t - task)
    (gate_aligned      ?t - task)
    (gate_passed       ?t - task)
    (speedgate_done    ?t - task)

    ; ── task type flags (set in problem file)
    (is_gate           ?t - task)
    (is_speedgate      ?t - task)
  )

  ; ══════════════════════════════════════════════
  ; SEARCH ACTIONS — used when objects are estimated
  ; ══════════════════════════════════════════════

  (:action search_for_green
    :parameters (?t - task)
    :precondition (not (green_confirmed ?t))
    :effect       (green_confirmed ?t)
  )

  (:action search_for_red
    :parameters (?t - task)
    :precondition (and
      (green_confirmed ?t)
      (not (red_confirmed ?t))
    )
    :effect (red_confirmed ?t)
  )

  (:action search_for_beacon
    :parameters (?t - task)
    :precondition (and
      (is_speedgate ?t)
      (gate_passed  ?t)
      (not (beacon_confirmed ?t))
    )
    :effect (beacon_confirmed ?t)
  )

  (:action search_for_yellow
    :parameters (?t - task)
    :precondition (and
      (is_speedgate     ?t)
      (beacon_confirmed ?t)
      (not (yellow_confirmed ?t))
    )
    :effect (yellow_confirmed ?t)
  )

  ; ══════════════════════════════════════════════
  ; GATE TASK ACTIONS
  ; ══════════════════════════════════════════════

  (:action identify_gate
    :parameters (?t - task)
    :precondition (and
      (green_confirmed ?t)
      (red_confirmed   ?t)
      (not (gate_identified ?t))
    )
    :effect (gate_identified ?t)
  )

  (:action align_to_gate
    :parameters (?t - task)
    :precondition (and
      (gate_identified ?t)
      (not (gate_aligned ?t))
    )
    :effect (gate_aligned ?t)
  )

  (:action pass_through_gate
    :parameters (?t - task)
    :precondition (and
      (is_gate       ?t)
      (gate_aligned  ?t)
      (not (gate_passed ?t))
    )
    :effect (gate_passed ?t)
  )

  ; ══════════════════════════════════════════════
  ; SPEEDGATE TASK ACTIONS
  ; ══════════════════════════════════════════════

  (:action enter_speedgate
    :parameters (?t - task)
    :precondition (and
      (is_speedgate  ?t)
      (gate_aligned  ?t)
      (not (gate_passed ?t))
    )
    :effect (gate_passed ?t)
  )

  (:action run_speedgate
    :parameters (?t - task)
    :precondition (and
      (is_speedgate     ?t)
      (gate_passed      ?t)
      (beacon_confirmed ?t)
      (yellow_confirmed ?t)
      (not (speedgate_done ?t))
    )
    :effect (speedgate_done ?t)
  )

)
