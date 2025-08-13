const form = document.getElementById("form");
const results = document.getElementById("results");
const resultTitle = document.getElementById("resultTitle");
const resultMeta = document.getElementById("resultMeta");
const adviceList = document.getElementById("adviceList");
const actionsDiv = document.getElementById("actions");
const analyzeBtn = document.getElementById("analyzeBtn");

function toast(msg) {
  alert(msg);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing...";

  const fd = new FormData(form);
  try {
    const res = await fetch("/predict", { method: "POST", body: fd });
    const data = await res.json();
    if (!data.ok) {
      toast(data.error || "Something went wrong");
      return;
    }
    // Render results
    results.style.display = "block";
    resultTitle.textContent = `${data.prediction.friendly}`;
    resultMeta.textContent = `Confidence: ${data.prediction.confidence} • Crop: ${data.crop}`;

    adviceList.innerHTML = "";
    data.advice.forEach((step) => {
      const li = document.createElement("li");
      li.textContent = step;
      adviceList.appendChild(li);
    });

    actionsDiv.innerHTML = "";
    data.actions.forEach((a) => {
      const btn = document.createElement("button");
      btn.className = "action-btn";
      btn.textContent = a.label;
      btn.onclick = () => doAction(a.id, data.crop, data.prediction.label);
      actionsDiv.appendChild(btn);
    });
  } catch (err) {
    toast(err.message || String(err));
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze";
  }
});

async function doAction(action, crop, disease) {
  try {
    const res = await fetch("/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, crop, disease }),
    });
    const data = await res.json();
    if (!data.ok) {
      toast(data.error || "Action failed");
      return;
    }

    if (data.type === "treatment_steps") {
      toast(`${data.title}\n\n- ${data.steps.join("\n- ")}`);
    } else if (data.type === "preventive_schedule") {
      toast(`${data.title}\n\n- ${data.schedule.join("\n- ")}`);
    } else if (data.type === "find_store") {
      const a = document.createElement("a");
      a.href = data.maps_url;
      a.target = "_blank";
      a.className = "link";
      a.textContent = "Open nearby agri stores (Google Maps)";
      actionsDiv.appendChild(a);
      toast("Opening maps link in a new tab.");
      window.open(data.maps_url, "_blank");
    } else if (data.type === "set_reminder") {
      toast(`${data.title}\n\n${data.message}`);
    } else {
      toast("Unknown action type");
    }
  } catch (err) {
    toast(err.message || String(err));
  }
}
