# Tech Stack Tracking & CVE Alerts — Design Doc

Status: **Phase 1 shipped, differently than originally specced below.**
This doc originally assumed account-based server-side tracking with
in-app/email notifications. The site doesn't offer login/registration right
now, so Phase 1 instead shipped as a **localStorage-based** tracker:
- Stack definitions (name + package list) live only in the browser
  (`frontend/lib/stacks-storage.ts`), with export/import as a JSON file
  for backup/portability — no server-side persistence at all.
- `POST /api/v1/techstack/match` (`backend/api/techstack.py`,
  `TechStackService.match_packages_stateless()`) checks a package list
  against current CVEs and returns matches without saving anything.
- "New since last check" is computed client-side by comparing each match's
  `published_at` against the stack's locally-stored `lastCheckedAt` — no
  push/email infrastructure involved.
- UI: `frontend/app/my-stack/page.tsx`, linked from the main nav.

The account-based version below remains a reasonable **Phase 2/3** if/when
logins return — real push/email delivery needs a real account to send to.
Keeping the original spec for reference.

## Why

Today, `/scan` (`frontend/app/scan/page.tsx`, `backend/api/techstack.py`)
lets a user upload `package.json`/`requirements.txt`/etc., matches it against
known CVEs once, and shows the results. Nothing is watched afterward — if a
new CVE is published next week affecting a package you scanned, you never
hear about it unless you scan again manually. The ask is to make this
continuous: save a stack once, get notified automatically as new CVEs land.

Most of the plumbing for this already exists (data model, matching engine,
notification system, task scheduler, email sender) — this is an integration
project more than a from-scratch build.

## What already exists (reuse, don't rebuild)

| Piece | Where | Reuse as |
|---|---|---|
| Persistent, user-owned stack storage | `TechStack` model, `backend/models.py:820` — has `user_id`, `packages` JSONB, is already saved (not ephemeral) | The tracked-stack record itself. No schema change needed. |
| CVE matching engine | `TechStackService.match_packages_to_cves()`, `backend/services/techstack_service.py:551` | The core "does this stack have a new hit" logic |
| Per-scan match snapshot | `TechStackMatch` model + `scan_tech_stack()`, `techstack_service.py:857` | Needs a behavior change — see [Open Question 1](#open-questions) |
| Notification delivery (in-app) | `create_*_notification()` pattern in `backend/utils/notifications.py`, `Notification` model (`type` is a free-text string, no enum) | Add `create_cve_match_notification()` alongside the existing mention/reply/vote helpers |
| Notification display | `frontend/components/NotificationCenter.tsx` | Renders new `cve_match` notifications automatically, no frontend work needed for Phase 1 |
| Periodic task scheduling | `backend/celery_app.py` `beat_schedule` dict (see `process-new-cves`, `fetch-cisa-kev` entries) | Add one new entry + one new task module, same shape as existing ones |
| Email delivery | `EmailService.send_email()`, `backend/services/email_service.py` (already used for waitlist verification emails) | Reuse for the Phase 2 email digest — note it's `async`, called from a sync Celery task, needs a small bridge (`asyncio.run(...)`) |

## Data model changes

None required for Phase 1. `TechStack.user_id` already exists; the one-shot
scan flow just never uses it to look the stack back up later. Phase 1 is
mostly "start doing that."

## Phase 1 — Persist + in-app notify

1. **Stop scoping stacks to a single scan.** `/scan` already supports
   `session_id` (anonymous) or `user_id` (logged in) ownership on `TechStack`
   — add a "Save & Track" action for logged-in users that keeps the record
   around indefinitely instead of treating it as scan-session scratch data.
   A user can have multiple named stacks (the model already supports
   `name`/`description` per stack).
2. **New Celery task: `tasks.rescan_tracked_stacks`.** Runs on a schedule
   (e.g. every 6 hours, alongside `fetch-nvd-recent`). For every `TechStack`
   with a non-null `user_id`:
   - Re-run `match_packages_to_cves()`.
   - Diff against the stack's existing `TechStackMatch` rows to find *new*
     `(package, cve_id)` pairs — this is the part `scan_tech_stack()`
     doesn't do today (it wipes and rebuilds unconditionally). Rescan needs
     to know what's new to avoid re-notifying on every run.
   - For each new match, call `create_cve_match_notification(db, user, cve,
     package_name)` (new helper, same shape as `create_reply_notification`)
     — dedup-checks for an existing `cve_match` notification for that
     `(user_id, cve_id)` pair before inserting, same pattern as the existing
     helpers.
3. **No frontend changes required** to see notifications — the existing
   `NotificationCenter` bell already polls and renders any `Notification`
   row regardless of `type`. Optionally add a small "why am I seeing this"
   line using the `cve_id` + package name already on the record.

## Phase 2 — Email digest + smarter matching

- Add a `notify_by_email` boolean preference (per stack, or per user) and a
  new `tasks.send_cve_alert_digest` periodic task that batches a user's
  unread `cve_match` notifications since the last digest into one email via
  `EmailService.send_email()`. Batching matters: a widely-used package
  (e.g. `lodash`) getting a new CVE could otherwise fire one email per user
  per CVE with no grouping.
- Move matching from name-only to version-range-aware. Today's
  `match_packages_to_cves()` matches on normalized package/vendor/product
  name against `affected_products` text and assigns a confidence score, but
  doesn't parse CVE version ranges against the user's installed version —
  so a user pinned to a patched version still gets flagged. This is the
  highest-leverage accuracy improvement and the main reason Phase 1 will
  produce some false positives worth tolerating short-term.

## Phase 3 — Integrations & control

- Notification preferences: mute a specific stack, mute below a severity
  threshold, mute a specific noisy package.
- Webhook/Slack delivery as an alternative to email, reusing the same
  diff-and-notify task as the trigger point — just a different delivery
  sink than `email_service`.

## Open Questions

1. **Diffing strategy for `scan_tech_stack()`.** Its current clear-then-rebuild
   behavior is fine for an on-demand manual scan but actively wrong for a
   background rescan (it would delete-and-recreate identical matches every
   run, giving no signal about what's *new*). Recommend adding a
   `rescan_tracked_stack()` variant (or a flag) that upserts instead of
   clearing, and returns the set of newly-created matches for the caller to
   notify on.
2. **Notification frequency limits.** A stack with a popular package (React,
   lodash, OpenSSL) could generate a burst of matches on a single rescan if
   NVD publishes several CVEs for it at once, or if a stack is scanned for
   the first time (existing matches would look "new"). Recommend: on first
   save/track of a stack, snapshot its current matches as a baseline
   *without* notifying, so only genuinely new CVEs (found on subsequent
   rescans) trigger notifications.
3. **Rescan cost at scale.** `match_packages_to_cves()` runs a regex query
   over `Vulnerability.affected_products` per stack (capped at 300 results).
   Fine for the current low count of tracked stacks; if this feature gets
   popular, the periodic task should batch/parallelize across stacks rather
   than looping serially, and possibly dedupe identical package sets across
   users before matching.
