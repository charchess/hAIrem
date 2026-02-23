-- hAIrem Deep Mind - Graph Schema V3 (FastEmbed / MiniLM 384)
-- Nodes
DEFINE TABLE fact SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD content ON TABLE fact TYPE string;
DEFINE FIELD embedding ON TABLE fact TYPE array<float, 384>;
DEFINE INDEX fact_embedding ON TABLE fact FIELDS embedding MTREE DIMENSION 384 DIST COSINE;

DEFINE TABLE subject SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD name ON TABLE subject TYPE string;
DEFINE INDEX subject_name ON TABLE subject FIELDS name UNIQUE;

DEFINE TABLE concept SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD name ON TABLE concept TYPE string;
DEFINE INDEX concept_name ON TABLE concept FIELDS name UNIQUE;

-- Edges
DEFINE TABLE BELIEVES SCHEMAFULL TYPE RELATION FROM subject TO fact PERMISSIONS FULL;
DEFINE FIELD confidence ON TABLE BELIEVES TYPE float DEFAULT 1.0;
DEFINE FIELD strength ON TABLE BELIEVES TYPE float DEFAULT 1.0;
DEFINE FIELD last_accessed ON TABLE BELIEVES TYPE datetime DEFAULT time::now();
DEFINE FIELD last_reinforced ON TABLE BELIEVES TYPE datetime DEFAULT time::now();
DEFINE FIELD permanent ON TABLE BELIEVES TYPE bool DEFAULT false;
DEFINE FIELD force_score ON TABLE BELIEVES TYPE float DEFAULT 0.5;
DEFINE FIELD affect ON TABLE BELIEVES TYPE float DEFAULT 0.5;
DEFINE FIELD importance ON TABLE BELIEVES TYPE float DEFAULT 0.5;
DEFINE FIELD relevance ON TABLE BELIEVES TYPE float DEFAULT 0.5;

DEFINE TABLE ABOUT SCHEMAFULL TYPE RELATION FROM fact TO subject PERMISSIONS FULL;

DEFINE TABLE CAUSED SCHEMAFULL TYPE RELATION FROM fact TO fact PERMISSIONS FULL;
DEFINE FIELD reason ON TABLE CAUSED TYPE string;

DEFINE TABLE KNOWS SCHEMAFULL TYPE RELATION FROM subject TO subject PERMISSIONS FULL;
DEFINE FIELD strength ON TABLE KNOWS TYPE float DEFAULT 1.0;

DEFINE TABLE TRUSTS SCHEMAFULL TYPE RELATION FROM subject TO subject PERMISSIONS FULL;
DEFINE FIELD level ON TABLE TRUSTS TYPE float DEFAULT 0.5;

-- Visual Imagination Assets
DEFINE TABLE visual_asset SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD url ON TABLE visual_asset TYPE string;
DEFINE FIELD prompt ON TABLE visual_asset TYPE string;
DEFINE FIELD embedding ON TABLE visual_asset TYPE array<float, 384>;
DEFINE FIELD agent_id ON TABLE visual_asset TYPE string;
DEFINE FIELD tags ON TABLE visual_asset TYPE array<string> DEFAULT [];
DEFINE FIELD last_used ON TABLE visual_asset TYPE datetime DEFAULT time::now();
DEFINE FIELD reference_image_used ON TABLE visual_asset TYPE option<string> DEFAULT "";

DEFINE INDEX visual_asset_embedding ON TABLE visual_asset FIELDS embedding MTREE DIMENSION 384 DIST COSINE;

-- Episodic Memory (Epic 24)
DEFINE TABLE episode SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD session_id ON TABLE episode TYPE string;
DEFINE FIELD agent_id ON TABLE episode TYPE string;
DEFINE FIELD user_id ON TABLE episode TYPE option<string>;
DEFINE FIELD started_at ON TABLE episode TYPE datetime DEFAULT time::now();
DEFINE FIELD ended_at ON TABLE episode TYPE option<datetime>;
DEFINE FIELD summary ON TABLE episode TYPE option<string>;
DEFINE FIELD emotion_arc ON TABLE episode TYPE array DEFAULT [];
DEFINE INDEX episode_session ON TABLE episode FIELDS session_id UNIQUE;

DEFINE TABLE EXTRACTED_FROM SCHEMAFULL TYPE RELATION FROM fact TO episode PERMISSIONS FULL;
DEFINE FIELD extracted_at ON TABLE EXTRACTED_FROM TYPE datetime DEFAULT time::now();

-- Spatial Presence (Epic 18)
DEFINE TABLE location SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD name ON TABLE location TYPE string;
DEFINE FIELD display_name ON TABLE location TYPE string DEFAULT name;
DEFINE FIELD background_prompt_template ON TABLE location TYPE option<string>;
DEFINE INDEX location_name ON TABLE location FIELDS name UNIQUE;

DEFINE TABLE PRESENT_IN SCHEMAFULL TYPE RELATION FROM subject TO location PERMISSIONS FULL;
DEFINE FIELD since ON TABLE PRESENT_IN TYPE datetime DEFAULT time::now();

-- Vault System (Named Inventory)
DEFINE TABLE vault SCHEMAFULL PERMISSIONS FULL;
DEFINE FIELD name ON TABLE vault TYPE string;
DEFINE FIELD agent_id ON TABLE vault TYPE string;
DEFINE FIELD asset_id ON TABLE vault TYPE record<visual_asset>;
DEFINE FIELD category ON TABLE vault TYPE string; -- "garment" | "background"
DEFINE FIELD uri ON TABLE vault TYPE string;
DEFINE FIELD prompt ON TABLE vault TYPE string;
DEFINE FIELD timestamp ON TABLE vault TYPE datetime DEFAULT time::now();
DEFINE INDEX vault_unique ON TABLE vault FIELDS agent_id, name UNIQUE;
