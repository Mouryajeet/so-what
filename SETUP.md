# So What? setup: what Mourya does once

The pipeline is built and day 1 (13 Nov) is real. These steps connect it to the internet. Each one is yours, because each needs your own login.

1. **GitHub** (free)
   - Sign in or create an account at github.com.
   - Create a **public** repository named `so-what`. It holds only public news data and pages.
   - In Claude Code's terminal, run `gh auth login` and follow the prompts.
   - Tell Claude it's done. Claude pushes this folder to the repo.
2. **Give the routine access**
   - On claude.ai/code, connect GitHub (the Claude GitHub app).
   - Allow it access to the `so-what` repository.
3. **The daily routine**
   - Claude creates it with you: daily at 05:30 IST (00:00 UTC), on your Claude plan, running ROUTINE.md.
4. **The Hostinger sync**
   - Claude uploads `hostinger/sync.sh` to your home folder (outside public_html).
   - Claude adds one hPanel cron job, hourly: `bash $HOME/so-what-sync.sh`, with your OK.
5. **Signups to a Google Sheet** (optional; until then the form opens WhatsApp)
   - Follow the 4 steps at the top of `hostinger/signup-apps-script.gs`.
   - Send Claude the `/exec` URL.

**Preview → public:**
- **During preview:** `site.json` has `"path": "so-what-preview"` and `"noindex": true`. It lives at brandmizer.com/so-what-preview/, unlinked.
- **To go public (after 3 days of real data and your yes):**
  - Set `"path": "so-what"` and `"noindex": false`.
  - Add the nav link and sitemap entry on the main site.
