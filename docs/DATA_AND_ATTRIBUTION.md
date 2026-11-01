# Data, assets and attribution

## Demonstration data

The 12-product workspace catalog is fictional, authored for this project. Names, prices, descriptions and availability illustrate the workflow and are not merchant offers, real stock, price comparisons or market research. Product SVG illustrations are original source assets created for this application. No external product photographs, customer records or third-party music are included in the demonstration catalog.

The app does not ship or fulfill products. PayPal sandbox uses test transactions only. The project does not claim affiliation with or endorsement by PayPal or any AI provider.

## AI data flow

Provider mode sends the shopper's free-text request, budget and supplied catalog context to the configured AI service. Do not put personal, confidential or payment information in the shopping request. A prompt containing such information would still be sent to the provider.

The payment flow does not deliberately send PayPal credentials, buyer approval details, payment tokens or capture responses to the AI service. PayPal order/capture requests are separate server calls. The model supplies product suggestions; server catalog data determines trusted prices.

Local planning mode does not contact an AI provider. SQLite stores browser session identifiers, plans (including the prompt), order records and request-limit records. The default browser session expires after seven days; cleanup of expired session records occurs when a new session is created, rather than on a guaranteed deletion schedule. See the README for deployment storage and deletion limitations. Hosting, AI provider and PayPal may retain their own operational records according to their terms; this document does not make claims about their retention policies.

## License review

The project source and original assets use the MIT license in the repository's `LICENSE`. Third-party packages retain their own licenses; the project license does not relicense dependencies, vendor names or provider services.

The following licenses were checked against the installed distributions' license files and metadata on 1 November 2026. This includes the 13 pinned runtime packages, not development tools such as pip. Review this table and the installed notices when updating dependencies.

| Package and inspected version | License |
| --- | --- |
| FastAPI 0.116.1 | MIT |
| Uvicorn 0.35.0 | BSD-3-Clause |
| python-dotenv 1.2.1 | BSD-3-Clause |
| Starlette 0.47.3 | BSD-3-Clause |
| Pydantic 2.14.2; pydantic-core 2.50.2 | MIT |
| AnyIO 4.15.1 | MIT |
| idna 3.20 | BSD-3-Clause |
| Click 8.5.0 | BSD-3-Clause |
| h11 0.16.0 | MIT |
| annotated-types 0.8.0; typing-inspection 0.4.4 | MIT |
| typing-extensions 4.16.0 | PSF-2.0 |

**Release check:** Review the final dependency list and installed license metadata before publication, and preserve required notices if redistributing dependency code. Package-installed license files remain with dependencies in the Docker image; the source release does not vendor dependency code. API documentation is linked in `SOURCES.md`; it has not been copied into the app.

The public submission must identify the AI provider/model actually used. Record any additional datasets, assets, SDKs or sponsor tools added after this document was written, including their source, license and any required attribution. Review visible vendor materials and usage permissions before publishing the demonstration video.
