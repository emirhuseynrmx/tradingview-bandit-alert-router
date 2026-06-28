#set page(margin: 16mm)
#set text(font: "Arial", size: 10pt)

#text(size: 18pt, weight: "bold")[TradingView Bandit Alert Router]

Sample routing report for a Thompson Sampling alert workflow.

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
  #block(fill: rgb("#f3f6fb"), radius: 4pt, inset: 8pt)[Routed\ #text(size: 18pt, weight: "bold")[3]]
][
  #block(fill: rgb("#f3f6fb"), radius: 4pt, inset: 8pt)[Blocked\ #text(size: 18pt, weight: "bold")[1]]
][
  #block(fill: rgb("#f3f6fb"), radius: 4pt, inset: 8pt)[Policy\ #text(size: 18pt, weight: "bold")[Thompson]]
]

#v(10pt)
#text(size: 12pt, weight: "bold")[Decision Log]

#table(
  columns: (1fr, .7fr, 1fr, 2fr),
  [Alert], [Status], [Route], [Reason],
  [report-0001], [routed], [telegram_ops], [selected by Thompson Sampling],
  [report-0002], [routed], [discord_research], [selected by Thompson Sampling],
  [report-0003], [blocked], [-], [confidence is below the routing threshold],
  [report-0004], [routed], [telegram_ops], [selected by Thompson Sampling],
)
