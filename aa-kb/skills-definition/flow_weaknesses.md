FLOW ASSESSMENT: Remaining Weaknesses
🔴 HIGH RISK (Likely to cause deviations)
#	Location	Weakness	Likely Deviation
1	_OUTPUT_GENERATION.md	citation_map not persisted as artifact — STEP 1.5 describes creating citation_map but doesn't require OUTPUTTING it. LLM may "think" it created one but not actually maintain it.	LLM skips to STEP 2 without real citation_map → end-list citations
2	Synthesizers	No checkpoint after analyst execution — Analysts launch, outputs collected, but no validation that outputs were actually received/parsed before integration.	LLM proceeds with empty/malformed analyst outputs, producing hallucinated integration
3	_OUTPUT_GENERATION.md	[Source: analyst-X] removal timing unclear — Instructions say "remove in prose" but no explicit step. LLM may remove too early (in outline) or keep them (in final).	Inconsistent source markers in output
4	Orchestrator → Synthesizer	context_documents handoff gap — Orchestrator collects L0 sources via PHASE 1.5, but synthesizer instructions don't explicitly show HOW to access/use them.	L0 sources ignored, defeating user research
🟡 MEDIUM RISK (May cause deviations under certain conditions)
#	Location	Weakness	Likely Deviation
5	Orchestrator PHASE 2	Clarification questions not tool-enforced — Says "Ask 1-2 targeted questions" but doesn't mandate AskUserQuestion tool.	LLM asks in prose, user responds in prose, no structured capture
6	Orchestrator PHASE 4	Outline approval checkpoint deferred to synthesizer — Orchestrator says "Present OUTLINE for user approval" but doesn't repeat AskUserQuestion requirement.	LLM may present outline and continue without waiting
7	All files	Language parameter implicit — "Detect from input" is fuzzy. No explicit language: "it" parameter in handoff.	Mixed EN/IT output, especially with Italian questions but English keywords
8	_OUTPUT_GENERATION.md	L2 Exa search result handling unspecified — Says "Max 3 Exa searches" but doesn't specify how to parse results into citation_map entries.	LLM does searches but doesn't properly integrate results
🟢 LOW RISK (Documented but could be clearer)
#	Location	Weakness	Note
9	Synthesizers	Timeout values documented but not enforced — Tables show 60s/90s timeouts but no mechanism ensures they're applied.	Relies on Task tool defaults
10	Template names	"Minto-Custom" vs "Minto" — Minor inconsistency in naming across files.	Unlikely to break flow
RECOMMENDED FIXES
Priority A: Fix #1 — Make citation_map an explicit artifact
Add to _OUTPUT_GENERATION.md after STEP 1.5:


### STEP 1.5 OUTPUT REQUIREMENT

After completing citation enrichment, you MUST output the citation_map in a code block:

```yaml
## CITATION MAP (Internal Artifact)

citation_map:
  - point_id: "1.2"
    url: "https://..."
    anchor_text: "..."
    pattern: factual
    source_level: L0
  [...]
This artifact:

Proves STEP 1.5 was executed
Provides explicit reference for STEP 2 link weaving
Can be shown to user if requested
DO NOT proceed to STEP 2 without outputting this artifact.



### Priority B: Fix #2 — Add analyst output validation checkpoint

Add to each synthesizer after Phase A (sub-agent launch):

```markdown
### ANALYST OUTPUT VALIDATION (Before Integration)

After collecting all outputs, verify:

```yaml
analyst_validation:
  - pestle-analyst: [received | partial | failed]
    has_frontmatter: [yes | no]
    key_findings_count: [N]
  - morphological-analyst: [received | partial | failed]
    has_frontmatter: [yes | no]
    key_findings_count: [N]
  [...]
IF 2+ fixed analysts = failed → ABORT synthesis
IF any output lacks frontmatter → treat as partial, note gap



### Priority C: Fix #4 — Explicit context_documents handoff

Add to synthesizer Phase B (Integration):

```markdown
### L0 Sources Access

If orchestrator passed `context_documents`:

1. Read the research_briefing.yaml structure
2. For each source in briefing:
   - Extract: url, anchor_suggestion, type, relevance
   - Store for STEP 1.5 citation matching
3. Priority order: official_document > report > academic > industry > news

IF context_documents empty or not provided:
   - Rely on L1 (agent Exa sources) and L2 (STEP 1.5 searches)
Priority D: Fix #5 — Enforce clarification tool use
In Orchestrator PHASE 2, change:


**MANDATORY:** If clarification needed, use AskUserQuestion tool.
DO NOT ask clarifying questions in prose text.
SUMMARY
Risk Level	Count	Action
🔴 HIGH	4	Fix immediately — these WILL cause problems
🟡 MEDIUM	4	Fix soon — problems under specific conditions
🟢 LOW	2	Optional cleanup
Most impactful fix: #1 (citation_map artifact) — This single change would prevent the end-list citation problem that was the original test failure.

Want me to implement these fixes?


==========

# python code solution

just a question. do not change or provide anything, just answer. Do you think that python code should be more appropriate (skills accept them)?
Honest answer: Yes, a hybrid approach would be more robust.

What Python would solve:

State persistence — citation_map, analyst_outputs, context_documents as actual data structures, not "mental" LLM state
Checkpoint enforcement — if not citation_map: raise StepSkippedError() is deterministic; markdown "MUST" is probabilistic
Validation — JSON schema for frontmatter, not checklist the LLM might skip
Orchestration — Sequential step execution with actual function calls, not hoping LLM follows the order
What markdown/LLM should still do:

Content generation (analyst reasoning, integration logic, prose expansion)
Natural language user interaction
Flexible adaptation to partial failures
Ideal architecture:


Python orchestrator
  ├── validate_inputs()
  ├── launch_analysts() → LLM calls
  ├── validate_analyst_outputs()  # schema check
  ├── integration() → LLM call
  ├── generate_outline() → LLM call
  ├── checkpoint_user_approval()  # blocks until response
  ├── citation_enrichment() → LLM + Exa calls
  ├── validate_citation_map()  # enforced
  ├── generate_full_text() → LLM call
  └── validate_frontmatter()  # schema check
The current all-markdown approach works but relies on LLM discipline. The weaknesses I identified (#1-4) are all state management problems that code would eliminate.

so only a Python orchestrator file should be enough ?
Yes, essentially. A single orchestrator.py would:


orchestrator.py
├── WorkflowState (dataclass)
│   ├── context_documents: List[Source]
│   ├── analyst_outputs: Dict[str, AnalystOutput]
│   ├── approved_outline: str
│   ├── citation_map: List[CitationEntry]
│   └── current_step: Enum
│
├── run_analysis(problem: str)
│   ├── phase_1_parse_problem() → LLM call
│   ├── phase_1_5_fresh_sources() → user prompt, blocks
│   ├── phase_2_clarify() → LLM + user if needed
│   ├── phase_3_propose() → LLM + user approval, blocks
│   ├── phase_4_execute()
│   │   ├── launch_analysts() → parallel LLM calls
│   │   ├── validate_outputs() → schema check
│   │   ├── integrate() → LLM call
│   │   ├── generate_outline() → LLM call
│   │   ├── user_approval() → blocks
│   │   ├── citation_enrichment() → LLM + Exa
│   │   ├── validate_citation_map() → enforced
│   │   └── generate_full_text() → LLM call
│   └── return final_document
What stays in markdown: The skill/agent prompts become templates that Python injects context into before LLM calls. Content generation logic stays there.

What moves to Python: Flow control, state, validation, checkpoints.

One file is enough because the complexity is in orchestration, not the prompts themselves. The prompts are relatively stable once written.

is it a long job?
Not huge. Rough estimate:

Component	Lines	Time
State dataclasses	~80	15 min
Prompt loader (read markdown)	~30	10 min
Anthropic API wrapper	~50	15 min
Exa integration	~40	15 min
Validation functions	~60	20 min
User interaction (CLI prompts)	~50	15 min
Main orchestration flow	~200	45 min
Total	~500 lines	~2-3 hours
MVP version that handles the 4 high-risk issues: probably 300 lines, 1.5 hours.

The hard part isn't the code — it's deciding:

Use Anthropic SDK directly or wrap Claude Code's Task tool?
CLI interaction or integrate with existing skill invocation?
How to handle parallel analysts (asyncio or sequential)?
Want me to draft the orchestrator structure first (pseudocode/skeleton) so you can evaluate before committing to full implementation?

draft the orchestrator structure with the simplest and more effective ways from
Use Anthropic SDK directly or wrap Claude Code's Task tool?
CLI interaction or integrate with existing skill invocation?
How to handle parallel analysts (asyncio or sequential)?
Here's my recommended architecture with the simplest, most effective choices:


"""
strategic_orchestrator.py
MVP Python orchestrator for strategic analysis workflow

DECISIONS:
- Anthropic SDK directly (cleaner, more control)
- CLI interaction (simple, standalone, testable)
- Sequential analysts (simpler for MVP, asyncio later if needed)
- Exa Python SDK for L2 searches (not MCP)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path
import anthropic
import yaml
# from exa_py import Exa  # uncomment when implementing L2

# ============== CONFIGURATION ==============

SKILLS_PATH = Path("/mnt/DATA/26space/.claude/skills")
AGENTS_PATH = Path("/mnt/DATA/26space/.claude/agents")
MODEL = "claude-sonnet-4-20250514"  # or claude-opus-4-20250514 for complex steps


# ============== DATA STRUCTURES ==============

class Step(Enum):
    INIT = "init"
    PROBLEM_PARSED = "problem_parsed"
    SOURCES_DECIDED = "sources_decided"
    PROPOSAL_APPROVED = "proposal_approved"
    ANALYSTS_COMPLETE = "analysts_complete"
    OUTLINE_APPROVED = "outline_approved"
    CITATIONS_MAPPED = "citations_mapped"
    COMPLETE = "complete"


@dataclass
class Source:
    url: str
    title: str
    type: str  # official_document, report, academic, industry, news
    anchor_suggestion: str
    level: str  # L0, L1, L2


@dataclass
class AnalystOutput:
    name: str
    status: str  # complete, partial, failed
    confidence: Optional[float]
    content: str
    exa_sources: list[Source] = field(default_factory=list)


@dataclass
class CitationEntry:
    point_id: str
    url: Optional[str]
    anchor_text: str
    pattern: str  # factual, data, context, deep, theoretical
    source_level: str  # L0, L1, L2, theoretical, unavailable


@dataclass
class WorkflowState:
    problem: str = ""
    language: str = "en"
    current_step: Step = Step.INIT
    
    # Phase 1.5 outputs
    fresh_sources_choice: str = ""  # A, B, C
    context_documents: list[Source] = field(default_factory=list)
    
    # Phase 3 outputs
    synthesizer: str = ""
    template: str = ""
    optional_analysts: list[str] = field(default_factory=list)
    web_search_enabled: bool = False
    
    # Phase 4 outputs
    analyst_outputs: dict[str, AnalystOutput] = field(default_factory=dict)
    outline: str = ""
    citation_map: list[CitationEntry] = field(default_factory=list)
    final_document: str = ""


# ============== PROMPT LOADING ==============

def load_skill(name: str) -> str:
    """Load a skill/synthesizer markdown file."""
    path = SKILLS_PATH / name / "SKILL.md"
    if not path.exists():
        path = SKILLS_PATH / f"{name}.md"  # for _OUTPUT_GENERATION.md etc.
    return path.read_text()


def load_agent(name: str) -> str:
    """Load an agent markdown file."""
    path = AGENTS_PATH / name / "AGENT.md"
    return path.read_text()


def load_output_generation() -> str:
    """Load the central output generation prompts."""
    return (SKILLS_PATH / "_OUTPUT_GENERATION.md").read_text()


# ============== LLM CALLS ==============

client = anthropic.Anthropic()


def llm_call(system: str, user: str, max_tokens: int = 4096) -> str:
    """Simple LLM call wrapper."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text


def llm_call_with_tools(system: str, user: str, tools: list) -> dict:
    """LLM call that may use tools (for Exa searches)."""
    # Implement when adding L2 Exa integration
    pass


# ============== USER INTERACTION ==============

def ask_user(prompt: str, options: list[str]) -> str:
    """CLI user interaction with numbered options."""
    print(f"\n{'='*60}")
    print(prompt)
    print("-" * 40)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("-" * 40)
    
    while True:
        choice = input("Enter choice (number or 'other' for custom): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        elif choice.lower() == "other":
            return input("Enter custom response: ").strip()
        print("Invalid choice. Try again.")


def confirm(prompt: str) -> bool:
    """Simple yes/no confirmation."""
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response in ("y", "yes")


# ============== VALIDATION ==============

def validate_analyst_output(output: str, analyst_name: str) -> AnalystOutput:
    """Parse and validate analyst output structure."""
    # Extract YAML frontmatter if present
    if output.startswith("---"):
        parts = output.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                return AnalystOutput(
                    name=analyst_name,
                    status=frontmatter.get("status", "complete"),
                    confidence=frontmatter.get("confidence"),
                    content=parts[2].strip(),
                    exa_sources=[]  # parse from output if present
                )
            except yaml.YAMLError:
                pass
    
    # Fallback: treat entire output as content
    return AnalystOutput(
        name=analyst_name,
        status="partial",
        confidence=None,
        content=output,
        exa_sources=[]
    )


def validate_citation_map(citation_map: list[CitationEntry], outline: str) -> bool:
    """Verify citation_map exists and is non-empty for factual outlines."""
    if not citation_map:
        # Check if outline has factual claims that need citations
        factual_indicators = ["€", "$", "%", "billion", "million", "2024", "2025", "according to"]
        has_factual_claims = any(ind in outline.lower() for ind in factual_indicators)
        if has_factual_claims:
            return False  # Should have citations but doesn't
    return True


def validate_frontmatter(document: str, required_fields: list[str]) -> tuple[bool, list[str]]:
    """Validate document frontmatter has all required fields."""
    missing = []
    if not document.startswith("---"):
        return False, ["No frontmatter found"]
    
    try:
        parts = document.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        for field in required_fields:
            if field not in frontmatter or not frontmatter[field]:
                missing.append(field)
    except (yaml.YAMLError, IndexError):
        return False, ["Invalid frontmatter format"]
    
    return len(missing) == 0, missing


# ============== MAIN WORKFLOW ==============

class StrategicOrchestrator:
    def __init__(self):
        self.state = WorkflowState()
    
    def run(self, problem: str) -> str:
        """Main entry point - run full analysis workflow."""
        self.state.problem = problem
        self.state.language = self._detect_language(problem)
        
        # Phase 1: Parse problem
        self._phase_1_parse()
        
        # Phase 1.5: Fresh sources decision
        self._phase_1_5_sources()
        
        # Phase 2: Clarification (if needed)
        self._phase_2_clarify()
        
        # Phase 3: Proposal
        self._phase_3_propose()
        
        # Phase 4: Execute
        self._phase_4_execute()
        
        return self.state.final_document
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        italian_indicators = ["analizza", "valuta", "strategia", "l'", "è", "perché"]
        if any(ind in text.lower() for ind in italian_indicators):
            return "it"
        return "en"
    
    def _phase_1_parse(self):
        """Parse problem, extract keywords, score synthesizers."""
        system = "You are a strategic analysis router. Analyze the problem and identify the best-fit synthesizer."
        user = f"""
Problem: {self.state.problem}

Score each synthesizer 0.0-1.0 and identify:
1. Best-fit synthesizer
2. Recommended template (BLUF/Hypothesis-Driven/POR/Minto-Custom)
3. Whether optional analysts should be activated
4. Whether web search would help

Return as YAML.
"""
        # LLM call to parse problem
        result = llm_call(system, user)
        # Parse result and update state
        self.state.current_step = Step.PROBLEM_PARSED
    
    def _phase_1_5_sources(self):
        """Evaluate fresh sources need and get user decision."""
        # Evaluate if HIGH/MEDIUM/LOW need
        # If HIGH, present options to user
        choice = ask_user(
            "This analysis would benefit from fresh sources. Choose approach:",
            [
                "A. Pause for research - I'll gather sources",
                "B. Proceed with Exa - use web search during analysis",
                "C. No fresh sources - use model knowledge only"
            ]
        )
        self.state.fresh_sources_choice = choice[0]  # "A", "B", or "C"
        
        if self.state.fresh_sources_choice == "A":
            # Wait for user to provide research_briefing.yaml
            path = input("Enter path to research_briefing.yaml (or press Enter to skip): ").strip()
            if path:
                self._load_context_documents(path)
        
        self.state.current_step = Step.SOURCES_DECIDED
    
    def _phase_2_clarify(self):
        """Ask clarification questions if needed."""
        # Only if ambiguous (multiple synthesizers scored 0.4-0.6)
        pass
    
    def _phase_3_propose(self):
        """Present proposal and get user approval."""
        proposal = self._generate_proposal()
        print(proposal)
        
        choice = ask_user(
            "Review the proposal above:",
            [
                "Approve proposal as-is",
                "Modify synthesizer selection",
                "Modify template",
                "Modify fresh sources configuration"
            ]
        )
        
        if "Approve" in choice:
            self.state.current_step = Step.PROPOSAL_APPROVED
        else:
            # Handle modifications, loop until approved
            pass
    
    def _phase_4_execute(self):
        """Execute the approved analysis."""
        # 1. Launch analysts (sequential for MVP)
        self._run_analysts()
        
        # 2. Validate analyst outputs
        failed_count = sum(1 for ao in self.state.analyst_outputs.values() if ao.status == "failed")
        if failed_count >= 2:
            raise RuntimeError("2+ fixed analysts failed. Aborting.")
        
        self.state.current_step = Step.ANALYSTS_COMPLETE
        
        # 3. Generate outline
        self._generate_outline()
        
        # 4. User approval checkpoint (ENFORCED)
        self._outline_approval_checkpoint()
        
        self.state.current_step = Step.OUTLINE_APPROVED
        
        # 5. Citation enrichment (ENFORCED)
        self._citation_enrichment()
        
        # 6. Validate citation_map (ENFORCED)
        if not validate_citation_map(self.state.citation_map, self.state.outline):
            raise RuntimeError("Citation map validation failed. Cannot proceed to full text.")
        
        self.state.current_step = Step.CITATIONS_MAPPED
        
        # 7. Generate full text
        self._generate_full_text()
        
        # 8. Validate frontmatter
        required = ["title", "description", "date", "version", "synthesizer", 
                    "analysts_fixed", "outline_template", "status", "language"]
        valid, missing = validate_frontmatter(self.state.final_document, required)
        if not valid:
            raise RuntimeError(f"Frontmatter validation failed. Missing: {missing}")
        
        self.state.current_step = Step.COMPLETE
    
    def _run_analysts(self):
        """Run all analysts sequentially."""
        # Get analyst list from synthesizer config
        synthesizer_config = self._get_synthesizer_config()
        analysts = synthesizer_config["fixed"] + self.state.optional_analysts
        
        for analyst_name in analysts:
            print(f"Running {analyst_name}...")
            agent_prompt = load_agent(analyst_name)
            
            system = agent_prompt
            user = f"Analyze: {self.state.problem}"
            
            try:
                output = llm_call(system, user, max_tokens=8192)
                self.state.analyst_outputs[analyst_name] = validate_analyst_output(output, analyst_name)
            except Exception as e:
                self.state.analyst_outputs[analyst_name] = AnalystOutput(
                    name=analyst_name,
                    status="failed",
                    confidence=None,
                    content=str(e)
                )
    
    def _generate_outline(self):
        """Generate outline from analyst outputs."""
        output_gen = load_output_generation()
        
        analyst_summary = "\n".join([
            f"### {name}\nStatus: {ao.status}\nContent:\n{ao.content[:2000]}..."
            for name, ao in self.state.analyst_outputs.items()
        ])
        
        system = f"""You are generating an outline using the {self.state.template} template.
{output_gen}
"""
        user = f"""
## Analyst Outputs:
{analyst_summary}

## Task:
Generate OUTLINE for: {self.state.problem}
Use template: {self.state.template}
"""
        self.state.outline = llm_call(system, user, max_tokens=8192)
    
    def _outline_approval_checkpoint(self):
        """ENFORCED: Must get user approval before proceeding."""
        print("\n" + "="*60)
        print("OUTLINE FOR APPROVAL")
        print("="*60)
        print(self.state.outline)
        print("="*60)
        
        while True:
            choice = ask_user(
                "Review the outline above:",
                [
                    "Approve outline - proceed to full text",
                    "Modify structure - reorder or change sections",
                    "Modify content - add, remove, or revise points",
                    "Regenerate - start from scratch"
                ]
            )
            
            if "Approve" in choice:
                return
            else:
                feedback = input("Describe the changes you want: ")
                self._regenerate_outline(feedback)
                print("\n" + "="*60)
                print("REVISED OUTLINE")
                print("="*60)
                print(self.state.outline)
    
    def _citation_enrichment(self):
        """ENFORCED: Map sources to outline points."""
        # Collect all available sources
        l0_sources = self.state.context_documents
        l1_sources = [s for ao in self.state.analyst_outputs.values() for s in ao.exa_sources]
        
        system = "You are enriching an outline with citations."
        user = f"""
## Approved Outline:
{self.state.outline}

## Available Sources:
L0 (context_documents): {[s.title for s in l0_sources]}
L1 (agent sources): {[s.title for s in l1_sources]}

## Task:
1. Identify citation needs in the outline
2. Match with available sources (prefer L0 > L1)
3. List unmatched needs that require L2 Exa search
4. Return citation_map as YAML
"""
        result = llm_call(system, user)
        
        # Parse citation_map from result
        # If unmatched needs, run L2 Exa searches (max 3)
        self._run_l2_searches_if_needed(result)
    
    def _run_l2_searches_if_needed(self, enrichment_result: str):
        """Run Exa searches for unmatched citation needs."""
        # Parse unmatched needs from result
        # For each (max 3), call Exa API
        # Add results to citation_map
        pass
    
    def _generate_full_text(self):
        """Generate final prose document with woven citations."""
        output_gen = load_output_generation()
        
        citation_yaml = yaml.dump([
            {"point_id": c.point_id, "url": c.url, "anchor_text": c.anchor_text, "pattern": c.pattern}
            for c in self.state.citation_map
        ])
        
        system = f"""You are expanding an outline into full text.
{output_gen}
"""
        user = f"""
## Approved Outline:
{self.state.outline}

## Citation Map:
{citation_yaml}

## Task:
Expand to full prose document.
- Weave citations INTO narrative (not end-list)
- Remove [Source: analyst-X] markers
- Use citation patterns (factual, data, context, deep)
- Include complete frontmatter with outline_template field
"""
        self.state.final_document = llm_call(system, user, max_tokens=16384)
    
    # Helper methods
    def _generate_proposal(self) -> str:
        """Generate the proposal text."""
        # Implementation
        pass
    
    def _get_synthesizer_config(self) -> dict:
        """Get synthesizer configuration (fixed/optional analysts)."""
        # Parse from synthesizer SKILL.md
        pass
    
    def _load_context_documents(self, path: str):
        """Load research_briefing.yaml into context_documents."""
        # Implementation
        pass
    
    def _regenerate_outline(self, feedback: str):
        """Regenerate outline with user feedback."""
        # Implementation
        pass


# ============== ENTRY POINT ==============

if __name__ == "__main__":
    problem = input("Enter your analysis problem: ")
    orchestrator = StrategicOrchestrator()
    
    try:
        result = orchestrator.run(problem)
        print("\n" + "="*60)
        print("FINAL DOCUMENT")
        print("="*60)
        print(result)
    except RuntimeError as e:
        print(f"\n❌ Analysis aborted: {e}")
Key Design Decisions
Decision	Choice	Rationale
LLM API	Anthropic SDK directly	Cleaner, no parsing Task tool output
User interaction	CLI with input()	Simple, testable, no dependencies
Analysts	Sequential	MVP simplicity; asyncio easy to add later
Exa	Direct SDK (commented)	Cleaner than MCP, explicit control
Enforced Checkpoints
Line 188: _outline_approval_checkpoint() — loops until "Approve"
Line 193: validate_citation_map() — raises if fails
Line 200: validate_frontmatter() — raises if missing fields
What This Solves
Weakness	Fixed By
#1 citation_map not persisted	self.state.citation_map is real data
#2 No analyst validation	validate_analyst_output() + failure count check
#3 Source marker timing	Explicit in _generate_full_text() prompt
#4 context_documents handoff	self.state.context_documents passed explicitly
~350 lines skeleton. Need ~150 more for helper implementations.