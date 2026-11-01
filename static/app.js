"use strict";

(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const money = cents => new Intl.NumberFormat("en-US", {style: "currency", currency: "USD"}).format((Number(cents) || 0) / 100);
  const state = {config: null, products: [], plan: null, orders: [], busy: false, category: "All", view: "workspace", modalBusy: false};
  const dialog = $("#action-dialog");
  let noticeTimer;

  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  }
  function notify(message, error = false, retry) {
    clearTimeout(noticeTimer);
    const notice = $("#notice");
    notice.replaceChildren(document.createTextNode(message));
    notice.className = `notice${error ? " error" : ""}`;
    notice.setAttribute("role", error ? "alert" : "status");
    notice.setAttribute("aria-live", error ? "assertive" : "polite");
    if (retry) { const button = element("button", "", "Try again"); button.addEventListener("click", retry); notice.append(button); }
    const dismiss = element("button", "notice-dismiss", "×");
    dismiss.setAttribute("aria-label", "Dismiss notification");
    dismiss.addEventListener("click", () => notice.classList.add("hidden"));
    notice.append(dismiss);
    if (!error) noticeTimer = setTimeout(() => notice.classList.add("hidden"), 8000);
  }
  async function api(path, options = {}) {
    const headers = {Accept: "application/json", ...(options.headers || {})};
    if (options.method && options.method !== "GET") {
      headers["Content-Type"] = "application/json";
      headers["X-CSRF-Token"] = state.config?.csrf_token || "";
    }
    let response;
    try { response = await fetch(path, {credentials: "same-origin", ...options, headers}); }
    catch (_) { throw new Error("We couldn’t reach the workspace. Check your connection and try again."); }
    let body;
    try { body = await response.json(); } catch (_) { throw new Error("The server returned an unexpected response. Please try again."); }
    if (!response.ok) {
      const message = typeof body.detail === "string" ? body.detail : "This request couldn’t be completed. Check your inputs and try again.";
      if (response.status === 401 || response.status === 403) {
        state.plan = null;
        sessionStorage.removeItem("trace-plan");
        renderPlan();
      }
      throw new Error(message);
    }
    return body;
  }
  function post(path, body = {}) { return api(path, {method: "POST", body: JSON.stringify(body)}); }
  function setBusy(busy, label) {
    state.busy = busy;
    $("#build-button").disabled = busy;
    $("#build-button .button-label").textContent = busy ? (label || "Considering your setup…") : "Build my setup";
    $("#build-button .button-label").classList.toggle("loading-dots", busy);
    $("#checkout-button").disabled = busy || !state.plan?.items?.length;
    $$(".quantity-row button,.add-product,.preset").forEach(button => { button.disabled = busy; });
  }
  function showView(view) {
    state.view = view;
    $$(".view").forEach(node => node.classList.toggle("hidden", node.id !== `${view}-view`));
    $$(".nav-item").forEach(node => {
      const active = node.dataset.view === view;
      node.classList.toggle("active", active);
      if (active) node.setAttribute("aria-current", "page"); else node.removeAttribute("aria-current");
    });
    $("#page-label").textContent = {workspace: "Workspace", catalog: "Product catalog", history: "Payment history"}[view];
    if (view === "history") loadOrders();
    window.scrollTo({top: 0, behavior: "smooth"});
  }
  function art(icon, color = "#a59379") {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 160 160");
    svg.setAttribute("aria-hidden", "true");
    const patterns = {
      monitor: '<path d="M67 116h26v12H67z" fill="#777c71"/><path d="M50 129h60" stroke="#656c60" stroke-width="5" stroke-linecap="round"/><rect x="16" y="28" width="128" height="87" rx="8" fill="#485047"/><rect x="23" y="35" width="114" height="70" rx="3" fill="#eac5ad"/><circle cx="112" cy="51" r="10" fill="#f7e8c7"/><path d="M23 91l34-34 38 27 20-16 22 25v12H23z" fill="#c49b84"/><path d="M23 104l46-31 45 32z" fill="#a5826b"/>',
      keyboard: '<path d="M16 66l120-15 13 61-121 15z" fill="#c8c0b0"/><path d="M16 62l120-15 13 61-121 15z" fill="#e9e4d7" stroke="#b7b09f" stroke-width="1.5"/><path d="M27 74l101-13m-98 25l101-13m-97 25l100-13m-96 25l101-13" stroke="#b5ad9d" stroke-width="7" stroke-dasharray="7 3"/><path d="M57 106l42-6" stroke="#a9a18f" stroke-width="6"/>',
      lamp: '<ellipse cx="81" cy="132" rx="37" ry="8" fill="#727c64"/><path d="M81 128V87l32-33-30-22" fill="none" stroke="#76836a" stroke-width="7" stroke-linecap="round"/><circle cx="81" cy="86" r="6" fill="#515f4c"/><path d="M82 31L60 48l39 19 5-27z" fill="#8b997c"/><path d="M60 48c12-5 30 2 39 19-17 0-31-6-39-19" fill="#e7d9b4"/>',
      headphones: '<path d="M37 88V69a43 43 0 0186 0v19" fill="none" stroke="#7b766a" stroke-width="14"/><path d="M40 78V69a40 40 0 0180 0v9" fill="none" stroke="#bab29e" stroke-width="5"/><rect x="25" y="73" width="29" height="54" rx="13" fill="#a69c85" transform="rotate(-8 40 100)"/><rect x="106" y="73" width="29" height="54" rx="13" fill="#a69c85" transform="rotate(8 120 100)"/><rect x="36" y="78" width="16" height="43" rx="7" fill="#d6cdbb"/><rect x="108" y="78" width="16" height="43" rx="7" fill="#d6cdbb"/>',
      stand: '<path d="M39 109l27-69 16 4-20 55 48 14-4 12z" fill="#b5b6af"/><path d="M27 111l75 18 31-19-75-18z" fill="#d8d7cf" stroke="#b5b6af" stroke-width="2"/><path d="M35 38l81-10 13 60-81 10z" fill="#858b82"/><path d="M40 43l71-8 10 47-71 10z" fill="#d4bda8"/><path d="M48 98l81-10-14 11-80 9z" fill="#bdbeb5"/><path d="M75 106l20-2" stroke="#8e9488" stroke-width="2"/>',
      chair: '<rect x="52" y="22" width="56" height="65" rx="17" fill="#9fa58c"/><path d="M48 86h64v19H48z" fill="#879377"/><path d="M80 105v27m0-3l-31 14m31-14l31 14" stroke="#707b68" stroke-width="6" stroke-linecap="round"/><path d="M42 73v23m76-23v23" stroke="#858d77" stroke-width="7" stroke-linecap="round"/><path d="M42 74h15m46 0h15" stroke="#a6ad96" stroke-width="7" stroke-linecap="round"/><circle cx="46" cy="144" r="5" fill="#59634f"/><circle cx="114" cy="144" r="5" fill="#59634f"/>',
      plant: '<path d="M51 97h58l-8 41H59z" fill="#cfaa8d"/><path d="M49 96h62v9H49z" fill="#dfbda0"/><path d="M80 98V43" stroke="#6c7e57" stroke-width="3"/><path d="M79 79C43 78 39 49 46 40c24 2 39 16 33 39m2-14c1-32 17-46 32-42 1 25-12 41-32 42m-1 29c4-27 22-36 35-29-3 20-16 29-35 29" fill="#8e9d73"/><path d="M79 80L50 47m32 18l26-34m-27 61l28-21" stroke="#74865c" stroke-width="2"/>',
      webcam: '<path d="M65 97h30v23H65z" fill="#83897d"/><path d="M49 120h62" stroke="#6b7464" stroke-width="7" stroke-linecap="round"/><rect x="22" y="47" width="116" height="50" rx="17" fill="#858c7f"/><rect x="27" y="51" width="106" height="42" rx="13" fill="#9ba18f"/><circle cx="80" cy="72" r="23" fill="#555e50"/><circle cx="80" cy="72" r="15" fill="#353e36"/><circle cx="80" cy="72" r="9" fill="#6c7e6d"/><circle cx="76" cy="68" r="4" fill="#b9c9b1"/><circle cx="119" cy="71" r="3" fill="#d7e6b6"/>',
      mouse: '<path d="M48 57c0-20 64-20 64 0v44c0 44-64 44-64 0z" fill="#b9b39f"/><path d="M48 65c0-36 64-36 64 0v29H48z" fill="#d4cfbd"/><path d="M80 37v47" stroke="#a09c88" stroke-width="1.5"/><rect x="76" y="49" width="8" height="20" rx="4" fill="#8e937d"/>',
      notebook: '<path d="M32 40l80-14 19 105-80 14z" fill="#948269"/><path d="M36 37l80-14 18 104-80 14z" fill="#b29d7d"/><path d="M43 36l18 103" stroke="#7d705c" stroke-width="3"/><path d="M65 60l38-7m-36 17l38-7" stroke="#d9c9ab" stroke-width="2"/><path d="M115 41l8-2 20 88-8 2z" fill="#6b7860"/><path d="M135 129l5 9 3-11z" fill="#c9b792"/>',
      desk: '<path d="M18 65h124v12H18z" fill="#c5a184"/><path d="M26 77h8v56h-8zm100 0h8v56h-8z" fill="#9c7b60"/><path d="M39 77h50v31H39z" fill="#b18d70"/><path d="M44 84h40m-40 15h40" stroke="#d4b79b" stroke-width="2"/><path d="M60 90h10m-10 14h10" stroke="#8e725d" stroke-width="2"/>',
      deskmat: '<path d="M19 56l108-18 21 77-108 18z" fill="#a9a091"/><path d="M19 52l108-18 21 77-108 18z" fill="#c0b5a4" stroke="#ada28f" stroke-width="2"/><path d="M25 57l98-16 19 65-98 17z" fill="none" stroke="#d6ccbd" stroke-dasharray="3 3"/><path d="M65 73l29-5 7 29-29 5z" fill="#bbb09e"/>',
      hub: '<path d="M32 77l84-16 15 32-84 16z" fill="#a4aaa2"/><path d="M32 72l84-16 15 32-84 16z" fill="#c3c8bf" stroke="#9da699" stroke-width="1.5"/><path d="M116 61l12-21 15-1" fill="none" stroke="#9fa79b" stroke-width="5" stroke-linecap="round"/><path d="M52 91l11-2m5-1l11-2m7-1l15-3m6-1l8-2" stroke="#687263" stroke-width="4"/>',
      microphone: '<rect x="62" y="27" width="36" height="65" rx="18" fill="#929c87"/><path d="M69 43h22m-22 9h22m-22 9h22m-22 9h22" stroke="#6b775f" stroke-width="3"/><path d="M51 70v12a29 29 0 0058 0V70m-29 41v20m-23 3h46" fill="none" stroke="#737f67" stroke-width="6" stroke-linecap="round"/>'
    };
    const template = document.createElement("template");
    // Only fixed, application-owned SVG strings enter this template.
    template.innerHTML = `<svg xmlns="${ns}">${patterns[icon] || patterns.stand}</svg>`;
    [...template.content.firstElementChild.childNodes].forEach(child => svg.append(child.cloneNode(true)));
    return svg;
  }
  function productFor(id) { return state.products.find(product => product.id === id); }
  function productCard(product, compact = false) {
    const card = element("article", "product-card");
    const visual = element("div", "product-art");
    const palette = {Focus: "#eeeade", Comfort: "#e9e8da", Lighting: "#efe3d4", Audio: "#e7e6df", Accessories: "#f0e8db"};
    visual.style.backgroundColor = palette[product.category] || "#eee8de";
    visual.append(art(product.icon), element("span", "product-tag", "THE WORKSPACE EDIT"));
    const body = element("div", "product-body");
    body.append(element("span", "product-category", product.category), element("h3", "", product.name));
    if (!compact) body.append(element("p", "product-description", product.description));
    const bottom = element("div", "product-bottom");
    const add = element("button", "add-product", "+");
    add.type = "button";
    add.setAttribute("aria-label", `Add ${product.name} to your setup`);
    add.disabled = state.busy;
    add.addEventListener("click", () => addProduct(product.id));
    bottom.append(element("strong", "", money(product.price_cents)), add);
    body.append(bottom); card.append(visual, body);
    return card;
  }
  function renderCatalog() {
    const featured = state.products.filter(p => ["lamp", "headphones", "keyboard", "stand"].includes(p.icon)).slice(0, 4);
    $("#featured-products").replaceChildren(...(featured.length >= 4 ? featured : state.products.slice(0, 4)).map(p => productCard(p, true)));
    const categories = ["All", ...new Set(state.products.map(p => p.category))];
    $("#category-filters").replaceChildren(...categories.map(category => {
      const button = element("button", `category-filter${state.category === category ? " selected" : ""}`, category);
      button.setAttribute("aria-pressed", String(state.category === category));
      button.addEventListener("click", () => { state.category = category; renderCatalog(); }); return button;
    }));
    $("#catalog-products").replaceChildren(...state.products.filter(p => state.category === "All" || p.category === state.category).map(p => productCard(p)));
    $("#empty-art").replaceChildren(art("headphones"), art("plant"));
  }
  function savePlan() {
    if (!state.plan || !state.config) return;
    try { sessionStorage.setItem("trace-plan", JSON.stringify({session: state.config.csrf_token, plan: state.plan})); } catch (_) { /* Private browsing may disable storage. */ }
  }
  function renderPlan() {
    const plan = state.plan;
    $("#empty-setup").classList.toggle("hidden", !!plan);
    $("#plan-content").classList.toggle("hidden", !plan);
    $("#item-count").textContent = `${plan ? plan.items.reduce((sum, item) => sum + item.quantity, 0) : 0} items`;
    $("#checkout-button").disabled = !plan?.items?.length || state.busy;
    if (!plan) return;
    $("#plan-title").textContent = plan.ai_source === "provider" ? "Your AI-curated setup" : "Your local planner’s selection";
    $("#plan-summary").textContent = plan.summary;
    $("#plan-items").replaceChildren(...plan.items.map(item => {
      const row = element("article", "plan-item");
      const image = element("div", "item-art"); image.append(art(productFor(item.product_id)?.icon));
      const info = element("div", "item-info"); info.append(element("h3", "", item.name), element("p", "", item.reason || "Added by you. Priced and budget-checked by the server."));
      const controls = element("div", "quantity-row");
      const minus = element("button", "", "−"), plus = element("button", "", "+"), remove = element("button", "remove-item", "Remove");
      minus.setAttribute("aria-label", `Decrease quantity of ${item.name}`);
      plus.setAttribute("aria-label", `Increase quantity of ${item.name}`);
      remove.setAttribute("aria-label", `Remove ${item.name}`);
      [minus, plus, remove].forEach(button => { button.type = "button"; button.disabled = state.busy; });
      minus.addEventListener("click", () => changeQuantity(item.product_id, -1));
      plus.addEventListener("click", () => changeQuantity(item.product_id, 1));
      remove.addEventListener("click", () => changeQuantity(item.product_id, -item.quantity));
      controls.append(minus, element("span", "", item.quantity), plus, remove); info.append(controls);
      row.append(image, info, element("strong", "item-price", money(item.line_total_cents))); return row;
    }));
    $("#subtotal").textContent = money(plan.total_cents);
    $("#total").replaceChildren(document.createTextNode(`${money(plan.total_cents)} `), element("small", "", "USD"));
    $("#remaining").textContent = `${money(plan.remaining_cents ?? plan.budget_cents - plan.total_cents)} left`;
    $("#budget-progress").value = Math.min(100, plan.total_cents / plan.budget_cents * 100);
    const tradeoffs = Array.isArray(plan.tradeoffs) ? plan.tradeoffs : [];
    $("#tradeoffs").textContent = tradeoffs.join(" ");
    $("#tradeoffs").classList.toggle("hidden", !tradeoffs.length);
    const real = state.config.mode === "sandbox";
    $("#checkout-label").textContent = real ? "Review PayPal sandbox checkout" : "Review rehearsal checkout";
    $("#checkout-note").textContent = real ? "PayPal sandbox · No real money or products. You approve every payment." : "Rehearsal only · Simulates checkout. Does not contact PayPal.";
    $$(".step-number").forEach((node, index) => node.classList.toggle("current", index <= 1));
  }
  async function buildPlan(event) {
    event?.preventDefault();
    if (state.busy || !state.config) return;
    const prompt = $("#prompt").value.trim();
    const budgetCents = Math.round(Number($("#budget").value) * 100);
    if (!prompt || !Number.isSafeInteger(budgetCents) || budgetCents < 1200 || budgetCents > 500000) { notify("Add your brief and choose a budget between $12 and $5,000.", true); return; }
    setBusy(true);
    try {
      state.plan = await post("/api/plans", {prompt, budget_cents: budgetCents});
      savePlan(); renderPlan();
      $("#notice").classList.add("hidden");
      if (window.innerWidth < 961) $(".setup-panel").scrollIntoView({behavior: "smooth", block: "start"});
    } catch (error) { notify(error.message, true, () => buildPlan()); }
    finally { setBusy(false); }
  }
  async function revise(items) {
    if (state.busy || !state.plan) return;
    if (!items.length) { notify("Keep at least one item in the setup, or write a new brief to start again.", true); return; }
    setBusy(true, "Updating your setup…");
    try { state.plan = await post(`/api/plans/${encodeURIComponent(state.plan.id)}/revise`, {items}); savePlan(); renderPlan(); return true; }
    catch (error) { notify(error.message, true); }
    finally { setBusy(false); }
  }
  function changeQuantity(productId, delta) {
    const items = state.plan.items.map(item => ({product_id: item.product_id, quantity: item.quantity + (item.product_id === productId ? delta : 0)})).filter(item => item.quantity > 0);
    revise(items);
  }
  function addProduct(productId) {
    if (!state.plan) { showView("workspace"); notify("Start with a workspace brief. Then you can add any catalog item to your setup."); $("#prompt").focus(); return; }
    const items = state.plan.items.map(item => ({product_id: item.product_id, quantity: item.quantity}));
    const existing = items.find(item => item.product_id === productId);
    if (existing) existing.quantity++; else items.push({product_id: productId, quantity: 1});
    revise(items).then(updated => { if (updated && state.view === "catalog") notify("Your setup has been updated. Open Workspace to review it."); });
  }
  function openDialog({title, kicker = "YOU HAVE THE FINAL SAY", icon = "↗", content, actions = []}) {
    $("#dialog-title").textContent = title;
    $("#dialog-kicker").textContent = kicker;
    $("#dialog-icon").textContent = icon;
    $("#dialog-content").replaceChildren(...content);
    $("#dialog-error").classList.add("hidden");
    $("#dialog-actions").replaceChildren(...actions.map(action => {
      const button = element("button", `button ${action.style || "primary"}`, action.label);
      button.addEventListener("click", action.run); return button;
    }));
    if (!dialog.open) dialog.showModal();
  }
  function dialogError(message) { $("#dialog-error").textContent = message; $("#dialog-error").classList.remove("hidden"); }
  function setModalBusy(busy) { state.modalBusy = busy; $$("#dialog-actions button,#dialog-close").forEach(button => { button.disabled = busy; }); }
  function totalNode(total) { const node = element("div", "dialog-total"); node.append(element("span", "", "Server-verified total"), element("strong", "", money(total))); return node; }
  function openCheckout() {
    if (!state.plan || state.busy) return;
    const real = state.config.mode === "sandbox";
    openDialog({title: real ? "Ready for your new setup?" : "Try the checkout flow.", kicker: real ? "PAYPAL SANDBOX · NO REAL MONEY" : "REHEARSAL · NOT A PAYPAL PAYMENT", content: [element("p", "", real ? "We’ll create a PayPal sandbox order for this exact setup. You’ll approve it on PayPal, then return here to complete the sandbox capture." : "This mode creates a simulated receipt so you can rehearse the product experience. It does not contact PayPal and isn’t a substitute for the real sandbox integration."), totalNode(state.plan.total_cents)], actions: [{label: "Keep editing", style: "secondary", run: () => dialog.close()}, {label: real ? "Continue to PayPal sandbox" : "Start rehearsal", run: createOrder}]});
  }
  async function createOrder() {
    if (state.modalBusy) return;
    setModalBusy(true);
    try {
      const order = await post("/api/orders", {plan_id: state.plan.id});
      if (order.status === "COMPLETED" || order.status === "SIMULATED") { showReceipt(order); return; }
      if (order.mode === "sandbox") {
        if (["APPROVED", "PENDING", "CAPTURING"].includes(order.status)) { openCapture(order); return; }
        if (!order.approval_url) throw new Error("This order has no approval link. Check Payment history and retry the checkout.");
        const url = new URL(order.approval_url);
        if (url.protocol !== "https:" || !["www.sandbox.paypal.com", "sandbox.paypal.com"].includes(url.hostname)) throw new Error("An unexpected payment approval URL was blocked.");
        savePlan(); window.location.assign(url.href);
      } else openCapture(order);
    } catch (error) { dialogError(error.message); }
    finally { setModalBusy(false); }
  }
  function openCapture(order) {
    const real = order.mode === "sandbox";
    openDialog({title: real ? "Complete your sandbox payment." : "Simulate your approval.", kicker: real ? "FINAL STEP · PAYPAL SANDBOX" : "REHEARSAL · NO MONEY MOVES", content: [element("p", "", real ? "Your approval is checked directly with PayPal. Complete this step to capture the sandbox payment and create your receipt. Pending payments will stay pending." : "You’re in control. Select the button below to simulate a completed checkout and see the receipt experience. No payment provider is called."), totalNode(order.total_cents)], actions: [{label: "Cancel checkout", style: "secondary", run: () => cancelOrder(order)}, {label: real ? "Complete sandbox payment" : "Simulate approval", run: () => captureOrder(order)}]});
  }
  async function captureOrder(order) {
    if (state.modalBusy) return;
    setModalBusy(true);
    try {
      const result = await post(`/api/orders/${encodeURIComponent(order.id)}/capture`);
      if (["COMPLETED", "SIMULATED"].includes(result.status)) showReceipt(result);
      else showPending(result);
      if (state.view === "history") loadOrders();
    } catch (error) { dialogError(error.message); }
    finally { setModalBusy(false); }
  }
  async function cancelOrder(order) {
    if (state.modalBusy) return;
    setModalBusy(true);
    try {
      const result = await post(`/api/orders/${encodeURIComponent(order.id)}/cancel`);
      handleCancellationResult(result);
      if (state.view === "history") loadOrders();
    }
    catch (error) { dialogError(error.message); }
    finally { setModalBusy(false); }
  }
  function showPending(order) {
    openDialog({title: "Your payment is still being checked.", kicker: "CHECK PAYMENT HISTORY BEFORE RETRYING", icon: "◷", content: [element("p", "", "This order has a pending or in-progress payment and cannot be canceled here. A completed payment has not yet been confirmed. Check Payment history for the latest status before starting another checkout."), totalNode(order.total_cents)], actions: [{label: "Open payment history", run: () => { dialog.close(); showView("history"); }}]});
  }
  function handleCancellationResult(order) {
    if (["COMPLETED", "SIMULATED"].includes(order.status)) showReceipt(order);
    else if (["PENDING", "CAPTURING"].includes(order.status)) showPending(order);
    else if (["CANCELLED", "CANCELED"].includes(order.status)) {
      dialog.close();
      notify("Checkout canceled. Your setup is still here when you’re ready.");
    } else {
      dialog.close();
      notify("The order has not been canceled. Check Payment history for its current status.", true);
      showView("history");
    }
  }
  function receiptLine(label, value) { const line = element("div", "receipt-line"); line.append(element("span", "", label), element("strong", "", value || "—")); return line; }
  function showReceipt(order) {
    const simulated = order.mode !== "sandbox" || order.status === "SIMULATED";
    const content = [element("p", "", simulated ? "Your rehearsal is complete. This receipt is simulated. No money moved and no products will be delivered." : "PayPal confirmed your sandbox capture. No real money moved and no products will be delivered."), receiptLine("Order", order.id), receiptLine("Status", order.status), receiptLine("Payment mode", simulated ? "Rehearsal — simulated" : "PayPal sandbox"), receiptLine("Provider order", order.provider_order_id), receiptLine("Capture", order.capture_id), totalNode(order.total_cents)];
    if (order.ai_provider) content.splice(content.length - 1, 0, receiptLine("Planner", order.ai_provider));
    if (order.ai_model) content.splice(content.length - 1, 0, receiptLine("AI model", order.ai_model));
    if (order.budget_cents) content.splice(content.length - 1, 0, receiptLine("Approved budget", money(order.budget_cents)));
    openDialog({title: simulated ? "A clear receipt. A practice run." : "Your setup, signed and sealed.", kicker: simulated ? "SIMULATED RECEIPT" : "SANDBOX PAYMENT CONFIRMED", icon: "✓", content, actions: [{label: "Download receipt", style: "secondary", run: () => downloadReceipt(order)}, {label: "Done", run: () => { dialog.close(); showView("history"); }}]});
    $$(".step-number").forEach(node => node.classList.add("current"));
  }
  function downloadReceipt(order) {
    const receipt = {project: "TRACE Commerce", notice: order.mode === "sandbox" ? "PayPal sandbox receipt. No real money. Fictional products; no fulfillment." : "Simulated rehearsal receipt. Not a PayPal payment. No money moved.", ...order};
    const blob = new Blob([JSON.stringify(receipt, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const anchor = element("a", ""); anchor.href = url; anchor.download = `trace-receipt-${String(order.id).replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 60)}.json`; document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function renderOrders() {
    const list = $("#history-list");
    if (!state.orders.length) { const empty = element("div", "history-empty"); empty.append(element("h3", "", "Your next step will leave a clear trail."), element("p", "", "Build a setup and review checkout. Orders and receipts from this browser session will appear here.")); list.replaceChildren(empty); return; }
    list.replaceChildren(...state.orders.map(order => {
      const card = element("article", "order-card");
      const info = element("div", "");
      const date = new Date(order.created_at);
      info.append(element("h3", "", `Workspace order · ${String(order.id).slice(0, 8)}`), element("p", "", Number.isNaN(date.valueOf()) ? "Current session" : date.toLocaleString(undefined, {dateStyle: "medium", timeStyle: "short"})), element("p", "", order.mode === "sandbox" ? "PayPal sandbox · No real money" : "Rehearsal · Not a PayPal payment"));
      if (order.ai_provider) info.append(element("p", "", `Planner: ${order.ai_provider}${order.ai_model ? ` · ${order.ai_model}` : ""}`));
      const total = element("div", "order-total", money(order.total_cents));
      const completed = ["COMPLETED", "SIMULATED"].includes(order.status);
      total.append(element("span", `status-pill${order.status === "SIMULATED" ? " simulated" : completed ? "" : " pending"}`, String(order.status).replaceAll("_", " ")));
      const actions = element("div", "order-actions");
      if (completed) {
        const receipt = element("button", "text-button", "View receipt ↗"); receipt.addEventListener("click", () => showReceipt(order));
        const download = element("button", "text-button", "Download JSON ↓"); download.addEventListener("click", () => downloadReceipt(order)); actions.append(receipt, download);
      } else if (!["CANCELLED", "CANCELED", "FAILED"].includes(order.status)) {
        if (order.mode === "sandbox" && order.approval_url && order.status === "CREATED") {
          const approval = element("button", "text-button", "Continue on PayPal ↗");
          approval.addEventListener("click", () => {
            try {
              const url = new URL(order.approval_url);
              if (url.protocol !== "https:" || !["www.sandbox.paypal.com", "sandbox.paypal.com"].includes(url.hostname)) throw new Error("An unexpected approval URL was blocked.");
              openDialog({title: "Continue your sandbox checkout.", kicker: "PAYPAL SANDBOX · NO REAL MONEY", content: [element("p", "", "Return to PayPal to review and approve this order. After approval, you can complete the sandbox payment here."), totalNode(order.total_cents)], actions: [{label: "Stay here", style: "secondary", run: () => dialog.close()}, {label: "Continue to PayPal", run: () => window.location.assign(url.href)}]});
            } catch (error) { notify(error.message, true); }
          });
          actions.append(approval);
        }
        const resume = element("button", "text-button", order.mode === "sandbox" ? "Already approved? Check payment →" : "Continue rehearsal →"); resume.addEventListener("click", () => openCapture(order)); actions.append(resume);
      } else actions.append(element("span", "text-button", "No completed payment"));
      card.append(info, total, actions); return card;
    }));
  }
  async function loadOrders() {
    $("#refresh-history").disabled = true;
    try { const response = await api("/api/orders"); state.orders = response.orders; renderOrders(); }
    catch (error) { notify(error.message, true, loadOrders); }
    finally { $("#refresh-history").disabled = false; }
  }
  function integrationDetails() {
    if (!state.config) { notify("Connect to the server to inspect the active integrations.", true); return; }
    const config = state.config;
    const model = config.ai_mode === "provider" ? (config.ai_model || "Not configured") : "No model calls in local rehearsal";
    openDialog({title: "PayPal + AI, end to end.", kicker: `BUILT WITH · TRACE COMMERCE ${config.project_version || ""}`, icon: "✦", content: [element("p", "", "AI turns your brief and budget into catalog suggestions. The server validates prices and totals. You review the cart before PayPal handles payment approval."), receiptLine("AI service", config.ai_provider || "Local rehearsal planner"), receiptLine("AI model", model), receiptLine("Payment platform", config.mode === "sandbox" ? "PayPal sandbox · OAuth + Orders v2" : "Rehearsal · PayPal is not called"), element("p", "", config.mode === "sandbox" ? "Checkout creates a PayPal sandbox order, redirects to PayPal for buyer approval, then verifies the captured order, USD amount and cart reference before issuing a receipt." : "This run simulates payment so you can practice. Configure PayPal sandbox and a real AI provider to demonstrate both integrations."), element("p", "", "The server keeps API keys private. Receipts retain the AI service/model used for the original plan alongside the payment references. All products are fictional; no real money moves.")], actions: [{label: "Back to my workspace", run: () => dialog.close()}]});
  }
  function about() {
    const provider = state.config?.ai_mode === "provider";
    openDialog({title: "A thoughtful shopping demo.", kicker: "TRACE COMMERCE", icon: "✦", content: [element("p", "", "TRACE turns a workspace brief into a catalog-backed cart, explains the selection, checks your budget, and keeps checkout in your hands."), element("p", "", "All products and prices are fictional. There is no delivery, tax calculation, stock reservation or real-money payment."), element("p", "", provider ? "AI provider mode is active. Your brief and catalog are sent to the configured model provider. Don’t enter private or sensitive information." : "Local planner mode is active. It uses deterministic matching rather than an AI model. Configure an AI provider and real PayPal sandbox credentials for a hackathon demonstration."), element("p", "", "Workspace and order access use this browser session. Clearing its cookies can remove your access. Merchant credentials remain on the server.")], actions: [{label: "Back to my workspace", run: () => dialog.close()}]});
  }
  async function handleReturn() {
    const params = new URLSearchParams(window.location.search);
    const checkout = params.get("checkout"), orderId = params.get("order");
    if (!checkout || !orderId) return;
    history.replaceState(null, "", window.location.pathname);
    try {
      const {orders} = await api("/api/orders"); state.orders = orders;
      const order = orders.find(order => order.id === orderId);
      if (!order) throw new Error("This order isn’t available in your current session. Use the same browser where checkout began.");
      if (checkout === "cancelled" || checkout === "canceled" || checkout === "cancel") { handleCancellationResult(await post(`/api/orders/${encodeURIComponent(order.id)}/cancel`)); }
      else if (checkout === "approved") { if (["COMPLETED", "SIMULATED"].includes(order.status)) showReceipt(order); else openCapture(order); }
    } catch (error) { notify(error.message, true); }
  }
  async function initialize() {
    $("#build-button").disabled = true;
    try {
      state.config = await api("/api/config");
      const catalog = await api("/api/catalog"); state.products = catalog.items;
      const real = state.config.mode === "sandbox", provider = state.config.ai_mode === "provider";
      $("#mode-badge").textContent = real ? "PayPal · sandbox" : "Payments · rehearsal";
      $("#ai-mode-badge").textContent = provider ? "AI · provider" : "AI · local rehearsal";
      $("#ai-integration-detail").textContent = provider ? `${state.config.ai_provider || "Configured AI provider"} · ${state.config.ai_model || "model not configured"}` : "Local rehearsal · no model calls";
      $("#paypal-integration-detail").textContent = real ? "Sandbox Orders v2 · you approve every payment" : "Rehearsal · no PayPal calls";
      $("#planning-step").textContent = provider ? "AI plans" : "Local plan";
      $("#planner-label").textContent = provider ? "AI assistant" : "Local planner · rehearsal";
      $("#privacy-label").textContent = provider ? "Your brief is sent to the configured AI provider. Keep sensitive information out of your brief." : "Local matching only. Your brief is stored for this session and is not sent to an AI provider.";
      renderCatalog();
      try { const saved = JSON.parse(sessionStorage.getItem("trace-plan") || "null"); if (saved?.session === state.config.csrf_token && saved.plan?.items) { state.plan = saved.plan; $("#prompt").value = saved.plan.prompt; $("#budget").value = saved.plan.budget_cents / 100; } else sessionStorage.removeItem("trace-plan"); } catch (_) { /* No restorable local state. */ }
      renderPlan();
      if ((provider && !state.config.ai_ready) || (real && !state.config.sandbox_ready)) notify("An integration isn’t configured yet. Check the project’s environment settings before demonstrating provider mode.", true);
      await handleReturn();
    } catch (error) { $("#mode-badge").textContent = "Connection unavailable"; $("#ai-mode-badge").textContent = "AI · unavailable"; $("#planner-label").textContent = "Waiting for server"; notify(error.message, true, initialize); }
    finally { $("#build-button").disabled = !state.config; }
  }
  document.addEventListener("click", event => { const button = event.target.closest("[data-view]"); if (button) showView(button.dataset.view); });
  $("#brief-form").addEventListener("submit", buildPlan);
  $$(".preset").forEach(button => button.addEventListener("click", () => { $("#prompt").value = button.dataset.prompt; $("#budget").value = button.dataset.budget; $("#prompt").focus(); }));
  $("#checkout-button").addEventListener("click", openCheckout);
  $("#refresh-history").addEventListener("click", loadOrders);
  $("#about-button").addEventListener("click", about);
  $("#integration-details-button").addEventListener("click", integrationDetails);
  $("#dialog-close").addEventListener("click", () => { if (!state.modalBusy) dialog.close(); });
  dialog.addEventListener("cancel", event => { if (state.modalBusy) event.preventDefault(); });
  initialize();
})();
