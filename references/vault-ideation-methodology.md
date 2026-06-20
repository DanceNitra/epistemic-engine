# Vault Ideation Methodology — Building from Unique IP

A repeatable process for when the user wants something "úplne nové" from their vault data.
Derived from the session that produced the epistemic-engine (June 2026).

## When to Use

- User says: "skus nieco uplne nove", "hladaj dalej", "stale slabota"
- After 3+ rejected product/SaaS/game ideas
- User has a large knowledge vault with unique empirical data

## The Process

### Phase 1: Quantify the Vault (REAL numbers)

Get exact counts before proposing anything. The user corrected "1,447" → "9,843" — real numbers matter.

```bash
# Total files
find /path/to/vault -name "*.md" | wc -l

# Concepts by domain
find "04 Resources/Concepts" -name "*.md" | wc -l

# Publications
find "04 Resources/Publications" -name "*.md" | wc -l

# Bridges
find "04 Resources/Concepts" -name "*Bridge*" | wc -l

# Domain breakdown
for d in "04 Resources/Concepts/Domains"/*/; do name=$(basename "$d"); count=$(find "$d" -name "*.md" | wc -l); echo "$name: $count"; done
```

### Phase 2: Find What's Unique

Search vault for what the vault claims that's unusual:

- **Empirical data**: Grounding-Coupling Law, Crucible results, calibration measurements
- **Structural claims**: Bridges, Why_X_Is_Y series, Pattern Language
- **Novel frameworks**: Percolation thresholds, anti-calibration, epistemic labels
- **Published IP**: Breaktruth series, Publications

### Phase 3: Research Outside World

Compare vault claims against published literature. Key questions:
- Does this exist in published form?
- If so, what's the methodology and how does vault differ?
- If not, is vault genuinely novel?

### Phase 4: Build ONE Concrete Thing

After 3+ rejections, do NOT offer more options. Build ONE thing now:
- Self-contained Python CLI (0 dependencies if possible)
- SKILL.md with embedded code
- Test all commands before reporting

## Pitfalls

- Do NOT propose SaaS/product/game/commercial after 2 rejections → switch to concept/empirical layer
- Do NOT touch systems managed by other agents ("agoru spracovava iny agent")
- Do NOT offer multiple options after repeated rejections — pick one and build it
- Do NOT say approximate vault numbers — get exact counts
- Fyzické veci (karty, postery, knihy) > software, but software built FROM vault data is acceptable if it's not "ešte jeden SaaS"