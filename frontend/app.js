const form = document.getElementById("healthForm");
const results = document.getElementById("results");
const errorBox = document.getElementById("errorBox");
const submitBtn = document.getElementById("submitBtn");

const URGENCY_LABELS = {
  home_care: "Home Care - No immediate danger detected.",
  see_doctor: "See a Doctor - Medical evaluation recommended.",
  emergency: "Emergency - Seek immediate medical attention!",
};

const MATCH_LABELS = {
  exact: "Nearest - Your Country",
  region: "Nearest - Your Region",
  global_fallback: "Latest Global Outbreak",
};

function clearChildren(node) {
  node.replaceChildren();
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);

  if (className) {
    element.className = className;
  }

  if (text !== undefined) {
    element.textContent = text;
  }

  return element;
}

function createLink(className, text, href, openInNewTab = true) {
  const link = createElement("a", className, text);
  link.href = href;

  if (openInNewTab) {
    link.target = "_blank";
    link.rel = "noopener";
  }

  return link;
}

async function getErrorMessage(res) {
  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    try {
      const err = await res.json();
      if (typeof err?.detail === "string" && err.detail.trim()) {
        return err.detail;
      }
    } catch (_) {
      // Fall back to text handling below.
    }
  }

  try {
    const text = await res.text();
    if (text.trim()) {
      return text.trim();
    }
  } catch (_) {
    // Ignore and fall back to generic message.
  }

  return `Request failed with status ${res.status}`;
}

function appendRiskItem(container, risk) {
  const item = createElement("div", "risk-item");
  const badge = createElement("span", `risk-badge badge-${risk.risk_level}`, risk.risk_level.toUpperCase());
  const info = createElement("div", "risk-info");
  const title = createElement("strong", "", risk.condition);
  const description = createElement("p", "", risk.explanation);

  info.append(title, description);
  item.append(badge, info);
  container.appendChild(item);
}

function appendFlagItem(container, flag) {
  container.appendChild(createElement("li", "", flag));
}

function appendAlertItem(container, alert) {
  const item = createElement("div", `alert-item alert-${alert.match_type}`);
  const header = createElement("div", "alert-header");
  const title = createElement("strong", "", alert.title);
  const badge = createElement(
    "span",
    `match-badge badge-${alert.match_type}`,
    MATCH_LABELS[alert.match_type] || alert.match_type
  );
  const summary = createElement("p", "", alert.summary);
  const footer = createElement("div", "alert-footer");

  const dateText = alert.date
    ? new Date(alert.date).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Date unknown";

  const date = createElement("span", "alert-date", `Date: ${dateText}`);
  const source = createElement("span", "alert-source", alert.source);
  const link = createLink("", "Read full alert ->", alert.link);

  header.append(title, badge);
  footer.append(date, source, link);
  item.append(header, summary, footer);
  container.appendChild(item);
}

function appendFacilityItem(container, facility, index) {
  const item = createElement("div", "facility-item");
  const header = createElement("div", "facility-header");
  const indexBadge = createElement("span", "facility-index", String(index + 1));
  const title = createElement("strong", "", facility.name);
  const meta = createElement("div", "facility-meta");
  const address = createElement("span", "facility-address", `Address: ${facility.address}`);
  const actions = createElement("div", "facility-actions");

  header.append(indexBadge, title);

  if (facility.open_now === true) {
    header.appendChild(createElement("span", "open-badge", "Open"));
  } else if (facility.open_now === false) {
    header.appendChild(createElement("span", "closed-badge", "Closed"));
  }

  meta.appendChild(address);

  if (facility.phone) {
    const callLink = createLink("facility-btn btn-call", `Call ${facility.phone}`, `tel:${facility.phone}`, false);
    actions.appendChild(callLink);
  } else {
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(`${facility.name} ${facility.address} phone number`)}`;
    const searchLink = createLink("facility-btn btn-search", "Find Phone", searchUrl);
    actions.appendChild(searchLink);
  }

  const mapLink = createLink("facility-btn btn-map", "Open in Google Maps", facility.maps_url);
  actions.appendChild(mapLink);

  item.append(header, meta, actions);
  container.appendChild(item);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  results.classList.add("hidden");
  errorBox.classList.add("hidden");
  submitBtn.disabled = true;
  document.getElementById("btnText").classList.add("hidden");
  document.getElementById("btnLoader").classList.remove("hidden");

  const bmiVal = document.getElementById("bmi").value;
  const payload = {
    systolic_bp: parseInt(document.getElementById("systolic_bp").value),
    diastolic_bp: parseInt(document.getElementById("diastolic_bp").value),
    fasting_glucose: parseFloat(document.getElementById("fasting_glucose").value),
    age: parseInt(document.getElementById("age").value),
    bmi: bmiVal ? parseFloat(bmiVal) : null,
    symptoms: document.getElementById("symptoms").value.trim(),
    question: document.getElementById("question").value.trim() || null,
    country: document.getElementById("country").value.trim() || null,
    city: document.getElementById("city").value.trim() || null,
  };

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const message = await getErrorMessage(res);
      throw new Error(message);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    errorBox.textContent = `Error: ${err.message}`;
    errorBox.classList.remove("hidden");
  } finally {
    submitBtn.disabled = false;
    document.getElementById("btnText").classList.remove("hidden");
    document.getElementById("btnLoader").classList.add("hidden");
  }
});

function renderResults(data) {
  const banner = document.getElementById("urgencyBanner");
  banner.className = `urgency-banner urgency-${data.urgency}`;
  banner.textContent = `${URGENCY_LABELS[data.urgency] || data.urgency} - ${data.urgency_reason}`;

  const riskList = document.getElementById("riskList");
  clearChildren(riskList);
  data.risks.forEach((risk) => appendRiskItem(riskList, risk));

  document.getElementById("guidelineAnswer").textContent = data.guideline_answer;

  const flagSection = document.getElementById("symptomFlags");
  const flagList = document.getElementById("flagList");
  clearChildren(flagList);
  if (data.symptom_flags.length > 0) {
    data.symptom_flags.forEach((flag) => appendFlagItem(flagList, flag));
    flagSection.classList.remove("hidden");
  } else {
    flagSection.classList.add("hidden");
  }

  const alertSection = document.getElementById("outbreakAlerts");
  const alertList = document.getElementById("alertList");
  clearChildren(alertList);
  if (data.outbreak_alerts && data.outbreak_alerts.length > 0) {
    data.outbreak_alerts.forEach((alert) => appendAlertItem(alertList, alert));
    alertSection.classList.remove("hidden");
  } else {
    alertSection.classList.add("hidden");
  }

  const facilitySection = document.getElementById("nearbyFacilities");
  const facilityList = document.getElementById("facilityList");
  clearChildren(facilityList);
  if (data.nearby_facilities && data.nearby_facilities.length > 0) {
    data.nearby_facilities.forEach((facility, index) => appendFacilityItem(facilityList, facility, index));
    facilitySection.classList.remove("hidden");
  } else {
    facilitySection.classList.add("hidden");
  }

  results.classList.remove("hidden");
  results.scrollIntoView({ behavior: "smooth" });
}
