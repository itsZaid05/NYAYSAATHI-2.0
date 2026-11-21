"""Small decoder schema; full Pydantic limits remain mandatory after generation."""


def decoder_schema(model, data=None):
    raw = model.model_json_schema()
    definitions = raw.get("$defs", {})
    keep = {
        "type",
        "properties",
        "items",
        "required",
        "enum",
        "const",
        "anyOf",
        "description",
    }

    def visit(value):
        if isinstance(value, list):
            return [visit(v) for v in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            name = value["$ref"].rsplit("/", 1)[-1]
            return visit(definitions[name])
        out = {}
        for key, item in value.items():
            if key not in keep:
                continue
            out[key] = (
                {name: visit(child) for name, child in item.items()}
                if key == "properties"
                else visit(item)
            )
        return out

    schema = visit(raw)
    if model.__name__ == "Extracted" and data and data.get("narrative_segments"):
        ids = list(data["narrative_segments"])
        from backend.services.issue_taxonomy import ISSUE_RUBRIC

        review = visit(definitions["IssueReview"])
        review["properties"]["fact_segment_ids"]["items"] = {
            "type": "string",
            "enum": ids,
        }
        schema["properties"]["issue_review"] = {
            "type": "object",
            "properties": {category: review for category in ISSUE_RUBRIC},
            "required": list(ISSUE_RUBRIC),
            "additionalProperties": False,
        }
        schema["properties"]["scope"] = {
            "type": "string",
            "enum": ["consumer", "unsupported", "unclear"],
        }
        schema["required"] = list(
            dict.fromkeys(schema.get("required", []) + ["scope", "issue_review"])
        )
        item = schema["properties"]["issue_details"]["items"]
        item["properties"].pop("fact_quotes", None)
        item["properties"]["fact_segment_ids"] = {
            "type": "array",
            "items": {"type": "string", "enum": ids},
            "minItems": 1,
        }
        item["required"] = list(
            dict.fromkeys(
                item.get("required", []) + ["fact_segment_ids", "evidence_needed"]
            )
        )
        for field in ("parties", "amounts"):
            entity = schema["properties"][field]["items"]
            entity["properties"].pop("quote", None)
            entity["properties"]["segment_id"] = {"type": "string", "enum": ids}
            entity["required"] = list(
                dict.fromkeys(
                    [k for k in entity.get("required", []) if k != "quote"]
                    + ["segment_id"]
                )
            )
    return schema
