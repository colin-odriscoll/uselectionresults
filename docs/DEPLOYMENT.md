# Cloudflare Pages deployment

This repository produces a static `dist/` directory, with no server or Worker required. No Cloudflare project or production deployment has been created by this implementation.

## GitHub integration

1. In Cloudflare, create a **Pages** project connected to `colin-odriscoll/uselectionresults`.
2. Select production branch `main`, framework preset **None**, root directory repository root.
3. Set build command:

   ```sh
   pip install -r requirements.txt && python scripts/validate.py && npm run build
   ```

4. Set output directory **`dist`**, `PYTHON_VERSION=3.12`, `NODE_VERSION=22`.
5. Deploy and verify the home page, `/#office=senate&state=MN`, `/data/results.json`, `/data/health.json`, and `/schema/results.schema.json`. Use the returned `pages.dev` address; no address is assumed in the repository.
6. Optionally add your domain in Pages after the initial deployment succeeds.

The build validates election data before publishing. `_headers` sets a restrictive same-origin content policy and forces data revalidation. A failed build keeps the previous deployment. A real `404.html` avoids treating missing data URLs as SPA routes.

Official references: [static HTML hosting](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/), [build settings](https://developers.cloudflare.com/pages/configuration/build-configuration/), and [deploy hooks](https://developers.cloudflare.com/pages/configuration/deploy-hooks/).

## Enable collection

The updater is installed at `.github/workflows/refresh.yml` and runs every 15 minutes by default. It was activated through the owner's existing GitHub browser access on November 3. The local Git token still cannot modify workflow files. The optional CI template remains at `docs/workflows/validate.yml`.
1. Review `config/sources.json` and run **Refresh official election data** manually from GitHub Actions. Before poll close the expected state is `waiting`. Source test mode produces a visible failure and preserves previous data.
2. The 15-minute scheduled job is enabled unless repository Actions variable **`ENABLE_LIVE_UPDATES=false`** is set. GitHub schedules are best-effort and can be delayed; they are not an election-night SLA.
3. Create a Cloudflare Pages **deploy hook** targeting `main`. Store its full URL as GitHub Actions secret **`CLOUDFLARE_PAGES_DEPLOY_HOOK`**. The updater posts to it after committing validated data/health. Keep the URL secret; it authorizes builds. This avoids relying solely on bot-commit webhook behavior. If normal Git integration also triggers builds, disable automatic production builds or remove the optional hook to avoid duplication after verifying your setup.
4. Confirm repository Actions can write contents and branch rules allow the data bot's `main` updates. The workflow never force-pushes. If another commit wins the race, the push fails visibly and the next run starts from the new head.
5. Monitor workflow errors, stale labels and source health. Retain source audit artifacts beyond the default 30 days if required. Set `ENABLE_LIVE_UPDATES=false` after the reporting period to stop consuming builds. Verify the plan's build quota before frequent deployment.

No AP key is needed for the current official adapter. AP integration is not implemented; do not put future API keys in public files. CNN/Fox call evidence goes through the reviewed editorial file, not an unattended scrape.

## Manual upload alternative

Run the validation/tests and `npm run build`, then upload `dist/` through Cloudflare's Pages Direct Upload flow. Data refreshes require another upload. Choose your preferred Pages project type at creation; do not assume a Direct Upload project can later use Git integration unchanged.

## Recovery

For an upstream failure, leave the last validated snapshot in place and inspect `health.json` plus raw artifacts. Fix the adapter against a new isolated fixture, rerun tests, then collect again. For an erroneous published record, correct its source/editorial record, regenerate, validate and publish; Git history provides an audit trail. For a website regression, use a previous successful Cloudflare deployment. Never replace missing official results with a test or historical file.
