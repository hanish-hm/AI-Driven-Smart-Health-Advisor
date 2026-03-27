const form       = document.getElementById("healthForm");
const results    = document.getElementById("results");
const errorBox   = document.getElementById("errorBox");
const submitBtn  = document.getElementById("submitBtn");

const URGENCY_LABELS = {
  home_care:  "✅ Home Care — No immediate danger detected.",
  see_doctor: "⚠️ See a Doctor — Medical evaluation recommended.",
  emergency:  "🚨 Emergency — Seek immediate medical attention!",
};

const MATCH_LABELS = {
  exact:           "📍 Nearest — Your Country",
  region:          "🌏 Nearest — Your Region",
  global_fallback: "🌍 Latest Global Outbreak",
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  results.classList.add("hidden");
  errorBox.classList.add("hidden");
  submitBtn.disabled = true;
  document.getElementById("btnText").classList.add("hidden");
  document.getElementById("btnLoader").classList.remove("hidden");

  const bmiVal = document.getElementById("bmi").value;
  const payload = {
    systolic_bp:     parseInt(document.getElementById("systolic_bp").value),
    diastolic_bp:    parseInt(document.getElementById("diastolic_bp").value),
    fasting_glucose: parseFloat(document.getElementById("fasting_glucose").value),
    age:             parseInt(document.getElementById("age").value),
    bmi:             bmiVal ? parseFloat(bmiVal) : null,
    symptoms:        document.getElementById("symptoms").value.trim(),
    question:        document.getElementById("question").value.trim() || null,
    country:         document.getElementById("country").value.trim() || null,
    city:            document.getElementById("city").value.trim() || null,
  };

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
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
  // Urgency banner
  const banner = document.getElementById("urgencyBanner");
  banner.className = `urgency-banner urgency-${data.urgency}`;
  banner.textContent = `${URGENCY_LABELS[data.urgency] || data.urgency} — ${data.urgency_reason}`;

  // Risk list
  const riskList = document.getElementById("riskList");
  riskList.innerHTML = data.risks.map(r => `
    <div class="risk-item">
      <span class="risk-badge badge-${r.risk_level}">${r.risk_level.toUpperCase()}</span>
      <div class="risk-info">
        <strong>${r.condition}</strong>
        <p>${r.explanation}</p>
      </div>
    </div>
  `).join("");

  // Guideline answer
  document.getElementById("guidelineAnswer").textContent = data.guideline_answer;

  // Symptom flags
  const flagSection = document.getElementById("symptomFlags");
  const flagList    = document.getElementById("flagList");
  if (data.symptom_flags.length > 0) {
    flagList.innerHTML = data.symptom_flags.map(f => `<li>${f}</li>`).join("");
    flagSection.classList.remove("hidden");
  } else {
    flagSection.classList.add("hidden");
  }

  // Outbreak alerts
  const alertSection = document.getElementById("outbreakAlerts");
  const alertList    = document.getElementById("alertList");
  if (data.outbreak_alerts && data.outbreak_alerts.length > 0) {
    alertList.innerHTML = data.outbreak_alerts.map(a => `
      <div class="alert-item alert-${a.match_type}">
        <div class="alert-header">
          <strong>${a.title}</strong>
          <span class="match-badge badge-${a.match_type}">${MATCH_LABELS[a.match_type] || a.match_type}</span>
        </div>
        <p>${a.summary}</p>
        <div class="alert-footer">
          <span class="alert-date">🕐 ${a.date ? new Date(a.date).toLocaleDateString("en-GB", {day:"numeric", month:"short", year:"numeric"}) : "Date unknown"}</span>
          <span class="alert-source">${a.source}</span>
          <a href="${a.link}" target="_blank" rel="noopener">Read full alert →</a>
        </div>
      </div>
    `).join("");
    alertSection.classList.remove("hidden");
  } else {
    alertSection.classList.add("hidden");
  }

  // Nearby facilities
  const facilitySection = document.getElementById("nearbyFacilities");
  const facilityList    = document.getElementById("facilityList");
  if (data.nearby_facilities && data.nearby_facilities.length > 0) {
    facilityList.innerHTML = data.nearby_facilities.map((f, i) => `
      <div class="facility-item">
        <div class="facility-header">
          <span class="facility-index">${i + 1}</span>
          <strong>${f.name}</strong>
          ${f.open_now === true  ? '<span class="open-badge">● Open</span>' : ''}
          ${f.open_now === false ? '<span class="closed-badge">● Closed</span>' : ''}
        </div>
        <div class="facility-meta">
          <span class="facility-address">📍 ${f.address}</span>
        </div>
        <div class="facility-actions">
          ${f.phone
            ? `<a class="facility-btn btn-call" href="tel:${f.phone}">📞 Call ${f.phone}</a>`
            : `<a class="facility-btn btn-search" href="https://www.google.com/search?q=${encodeURIComponent(f.name + ' ' + f.address + ' phone number')}" target="_blank" rel="noopener">🔍 Find Phone</a>`
          }
          <a class="facility-btn btn-map" href="${f.maps_url}" target="_blank" rel="noopener">🗺️ Open in Google Maps</a>
        </div>
      </div>
    `).join("");
    facilitySection.classList.remove("hidden");
  } else {
    facilitySection.classList.add("hidden");
  }

  results.classList.remove("hidden");
  results.scrollIntoView({ behavior: "smooth" });
}
