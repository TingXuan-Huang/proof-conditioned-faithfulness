import Lean.Elab.Command
import Lean.Elab.Term
import Lean.Parser.Extension
import Lean.Util.CollectAxioms

/-! Machine-readable axiom reports for trusted proof checks. -/

namespace ProofFaithfulness.Audit

open Lean Elab Command Term

/-- Parse a candidate as exactly one term, requiring complete input consumption. -/
def parseCandidateTerm (environment : Environment) (source : String) : Except String Syntax :=
  Parser.runParserCategory environment `term source "<candidate>"

/-- Elaborate an escaped candidate string as a term without splicing command syntax. -/
syntax (name := checkedCandidate) "pf_checked_candidate% " str : term

@[term_elab checkedCandidate]
def elabCheckedCandidate : TermElab := fun stx expectedType? =>
  match stx with
  | `(pf_checked_candidate% $source:str) => do
      let parsed ← match parseCandidateTerm (← getEnv) source.getString with
        | .ok parsed => pure parsed
        | .error message => throwErrorAt source "candidate is not exactly one Lean term: {message}"
      elabTerm parsed expectedType?
  | _ => throwUnsupportedSyntax

/-- Emit the transitive axioms of a declaration behind a stable marker. -/
syntax (name := proofAxioms) "#proof_axioms " ident : command

@[command_elab proofAxioms]
def elabProofAxioms : CommandElab := fun
  | `(#proof_axioms $id:ident) => do
      let declarationName := id.getId
      let _ ← getConstInfo declarationName
      let axioms ← collectAxioms declarationName
      let names := axioms.qsort Name.lt |>.map Name.toString
      logInfo m!"PF_AXIOMS_JSON:{(toJson names).compress}"
  | stx => throwErrorAt stx "invalid #proof_axioms command"

end ProofFaithfulness.Audit
