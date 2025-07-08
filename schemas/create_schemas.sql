create table contract_versions(
	contract_version_id VARCHAR,
	contract_file_path VARCHAR,
	updated_at TIMESTAMP,
);


create table contract_revisions(
	revision_id VARCHAR,
	contract_version_id VARCHAR, -- foreign key
	contract_meta VARCHAR,
    contract_clause_uuid VARCHAR,
	updated_at TIMESTAMP,
);


create table revision_analyses(
	analysis_id VARCHAR,
    revision_id VARCHAR, -- foreign key
	analysis_summary VARCHAR,
	risk_assessment VARCHAR, -- "L", "M", "H"
	recommended_action VARCHAR, -- "A", "R", or "P"
	suggested_response VARCHAR,
	updated_at TIMESTAMP,
);
