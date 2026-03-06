const API_BASE = "http://localhost:5000";
const BUSINESS_TIMEZONE = "America/Sao_Paulo";
const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const now = new Date();

const state = {
  token: localStorage.getItem("gestormei_token") || "",
  user: JSON.parse(localStorage.getItem("gestormei_user") || "null"),
  products: [],
  sales: [],
  stats: null,
  monthlyStats: null,
  monthlySnapshots: [],
  employees: [],
  employeeAnalytics: [],
  auditLogs: [],
  employeeAnalyticsDays: Number(localStorage.getItem("gestormei_employee_days") || 30),
  salesPeriod: {
    month: Number(localStorage.getItem("gestormei_sales_month") || -1),
    year: Number(localStorage.getItem("gestormei_sales_year") || now.getFullYear()),
    enabled: localStorage.getItem("gestormei_sales_filter_enabled") === "true",
  },
  dashboardPeriod: {
    month: Number(localStorage.getItem("gestormei_dashboard_month") || now.getMonth() + 1),
    year: Number(localStorage.getItem("gestormei_dashboard_year") || now.getFullYear()),
  },
  productMeta: JSON.parse(localStorage.getItem("gestormei_product_meta") || "{}"),
  editingProductId: null,
  creatingAccount: false,
};

function saveProductMeta() {
  localStorage.setItem("gestormei_product_meta", JSON.stringify(state.productMeta));
}

function getMeta(productId) {
  if (!state.productMeta[productId]) {
    state.productMeta[productId] = { cat: "Sem categoria", custo: 0, min: 10, max: 100 };
  }
  return state.productMeta[productId];
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(value) {
  if (!value) return "-";
  const dt = new Date(value);
  return dt.toLocaleString("pt-BR");
}

function formatDateKeyLocal(value) {
  const dt = value instanceof Date ? value : new Date(value);
  const year = dt.getFullYear();
  const month = String(dt.getMonth() + 1).padStart(2, "0");
  const day = String(dt.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateKeyBusiness(value) {
  const dt = value instanceof Date ? value : new Date(value);
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: BUSINESS_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(dt);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}


