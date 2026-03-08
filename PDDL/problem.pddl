(define (problem roboboat-mission)
  (:domain maritime-autonomy)

  (:objects
    task1 task2 - task
  )

  (:init
    (is_speedgate task1)
    (is_gate task2)
  )

  (:goal
    (and
      (speedgate_done task1)
      (gate_passed task2)
    )
  )

)
