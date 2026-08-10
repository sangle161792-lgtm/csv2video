# YAML schema
An episode declares render metadata and ordered shots. A shot has semantic `camera`, `environment`, optional dialogue and actions. Durations are seconds or `auto`; auto uses measured voice length plus handles. Supported actions: `idle`, `blink`, `look_up`, `jump`, `talk`, `proud`, `surprised`, `enter`, `exit`. Validation reports the exact YAML path.
