# Hackathon readiness

This is an implementation checklist, not a determination of entrant eligibility or a guarantee of acceptance. It uses the supplied rules, the organizer reminder supplied with this request, and the [official rules](https://paypalaihackathon.devpost.com/rules), [requirements](https://paypalaihackathon.devpost.com/) and [FAQs](https://paypalaihackathon.devpost.com/details/faqs), checked 1 November 2026. Recheck the official page before submitting.

The reminder offers **early eligibility review for submissions made by Thursday, 5 November 2026**, with editing allowed until the final deadline. Treat this as the submission target so there is time to fix issues. The reminder gives no cutoff time or timezone for 5 November; no exact India-time cutoff is assumed. This is an optional early review, not an eligibility approval or a new final deadline.

## Dates in India

| Milestone | Asia/Kolkata |
| --- | --- |
| Submission opens | 1 October 2026, 9:45 pm IST |
| **Submission deadline** | **13 November 2026, 1:30 am IST** |
| Judging begins | 2 December 2026, 3:30 am IST |
| Judge access must remain available through | 15 December 2026, 9:30 pm IST |

The deadline is 12 November at noon Pacific Standard Time. Do not confuse the Indian calendar date with the Pacific date.

## Requirements and evidence

| Rule requirement | Project provision | Evidence or action still required |
| --- | --- | --- |
| PayPal sandbox is central, with meaningful AI | Budget request → AI product selection → server-validated cart → sandbox order, buyer approval, capture and receipt | Real Nebius AI and a $215.00 USD sandbox approval/capture verified 1 November 2026, including independent read-only PayPal confirmation. Record the combined journey with `AI_MODE=provider` and `PAYMENT_MODE=sandbox`. Local rehearsal alone is insufficient. |
| Consistently runnable application | Source, configuration example, run instructions and deployment files | Follow README checks in a clean checkout; validate real credentials and chosen hosting environment. |
| Functional judge access | Local run instructions and judge guide | Provide a working build or hosted URL and any private access instructions; keep it available through judging. |
| Public open-source repository | Project license and release source | Publish to GitHub, GitLab or Bitbucket; verify visibility and automatic license detection. |
| English description and tool explanation | `SUBMISSION.md`, including an explicit Built With table | Name PayPal sandbox Orders v2 and the actual AI service/model in the description, Built With fields and video. Fill repository/demo URLs and keep all claims aligned with the final build. |
| Public YouTube demo under three minutes | `DEMO_SCRIPT.md` | Record functioning provider+sandbox footage, upload publicly and submit its URL. |
| New work or significant updates during the period | New commerce workspace separated from the earlier TRACE chatbot | Preserve dated commits and explain the new shopping, validation and payment flow in the submission. |
| Authorized third-party use and original contribution | Fictional catalog, original product illustrations, attribution notes | Entrant confirms rights, licenses and ownership; review all media used in the video. |

The included automated checks use test doubles; they do not establish successful external API calls, deployment or completed submission. See the README for the actual validation result.

## Evidence to make PayPal and AI visible

- **Description:** explain that Nebius AI selects and explains catalog products, then PayPal sandbox creates, approves and captures the reviewed cart.
- **Built With:** list **PayPal Developer Platform, PayPal sandbox, Orders v2 REST API, OAuth 2.0, Nebius Token Factory, `nvidia/Nemotron-3_5-Lightning`, Python, FastAPI, SQLite, JavaScript, HTML and CSS**. Replace the model if the final build uses a different one. Do not list optional products as integrated merely because their documentation was linked.
- **Video:** show the real configured AI response, server-checked budget, PayPal sandbox buyer approval and verified capture receipt in one understandable journey, under three minutes.
- **Runnable access:** provide a working hosted build or complete local setup instructions and required private test access. A mockup or rehearsal-only recording is insufficient.
- **Secrets:** keep merchant secrets and AI keys in server environment variables; never commit them, include them in screenshots, or put them in the public Devpost description.

The resource choices and integration status are documented in [RESOURCES.md](RESOURCES.md). The PayPal JavaScript SDK, AI Toolkit, MCP server and every sponsor tool are not all mandatory; this project uses PayPal REST directly and a separately configured AI model.

## Pre-submission checks

Run `python scripts/check_submission.py --artifacts-only` to inspect the packaged source and documentation without external requests. After setting private server credentials, run `python scripts/check_submission.py` as well: its strict configuration check rejects local/rehearsal mode for the actual hackathon demonstration. Passing that configuration check does not prove a real PayPal transaction or confirm entrant eligibility.

Use `python scripts/smoke_demo.py --base-url http://127.0.0.1:8000` for a running no-key rehearsal. The optional `--allow-provider` flag permits a real AI request and its provider cost; the smoke tool still requires rehearsal payments. Complete the real buyer approval/capture manually using the judge guide. The [Postman guide](../postman/README.md) explains the included collection and guarded manual sandbox requests.

## Entrant actions

- Confirm legal age, residence eligibility, conflicts of interest and absence of disqualifying sponsor/administrator financial or preferential support. The rules' exclusion examples are not an exhaustive country list.
- If entering as a team or organization, authorize an eligible representative and confirm rights to the submission.
- Join the hackathon and complete every required Devpost field before the deadline.
- Aim to submit by 5 November for the early review described in the organizer reminder, then resolve feedback and finalize before 12 November at noon PST.
- Use dedicated sandbox buyer credentials and provide necessary judge access privately. Keep merchant secrets and AI API keys outside the public repository.
- Ensure screenshots, music, trademarks and other media are authorized. Publicity and other participation terms remain the entrant's responsibility.

## Judging and prize claims

Implementation, design, potential impact, innovation and presentation are equally weighted. The product makes a specific demonstration case for budget-conscious students and remote workers; no measured savings, user adoption or market novelty is claimed.

The full rules extend beyond the supplied excerpt. Section 8 makes sponsor awards conditional on actual use of the respective sponsor's tools. Optional sponsor integrations are not mandatory. The included Postman collection is an API-testing artifact; record an actual Postman run before claiming that testing was performed there. Deployment configuration for Render is preparation; claim Render use only after actually using it. Do not claim prize eligibility or awards as achieved. The official rules also govern permitted prize combinations, verification and later rule amendments.
