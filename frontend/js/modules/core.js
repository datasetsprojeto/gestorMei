const { API_BASE, state, escapeHtml, formatCurrency, formatDate } = window.GestorMei;

const toast = (...args) => window.toast(...args);
const initDashboardPeriodControls = (...args) => window.initDashboardPeriodControls(...args);
const initSalesPeriodControls = (...args) => window.initSalesPeriodControls(...args);
const fetchProducts = (...args) => window.fetchProducts(...args);
const fetchSales = (...args) => window.fetchSales(...args);
const fetchStats = (...args) => window.fetchStats(...args);
const fetchMonthlyStats = (...args) => window.fetchMonthlyStats(...args);
const fetchStockEntries = (...args) => window.fetchStockEntries(...args);
const carregarMesesSalvos = (...args) => window.carregarMesesSalvos(...args);
const fetchEmployeeAnalytics = (...args) => window.fetchEmployeeAnalytics(...args);
const renderDashboard = (...args) => window.renderDashboard(...args);
const renderVendas = (...args) => window.renderVendas(...args);
const renderProdutos = (...args) => window.renderProdutos(...args);
const renderEstoque = (...args) => window.renderEstoque(...args);
const renderEntradas = (...args) => window.renderEntradas(...args);
const renderFuncionarios = (...args) => window.renderFuncionarios(...args);
const syncEmployeePeriodChips = (...args) => window.syncEmployeePeriodChips(...args);
const populateProductSelectors = (...args) => window.populateProductSelectors(...args);
const initEntriesPeriodControls = (...args) => window.initEntriesPeriodControls(...args);

async function api(path, options = {}, auth = true) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = { raw: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.error || data.message || `Erro ${response.status}`);
  }

  return data;
}

function showApp() {
  document.getElementById("login-screen").style.display = "none";
  document.getElementById("app").style.display = "flex";
  const userName = state.user?.name || "Admin";
  document.querySelector(".user-name").textContent = userName;
  document.querySelector(".user-avatar").textContent = userName.slice(0, 1).toUpperCase();
  const navFuncionarios = document.getElementById("nav-funcionarios");
  const navLimpeza = document.getElementById("nav-limpeza");
  const sidebarAdmin = document.getElementById("sidebar-admin");
  const isOwner = state.user?.is_owner !== false;
  if (navFuncionarios) {
    navFuncionarios.style.display = isOwner ? "flex" : "none";
  }
  if (navLimpeza) {
    navLimpeza.style.display = isOwner ? "flex" : "none";
  }
  if (sidebarAdmin) {
    sidebarAdmin.style.display = isOwner ? "block" : "none";
  }
  initDashboardPeriodControls();
  initSalesPeriodControls();
  initEntriesPeriodControls();
}

function showLogin() {
  document.getElementById("app").style.display = "none";
  document.getElementById("login-screen").style.display = "flex";
  document.getElementById("login-screen").classList.remove("hidden");
}

async function doLogin() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-pass").value;

  if (!email || !password) {
    toast("Preencha e-mail e senha.");
    return;
  }

  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false);

    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem("gestormei_token", state.token);
    localStorage.setItem("gestormei_user", JSON.stringify(state.user));
    showApp();
    await refreshAll();
    toast("Login realizado com sucesso.");
  } catch (error) {
    toast(`Falha no login: ${error.message}`);
  }
}

function toggleAccountForm() {
  const form = document.getElementById("account-form");
  const shouldOpen = !form.classList.contains("open");
  form.classList.toggle("open", shouldOpen);
  state.creatingAccount = shouldOpen;
  if (shouldOpen) {
    document.getElementById("register-name").focus();
  }
}

async function doRegister() {
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const phone = document.getElementById("register-phone").value.trim();

  if (!name || !email || !phone) {
    toast("Preencha nome, e-mail e telefone para criar a conta.");
    return;
  }

  try {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, phone }),
    }, false);

    document.getElementById("register-name").value = "";
    document.getElementById("register-email").value = "";
    document.getElementById("register-phone").value = "";

    document.getElementById("login-email").value = email;
    document.getElementById("login-pass").value = "";
    toast("Conta criada. A senha foi enviada por e-mail.");
    toggleAccountForm();
  } catch (error) {
    toast(`Falha ao criar conta: ${error.message}`);
  }
}

function doLogout() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("gestormei_token");
  localStorage.removeItem("gestormei_user");
  showLogin();
}

function goTo(page, el) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById(`page-${page}`).classList.add("active");
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  el.classList.add("active");
  const titles = {
    dashboard: "Dashboard",
    vendas: "Vendas",
    produtos: "Produtos",
    estoque: "Estoque",
    entradas: "Entradas",
    funcionarios: "Funcionários",
    limpeza: "Limpar Dados",
  };
  document.getElementById("page-title").textContent = titles[page];
  if (page === "limpeza") {
    fetchAuditLogs(false);
  }
}

function statusBadge(qty, min, max) {
  if (qty <= min * 0.5) return '<span class="badge low">Critico</span>';
  if (qty <= min) return '<span class="badge med">Baixo</span>';
  if (qty >= max * 0.9) return '<span class="badge ok">Alto</span>';
  return '<span class="badge ok">Normal</span>';
}

async function refreshAll() {
  const today = new Date();
  document.getElementById("date-badge").textContent = today.toLocaleDateString("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  await Promise.all([
    fetchProducts(),
    fetchSales(),
    fetchStats(),
    fetchMonthlyStats(),
    fetchStockEntries(),
    carregarMesesSalvos(true),
    fetchEmployeeAnalytics(false),
  ]);
  renderDashboard();
  renderVendas(document.getElementById("search-vendas").value || "");
  renderProdutos(document.getElementById("search-prod").value || "");
  renderEstoque(document.getElementById("search-est").value || "");
  renderEntradas(document.getElementById("search-entradas")?.value || "");
  renderFuncionarios();
  renderAuditLogs();
  syncEmployeePeriodChips();
  populateProductSelectors();
}

async function fetchAuditLogs(showToast = false) {
  if (state.user?.is_owner === false) {
    state.auditLogs = [];
    renderAuditLogs();
    return;
  }

  try {
    const data = await api("/auth/audit-logs?limit=150");
    state.auditLogs = data.logs || [];
    renderAuditLogs();
    if (showToast) toast("Auditoria atualizada.");
  } catch (error) {
    if (showToast) toast(`Falha ao carregar auditoria: ${error.message}`);
  }
}

function renderAuditLogs() {
  const tb = document.getElementById("tb-audit-logs");
  if (!tb) return;

  if (state.user?.is_owner === false) {
    tb.innerHTML = '<tr><td colspan="4" style="color:var(--muted)">Apenas o proprietário visualiza a auditoria.</td></tr>';
    return;
  }

  if (!state.auditLogs.length) {
    tb.innerHTML = '<tr><td colspan="4" style="color:var(--muted)">Sem registros de auditoria.</td></tr>';
    return;
  }

  tb.innerHTML = state.auditLogs.map((entry) => {
    const action = escapeHtml(entry.action || "-");
    const resource = `${escapeHtml(entry.resource_type || "-")} #${escapeHtml(entry.resource_id || "-")}`;
    const details = escapeHtml(JSON.stringify(entry.details || {}));
    return `<tr>
      <td style="font-family:'DM Mono',monospace;color:var(--muted)">${formatDate(entry.created_at)}</td>
      <td style="font-family:'DM Mono',monospace">${action}</td>
      <td>${resource}</td>
      <td style="font-size:12px;color:var(--muted)">${details}</td>
    </tr>`;
  }).join("");
}

Object.assign(window, {
  api,
  showApp,
  showLogin,
  doLogin,
  toggleAccountForm,
  doRegister,
  doLogout,
  goTo,
  statusBadge,
  refreshAll,
  fetchAuditLogs,
  renderAuditLogs,
});

export {};

