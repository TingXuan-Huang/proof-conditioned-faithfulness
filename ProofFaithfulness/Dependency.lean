import Lean.Elab.Command
import Lean.Util.FoldConsts
import ProofFaithfulness.Audit

/-! Machine-readable proof-term dependency and local-binding inspection. -/

namespace ProofFaithfulness.Dependency

open Lean Elab Command

structure BindingUse where
  name : String
  kind : String
  used : Bool
  rootParameter : Bool
deriving ToJson

structure LocalFactUse where
  name : String
  used : Bool
deriving ToJson

structure DependencyReport where
  usedConstants : Array String
  bindings : Array BindingUse
  localFacts : Array LocalFactUse
  tacticEvidence : Array String
  explicitLocalNames : Array String
deriving ToJson

private partial def usesBoundVariable (expression : Expr) : Bool :=
  expression.hasLooseBVar 0

private partial def collectBindingsAt
    (expression : Expr) (rootParameter : Bool) : Array BindingUse :=
  match expression with
  | .forallE name type body _ =>
      #[⟨name.toString, "forall", usesBoundVariable body, false⟩]
        ++ collectBindingsAt type false
        ++ collectBindingsAt body false
  | .lam name type body _ =>
      #[⟨name.toString, "lambda", usesBoundVariable body, rootParameter⟩]
        ++ collectBindingsAt type false
        ++ collectBindingsAt body rootParameter
  | .letE name type value body _ =>
      #[⟨name.toString, "let", usesBoundVariable body, false⟩]
        ++ collectBindingsAt type false
        ++ collectBindingsAt value false
        ++ collectBindingsAt body false
  | .app function argument =>
      collectBindingsAt function false ++ collectBindingsAt argument false
  | .mdata _ body => collectBindingsAt body rootParameter
  | .proj _ _ body => collectBindingsAt body false
  | _ => #[]

private def collectBindings (expression : Expr) : Array BindingUse :=
  collectBindingsAt expression true

private partial def collectLocalFacts (expression : Expr) : Array LocalFactUse :=
  match expression.letFunAppArgs? with
  | some (arguments, name, type, value, body) =>
      #[⟨name.toString, usesBoundVariable body⟩]
        ++ collectLocalFacts value
        ++ collectLocalFacts body
        ++ arguments.foldl (fun facts argument => facts ++ collectLocalFacts argument) #[]
  | none =>
      match expression with
      | .forallE _ _ body _ => collectLocalFacts body
      | .lam _ _ body _ => collectLocalFacts body
      | .letE name _ value body _ =>
          #[⟨name.toString, usesBoundVariable body⟩]
            ++ collectLocalFacts value
            ++ collectLocalFacts body
      | .app function argument => collectLocalFacts function ++ collectLocalFacts argument
      | .mdata _ body => collectLocalFacts body
      | .proj _ _ body => collectLocalFacts body
      | _ => #[]

private partial def collectSyntaxKinds : Syntax → Array String
  | .node _ kind children =>
      children.foldl
        (fun kinds child => kinds ++ collectSyntaxKinds child)
        #[kind.toString]
  | stx => #[stx.getKind.toString]

private partial def collectIdentifiers : Syntax → Array String
  | .ident _ _ value _ => #[value.toString]
  | .node _ _ children =>
      children.foldl (fun names child => names ++ collectIdentifiers child) #[]
  | _ => #[]

private partial def explicitLocalNames : Syntax → Array String
  | .node _ kind children =>
      let nested := children.foldl (fun names child => names ++ explicitLocalNames child) #[]
      if kind == `Lean.Parser.Tactic.tacticHave_ || kind == `Lean.Parser.Tactic.tacticLet_ then
        let identifiers := children.foldl (fun names child => names ++ collectIdentifiers child) #[]
        if identifiers.isEmpty then nested else #[identifiers[0]!] ++ nested
      else
        nested
  | _ => #[]

private def tacticEvidence (proofSyntax : Syntax) : Array String := Id.run do
  let mut evidence := #[]
  let kinds := collectSyntaxKinds proofSyntax
  if kinds.any fun kind => kind == "Lean.Parser.Tactic.induction" then
    evidence := evidence.push "induction"
  if kinds.any fun kind =>
      kind.endsWith ".ring"
        || kind.endsWith ".ringNF"
        || kind.endsWith ".ring1"
        || kind.endsWith ".ring1NF" then
    evidence := evidence.push "ring_normalization"
  if kinds.any fun kind =>
      kind == "Lean.Parser.Tactic.tacticHave_" || kind == "Lean.Parser.Tactic.tacticLet_" then
    evidence := evidence.push "explicit_local"
  if kinds.any fun kind =>
      kind == "Lean.Parser.Tactic.omega"
        || kind == "Lean.Parser.Tactic.aesop"
        || kind == "Lean.Parser.Tactic.simpAll"
        || kind == "Lean.Parser.Tactic.decide"
        || kind == "Lean.Parser.Tactic.solveByElim" then
    evidence := evidence.push "automation"
  return evidence

/-- Emit dependencies for a declaration and tactic evidence for its exact source. -/
syntax (name := proofDependency) "#proof_dependency " ident ppSpace str : command

@[command_elab proofDependency]
def elabProofDependency : CommandElab := fun
  | `(#proof_dependency $id:ident $source:str) => do
      let declarationName := id.getId
      let info ← getConstInfo declarationName
      let value ← match info.value? with
        | some value => pure value
        | none => throwErrorAt id "declaration has no inspectable value"
      let names := value.getUsedConstants
        |>.qsort Name.lt
        |>.map Name.toString
      let proofSyntax ← match Audit.parseCandidateTerm (← getEnv) source.getString with
        | .ok parsed => pure parsed
        | .error message => throwErrorAt source "candidate term parse failed: {message}"
      let report : DependencyReport := {
        usedConstants := names
        bindings := collectBindings value
        localFacts := collectLocalFacts value
        tacticEvidence := tacticEvidence proofSyntax
        explicitLocalNames := explicitLocalNames proofSyntax
      }
      logInfo m!"PF_DEPENDENCY_JSON:{(toJson report).compress}"
  | stx => throwErrorAt stx "invalid #proof_dependency command"

end ProofFaithfulness.Dependency
