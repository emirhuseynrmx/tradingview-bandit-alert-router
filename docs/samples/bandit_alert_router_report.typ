#set page(margin: 15mm)
#set text(font: "Arial", size: 10pt)
#set heading(numbering: none)

#let ink = rgb("#111827")
#let muted = rgb("#64748b")
#let panel = rgb("#f3f6fb")
#let line = rgb("#d7dee8")
#let warn = rgb("#b45309")

#let card(label, value, note: none) = block[
  #rect(fill: panel, radius: 6pt, inset: 9pt, width: 100%)[
    #text(size: 8pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 19pt, fill: ink, weight: "bold")[#value]
    #if note != none [#linebreak() #text(size: 8pt, fill: muted)[#note]]
  ]
]

#let check(label, value) = block[
  #text(weight: "bold")[#label]
  #linebreak()
  #text(fill: muted)[#value]
]

#text(size: 22pt, weight: "bold", fill: ink)[TradingView Bandit Alert Router]

#text(fill: muted)[Sample routing report for a Thompson Sampling alert workflow. The router validates, blocks, routes, and records feedback without touching broker execution.]

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
  #card("Routed", "3", note: "accepted alerts")
][
  #card("Blocked", "1", note: "guarded before policy")
][
  #card("Policy", "Thompson", note: "route selection")
]

#v(10pt)
#grid(columns: (1.75fr, .95fr), gutter: 14pt)[
  #text(size: 13pt, weight: "bold")[Decision Log]
  #v(4pt)
  #table(
    columns: (.9fr, .6fr, 1.25fr, 2.25fr),
    stroke: line,
    inset: 5pt,
    [*Alert*], [*Status*], [*Route*], [*Reason*],
  [report-0001], [routed], [telegram_ops], [selected by Thompson Sampling],
  [report-0002], [routed], [discord_research], [selected by Thompson Sampling],
  [report-0003], [blocked], [-], [confidence is below the routing threshold],
  [report-0004], [routed], [telegram_ops], [selected by Thompson Sampling],
  )
][
  #text(size: 13pt, weight: "bold")[Evidence Contract]
  #v(4pt)
  #block(stroke: line, radius: 6pt, inset: 8pt)[
    #check("Validation", "Pydantic rejects malformed webhook payloads.")
    #v(5pt)
    #check("Idempotency", "Duplicate alert IDs do not receive new route decisions.")
    #v(5pt)
    #check("Risk guard", "Low-confidence or oversized alerts are blocked first.")
    #v(5pt)
    #check("Boundary", "Routing feedback is not a profit forecast.")
  ]
]

#v(10pt)
#block(fill: rgb("#fffbeb"), radius: 6pt, inset: 8pt)[
  #text(weight: "bold", fill: warn)[Interpretation:] This service is a decision router. Live capital deployment, broker credentials, and exchange adapters belong in a separate, stricter execution boundary.
]
