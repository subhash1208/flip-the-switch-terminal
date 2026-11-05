# Agent plugins

## Purpose

This page explains how team members install the agent plugins for GitHub Copilot CLI (the primary tool) and Claude Code (used by some members). It lists where each plugin comes from and which Claude Code install commands have been verified.

## Copilot CLI install

Install each plugin with the command in the table. For marketplace plugins, add the marketplace once, then install the plugin.

Equivalent interactive commands inside a Copilot CLI session:

- `/plugin marketplace add <owner/repo>`
- `/plugin install <plugin>@<marketplace>`

Check what is installed with `copilot plugin list`.

| Plugin | Source | Command |
| --- | --- | --- |
| superpowers | obra/superpowers (direct repo install) | `copilot plugin install obra/superpowers` |
| mattpocock-skills | mattpocock/skills (direct repo install) | `copilot plugin install mattpocock/skills` |
| andrej-karpathy-skills | forrestchang/andrej-karpathy-skills (direct repo install) | `copilot plugin install forrestchang/andrej-karpathy-skills` |
| insecure-defaults | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/insecure-defaults` |
| differential-review | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/differential-review` |
| property-based-testing | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/property-based-testing` |
| mutation-testing | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/mutation-testing` |
| static-analysis | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/static-analysis` |
| sharp-edges | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/sharp-edges` |
| regression-hunt | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/regression-hunt` |
| supply-chain-risk-auditor | trailofbits/skills, plugin subpath | `copilot plugin install trailofbits/skills:plugins/supply-chain-risk-auditor` |
| pstack | marketplace balazstasi/pstack-copilot | `copilot plugin marketplace add balazstasi/pstack-copilot` then `copilot plugin install pstack@pstack-copilot` |
| caveman | marketplace JuliusBrussee/caveman | `copilot plugin marketplace add JuliusBrussee/caveman` then `copilot plugin install caveman@caveman` |
| ponytail | marketplace DietrichGebert/ponytail | `copilot plugin marketplace add DietrichGebert/ponytail` then `copilot plugin install ponytail@ponytail` |
| paad | marketplace Ovid/paad | `copilot plugin marketplace add Ovid/paad` then `copilot plugin install paad@paad` |

Notes:

- The three direct repo installs (superpowers, mattpocock-skills, andrej-karpathy-skills) work, but Copilot CLI warns that direct plugin installs are deprecated. Prefer a marketplace install if one is published for the plugin. See Troubleshooting.
- The Trail of Bits plugins are installed from subpaths of one repo. Install them one at a time. See Troubleshooting.
- Ponytail's Copilot CLI slash commands are `/ponytail:ponytail` and `/ponytail-review`.

## Claude Code install

Claude Code plugins are installed from inside a Claude Code session with `/plugin`. Only the rows marked **verified** were checked against the upstream READMEs. For rows marked **unverified**, check the upstream README for the current command before you run anything. Do not guess the command.

Run each `/plugin marketplace add` and `/plugin install` as a separate prompt.

| Plugin | Status | Claude Code command |
| --- | --- | --- |
| caveman | verified | `/plugin marketplace add JuliusBrussee/caveman`, then `/plugin install caveman@caveman` |
| ponytail | verified | `/plugin marketplace add DietrichGebert/ponytail`, then `/plugin install ponytail@ponytail` (send as two separate prompts) |
| paad | verified | `/plugin marketplace add Ovid/paad`, then `/plugin install paad@paad`, then `/reload-plugins` |
| superpowers | unverified | Claude Code install: unverified, check the upstream README (obra/superpowers) |
| mattpocock-skills | unverified | Claude Code install: unverified, check the upstream README (mattpocock/skills) |
| andrej-karpathy-skills | unverified | Claude Code install: unverified, check the upstream README (forrestchang/andrej-karpathy-skills) |
| insecure-defaults | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| differential-review | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| property-based-testing | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| mutation-testing | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| static-analysis | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| sharp-edges | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| regression-hunt | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| supply-chain-risk-auditor | unverified | Claude Code install: unverified, check the upstream README (trailofbits/skills) |
| pstack | unverified | Claude Code install: unverified, check the upstream README (balazstasi/pstack-copilot) |

## Local repo skills

These skills are kept in the repo, not installed from a plugin. They stay in place after the plugin deduplication.

Skills in `.claude/skills/` (one folder each, each with a `SKILL.md`):

- `content-producer-skill`
- `html-slides`
- `pptx`
- `pptx-slides`
- `slide-design`
- `technical-article-writer`
- `technical-writing-best-practices`
- `video-production`

Repo-local commands in `.github/skills/`: `/plan`, `/review`, `/remember`. These are not plugins and do not need installing.

## Updating plugins

Copilot CLI: update a single plugin by name.

```
copilot plugin update <name>
```

Claude Code: open `/plugin` and use the **Installed** tab to see installed plugins and update them there.

## Troubleshooting

**"Direct plugin installs are deprecated" warning (Copilot CLI).** Copilot CLI prints this when a plugin is installed straight from a repo. The install still works. To remove the warning, use a marketplace install for that plugin where one exists: `copilot plugin marketplace add <owner/repo>`, then `copilot plugin install <plugin>@<marketplace>`.

**Git-cache lock error when installing Trail of Bits plugins (Copilot CLI).** The Trail of Bits plugins share one repo, and installing several at once can fail with a git-cache lock error. Install one plugin at a time, and wait for each install to finish before starting the next. If the error persists, run `copilot plugin list` to see what was installed before retrying.
