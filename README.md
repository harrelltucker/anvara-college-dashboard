# College Sponsorship Opportunity Dashboard

Ranks U.S. college athletic departments by their attractiveness as sponsorship-marketplace partners for Anvara: **financial pressure** (incentive to grow revenue), **commercial opportunity** (size of sponsorship dollars), and **growth catalysts** (evidence of active commercial expansion), with rights-holder intelligence as context.

It ranks opportunity. It does not claim any school has unsold sponsorship inventory.

## Run it (Windows, PowerShell)

First time only:
```powershell
cd C:\Users\Tucker\Projects\anvara-college-dashboard
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Every time:
```powershell
cd C:\Users\Tucker\Projects\anvara-college-dashboard
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```
The dashboard opens in your browser. Keep the PowerShell window open while using it; close it to stop.

If PowerShell says running scripts is disabled, run once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Public version (what Anvara sees)

Setting `PUBLIC=1` shows a simpler, read-only app: **Top opportunities**, **School profiles**, **How it works** and
**Sources**, with top navigation and default weights. The research workflow (review queue, adding findings, data
quality), demonstration data and confidence labels are left out. Pages live in `views/public/`.

- Preview it locally: double-click `Preview Public Version.bat` (opens http://localhost:8502).
- Host it on Streamlit Community Cloud: connect this repo, main file `app.py`, Python 3.13, and add
  `PUBLIC = "1"` under **Secrets**.

## Check the scoring rules
```powershell
python -m pytest
```

## How it's organized

| Folder | What's in it |
|---|---|
| `app.py`, `views/`, `ui/` | The dashboard (pages, sidebar, formatting) |
| `engine/` | Data loading, metric definitions, scoring, validation, research workflow (no dashboard code) |
| `config/weights.toml` | Default weights and rules |
| `data/research/` | Verified research data (CSV; open in Excel) |
| `data/pending/` | Findings awaiting human verification; they don't affect scores |
| `data/demo/` | Fictional demonstration data (`python tools/make_demo_data.py`) |
| `docs/` | Methodology and research log |
| `tests/` | Rules the scoring must always follow |

## Research workflow

1. **Research & data quality → Research checklist** lists what each school is missing and where to look.
2. New findings, from you or an AI research assistant, go in through **Add a finding** with a source link.
3. In the **Review queue**, open the source, confirm it, and click **Verify**. Only then does the finding enter the scored data.
