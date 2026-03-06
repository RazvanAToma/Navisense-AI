(define (domain maritime-autonomy)

  (:requirements :strips :typing :negative-preconditions)

  (:types gate)

  (:predicates
    (gate_identified   ?g - gate)   ; both buoys confirmed within range
    (boat_aligned      ?g - gate)   ; boat is heading toward gate center
    (gate_passed       ?g - gate)   ; gate has been transited
    (green_confirmed   ?g - gate)   ; green buoy confirmed by sensors
    (red_confirmed     ?g - gate)   ; red buoy confirmed by sensors
  )

  ; ── Search for green buoy (estimated position only)
  (:action search_for_green
    :parameters (?g - gate)
    :precondition (not (green_confirmed ?g))
    :effect       (green_confirmed ?g)
  )

  ; ── Move to estimated green buoy position (already detected)
  (:action move_to_green
    :parameters (?g - gate)
    :precondition (and
      (green_confirmed ?g)
      (not (red_confirmed ?g))
    )
    :effect (green_confirmed ?g)  ; no change, just movement
  )

  ; ── Orbit green buoy to find red partner
  (:action orbit_for_red
    :parameters (?g - gate)
    :precondition (and
      (green_confirmed ?g)
      (not (red_confirmed ?g))
    )
    :effect (red_confirmed ?g)
  )

  ; ── Move to estimated red buoy area to confirm it
  (:action move_to_red_estimate
    :parameters (?g - gate)
    :precondition (and
      (green_confirmed ?g)
      (not (red_confirmed ?g))
    )
    :effect (red_confirmed ?g)
  )

  ; ── Identify gate once both buoys confirmed
  (:action identify_gate
    :parameters (?g - gate)
    :precondition (and
      (green_confirmed ?g)
      (red_confirmed  ?g)
      (not (gate_identified ?g))
    )
    :effect (gate_identified ?g)
  )

  ; ── Align boat to gate centerline
  (:action align_to_gate
    :parameters (?g - gate)
    :precondition (and
      (gate_identified ?g)
      (not (boat_aligned ?g))
      (not (gate_passed  ?g))
    )
    :effect (boat_aligned ?g)
  )

  ; ── Transit the gate
  (:action pass_through_gate
    :parameters (?g - gate)
    :precondition (and
      (gate_identified ?g)
      (boat_aligned    ?g)
      (not (gate_passed ?g))
    )
    :effect (gate_passed ?g)
  )

)
