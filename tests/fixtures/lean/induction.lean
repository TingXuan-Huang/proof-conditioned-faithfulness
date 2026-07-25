by
  induction n with
  | zero => rfl
  | succ n inductionHypothesis => exact congrArg Nat.succ inductionHypothesis
