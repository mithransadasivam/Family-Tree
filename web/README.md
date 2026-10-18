# Kinship Web

React + TypeScript (Vite) client for the Kinship Django REST backend (`Family-Tree` repo).
Implements the build plan in `Kinship Web App - Design and Function Doc.md`.

## Where this lives

This folder (`web/`) is the **source** of the Kinship website. It is separate from the Android app
(`app/`) and the Django backend (`config/`, `users/`, ...). The backend serves the *built* site from
`../webapp/`, so `web/` = source you edit, `webapp/` = generated output, do not edit by hand.

## Run

```bash
cd web
npm install
cp .env.example .env     # VITE_API_URL=http://localhost:8000 for a local backend
npm run dev              # http://localhost:5173
```

With no `VITE_GOOGLE_CLIENT_ID`, dev builds show a "Dev sign-in" button, which only works
against a backend whose Google verification is stubbed out.

## Publish a new version

```bash
cd web
npm run build:backend    # builds straight into ../webapp (uses .env.production)
```

Then commit `webapp/` and deploy the backend to Railway. Do not deploy from a plain
`git archive` on Windows (it writes CRLF line endings into `build.sh` and crashes the deploy).

## What is built

| Area | Status |
| --- | --- |
| Google sign-in (GIS) to cookie session, auto-refresh on 401 (`auth.ts`, `LoginPage.tsx`) | built; the Google button is untested without a real client ID |
| Trees: list, create (`TreesPage.tsx`) | built, tested |
| Tree view: pan/zoom, couples drawn side by side with a rings link, children hanging from the pair, every family line shown (in-laws' parents linked to their child), search that pans to the person (`TreeView.tsx`, `graph.ts`) | built, tested |
| Members: add, edit, delete, photo by URL (`MemberForm.tsx`, `DetailPanel.tsx`) | add/edit/delete tested via API; form UI partly tested |
| Relationships: add, edit, remove; 34 canonical types, English picker grouped by category (`TermPicker.tsx`; other-language terms from Android are kept in `relationshipTerms.ts` but not shown); grandparent links drop a generation | built, add/edit tested |
| Top bar: "Create a family" and "Join with a code" dialogs next to Sign out (`FamilyDialogs.tsx`, `Protected.tsx`) | built, tested |
| Add person: First name* + Last name* + a required relationship ("X is the ___ of Y"; none needed for the first person); birth details/photo via Edit; no death fields (`MemberForm.tsx`) | built, tested |
| Root protection: a person with children/grandchildren cannot be deleted (UI disabled + server rule in `family_members/views.py`) | built, tested |
| Relationship rules: one link per pair (no Husband+Brother), no parent/child loops, same family only; enforced by the server (`relationships/rules.py`), and already-connected people are hidden in the pickers | built, tested |
| Cards show first name on top, last name below, then years; long names shrink to fit before they are ever cut off (`cardLines` in `layout.ts`, used by the tree and the poster) | built, tested |
| Relationship labels in the person panel are gendered from either side (Father/Mother, Son/Daughter, Brother/Sister...), inferred from how people were described (`inferGenders` in `graph.ts`) | built, tested |
| Gender (one-click ♂/♀ toggle; starts on Male when adding, "Not set" when editing someone without one): relationship words use it (Son vs Child), and the type picker hides contradictory choices (`family_members` migration 0002, `MemberForm.tsx`, `inferGenders`) | built, tested |
| Undo (10 s) after deleting a person or removing a relationship; the person is re-created with all details and relationships re-linked (`UndoBar.tsx`, `useRestore` in `queries.ts`) | built, tested against Django |
| Poster: print-ready tree as PNG, SVG, PDF (print dialog) or share sheet, light/dark (`PosterDialog.tsx`, `poster.ts`) | built; PNG, preview and print HTML tested, a real print dialog not |
| Manage page (`ManagePage.tsx`): invite codes, require-approval setting, approve/reject join requests, edit history, delete (owner) / leave (member) | built, tested against Django |
| Join a tree by code + "my join requests" (`TreesPage.tsx`) | built; error path tested, a successful request not |
| Responsive layout, loading/error states, SPA deploy config | built; mobile layout and deploy not tested |

## Not built yet (Android has these)

User profile screen and the multi-language relationship terms. Photos are URLs (`photo_url`), as in
Android; there is no upload endpoint.

## How it maps to the backend

- API contract: `src/api.ts` (`ENDPOINTS`) and `src/types.ts` mirror the Django URLs/serializers.
- Relationship direction: `relationship_type_name` says what `member_1` IS to `member_2`
  ("Father": member_1 is member_2's father). The tree classifies types exactly as the Android
  `TreeViewScreen.kt` does (`src/graph.ts`). Siblings/cousins/in-laws are not drawn as edges.
- Auth: Django sets httpOnly `kinship_access` / `kinship_refresh` cookies on `/api/auth/google/`.
  The JWTs in the response body are for Android and ignored here, so page JavaScript never holds a token.

## Backend changes (already made in `Family-Tree`, uncommitted)

- `users/authentication.py`: `CookieJWTAuthentication` (Bearer header still wins, so Android is
  unchanged; cookie-authenticated writes must come from an origin in `WEB_ORIGINS`).
- `users/views.py`, `users/urls.py`: cookies set on login; new `POST /api/auth/refresh/` and
  `POST /api/auth/logout/`; auth disabled on those views so a stale cookie can't block sign-in.
- `relationships/views.py`: new `PATCH /api/relationships/<id>/` (type and members; validates same tree, no self-relation) so relationships can be edited in place.
- `config/settings.py`: CORS limited to `WEB_ORIGINS` with credentials, cookie settings,
  `GOOGLE_CLIENT_ID` may now be comma-separated.

**Environment variables to set on Railway:** `WEB_ORIGINS` (e.g. `https://kinship.vercel.app`),
and if the web app and API are on different sites, `AUTH_COOKIE_SAMESITE=None`. Easier: proxy
`/api/*` through Vercel (rewrite to the Railway URL) and leave `VITE_API_URL` empty.
Android's Google Web client ID can be reused for the web app: add the web origins under that
client's "Authorized JavaScript origins" in Google Cloud Console.

## Deploy

Railway serves the site and API from one service. A free Netlify site
(kinship-family.netlify.app) forwards to it; set `WEB_ORIGINS` on Railway to any such front address.
