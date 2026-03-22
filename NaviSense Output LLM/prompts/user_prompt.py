def build_user_prompt(task: dict) -> str:
    buoy_list = ", ".join(f'"{b}"' for b in task["buoys"])
    return f"""Plan the "{task['name']}" task. Output a single JSON object. No explanation.
You MUST only use these exact object ids: {buoy_list}. No other ids are valid.
If multiple objects are [estimated], group them ALL into one single SearchPattern step.

The following is a FORMAT EXAMPLE ONLY. Do not copy node names or ids from it.
{{
  "ts": [
    {{
      "t": "task_name",
      "s": [
        {{
          "n": "NodeName",
          "i": {{"ids": ["object_id"]}}
        }}
      ]
    }}
  ]
}}"""