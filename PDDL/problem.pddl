(define (problem roboboat-gates)
  (:domain maritime-autonomy)

  (:objects
    gate1 gate2 - gate
  )

  (:init
    (green_confirmed gate1)
    (green_confirmed gate2)
  )

  (:goal
    (and
      (gate_passed gate1)
      (gate_passed gate2)
    )
  )

)
