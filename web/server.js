import express from "express";
import fetch from "node-fetch";
import path from "path";
import { fileURLToPath } from "url";

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

const API_BASE = process.env.API_BASE || "http://api:8000";

async function apiGet(url) {
  const r = await fetch(url);
  const text = await r.text();
  try { return JSON.parse(text); } catch { return { raw: text, status: r.status }; }
}
async function apiPost(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {})
  });
  const text = await r.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${JSON.stringify(data)}`);
  return data;
}
async function getSettingsStatusSafe() {
  try { return await apiGet(`${API_BASE}/settings/status`); }
  catch (e) { return { error: String(e) }; }
}

app.get("/", async (req, res) => {
  res.render("index", { api: API_BASE, project_id: "", project: null, workflow: null, error: null });
});

app.post("/create", async (req, res) => {
  try {
    const data = await apiPost(`${API_BASE}/projects`, {
      project_type: "generic",
      targets: [{ id: "t1", host: "local" }],
      request_text: req.body.request_text || "run basic check"
    });
    res.render("index", { api: API_BASE, project_id: data.project_id, project: data.state, workflow: null, error: null });
  } catch (e) {
    res.render("index", { api: API_BASE, project_id: "", project: null, workflow: null, error: String(e) });
  }
});

app.post("/load", async (req, res) => {
  const project_id = (req.body.project_id || "").trim();
  try {
    const project = await apiGet(`${API_BASE}/projects/${project_id}`);
    res.render("index", { api: API_BASE, project_id, project, workflow: null, error: null });
  } catch (e) {
    res.render("index", { api: API_BASE, project_id, project: null, workflow: null, error: String(e) });
  }
});

app.post("/workflow/run", async (req, res) => {
  const project_id = (req.body.project_id || "").trim();
  const request_text = req.body.wf_request_text || "basic system snapshot";
  const timeout_s = Number(req.body.timeout_s || 60);
  const max_retries = Number(req.body.max_retries || 2);

  try {
    const workflow = await apiPost(`${API_BASE}/projects/${project_id}/run_workflow`, { request_text, timeout_s, max_retries });
    const project = await apiGet(`${API_BASE}/projects/${project_id}`);
    res.render("index", { api: API_BASE, project_id, project, workflow, error: null });
  } catch (e) {
    const project = project_id ? await apiGet(`${API_BASE}/projects/${project_id}`) : null;
    res.render("index", { api: API_BASE, project_id, project, workflow: null, error: String(e) });
  }
});

// Evidence ZIP proxy
app.get("/projects/:id/evidence.zip", async (req, res) => {
  const id = req.params.id;
  const url = `${API_BASE}/projects/${id}/evidence.zip`;
  const r = await fetch(url);
  if (!r.ok) {
    const text = await r.text();
    res.status(r.status).send(text);
    return;
  }
  const cd = r.headers.get("content-disposition");
  if (cd) res.setHeader("content-disposition", cd);
  res.setHeader("content-type", r.headers.get("content-type") || "application/zip");
  r.body.pipe(res);
});

// ---- MasterGate screens ----
app.get("/mastergate", async (req, res) => {
  const approvals = await apiGet(`${API_BASE}/approvals`);
  const settings = await getSettingsStatusSafe();
  res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: null });
});

app.post("/mastergate/request", async (req, res) => {
  try {
    const created = await apiPost(`${API_BASE}/mastergate/request`, {
      title: req.body.title || "Ask Master",
      draft_prompt: req.body.draft_prompt || "",
      context_snippets: req.body.context_snippets || "",
      require_approval: true
    });
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created, selected: created, settings, error: null });
  } catch (e) {
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: String(e) });
  }
});

app.get("/approvals/:id", async (req, res) => {
  const id = req.params.id;
  try {
    const selected = await apiGet(`${API_BASE}/approvals/${id}`);
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected, settings, error: null });
  } catch (e) {
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: String(e) });
  }
});

app.post("/approvals/:id/decide", async (req, res) => {
  const id = req.params.id;
  try {
    await apiPost(`${API_BASE}/approvals/${id}/decide`, {
      decision: req.body.decision,
      actor: req.body.actor || "admin",
      reason: req.body.reason || ""
    });
    const selected = await apiGet(`${API_BASE}/approvals/${id}`);
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected, settings, error: null });
  } catch (e) {
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: String(e) });
  }
});

app.post("/approvals/:id/ask_master", async (req, res) => {
  const id = req.params.id;
  try {
    await apiPost(`${API_BASE}/approvals/${id}/ask_master`, { provider: req.body.provider || "ollama" });
    const selected = await apiGet(`${API_BASE}/approvals/${id}`);
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected, settings, error: null });
  } catch (e) {
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: String(e) });
  }
});

// ✅ M2-2: Apply + Validate (closed loop)
app.post("/approvals/:id/apply_feedback_and_validate", async (req, res) => {
  const id = req.params.id;
  try {
    await apiPost(`${API_BASE}/approvals/${id}/apply_feedback_and_validate`, {
      actor: req.body.actor || "system",
      max_commands: Number(req.body.max_commands || 6),
      timeout_s: Number(req.body.timeout_s || 60),
      stop_on_fail: (req.body.stop_on_fail || "on") === "on"
    });
    const selected = await apiGet(`${API_BASE}/approvals/${id}`);
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected, settings, error: null });
  } catch (e) {
    const approvals = await apiGet(`${API_BASE}/approvals`);
    const settings = await getSettingsStatusSafe();
    res.render("mastergate", { api: API_BASE, approvals: approvals.items || [], created: null, selected: null, settings, error: String(e) });
  }
});

app.listen(80, "0.0.0.0", () => console.log("web listening on :80"));

// Approval Evidence ZIP proxy
app.get("/approvals/:id/evidence.zip", async (req, res) => {
  const id = req.params.id;
  const url = `${API_BASE}/approvals/${id}/evidence.zip`;

  const r = await fetch(url);
  if (!r.ok) {
    const text = await r.text();
    res.status(r.status).send(text);
    return;
  }

  const cd = r.headers.get("content-disposition");
  if (cd) res.setHeader("content-disposition", cd);
  res.setHeader("content-type", r.headers.get("content-type") || "application/zip");
  r.body.pipe(res);
});

// M2-6: Bulk decide proxy
app.post("/approvals/bulk_decide", async (req, res) => {
  try {
    const r = await fetch(`${API_BASE}/approvals/bulk_decide`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(req.body || {}),
    });
    const text = await r.text();
    res.status(r.status).send(text);
  } catch (e) {
    res.status(500).send(String(e));
  }
});
