# 2 minute 40 second demonstration

Record the real application in a desktop browser. Use `AI_MODE=provider` and `PAYMENT_MODE=sandbox`, with valid server-side credentials. A local planner or simulated payment is useful practice but must not stand in for the required integrations in the final demonstration.

## Before recording

1. Follow `JUDGE_GUIDE.md`; verify a real AI request and a completed PayPal sandbox capture.
2. Prepare a dedicated sandbox personal buyer account, distinct from the merchant account. Sign in before recording to reduce login delay. Never show credentials, `.env`, tokens or terminal history containing secrets.
3. Open a fresh browser session. Use an example such as “A comfortable study desk for video calls; prioritize lighting and a keyboard” with a $150 budget. Rehearse it against the current catalog and provider; choose a budget that gives a valid result.
4. Use original narration and no music unless you have the required rights. Review visible third-party materials and their usage permissions.
5. Make **PayPal sandbox** and **Nebius AI** readable in the application and say both names aloud. Confirm the exact service/model in the recording matches the description and Built With fields. Optional sponsor references are not a substitute for showing the two core integrations working.

## Footage and narration

| Time | Show | Suggested narration |
| --- | --- | --- |
| 0:00–0:20 | Product workspace, visible AI/PayPal mode labels and budget input | “TRACE Commerce combines Nebius AI shopping plans with PayPal sandbox checkout, helping students and remote workers choose a useful desk setup within a fixed budget.” |
| 0:20–0:55 | Enter the example, request the plan, show the real provider result | “I describe what I need and set my spending limit. Nebius Token Factory runs our configured AI model, selects products from our demonstration catalog and explains the trade-offs.” |
| 0:55–1:20 | Review chosen products, cart total and budget remaining; adjust a quantity if appropriate | “I review the items before paying. The server checks product IDs and quantities and calculates the total from its own catalog. The model does not control prices.” |
| 1:20–2:05 | Start checkout, show PayPal sandbox approval, approve with the sandbox buyer and return | “Checkout creates a PayPal sandbox order. I explicitly approve it in PayPal. This is test money, with no live purchase or fulfillment.” |
| 2:05–2:25 | Show the captured receipt, order reference and AI provider/model provenance | “The server verifies the capture and records the cart's payment reference and original AI model. The receipt connects the recommendation to its approved sandbox checkout.” |
| 2:25–2:40 | End on receipt, Built With names and repository/demo links | “Nebius AI handles the plan; PayPal sandbox handles the approved payment. The public source includes an open-source license, setup and judge testing instructions.” |

Target 2:40 total; leave a margin below three minutes. If a provider or sandbox operation is slow, record a successful complete session and trim pauses. Disclose cuts; do not replace actual responses or payment states with fabricated footage. Show the distinction between buyer approval and capture; present the payment as completed only after a verified capture receipt appears.

Upload to **publicly visible YouTube**, add its URL to Devpost, and check playback while signed out. Verify the submitted recording matches the final code and the judges' accessible build.
