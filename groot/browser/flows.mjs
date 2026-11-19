// Groot's click-through tests. Started by groot/browser_run.py against a throwaway local server.
// Everything created here (accounts, the "Groot Test Family", the "Groot Village" community) lives
// in a temporary database that is deleted afterwards.
import { chromium } from '../../web/node_modules/playwright-core/index.mjs'
import fs from 'node:fs'
import path from 'node:path'

const URL = process.env.GROOT_URL
const REPORTS = process.env.GROOT_REPORTS
const tokens = JSON.parse(fs.readFileSync(process.env.GROOT_TOKENS, 'utf8'))
const browser = await chromium.launch({ executablePath: process.env.GROOT_BROWSER, headless: true })

const problems = [] // things that went wrong inside the browser, whatever the step was
let failures = 0
let passes = 0
let shots = 0

async function person(key, viewport = { width: 1280, height: 860 }) {
  const ctx = await browser.newContext({ viewport })
  ctx.setDefaultTimeout(9000)
  await ctx.addCookies([
    { name: 'kinship_access', value: tokens[key].access, url: URL + '/api/' },
    { name: 'kinship_refresh', value: tokens[key].refresh, url: URL + '/api/' },
  ])
  const page = await ctx.newPage()
  page.on('pageerror', (e) => problems.push(`${key}: page error: ${e.message}`))
  page.on('console', (m) => {
    if (m.type() === 'error' && !/favicon|Failed to load resource: the server responded with a status of (401|403|404|409|400)/.test(m.text())) {
      problems.push(`${key}: console error: ${m.text().slice(0, 200)}`)
    }
  })
  page.on('response', (r) => {
    if (r.status() >= 500) problems.push(`${key}: server error ${r.status()} on ${r.request().method()} ${r.url().replace(URL, '')}`)
  })
  page.on('requestfailed', (r) => {
    if (!/net::ERR_ABORTED/.test(r.failure()?.errorText ?? '')) problems.push(`${key}: request failed ${r.url().replace(URL, '')}`)
  })
  page.key = key
  return page
}

async function api(key, method, p, body) {
  const r = await fetch(URL + p, {
    method,
    headers: { Authorization: `Bearer ${tokens[key].access}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  const raw = await r.text()
  let json = null
  try {
    json = raw ? JSON.parse(raw) : null
  } catch {
    /* not JSON: leave null, the status tells the story */
  }
  return { status: r.status, json }
}

async function shot(page, name) {
  try {
    await page.screenshot({ path: path.join(REPORTS, `${String(++shots).padStart(2, '0')}-${name}.jpg`), type: 'jpeg', quality: 55 })
  } catch {
    /* the page may already be gone */
  }
}

async function step(name, fn, page) {
  try {
    await fn()
    passes++
    console.log(`PASS ${name}`)
    return true
  } catch (e) {
    failures++
    console.log(`FAIL ${name}\n     ${String(e.message ?? e).split('\n').slice(0, 4).join('\n     ')}`)
    if (page) await shot(page, `FAILED-${name.replace(/\W+/g, '-').slice(0, 40)}`)
    return false
  }
}

const expect = (cond, msg) => {
  if (!cond) throw new Error(msg)
}
const text = (page) => page.locator('body').innerText()
const settle = (page) => page.waitForLoadState('networkidle').catch(() => {})
const today = () => new Date().toLocaleDateString('en-CA')

async function addPerson(page, { first, last, gender = 'male', relation }) {
  await page.getByRole('button', { name: 'Add person' }).first().click()
  const form = page.locator('form')
  await form.getByLabel(/First name/).fill(first)
  await form.getByLabel(/Last name/).fill(last)
  const toggle = form.getByRole('button', { name: /^Gender:/ })
  if ((await toggle.getAttribute('aria-label')).includes(`Gender: ${gender === 'male' ? 'Female' : 'Male'}`)) await toggle.click()
  if (relation) {
    await form.getByLabel('Relationship type').selectOption({ label: relation.type })
    await form.getByLabel('Related person').selectOption({ label: relation.of })
  }
  await form.getByRole('button', { name: 'Add person' }).click()
  await page.locator('.modal-backdrop').waitFor({ state: 'detached' })
  await settle(page)
}

const openPerson = async (page, first) => {
  await page.getByText(first, { exact: true }).first().click()
  await page.getByRole('complementary').waitFor()
}

let treeId, memberTreeId, communityId

// ─────────────────────────────────────────────────────────────── the owner builds a family
const owner = await person('owner')

await step('a new account sees the empty families page', async () => {
  await owner.goto(URL + '/', { waitUntil: 'networkidle' })
  expect((await text(owner)).includes('Your families'), 'no "Your families" heading')
  await shot(owner, 'home-empty')
}, owner)

await step('create a family', async () => {
  await owner.getByRole('button', { name: /Create a family/ }).first().click()
  await owner.getByPlaceholder('e.g. The Sadasivam family').fill('Groot Test Family')
  await owner.getByRole('button', { name: 'Create family' }).click()
  await owner.waitForURL(/\/trees\/\d+/)
  treeId = Number(owner.url().match(/trees\/(\d+)/)[1])
}, owner)

await step('add the first person', async () => {
  await owner.getByRole('button', { name: 'Add the first person' }).click()
  const form = owner.locator('form')
  await form.getByLabel(/First name/).fill('Grace')
  await form.getByLabel(/Last name/).fill('Groot')
  await form.getByRole('button', { name: 'Add person' }).click()
  await owner.locator('.modal-backdrop').waitFor({ state: 'detached' })
  await settle(owner)
  expect(/1\s*person/.test(await text(owner)), 'the tree should say 1 person')
}, owner)

await step('add a father through the relationship picker', async () => {
  await addPerson(owner, { first: 'Gus', last: 'Groot', relation: { type: 'Father', of: 'Grace Groot' } })
  const t = await text(owner)
  expect(/2\s*people/.test(t), 'the tree should say 2 people')
  expect(/2\s*generations/.test(t), 'father and child should make 2 generations')
}, owner)

await step('add a wife for the father (gender switch)', async () => {
  await addPerson(owner, { first: 'Gwen', last: 'Groot', gender: 'female', relation: { type: 'Wife', of: 'Gus Groot' } })
  expect(/3\s*people/.test(await text(owner)), 'the tree should say 3 people')
}, owner)

await step('a pair that is already connected cannot be connected again', async () => {
  await openPerson(owner, 'Gus')
  const panel = owner.getByRole('complementary')
  const t = await panel.innerText()
  expect(/Grace/.test(t) && /Gwen/.test(t), 'Gus should list his son and his wife')
  // Gus is already linked to both other people, so the connect area has nobody left to offer.
  expect(/already connected to everyone else/i.test(t), 'the panel should say Gus is already connected to everyone')
  await shot(owner, 'tree-three-people')
}, owner)

await step('a person with children cannot be deleted', async () => {
  const t = await owner.getByRole('complementary').innerText()
  expect(/has children in the family/i.test(t), 'the panel should explain why Gus cannot be deleted')
  expect(await owner.getByRole('complementary').getByRole('button', { name: 'Delete' }).isDisabled(), 'the Delete button should be disabled')
}, owner)

await step('editing a person: phone, email, address start hidden; the eye turns one on', async () => {
  await openPerson(owner, 'Grace')
  await owner.getByRole('complementary').getByRole('button', { name: 'Edit', exact: true }).click()
  const form = owner.locator('form')
  await form.getByRole('textbox', { name: 'Phone number' }).fill('555-0199')
  await form.getByRole('textbox', { name: 'Email address' }).fill('grace@example.test')
  await form.getByRole('textbox', { name: 'Address', exact: true }).fill('1 Test Lane')
  for (const what of ['phone number', 'email address', 'address']) {
    expect(await form.getByRole('button', { name: `Show ${what} to others` }).count() === 1, `${what} should start hidden`)
  }
  await form.getByRole('button', { name: 'Show phone number to others' }).click()
  expect(await form.getByRole('button', { name: 'Hide phone number from others' }).count() === 1, 'the eye should switch to open')
  await shot(owner, 'edit-person-eyes')
  await form.getByRole('button', { name: 'Save changes' }).click()
  await owner.locator('.modal-backdrop').waitFor({ state: 'detached' })
  await settle(owner)
  const t = await owner.getByRole('complementary').innerText()
  expect(/Phone 555-0199 · public/.test(t), `phone should show as public, panel says: ${t.slice(0, 300)}`)
  expect(/Email grace@example.test · private/.test(t), 'email should show as private')
  expect(/Address 1 Test Lane · private/.test(t), 'address should show as private')
}, owner)

await step('the birth-date box does not allow future dates', async () => {
  await owner.getByRole('complementary').getByRole('button', { name: 'Edit', exact: true }).click()
  const max = await owner.locator('form input[type=date]').getAttribute('max')
  expect(max === today(), `max should be today (${today()}) but is ${max}`)
  await owner.getByRole('button', { name: 'Cancel' }).click()
  await owner.locator('.modal-backdrop').waitFor({ state: 'detached' })
}, owner)

await step('a person with no children can be deleted, and undone', async () => {
  await addPerson(owner, { first: 'Temp', last: 'Person', relation: { type: 'Brother', of: 'Grace Groot' } })
  expect(/4\s*people/.test(await text(owner)), 'should be 4 people')
  await openPerson(owner, 'Temp')
  await owner.getByRole('complementary').getByRole('button', { name: 'Delete', exact: true }).click()
  await owner.getByText('Deleted Temp Person').waitFor()
  await owner.waitForFunction(() => /3\s*people/.test(document.body.innerText))
  await owner.getByRole('button', { name: 'Undo' }).click()
  await owner.waitForFunction(() => /4\s*people/.test(document.body.innerText))
  await openPerson(owner, 'Temp')
  await owner.getByRole('complementary').getByRole('button', { name: 'Delete', exact: true }).click()
  await owner.waitForFunction(() => /3\s*people/.test(document.body.innerText))
}, owner)

// ─────────────────────────────────────────────────────────────── profile
await step('profile: the eye buttons start hidden, toggle, and are remembered after a reload', async () => {
  await owner.goto(URL + '/profile', { waitUntil: 'networkidle' })
  const eye = owner.getByRole('button', { name: 'Show email address to others' })
  expect(await eye.count() === 1, 'email eye should start hidden')
  await eye.click()
  await owner.getByRole('button', { name: 'Hide email address from others' }).waitFor()
  await owner.reload({ waitUntil: 'networkidle' })
  expect(await owner.getByRole('button', { name: 'Hide email address from others' }).count() === 1, 'the open eye should survive a reload')
  await shot(owner, 'profile-eyes')
  await owner.getByRole('button', { name: 'Hide email address from others' }).click()
  await owner.getByRole('button', { name: 'Show email address to others' }).waitFor()
}, owner)

// ─────────────────────────────────────────────────────────────── a second person joins the family
const member = await person('member')
const outsider = await person('outsider')

await step('a member joins the family with a code and the owner approves it', async () => {
  const code = await api('owner', 'POST', '/api/family-codes/generate/', { tree_id: treeId })
  expect(code.status === 201, `could not make a code: ${code.status}`)
  await member.goto(URL + '/', { waitUntil: 'networkidle' })
  await member.getByRole('button', { name: /Join with a code/ }).first().click()
  const dialog = member.getByRole('dialog')
  await dialog.locator('input').first().fill(code.json.code)
  await dialog.getByRole('button', { name: 'Request to join' }).click()
  await dialog.getByText(/Request sent|joined/i).first().waitFor()
  const pending = await api('owner', 'GET', `/api/join-requests/?tree_id=${treeId}`)
  const req = (Array.isArray(pending.json) ? pending.json : pending.json?.results ?? []).find((r) => r.status === 'pending')
  if (!req) {
    const mineNow = await api('member', 'GET', '/api/family-trees/')
    if (!mineNow.json?.some((t) => t.id === treeId)) {
      throw new Error(`no pending request and the member is not in the family. Requests: ${JSON.stringify(pending.json).slice(0, 200)}. Member screen: ${(await text(member)).slice(0, 200)}`)
    }
  } else {
    // the page the owner's email links to
    await owner.goto(`${URL}/approve/tree/${req.id}`, { waitUntil: 'networkidle' })
    expect(/Mia Member/.test(await text(owner)), 'the approve page should name the person asking')
    await owner.getByRole('button', { name: 'Approve' }).click()
    await owner.getByText(/Approved/).first().waitFor()
  }
  const mine = await api('member', 'GET', '/api/family-trees/')
  expect(mine.json.some((t) => t.id === treeId), 'the member should now see the family')
}, owner)

await step('the member sees the family, the public phone, and none of the private details', async () => {
  await member.goto(`${URL}/trees/${treeId}`, { waitUntil: 'networkidle' })
  await openPerson(member, 'Grace')
  const t = await member.getByRole('complementary').innerText()
  expect(/555-0199/.test(t), 'Grace\'s public phone should be visible to the member')
  expect(!/grace@example\.test/.test(t), 'Grace\'s private email must not be shown to the member')
  expect(!/1 Test Lane/.test(t), 'Grace\'s private address must not be shown to the member')
  await shot(member, 'member-view-of-family')
}, member)

await step('the member has no Delete buttons', async () => {
  expect((await member.getByRole('button', { name: 'Delete' }).count()) === 0, 'a plain member must not see Delete')
}, member)

await step('someone outside the family cannot open it', async () => {
  await outsider.goto(`${URL}/trees/${treeId}`, { waitUntil: 'networkidle' })
  const t = await text(outsider)
  expect(!/Grace|Gus|Gwen/.test(t), 'the outsider must not see anyone from the family')
  const direct = await api('outsider', 'GET', `/api/family-members/?tree_id=${treeId}`)
  expect(direct.status === 403, `the API should refuse the outsider (got ${direct.status})`)
  await shot(outsider, 'outsider-turned-away')
}, outsider)

// ─────────────────────────────────────────────────────────────── communities
await step('create a community, and the top button says "Communities" / "Families"', async () => {
  await owner.goto(URL + '/', { waitUntil: 'networkidle' })
  await owner.getByRole('link', { name: 'Communities', exact: true }).click()
  await owner.waitForURL(/\/communities$/)
  await owner.getByRole('heading', { name: /communities/i }).first().waitFor()
  expect(await owner.locator('header').getByRole('link', { name: 'Families', exact: true }).count() === 1, 'on the communities page the top button should say Families')
  await owner.getByRole('button', { name: /New community/ }).click()
  await owner.getByPlaceholder('e.g. Riverside Village').fill('Groot Village')
  await owner.getByRole('button', { name: 'Create community' }).click()
  await owner.getByText('Groot Village').first().waitFor()
  await owner.getByText('Groot Village').first().click()
  await owner.waitForURL(/\/communities\/\d+/)
  communityId = Number(owner.url().match(/communities\/(\d+)/)[1])
}, owner)

await step('the owner shares the family with the community', async () => {
  const card = owner.locator('.request', { hasText: 'Groot Test Family' })
  await card.getByRole('button', { name: 'Share' }).click()
  await owner.getByText('Stop sharing').first().waitFor()
  await owner.getByText('Grace Groot').first().waitFor()
  await shot(owner, 'community-owner')
}, owner)

await step('a member asks to join and picks which of their families to add', async () => {
  // the member's own family, made through the screens
  await member.goto(URL + '/', { waitUntil: 'networkidle' })
  await member.getByRole('button', { name: /Create a family/ }).first().click()
  await member.getByPlaceholder('e.g. The Sadasivam family').fill('Mia Family')
  await member.getByRole('button', { name: 'Create family' }).click()
  await member.waitForURL(/\/trees\/\d+/)
  memberTreeId = Number(member.url().match(/trees\/(\d+)/)[1])
  await member.getByRole('button', { name: 'Add the first person' }).click()
  const form = member.locator('form')
  await form.getByLabel(/First name/).fill('Mia')
  await form.getByLabel(/Last name/).fill('Member')
  await form.getByRole('button', { name: /^Gender:/ }).click() // female
  await form.getByRole('button', { name: 'Add person' }).click()
  await member.locator('.modal-backdrop').waitFor({ state: 'detached' })
  await settle(member)

  await member.goto(URL + '/communities', { waitUntil: 'networkidle' })
  await member.getByPlaceholder(/at least 2 letters/).fill('Groot')
  const row = member.locator('.request', { hasText: 'Groot Village' })
  await row.getByRole('button', { name: 'Join' }).click()
  const pick = row.getByLabel('Which family to add')
  const options = await pick.locator('option').allInnerTexts()
  expect(options.includes('Mia Family'), `the dropdown should list Mia Family, it lists: ${options.join(', ')}`)
  expect(options.includes('No family yet'), 'the dropdown should offer "No family yet"')
  await shot(member, 'join-dropdown')
  await row.getByRole('button', { name: 'Send request' }).click()
  await row.getByText('Request sent').waitFor()
}, member)

await step('the owner approves from the emailed link and the family is shared automatically', async () => {
  const reqs = await api('owner', 'GET', `/api/communities/${communityId}/requests/`)
  expect(reqs.json.length === 1 && reqs.json[0].tree_name === 'Mia Family', 'the owner should see the offered family in the request')
  await owner.goto(`${URL}/approve/community/${reqs.json[0].id}`, { waitUntil: 'networkidle' })
  const t = await text(owner)
  expect(/Mia Member/.test(t) && /Mia Family/.test(t), 'the approve page should name the person and the family')
  await owner.getByRole('button', { name: 'Approve' }).click()
  await owner.getByText(/Approved/).first().waitFor()
  const mine = await api('member', 'GET', `/api/communities/${communityId}/`)
  expect(mine.json.my_trees.find((x) => x.id === memberTreeId)?.shared === true, 'Mia Family should be shared once approved')
}, owner)

await step('community search: name, gender and age filters; only living people; no private details', async () => {
  await member.goto(`${URL}/communities/${communityId}`, { waitUntil: 'networkidle' })
  const list = () => member.locator('.person-row').allInnerTexts()
  const names = (await list()).join(' ')
  expect(/Grace/.test(names) && /Gus/.test(names) && /Gwen/.test(names) && /Mia/.test(names), `everyone shared should be listed: ${names}`)
  expect(!/Temp/.test(names), 'a deleted person must not be listed')
  expect(!/Deceased|Status/.test(await text(member)), 'the community search has no Deceased/Status option any more')
  await member.getByPlaceholder('Search by name').fill('Gus')
  await member.waitForFunction(() => document.querySelectorAll('.person-row').length === 1)
  await member.getByPlaceholder('Search by name').fill('')
  await member.getByRole('button', { name: 'Women', exact: true }).click()
  await member.waitForFunction(() => [...document.querySelectorAll('.person-row')].every((r) => /Gwen|Mia/.test(r.innerText)) && document.querySelectorAll('.person-row').length === 2)
  await member.getByRole('button', { name: 'Men', exact: true }).click()
  await member.waitForFunction(() => [...document.querySelectorAll('.person-row')].every((r) => /Gus|Grace/.test(r.innerText)) && document.querySelectorAll('.person-row').length === 2)
  const page = await text(member)
  expect(!/grace@example\.test|1 Test Lane/.test(page), 'private details must not appear in the community')
  expect(/555-0199/.test(page), 'the public phone number should appear in the community')
  await shot(member, 'community-search')
}, member)

await step('a stranger cannot read the community', async () => {
  const r = await api('outsider', 'GET', `/api/communities/${communityId}/people/`)
  expect(r.status === 404, `expected 404 for a non-member, got ${r.status}`)
}, outsider)

// ─────────────────────────────────────────────────────────────── small screens and sign-out
const phone = await person('owner', { width: 360, height: 800 })
await step('on a small phone screen (360px wide) nothing slides sideways', async () => {
  for (const p of ['/', '/profile', '/communities', `/communities/${communityId}`]) {
    await phone.goto(URL + p, { waitUntil: 'networkidle' })
    const over = await phone.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    if (over > 1) {
      const who = await phone.evaluate(() =>
        [...document.querySelectorAll('body *')]
          .filter((el) => {
            if (el.getBoundingClientRect().right <= window.innerWidth + 1) return false
            for (let a = el.parentElement; a && a !== document.documentElement; a = a.parentElement) {
              const o = getComputedStyle(a)
              if (o.overflowX !== 'visible' || o.position === 'fixed') return false // clipped, or not part of the page flow
            }
            return getComputedStyle(el).position !== 'fixed'
          })
          .slice(0, 4)
          .map((el) => `${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} (${Math.round(el.getBoundingClientRect().right)}px)`),
      )
      throw new Error(`${p} is ${over}px wider than the screen. Wide parts: ${who.join(', ')}`)
    }
  }
  await shot(phone, 'phone-community')
}, phone)

await step('the profile menu signs you out', async () => {
  await outsider.goto(URL + '/', { waitUntil: 'networkidle' })
  await outsider.locator('.menu-wrap button').first().click()
  await outsider.getByRole('menuitem', { name: /Sign out/ }).or(outsider.getByRole('button', { name: /Sign out/ })).first().click()
  await outsider.waitForURL(/\/login/)
  await shot(outsider, 'signed-out')
}, outsider)

await step('no browser errors and no server errors happened during the whole run', async () => {
  expect(problems.length === 0, `${problems.length} problem(s):\n     ${[...new Set(problems)].slice(0, 6).join('\n     ')}`)
})

await browser.close()
console.log(`\n${passes} passed, ${failures} failed`)
process.exit(failures ? 1 : 0)
