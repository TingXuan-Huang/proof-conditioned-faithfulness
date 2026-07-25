/- API probe for reference-proof generation (briefs 001/033/036/040/041).

Run on the server with the project toolchain:

    lake env lean data/benchmark/reference-briefs/PROBE-API.lean

and paste the FULL output back to the human — INCLUDING errors: an
"unknown identifier" error is the answer "this name has drifted; find the
successor". Each #check is an independent command; errors do not stop the file.
If the Lean project does not yet depend on Mathlib, adding it (with the exact
pinned revision recorded per T003) is prerequisite S2 work — do that first. -/
import Mathlib

-- ===== Candidate 001 (6 ∣ n³ − n) =====
#check @Int.even_mul_succ_self
#check @Int.induction_on
#check @IsCoprime.mul_dvd
#check @Int.isCoprime_iff_gcd_eq_one
#check @Int.even_iff_two_dvd
#check @dvd_neg
#check @Odd.neg_pow

-- ===== Candidate 033 (digits perm → 9 ∣ m − n) =====
#check @Nat.ofDigits
#check @Nat.ofDigits_cons
#check @Nat.ofDigits_digits
#check @List.Perm.sum_eq
#check @Nat.ModEq
#check @Int.ModEq
#check @Int.ModEq.sub
#check @Nat.cast_ofDigits
#check @sub_add_sub_cancel

-- ===== Candidate 036 (coins 3/5) =====
#check @Nat.strong_induction_on
#check @Nat.strongRecOn
#check @Nat.le_induction
#check @Nat.find
#check @Nat.find_spec
#check @Nat.find_min
#check @Nat.find_min'

-- ===== Candidate 040 (Irrational (Real.logb 2 3)) =====
#check @Real.logb
#check @Real.logb_pos
#check @Real.rpow_logb
#check @Real.rpow_natCast
#check @Real.rpow_mul
#check @Real.log_pow
#check @Real.log_pos
#check @Real.log_injOn_pos
#check @Real.exp_log
#check @Irrational
#check @Rat.num_div_den
#check @Rat.cast_def
#check @div_mul_cancel₀
#check @Nat.Coprime.pow
#check @Nat.coprime_self_iff_one

-- ===== Candidate 041 (8q³ − 6q − 1 ≠ 0) =====
#check @Rat.reduced
#check @Rat.numDenCasesOn
#check @Rat.num_dvd
#check @Rat.den_dvd
#check @Int.even_or_odd
#check @Int.even_pow
#check @Int.even_mul
#check @Int.even_add
#check @Int.even_sub
#check @Int.natAbs_dvd
#check @Int.dvd_natAbs
#check @Polynomial.num_dvd_of_isRoot
#check @Polynomial.den_dvd_of_isRoot

-- ===== Tactic smoke (tactics have no #check; these examples exercise them) =====
section TacticSmoke
example (a b : ℕ) (h : 11 ≤ b) : 8 ≤ b - 3 := by omega
example : (8 : ℚ) * 1 ^ 3 - 6 * 1 - 1 ≠ 0 := by norm_num
example (x : ℕ) (h : x < 4) : x ≤ 3 := by interval_cases x <;> omega
example (a : ℕ) : ((a : ℤ) : ℚ) = (a : ℚ) := by push_cast; ring
end TacticSmoke
