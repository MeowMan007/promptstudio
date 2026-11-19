export type Artifact = {
  id: string;
  alias: string;
  project_id: string;
  /**
   * Closed artifact type from machine/type-registry.json
   */
  type:
    | "accessibility_rule"
    | "adr"
    | "alternative"
    | "api_endpoint"
    | "assumption"
    | "attachment"
    | "brief"
    | "claim"
    | "component"
    | "component_spec"
    | "constraint"
    | "data_entity"
    | "decision"
    | "design_token"
    | "environment"
    | "epic"
    | "evaluation_case"
    | "event_contract"
    | "exclusion"
    | "feature"
    | "field_binding"
    | "hypothesis"
    | "idea"
    | "insight"
    | "integration"
    | "interaction"
    | "issue"
    | "metric"
    | "milestone"
    | "note"
    | "persona"
    | "problem"
    | "prompt"
    | "prompt_block"
    | "prompt_flow"
    | "prompt_variable"
    | "question"
    | "requirement"
    | "risk"
    | "screen"
    | "skill"
    | "source"
    | "task"
    | "test_case"
    | "threat"
    | "tool_definition"
    | "ui_state"
    | "user_flow"
    | "user_story"
    | "wireframe_component";
  schema_version: string;
  title: string;
  body?: string;
  payload: {
    [k: string]: unknown;
  };
  status: "scratch" | "proposed" | "in_review" | "approved" | "rejected" | "deprecated" | "archived";
  revision: number;
  created_by: string;
  updated_by: string;
  visibility?: "project" | "private" | "restricted";
  owner?: string | null;
  tags?: string[];
  sensitivity?: "public" | "internal" | "confidential" | "secret-bearing";
  locked_fields?: string[];
  provenance: {
    origin: "user_input" | "prompt_run" | "import" | "system" | "integration";
    run_id?: string | null;
    prompt_version?: string | null;
    skill_version?: string | null;
    model?: string | null;
    input_artifact_ids?: string[];
    source_ids?: string[];
    confidence?: number | null;
    [k: string]: unknown;
  };
  created_at: string;
  updated_at: string;
};
