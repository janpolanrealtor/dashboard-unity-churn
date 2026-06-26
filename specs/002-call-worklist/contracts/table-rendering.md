# Contract: Worklist Table Rendering

## Type
UI rendering contract — HTML table generated in Python and injected via `st.markdown(unsafe_allow_html=True)`.

## Interface

### Input
A pandas DataFrame with columns matching the WorklistRow entity (see `data-model.md`).

### Output
HTML string rendered inside `<div class="portfolio-wrap">` with `<table class="portfolio-table">`.

## Column Specifications

| Column | Content | Formatting Rules |
|---|---|---|
| **Account** | `ACCOUNT_NAME` (bold) + `MARKET_NAME` (smaller, gray `#726A60`) | If `MARKET_NAME = "Unknown"`, display "National (VIP Package)" |
| **Expiring ACV** | `EXPIRING_VALUE_ACV` formatted by `fmt_currency()` | If `ROI_PER_LEAD < 0`, append `<div style="color:#D92228;font-size:11px">below viability</div>` below the ACV |
| **Churn Risk** | Custom HTML progress bar | 80px wide, gray track `#E9E7E4`, colored fill + circle indicator at position = CHURN_PROB * 80px; high >0.7 red `#D92228`, medium 0.4–0.7 yellow `#685700` with `#FFF2D0` background, low <0.4 green `#46A758` |
| **Top Driver** | `MOST_IMPORTANT_FEATURE` text | Append trend arrow: `↑` green if improving, `↓` red if worsening, `–` gray if neutral/missing |
| **Renews In** | `fmt_renews_in(DAYS_UNTIL_EXPIRY)` | `<0` → "Expired" gray `#726A60`; `0–15` → bold red `#D92228`; else charcoal `#3F3B36` |

## Example Churn Risk Bar HTML

```html
<div style="width:80px;height:6px;background:#E9E7E4;border-radius:3px;position:relative;">
  <div style="position:absolute;left:0;top:0;height:6px;width:{pct*80}px;background:{color};border-radius:3px;"></div>
  <div style="position:absolute;left:{pct*80-4}px;top:-3px;width:12px;height:12px;background:{color};border:2px solid #fff;border-radius:999px;box-shadow:0 0 2px rgba(0,0,0,0.2);"></div>
</div>
```

## Validation

- All numeric values MUST pass through `df.replace([np.inf, -np.inf], np.nan)` before rendering
- Any cell receiving NaN or None MUST display `"—"`
- Worklist MUST never exceed 200 rows
