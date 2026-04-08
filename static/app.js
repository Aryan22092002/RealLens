const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const snapshot = document.getElementById("snapshot");

const startBtn = document.getElementById("startBtn");
const captureBtn = document.getElementById("captureBtn");
const predictBtn = document.getElementById("predictBtn");
const recaptureBtn = document.getElementById("recaptureBtn");

const productNameInput = document.getElementById("productName");
const productNameError = document.getElementById("productNameError");

const predictionText = document.getElementById("predictionText");
const confidenceText = document.getElementById("confidenceText");

const insightPanel = document.getElementById("insightPanel");
const insightSubtitle = document.getElementById("insightSubtitle");
const wikiBlock = document.getElementById("wikiBlock");
const wikiThumb = document.getElementById("wikiThumb");
const wikiTitle = document.getElementById("wikiTitle");
const wikiExtract = document.getElementById("wikiExtract");
const wikiLink = document.getElementById("wikiLink");
const refNote = document.getElementById("refNote");
const refGrid = document.getElementById("refGrid");
const refBest = document.getElementById("refBest");
const refBlockTitle = document.getElementById("refBlockTitle");
const webSearchBlock = document.getElementById("webSearchBlock");
const webSearchList = document.getElementById("webSearchList");
const webSearchQuery = document.getElementById("webSearchQuery");
const resultWebSearch = document.getElementById("resultWebSearch");

let capturedImageData;
let capturedImageBase64;

/** POST must hit Flask (port 5000), not Live Server / file — avoids HTTP 405. */
function apiBaseUrl() {
  if (/^file:/i.test(window.location.href)) return "http://127.0.0.1:5000";
  const port = window.location.port;
  if (port === "5000") return window.location.origin;
  return "http://127.0.0.1:5000";
}

const ANALYZE_ENDPOINT = `${apiBaseUrl()}/api/analyze`;
const PRODUCT_CONTEXT_ENDPOINT = `${apiBaseUrl()}/api/product-context`;

/** Load Wikipedia-style + web links for a name (works when full analyze failed). */
async function enrichWithProductContext(baseResult, productName) {
  try {
    const url = `${PRODUCT_CONTEXT_ENDPOINT}?product_name=${encodeURIComponent(productName)}`;
    const r = await fetch(url);
    if (!r.ok) return baseResult;
    const ctx = await r.json();
    return {
      ...baseResult,
      product_info: ctx.product_info || baseResult.product_info,
      web_search: ctx.web_search || baseResult.web_search,
      brand_detection: { ...baseResult.brand_detection, ...ctx.brand_detection },
    };
  } catch {
    return baseResult;
  }
}

/** When the server is unreachable or returns an error, show neutral 50% (same shape as API). */
function buildFallbackResult(productName, reason) {
  const name = (productName || "Device").trim() || "Device";
  return {
    brand_detection: {
      product_name: name,
      primary_brand: "Unknown",
      confidence: 50,
      alternatives: [],
    },
    image_quality: { sharpness: 50, saturation: 50 },
    authentication: {
      status: "Uncertain",
      confidence: 50,
      factors: {},
      score: 50,
      visual_similarity_percent: null,
    },
    reference_match: {
      image_matching_skipped: true,
      query: "",
      reference_image_urls: [],
      per_reference: [],
      best_visual_similarity_percent: null,
      method: null,
      note: reason || "Could not analyze. Default estimate shown.",
    },
    product_info: { title: name, extract: null, page_url: null, thumbnail: null },
    web_search: { query: "", results: [], validated: false },
    final_verdict: {
      status: "Uncertain",
      confidence: 50,
      recommendation:
        "Analysis unavailable. Default neutral score: 50%. Check the product with an official seller or manufacturer.",
    },
    degraded: true,
  };
}

/** Keep phrase and token lists in sync with app.py (is_electronics_product_name). */
const ELECTRONICS_PHRASES = [
  "macbook",
  "iphone",
  "ipad",
  "airpods",
  "air pods",
  "apple watch",
  "galaxy s",
  "galaxy z",
  "galaxy tab",
  "galaxy bud",
  "galaxy watch",
  "google pixel",
  "surface pro",
  "surface laptop",
  "surface book",
  "surface go",
  "playstation",
  "ps5",
  "ps4",
  "ps vr",
  "xbox",
  "xbox series",
  "nintendo switch",
  "steam deck",
  "steamdeck",
  "meta quest",
  "oculus quest",
  "smart tv",
  "android tv",
  "fire tv",
  "apple tv",
  "mechanical keyboard",
  "gaming laptop",
  "gaming mouse",
  "gaming headset",
  "gaming pc",
  "wireless charger",
  "fast charger",
  "power bank",
  "powerbank",
  "bluetooth speaker",
  "smart speaker",
  "sound bar",
  "soundbar",
  "graphics card",
  "video card",
  "wireless earbuds",
  "vr headset",
  "noise cancelling",
  "noise-canceling",
  "smart watch",
  "smartwatch",
  "robot vacuum",
  "roomba",
];

const ELECTRONICS_TOKENS = new Set(
  `
iphone ipad ipod imac macbook macmini macstudio macpro airpods airpod
galaxy pixel oneplus xiaomi redmi poco oppo vivo realme fairphone nothing
smartphone android handheld
laptop chromebook notebook ultrabook thinkpad ideapad zenbook vivobook
legion alienware surface inspiron pavilion xps spectre envy omen blade
tablet kindle ereader e-reader
earbuds earphones headphones headset earbud
smartwatch fitbit garmin whoop
playstation psvr ps4 ps5 xbox nintendo switch steamdeck
nvidia geforce radeon rtx rx580 rx6700 ryzen threadripper epyc
intel celeron pentium xeon snapdragon exynos bionic tensor
m1 m2 m3 m4 a14 a15 a16 a17 a18
gpu ssd nvme hdd motherboard
router modem mesh eero ubiquiti tplink netgear orbi
keyboard mouse webcam trackpad touchpad
monitor ultrawide oled qled mini-led
dslr mirrorless gopro insta360 dji mavic drone
charger powerbank anker belkin logitech razer corsair steelseries hyperx
beats bose jabra sennheiser shure
dell asus acer msi lenovo hp samsung apple google microsoft sony lg
huawei motorola nokia blackberry
oculus quest echo dot firestick chromecast roku appletv homepod nest
soundbar subwoofer amplifier dac
  `
    .trim()
    .split(/\s+/)
);

function isElectronicsProductName(name) {
  const lowered = name.trim().toLowerCase();
  if (!lowered) return false;
  for (let i = 0; i < ELECTRONICS_PHRASES.length; i++) {
    if (lowered.includes(ELECTRONICS_PHRASES[i])) return true;
  }
  const tokens = lowered.match(/[a-z0-9]+/g) || [];
  for (let i = 0; i < tokens.length; i++) {
    if (ELECTRONICS_TOKENS.has(tokens[i])) return true;
  }
  return /\btv\b/.test(lowered);
}

function setProductNameValidity(ok, message) {
  if (!productNameInput || !productNameError) return;
  if (ok) {
    productNameError.classList.add("hidden");
    productNameError.textContent = "";
    productNameInput.classList.remove("input-invalid");
    productNameInput.setAttribute("aria-invalid", "false");
  } else {
    productNameError.classList.remove("hidden");
    productNameError.textContent = message;
    productNameInput.classList.add("input-invalid");
    productNameInput.setAttribute("aria-invalid", "true");
  }
}

startBtn.addEventListener("click", startCamera);
captureBtn.addEventListener("click", captureImage);
predictBtn.addEventListener("click", analyzeProduct);
recaptureBtn.addEventListener("click", recaptureImage);

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    startBtn.disabled = true;
    startBtn.textContent = "Camera Started";
    captureBtn.disabled = false;
    predictionText.innerText = "Camera ready. Capture a product image.";
  } catch (error) {
    predictionText.innerText = "❌ Camera access denied.";
    console.error("Camera error:", error);
  }
}

const MAX_CAPTURE_SIDE = 1280;
const JPEG_QUALITY = 0.85;

/** Downscale for smaller JSON payloads and reliable API parsing. */
function canvasToJpegDataUrl(sourceCanvas) {
  let w = sourceCanvas.width;
  let h = sourceCanvas.height;
  if (w <= 0 || h <= 0) return null;
  const scale = Math.min(1, MAX_CAPTURE_SIDE / Math.max(w, h));
  const tw = Math.max(1, Math.round(w * scale));
  const th = Math.max(1, Math.round(h * scale));
  const out = document.createElement("canvas");
  out.width = tw;
  out.height = th;
  const octx = out.getContext("2d");
  octx.drawImage(sourceCanvas, 0, 0, tw, th);
  return out.toDataURL("image/jpeg", JPEG_QUALITY);
}

function captureImage() {
  if (!video.videoWidth || !video.videoHeight) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);

  capturedImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

  capturedImageBase64 = canvasToJpegDataUrl(canvas);
  if (!capturedImageBase64) {
    predictionText.innerText = " Could not encode image.";
    return;
  }

  snapshot.src = capturedImageBase64;
  snapshot.hidden = false;
  video.hidden = true;

  predictionText.innerText = "Image captured. Ready for analysis.";
  confidenceText.innerText = "";
  predictBtn.disabled = false;

  captureBtn.disabled = true;
  captureBtn.textContent = "Image Captured";
}

function recaptureImage() {
  snapshot.hidden = true;
  snapshot.src = "";
  video.hidden = false;

  predictionText.innerText = "Camera ready. Capture a product image.";
  confidenceText.innerText = "";

  captureBtn.disabled = false;
  captureBtn.textContent = "Capture";
  predictBtn.disabled = true;
  recaptureBtn.disabled = true;

  capturedImageData = null;
  capturedImageBase64 = null;

  hideInsightPanel();
  setProductNameValidity(true, "");
}

function hideInsightPanel() {
  insightPanel.classList.add("hidden");
  wikiBlock.classList.add("hidden");
  wikiThumb.hidden = true;
  refGrid.innerHTML = "";
  if (webSearchBlock) {
    webSearchBlock.classList.add("hidden");
    webSearchList.innerHTML = "";
    webSearchQuery.textContent = "";
  }
  if (resultWebSearch) {
    resultWebSearch.classList.add("hidden");
    resultWebSearch.innerHTML = "";
  }
}

function fillWebSearchPanel(ws) {
  const results = (ws && ws.results) || [];
  if (!webSearchBlock || !webSearchList) return;
  if (!results.length) {
    webSearchBlock.classList.add("hidden");
    webSearchList.innerHTML = "";
    webSearchQuery.textContent = "";
    return;
  }
  webSearchBlock.classList.remove("hidden");
  webSearchQuery.textContent = ws.query ? `Query: ${ws.query}` : "";
  webSearchList.innerHTML = "";
  results.forEach((row) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = row.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = row.title || row.url || "Link";
    li.appendChild(a);
    if (row.snippet) {
      const span = document.createElement("div");
      span.className = "subtle";
      span.style.marginTop = "0.25rem";
      span.style.fontSize = "0.82rem";
      span.textContent = row.snippet;
      li.appendChild(span);
    }
    webSearchList.appendChild(li);
  });
}

function fillResultWebSearch(ws) {
  if (!resultWebSearch) return;
  const results = (ws && ws.results) || [];
  if (!results.length) {
    resultWebSearch.classList.add("hidden");
    resultWebSearch.innerHTML = "";
    return;
  }
  resultWebSearch.classList.remove("hidden");
  const parts = ["<strong>Web references</strong>"];
  results.slice(0, 3).forEach((row) => {
    const u = row.url || "#";
    const t = row.title || "Link";
    parts.push(`<div><a href="${u}" target="_blank" rel="noopener noreferrer">${t}</a></div>`);
  });
  resultWebSearch.innerHTML = parts.join("");
}

function displayInsight(result) {
  const productName = result.brand_detection?.product_name || "";
  insightSubtitle.textContent = productName
    ? `What you searched: “${productName}”`
    : "";

  fillWebSearchPanel(result.web_search);

  const info = result.product_info;
  if (info && info.title) {
    wikiBlock.classList.remove("hidden");
    wikiTitle.textContent = info.title || productName || "Product";
    wikiExtract.textContent =
      info.extract ||
      "No Wikipedia summary matched this exact name. Try a broader name (e.g. brand + model).";
    if (info.page_url) {
      wikiLink.href = info.page_url;
      wikiLink.hidden = false;
    } else {
      wikiLink.hidden = true;
    }
    if (info.thumbnail) {
      wikiThumb.src = info.thumbnail;
      wikiThumb.hidden = false;
      wikiThumb.alt = info.title || "Product thumbnail";
    } else {
      wikiThumb.hidden = true;
      wikiThumb.removeAttribute("src");
    }
  } else {
    wikiBlock.classList.add("hidden");
  }

  const ref = result.reference_match || {};
  refNote.textContent = ref.note || "";

  if (refBlockTitle) {
    refBlockTitle.textContent = ref.image_matching_skipped
      ? "Image matching "
      : "Reference images & match";
  }

  refGrid.innerHTML = "";
  if (ref.image_matching_skipped) {
    const skipMsg = document.createElement("p");
    skipMsg.className = "subtle";
    skipMsg.style.margin = "0";
    skipMsg.textContent =
      " Use Wikipedia and web links above.";
    refGrid.appendChild(skipMsg);
    refBest.textContent = "";
    insightPanel.classList.remove("hidden");
    return;
  }

  const rows = ref.per_reference || [];
  rows.forEach((row) => {
    const cell = document.createElement("div");
    cell.className = "ref-cell";
    const img = document.createElement("img");
    img.className = "ref-thumb";
    img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    img.alt = "Reference product image";
    img.src = row.url;
    img.onerror = () => {
      img.remove();
      const ph = document.createElement("div");
      ph.className = "ref-placeholder";
      ph.textContent = "Preview blocked";
      cell.insertBefore(ph, cap);
    };
    const cap = document.createElement("p");
    cap.className = "ref-cap";
    if (row.similarity_percent != null) {
      cap.textContent = `${row.similarity_percent}% similar`;
    } else if (row.error) {
      cap.textContent = "Could not compare";
      cap.title = row.error;
    } else {
      cap.textContent = "—";
    }
    cell.appendChild(img);
    cell.appendChild(cap);
    refGrid.appendChild(cell);
  });

  if (!rows.length && (ref.reference_image_urls || []).length === 0) {
    const empty = document.createElement("p");
    empty.className = "subtle";
    empty.textContent = "No reference images returned for this query.";
    refGrid.appendChild(empty);
  }

  const best = ref.best_visual_similarity_percent;
  if (best != null) {
    refBest.textContent = `Best visual match vs references: ${best}% (pHash — lighting and angle affect this).`;
  } else {
    refBest.textContent = "";
  }

  insightPanel.classList.remove("hidden");
}

async function analyzeProduct() {
  if (!capturedImageBase64) {
    predictionText.innerText = " No image captured.";
    return;
  }

  const productName = (productNameInput?.value || "").trim() || "Electronic device";
  setProductNameValidity(true, "");

  try {
    predictionText.innerText = "Analyzing…";
    confidenceText.innerText = `Using API: ${ANALYZE_ENDPOINT}`;
    predictBtn.disabled = true;

    const payload = {
      image: capturedImageBase64,
      product_name: productName,
      filename: productName.replace(/\s+/g, "_").slice(0, 80),
    };

    let response;
    try {
      response = await fetch(ANALYZE_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=UTF-8",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });
    } catch (netErr) {
      let fb = buildFallbackResult(
        productName,
        "Network error — is Flask running? (python app.py) Try http://127.0.0.1:5000"
      );
      fb = await enrichWithProductContext(fb, productName);
      fb.reference_match = {
        ...fb.reference_match,
        image_matching_skipped: true,
        note:
          (fb.reference_match && fb.reference_match.note) ||
          "Could not reach analyze API; image matching skipped.",
      };
      displayResults(fb);
      displayInsight(fb);
      console.error(netErr);
      predictBtn.disabled = false;
      recaptureBtn.disabled = false;
      return;
    }

    const rawText = await response.text();
    let result;
    try {
      result = rawText ? JSON.parse(rawText) : {};
    } catch {
      let fb = buildFallbackResult(
        productName,
        `HTTP ${response.status} — response was not JSON (often wrong server or 405).`
      );
      fb = await enrichWithProductContext(fb, productName);
      fb.reference_match = {
        ...fb.reference_match,
        image_matching_skipped: true,
        note: fb.reference_match?.note || "Bad API response; image matching skipped.",
      };
      displayResults(fb);
      displayInsight(fb);
      predictBtn.disabled = false;
      recaptureBtn.disabled = false;
      return;
    }

    if (!response.ok) {
      let fb = buildFallbackResult(
        productName,
        result.error || `HTTP ${response.status} (e.g. 405 = wrong URL or method).`
      );
      fb = await enrichWithProductContext(fb, productName);
      fb.reference_match = {
        ...fb.reference_match,
        image_matching_skipped: true,
        note: fb.reference_match?.note || "Request failed; image matching skipped.",
      };
      displayResults(fb);
      displayInsight(fb);
      predictBtn.disabled = false;
      recaptureBtn.disabled = false;
      return;
    }

    displayResults(result);
    displayInsight(result);
  } catch (error) {
    let fb = buildFallbackResult(productName, String(error.message || error));
    fb = await enrichWithProductContext(fb, productName);
    fb.reference_match = {
      ...fb.reference_match,
      image_matching_skipped: true,
      note: fb.reference_match?.note || "Error during analyze; image matching skipped.",
    };
    displayResults(fb);
    displayInsight(fb);
    console.error("Analysis error:", error);
    predictBtn.disabled = false;
    recaptureBtn.disabled = false;
  }
}

function displayResults(result) {
  const verdict = result.final_verdict || {};
  const brandInfo = result.brand_detection || {};
  const refm = result.reference_match || {};

  const st = verdict.status || "Uncertain";
  const statusEmoji = st.includes("Genuine")
    ? "✅"
    : st.includes("Uncertain")
      ? "⚠️"
      : "❌";

  const productLabel = brandInfo.product_name
    ? `Product: ${brandInfo.product_name}`
    : "";
  predictionText.innerHTML = `
    <strong>${statusEmoji} ${st}</strong><br>
    Brand estimate: ${brandInfo.primary_brand || "Unknown"} (${brandInfo.confidence ?? 50}% confidence)
    ${productLabel ? `<br><small>${productLabel}</small>` : ""}
  `;

  const vis =
    refm && refm.best_visual_similarity_percent != null
      ? ` · Reference match: ${refm.best_visual_similarity_percent}%`
      : "";

  const sharp =
    result.image_quality && typeof result.image_quality.sharpness === "number"
      ? Math.round(result.image_quality.sharpness)
      : "—";
  const degradedNote = result.degraded
    ? "<br><small>Offline / fallback mode — neutral 50% estimate.</small>"
    : "";

  confidenceText.innerHTML = `
    Confidence: ${verdict.confidence ?? 50}%${vis} ·
    Image quality (sharpness): ${sharp}${degradedNote}<br>
    <small>${verdict.recommendation || ""}</small>
  `;

  fillResultWebSearch(result.web_search);

  console.log("Analysis result:", result);

  recaptureBtn.disabled = false;
  predictBtn.disabled = false;
}

productNameInput?.addEventListener("input", () => {
  const v = (productNameInput.value || "").trim();
  if (!v) {
    setProductNameValidity(true, "");
    return;
  }
  if (isElectronicsProductName(v)) setProductNameValidity(true, "");
});

productNameInput?.addEventListener("blur", () => {
  const v = (productNameInput.value || "").trim();
  if (v && !isElectronicsProductName(v)) {
    setProductNameValidity(
      false,
      "That does not look like an electronic device. Add a device type or brand (e.g. Pixel, Switch, RTX 4070)."
    );
  }
});

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".chip[data-device]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = btn.getAttribute("data-device") || "";
      if (productNameInput) {
        productNameInput.value = v;
        productNameInput.focus();
        setProductNameValidity(true, "");
      }
    });
  });
  console.log("RealLens loaded");
});
