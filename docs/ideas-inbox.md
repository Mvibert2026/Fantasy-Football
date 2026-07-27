# Ideas inbox

**Append-only. PM-owned. Not a thread, not read by any tooling.**

Raw founder ideas land here the moment they are said, unprocessed, in his words. Nothing is shaped,
scoped or converted at capture time — that happens in batch at a session reset
(`docs/session-reset-protocol.md`).

**Why this file exists.** On 2026-07-27 the PM converted each founder remark into a thread on arrival
and produced twelve threads in an hour with at least eight overlapping pairs. The cause was not a
missing check — it was converting immediately, so no idea was ever seen next to its siblings. Batching
is the fix. You cannot deduplicate an idea against nothing.

**Safety by construction.** No IDs. No frontmatter. No cross-references. Nothing here is parsed by
`tools/handoffs.py` or read by any agent. Appending to this file cannot collide with an agent, cannot
break the mailbox, and cannot corrupt the index. That is deliberate — the capture step must be
zero-risk or the PM will hesitate to use it.

**Exception — defects bypass this file.** A bug the founder observes in the running app goes straight
to a thread. It is time-sensitive, self-contained, and there is no deduplication value in holding it.
Ideas buffer; defects go through.

## Status vocabulary

| Tag | Meaning |
|---|---|
| `RAW` | Captured, not yet reviewed. |
| `→ NNN` | Converted to thread NNN. |
| `FOLDED INTO NNN` | Merged into an existing thread rather than given its own. |
| `DECLINED — <reason>` | Considered and not doing it. **The reason is mandatory.** Without it the idea gets silently dropped and re-raised weeks later as though it were new. |
| `PARKED — <condition>` | Good, blocked on something. Name the unblocking condition. |

---

## 2026-07-27

*(Ideas from this session were converted directly to threads before this file existed. Recorded here
for continuity — see `docs/handoffs/RECONCILIATION-2026-07.md` for their dispositions.)*

- Follow news hype and ADP movement toward draft date — `→ 059`, `→ 057`
- Injury duration, recovery ramp-up in rankings — `→ 057`, Fable mandate Addendum 2
- Off-field issues and suspension probability — `→ 057`; probability modelling `DECLINED — single-digit
  positive cases per season, no validation set possible; known suspensions handled deterministically
  instead`
- Bye weeks in roster-aware recommendations — `→ 059`
- Pre-pick recommendations reviewable ahead of the clock — `→ 059` (FR-008)
- Draft-time strategy chatbot — `PARKED — depends on 059 and 049`  (FR-006)
- Every pick triggers recomputation — `→ 060`
- FantasyPros recommendation percentages — `→ 061`
- Table stakes must all be covered — `→ FR-007`, Fable mandate Priority 2A
