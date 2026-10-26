Delegate to the `memory-updater` agent to consolidate the following into the project's knowledge graph.

**What to save:** $ARGUMENTS

**Instructions for memory-updater:**
1. Use `sequentialthinking` to decide if this is a durable fact worth storing (would a future session pay to rediscover it?).
2. Search the graph first with `search_nodes` using a SHORT keyword — never a long phrase.
3. If the entity already exists, use `add_observations`. If it's new, `create_entities` and wire it to the repo hub.
4. Follow the fixed ontology (Repo, Component, Feature, BugPattern, Investigation, Decision, Process, Config, Rule, Agent).
5. Keep each observation atomic and under 250 characters, prefixed with today's date.
6. If this fact is not durable (one-off status, something the code already says), skip it and say why.
