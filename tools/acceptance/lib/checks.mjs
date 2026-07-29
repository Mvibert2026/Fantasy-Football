/**
 * Every check here cross-references rendered text/DOM against the real
 * data/export/*.json files (ground truth). None of them compare against a
 * stored image or a stored "last known good" snapshot -- a false claim that
 * was already wrong the first time a baseline was captured would pass a
 * pixel diff forever. These checks compare against the current, real data,
 * every run.
 */

function result(name, ok, expected, actual, detail) {
  return { name, ok, expected, actual, detail };
}

/** Fault #4 target: the Prep/Draft/Season mode switcher must be present and
 *  reflect the active mode once the app has finished loading. */
export async function checkModeSwitcher(page) {
  const labels = ['Prep', 'Draft', 'Season'];
  const states = [];
  for (const label of labels) {
    const btn = page.getByRole('button', { name: label, exact: true });
    const count = await btn.count();
    if (count === 0) {
      return result(
        'mode-switcher-present',
        false,
        `buttons for ${labels.join(', ')} all present`,
        `"${label}" button not found`,
        'The Prep/Draft/Season mode switcher is missing from the loaded state.',
      );
    }
    const pressed = await btn.first().getAttribute('aria-pressed');
    states.push({ label, pressed: pressed === 'true' });
  }
  const pressedCount = states.filter((s) => s.pressed).length;
  if (pressedCount !== 1) {
    return result(
      'mode-switcher-present',
      false,
      'exactly one mode marked active (aria-pressed=true)',
      `${pressedCount} active: ${JSON.stringify(states)}`,
      'Mode switcher is present but its active-state marking is wrong.',
    );
  }
  return result('mode-switcher-present', true, 'all three modes present, one active', JSON.stringify(states), null);
}

/** Fault #3 target: the league name shown in the top bar switcher must equal
 *  data/export/league.json's real league_name, not a hardcoded placeholder. */
export async function checkLeagueName(page, groundTruth) {
  const select = page.locator('select[aria-label="Select league"]');
  if ((await select.count()) === 0) {
    return result('league-name-matches-config', false, groundTruth.league.league_name, '(select not found)', null);
  }
  const shownName = await select.evaluate((el) => el.options[el.selectedIndex]?.text ?? null);
  const expected = groundTruth.league.league_name;
  const ok = shownName === expected;
  return result(
    'league-name-matches-config',
    ok,
    expected,
    shownName,
    ok ? null : `League switcher shows "${shownName}" but data/export/league.json:league_name is "${expected}".`,
  );
}

/** Fault #1 target: the board header's provenance line states "N of TOTAL
 *  players loaded" -- TOTAL must equal the real player count in board.json,
 *  not a hardcoded figure that can drift as the export grows or shrinks. */
export async function checkPlayerCountHeader(page, groundTruth) {
  const text = await page.locator('body').innerText();
  const m = text.match(/(\d+)\s+of\s+(\d+)\s+players loaded/);
  if (!m) {
    return result('board-header-player-count', false, 'a "N of TOTAL players loaded" line', '(not found)', null);
  }
  const [, loaded, total] = m.map(Number);
  const expected = groundTruth.playerCount;
  const ok = total === expected && loaded === expected;
  return result(
    'board-header-player-count',
    ok,
    `${expected} of ${expected}`,
    `${loaded} of ${total}`,
    ok
      ? null
      : `Header claims ${total} total players; data/export/board.json actually has ${expected} player rows.`,
  );
}

/** Fault #5 target (and a second angle on #1): the board's own "N players"
 *  footer count, and the absence of the empty-filter state, at the default
 *  ALL-position filter on first load. */
export async function checkBoardRowsRendered(page, groundTruth) {
  const emptyState = page.getByText('Nothing matches these filters.');
  const isEmpty = (await emptyState.count()) > 0;

  const footerText = await page.getByText(/^\d+ players$/).first().innerText().catch(() => null);
  const footerCount = footerText ? Number(footerText.match(/^(\d+) players$/)[1]) : null;

  const expected = groundTruth.playerCount;
  const ok = !isEmpty && footerCount === expected && expected > 0;

  return result(
    'board-renders-nonzero-rows',
    ok,
    `${expected} players, no empty-state message`,
    isEmpty ? 'empty-state message shown' : `${footerCount} players shown`,
    ok
      ? null
      : isEmpty
        ? 'Board shows "Nothing matches these filters." on the default, unfiltered ALL tab despite the export having real players.'
        : `Board's own player-count footer (${footerCount}) does not match data/export/board.json (${expected}).`,
  );
}

/** Fault #2 target: the freshness/status banner's STALE-vs-fresh claim and
 *  its age figures must match board.json's own snapshot_stale /
 *  snapshot_age_days / snapshot_max_age_days fields. */
export async function checkStatusBanner(page, groundTruth) {
  const banner = page.locator('[data-testid="freshness-note"]');
  if ((await banner.count()) === 0) {
    return result('status-banner-matches-data', false, 'freshness-note banner present', '(not found)', null);
  }
  const text = await banner.innerText();
  const { snapshot_stale, snapshot_age_days, snapshot_max_age_days } = groundTruth.board;
  const hasFreshness = snapshot_stale !== undefined && snapshot_age_days !== undefined && snapshot_max_age_days !== undefined
    && snapshot_stale !== null && snapshot_age_days !== null && snapshot_max_age_days !== null;

  if (!hasFreshness) {
    const ok = /snapshot freshness not exported by backend/.test(text);
    return result(
      'status-banner-matches-data',
      ok,
      'banner states freshness is not exported (board.json carries no snapshot_stale field)',
      text,
      ok ? null : 'board.json has no freshness fields, but the banner claims a freshness value anyway.',
    );
  }

  const m = text.match(/snapshot (STALE|fresh) \((\d+)d old, max (\d+)d\)/);
  if (!m) {
    return result('status-banner-matches-data', false, 'a parseable "snapshot STALE|fresh (Xd old, max Yd)" claim', text, null);
  }
  const [, staleWord, ageStr, maxStr] = m;
  const shownStale = staleWord === 'STALE';
  const ok = shownStale === Boolean(snapshot_stale) && Number(ageStr) === snapshot_age_days && Number(maxStr) === snapshot_max_age_days;

  const expected = `${snapshot_stale ? 'STALE' : 'fresh'} (${snapshot_age_days}d old, max ${snapshot_max_age_days}d)`;
  const actual = `${staleWord} (${ageStr}d old, max ${maxStr}d)`;
  return result(
    'status-banner-matches-data',
    ok,
    expected,
    actual,
    ok ? null : `Status banner claims "${actual}" but board.json says "${expected}".`,
  );
}

export const ALL_CHECKS = [
  checkModeSwitcher,
  checkLeagueName,
  checkPlayerCountHeader,
  checkBoardRowsRendered,
  checkStatusBanner,
];
