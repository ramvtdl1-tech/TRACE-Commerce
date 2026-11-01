# Hackathon resources and actual use

The [official resources](https://paypalaihackathon.devpost.com/resources) are a menu of supported capabilities. The [FAQ](https://paypalaihackathon.devpost.com/details/faqs) confirms that sponsor tools are optional: the core requirement is meaningful **PayPal + AI**. This project chooses a shopping and checkout journey and records each resource's actual status below.

## What this release uses

| Resource | Project use | Verification status |
| --- | --- | --- |
| [PayPal REST API](https://developer.paypal.com/api/rest/) and [Checkout](https://developer.paypal.com/checkout/) | Sandbox OAuth, Orders v2 create, buyer approval, capture, retrieval and server-verified receipts | Implemented and covered by controlled tests. A real $215.00 USD sandbox buyer approval/capture was independently verified on 1 November 2026. |
| [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/) and [sandbox setup example](https://github.com/paypaldev/getting-started-with-paypal-sandbox) | Owner setup for a sandbox business REST app and a separate personal buyer account | Sandbox seller/buyer setup completed for the verified test. Merchant secrets remain private server environment variables. |
| [Nebius Token Factory](https://api.tokenfactory.nebius.com/docs) | Configurable AI chat-completions model selects and explains products; server validates catalog IDs and budget | Real requests verified with `nvidia/Nemotron-3_5-Lightning`; record the actual final model in Built With and the video. |
| [Postman sponsor resource](https://paypalaihackathon.devpost.com/details/postman) | Importable collection, environment template and instructions in [`../postman/README.md`](../postman/README.md) for reproducible API inspection | Testing artifact included. Do not claim that Postman itself was run unless a real Postman run has been recorded. |
| [Render sponsor resource](https://paypalaihackathon.devpost.com/details/render) | [`../render.yaml`](../render.yaml) prepares a persistent, single-instance Python deployment | Blueprint included; no hosted deployment or Render Workflows use is claimed. Review the host's charges and credit terms before deployment. |

The app's integration details identify the active AI provider/model and payment mode. Plans and order receipts preserve the provider/model that generated the original recommendation, including after manual cart revisions. Configuration badges alone do not prove a completed external request. Local planning and rehearsal checkout stay visibly labeled; they are useful practice but do not prove the two required external integrations.

## Optional sponsor resources

| Resource | Status in this release |
| --- | --- |
| [AG Grid](https://paypalaihackathon.devpost.com/details/aggrid) | Reference only; no grid package or license is bundled. |
| [APIMatic](https://paypalaihackathon.devpost.com/details/apimatic) | Reference only; no APIMatic SDK/context plugin is used. |
| [Astropods](https://paypalaihackathon.devpost.com/details/astropods) | Reference only; no service integration. |
| [Bryntum](https://paypalaihackathon.devpost.com/details/bryntum) | Reference only; no Bryntum components are bundled. |
| [Channel3](https://paypalaihackathon.devpost.com/details/channel3) | Reference only; the catalog is fictional and locally authored. |
| [Elastic](https://paypalaihackathon.devpost.com/details/elastic) | Reference only; storage uses SQLite. |
| [KERNEL](https://paypalaihackathon.devpost.com/details/kernel) | Reference only; the app does not automate buyer approval through a remote browser. |
| [Postman](https://paypalaihackathon.devpost.com/details/postman) | Collection and setup artifacts supplied; execution is a separate verification step. |
| [Render](https://paypalaihackathon.devpost.com/details/render) | Deployment Blueprint supplied; actual hosting remains pending. |
| [Zapier](https://paypalaihackathon.devpost.com/details/zapier) | Reference only; no Zapier MCP connection or workflow. |

Do not select a sponsor tool in an actual-use claim solely because its URL appears here. Follow the sponsor's access/license conditions before adding it, demonstrate the resulting functionality, and recheck section 8 of the [official rules](https://paypalaihackathon.devpost.com/rules) before making a prize claim.

## PayPal SDK and agent resources

- [PayPal Developer docs](https://developer.paypal.com/) and [Payments](https://developer.paypal.com/payments/) provide the platform entry points. The implemented payment contract is Orders v2 REST.
- [JavaScript SDK v6](https://developer.paypal.com/sdk/js/) is an alternative checkout integration. This build uses server REST and a PayPal approval redirect; it does not import the JavaScript SDK.
- [PayPal AI Toolkit](https://github.com/paypal/AI-Toolkit), [AI docs](https://docs.paypal.ai/), [Agent Toolkit quickstart](https://docs.paypal.ai/developer/tools/ai/agent-toolkit-quickstart), [MCP server quickstart](https://docs.paypal.ai/developer/tools/ai/mcp-quickstart) and [agent tools reference](https://docs.paypal.ai/developer/tools/ai/agent-tools-ref) are reference options, not runtime dependencies here. The app's bounded AI planner suggests a cart; explicit buyer review authorizes checkout.
- [Webhooks](https://developer.paypal.com/api/webhooks/overview) are a useful future reconciliation path. This build verifies Orders API responses and supports explicit retry/retrieval; it does not claim a background webhook service.

## Other payment capabilities

The following official capabilities are references and are **not implemented** in this desk-setup checkout: [payment links/buttons](https://developer.paypal.com/payment-links-buttons/overview), [Pay Later](https://developer.paypal.com/pay-later/overview), [Subscriptions](https://developer.paypal.com/platforms/subscriptions), [Invoicing](https://developer.paypal.com/invoicing/about), [Payouts](https://developer.paypal.com/docs/payouts/), [Disputes](https://developer.paypal.com/platforms/disputes/overview), and [Donations](https://developer.paypal.com/sdk/donate/). Do not describe them as shipped features.

## Supplied webinar references

These links are listed in the official resource index and the organizer material. They are learning resources; this release does not claim the recordings were watched or incorporated as source code.

- [6 October — Start building with PayPal](https://www.youtube.com/watch?v=FFJfCW9z3Do)
- [7 October — APIMatic Context Plugins](https://www.youtube.com/watch?v=zRWixN68tDg)
- [12 October — Build a payments dashboard without building a dashboard](https://www.youtube.com/watch?v=LGfG44i1Fj8)
- [13 October — Start building with PayPal](https://www.youtube.com/watch?v=ck_zyB66p_Y)

For account or sponsor-access questions, use the [official FAQ](https://paypalaihackathon.devpost.com/details/faqs) or [PayPal Discord](https://discord.gg/sJ2G6DyvSK). No account enrollment, sponsor-credit claim, legal agreement or Devpost submission is performed by generating these files.
