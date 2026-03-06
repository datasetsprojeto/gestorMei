async function fetchProducts() {
  const data = await api("/products");
  state.products = data.products || [];
  const pendingSync = [];

  state.products.forEach((p) => {
    const meta = getMeta(p.id);
    const legacyCost = Number(meta.custo || 0);
    const legacyMin = Number(meta.min ?? 10);
    const legacyMax = Number(meta.max ?? 100);

    if (typeof p.cost !== "undefined") {
      meta.custo = Number(p.cost || 0);
    }
    if (typeof p.min_stock !== "undefined") {
      meta.min = Number(p.min_stock || 0);
    }
    if (typeof p.max_stock !== "undefined") {
      meta.max = Number(p.max_stock || 100);
    }

    const needsCostSync = Number(p.cost || 0) === 0 && legacyCost > 0;
    const needsMinSync = Number(p.min_stock ?? 10) === 10 && legacyMin !== 10;
    const needsMaxSync = Number(p.max_stock ?? 100) === 100 && legacyMax !== 100;

    if (needsCostSync || needsMinSync || needsMaxSync) {
      pendingSync.push(
        api(`/products/${p.id}`, {
          method: "PUT",
          body: JSON.stringify({
            cost: needsCostSync ? legacyCost : Number(p.cost || 0),
            min_stock: needsMinSync ? legacyMin : Number(p.min_stock ?? 10),
            max_stock: needsMaxSync ? legacyMax : Number(p.max_stock ?? 100),
          }),
        })
      );
    }
  });

  if (pendingSync.length) {
    await Promise.allSettled(pendingSync);
    const refreshed = await api("/products");
    state.products = refreshed.products || [];
  }

  saveProductMeta();
}

async function fetchSales() {
  let path = "/sales";
  if (state.salesPeriod.enabled) {
    const y = Number(state.salesPeriod.year);
    const m = Number(state.salesPeriod.month);
    if (m === -1) {
      path = `/sales?start_date=${y}-01-01&end_date=${y}-12-31`;
    } else if (m > 0) {
      const startDate = `${y}-${String(m).padStart(2, "0")}-01`;
      const monthEnd = new Date(y, m, 0).getDate();
      const endDate = `${y}-${String(m).padStart(2, "0")}-${String(monthEnd).padStart(2, "0")}`;
      path = `/sales?start_date=${startDate}&end_date=${endDate}`;
    }
  }

  const data = await api(path);
  const baseSales = data.sales || [];

  // Enriquecer vendas com categorias dos produtos vendidos para exibição na tabela.
  const detailedSales = await Promise.all(
    baseSales.map(async (sale) => {
      try {
        const details = await api(`/sales/${sale.id}`);
        const products = Array.from(new Set(
          (details.items || []).map((item) => item.product_name || "Sem produto")
        ));
        const categories = Array.from(new Set(
          (details.items || []).map((item) => {
            const meta = getMeta(item.product_id);
            return meta.cat || "Sem categoria";
          })
        ));

        return {
          ...sale,
          products,
          products_label: products.join(", "),
          categories,
          categories_label: categories.join(", "),
        };
      } catch (error) {
        return {
          ...sale,
          products: ["Sem produto"],
          products_label: "Sem produto",
          categories: ["Sem categoria"],
          categories_label: "Sem categoria",
        };
      }
    })
  );

  state.sales = detailedSales;
}

function initSalesPeriodControls() {
  const monthSelect = document.getElementById("sales-month-filter");
  const yearSelect = document.getElementById("sales-year-filter");
  if (!monthSelect || !yearSelect) return;

  monthSelect.innerHTML = [
    '<option value="0">Todos os meses</option>',
    '<option value="-1">Ano inteiro</option>',
    ...MONTH_NAMES.map((name, idx) => `<option value="${idx + 1}">${name}</option>`),
  ].join("");

  const currentYear = new Date().getFullYear();
  const years = [];
  for (let y = currentYear; y >= currentYear - 8; y -= 1) {
    years.push(`<option value="${y}">${y}</option>`);
  }
  yearSelect.innerHTML = years.join("");

  monthSelect.value = state.salesPeriod.enabled ? String(state.salesPeriod.month) : "0";
  yearSelect.value = String(state.salesPeriod.year);
}

async function aplicarFiltroMesVendas() {
  const monthSelect = document.getElementById("sales-month-filter");
  const yearSelect = document.getElementById("sales-year-filter");
  if (!monthSelect || !yearSelect) return;

  const month = Number(monthSelect.value || 0);
  const year = Number(yearSelect.value || new Date().getFullYear());
  state.salesPeriod.enabled = month !== 0;
  state.salesPeriod.month = month || -1;
  state.salesPeriod.year = year;

  localStorage.setItem("gestormei_sales_filter_enabled", String(state.salesPeriod.enabled));
  localStorage.setItem("gestormei_sales_month", String(state.salesPeriod.month));
  localStorage.setItem("gestormei_sales_year", String(state.salesPeriod.year));

  await fetchSales();
  renderVendas(document.getElementById("search-vendas").value || "");
  if (!state.salesPeriod.enabled) {
    toast("Filtro mensal removido. Exibindo todas as vendas.");
  } else if (state.salesPeriod.month === -1) {
    toast(`Vendas filtradas para o ano de ${state.salesPeriod.year}.`);
  } else {
    toast(`Vendas filtradas para ${String(state.salesPeriod.month).padStart(2, "0")}/${state.salesPeriod.year}.`);
  }
}

async function fetchStats() {
  const referenceDate = formatDateKeyBusiness(new Date());
  state.stats = await api(`/sales/stats?days=30&reference_date=${referenceDate}`);
}

async function fetchMonthlyStats() {
  const year = Number(state.dashboardPeriod.year);
  const month = Number(state.dashboardPeriod.month);
  state.monthlyStats = await api(`/sales/reports/monthly?year=${year}&month=${month}&format=json`);
}

function initDashboardPeriodControls() {
  const monthSelect = document.getElementById("dash-month");
  const yearSelect = document.getElementById("dash-year");
  if (!monthSelect || !yearSelect) return;

  monthSelect.innerHTML = MONTH_NAMES.map((name, idx) => {
    const month = idx + 1;
    return `<option value="${month}">${name}</option>`;
  }).join("");

  const currentYear = new Date().getFullYear();
  const years = [];
  for (let y = currentYear; y >= currentYear - 8; y -= 1) {
    years.push(`<option value="${y}">${y}</option>`);
  }
  yearSelect.innerHTML = years.join("");

  monthSelect.value = String(state.dashboardPeriod.month);
  yearSelect.value = String(state.dashboardPeriod.year);
}

async function onDashboardMonthChange() {
  state.dashboardPeriod.month = Number(document.getElementById("dash-month").value);
  state.dashboardPeriod.year = Number(document.getElementById("dash-year").value);
  localStorage.setItem("gestormei_dashboard_month", String(state.dashboardPeriod.month));
  localStorage.setItem("gestormei_dashboard_year", String(state.dashboardPeriod.year));
  await carregarMesSelecionado(true);
}

async function carregarMesSelecionado(skipToast = false) {
  try {
    await fetchMonthlyStats();
    renderDashboard();
    if (!skipToast) {
      toast(`Período carregado: ${String(state.dashboardPeriod.month).padStart(2, "0")}/${state.dashboardPeriod.year}`);
    }
  } catch (error) {
    toast(`Falha ao carregar mês: ${error.message}`);
  }
}

async function salvarMesSelecionado() {
  try {
    const payload = {
      month: Number(state.dashboardPeriod.month),
      year: Number(state.dashboardPeriod.year),
    };
    await api("/sales/reports/monthly/save", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await carregarMesesSalvos(true);
    toast(`Mês ${String(payload.month).padStart(2, "0")}/${payload.year} salvo.`);
  } catch (error) {
    toast(`Falha ao salvar mês: ${error.message}`);
  }
}

function renderSavedMonths() {
  const container = document.getElementById("saved-month-list");
  if (!container) return;
  if (!state.monthlySnapshots.length) {
    container.innerHTML = '<div class="empty-panel" style="margin:0">Nenhum mês salvo ainda.</div>';
    return;
  }

  container.innerHTML = state.monthlySnapshots
    .slice(0, 12)
    .map((snap) => {
      const m = String(snap.month).padStart(2, "0");
      const y = snap.year;
      const label = `${m}/${y} · ${formatCurrency(snap.total_amount)}`;
      return `<button class="saved-month-chip" onclick="aplicarMesSalvo(${y}, ${snap.month})">${escapeHtml(label)}</button>`;
    })
    .join("");
}

async function carregarMesesSalvos(silent = false) {
  try {
    const data = await api("/sales/reports/monthly/saved");
    state.monthlySnapshots = data.snapshots || [];
    renderSavedMonths();
    if (!silent && state.monthlySnapshots.length) {
      toast("Meses salvos atualizados.");
    }
  } catch (error) {
    state.monthlySnapshots = [];
    renderSavedMonths();
    if (!silent) {
      toast(`Falha ao listar meses salvos: ${error.message}`);
    }
  }
}

async function aplicarMesSalvo(year, month) {
  state.dashboardPeriod.year = Number(year);
  state.dashboardPeriod.month = Number(month);
  localStorage.setItem("gestormei_dashboard_month", String(state.dashboardPeriod.month));
  localStorage.setItem("gestormei_dashboard_year", String(state.dashboardPeriod.year));
  document.getElementById("dash-month").value = String(state.dashboardPeriod.month);
  document.getElementById("dash-year").value = String(state.dashboardPeriod.year);
  await carregarMesSelecionado();
}

function renderDashboard() {
  const daily = state.stats?.daily_sales || [];
  const browserTodayKey = formatDateKeyBusiness(new Date());
  const serverTodayKey = state.stats?.summary?.today_date;
  const todayEntry = daily.find((item) => item.date === browserTodayKey)
    || daily.find((item) => item.date === serverTodayKey)
    || {};
  const todayNet = Number(todayEntry.total_profit ?? state.stats?.summary?.today_net ?? 0);
  const todayGross = Number(todayEntry.gross_total ?? state.stats?.summary?.today_gross ?? 0);
  const todaySalesCount = Number(todayEntry.sales_count ?? state.stats?.summary?.today_sales_count ?? 0);
  const totalMonth = state.monthlyStats?.summary?.total_profit || state.monthlyStats?.summary?.total_amount || 0;
  const totalSales = state.monthlyStats?.summary?.total_sales || 0;
  const totalGross = state.monthlyStats?.summary?.gross_amount || 0;
  const selectedLabel = `${String(state.dashboardPeriod.month).padStart(2, "0")}/${state.dashboardPeriod.year}`;

  document.getElementById("metric-hoje-liq").textContent = formatCurrency(todayNet);
  document.getElementById("metric-hoje-liq-change").textContent = todayGross > 0 ? `${todaySalesCount} venda(s) hoje (${browserTodayKey})` : "Sem vendas hoje";
  document.getElementById("metric-hoje-bruto").textContent = formatCurrency(todayGross);
  document.getElementById("metric-hoje-bruto-change").textContent = todayGross > 0 ? `Bruto diário sem desconto (${browserTodayKey})` : "Sem vendas hoje";
  document.getElementById("metric-mes-liq").textContent = formatCurrency(totalMonth);
  document.getElementById("metric-mes-liq-change").textContent = `${totalSales} vendas em ${selectedLabel} (venda - custo)`;
  document.getElementById("metric-mes-bruto").textContent = formatCurrency(totalGross);
  document.getElementById("metric-mes-bruto-change").textContent = `${totalSales} vendas em ${selectedLabel} (bruto)`;

  renderSevenDayRevenue();
  renderTopProducts();
  renderRecentActivity();
  renderCriticalStock();
}

function renderSevenDayRevenue() {
  const entries = [...(state.stats?.daily_sales || [])]
    .slice(0, 7)
    .reverse()
    .map((item) => ({
      date: item.date,
      gross: Number(item.gross_total || 0),
      net: Number(item.total_profit || item.total || 0),
    }));

  const lineEl = document.getElementById("sparkline-line");
  const areaEl = document.getElementById("sparkline-area");
  const netLineEl = document.getElementById("sparkline-line-net");
  const dotEl = document.getElementById("sparkline-dot");
  const netDotEl = document.getElementById("sparkline-dot-net");
  const labelsEl = document.getElementById("sparkline-labels");
  const dayListEl = document.getElementById("sparkline-day-list");
  if (!lineEl || !areaEl || !dotEl || !labelsEl || !netLineEl || !netDotEl || !dayListEl) return;

  if (!entries.length) {
    lineEl.setAttribute("d", "M0,60 L400,60");
    netLineEl.setAttribute("d", "M0,60 L400,60");
    areaEl.setAttribute("d", "M0,60 L400,60 L400,60 L0,60 Z");
    dotEl.setAttribute("cx", "400");
    dotEl.setAttribute("cy", "60");
    netDotEl.setAttribute("cx", "400");
    netDotEl.setAttribute("cy", "60");
    labelsEl.innerHTML = "";
    dayListEl.innerHTML = '<div class="empty-panel">Sem vendas nos últimos 7 dias.</div>';
    return;
  }

  const width = 400;
  const height = 60;
  const maxVal = Math.max(...entries.map((item) => Math.max(item.gross, item.net)), 1);
  const step = entries.length > 1 ? width / (entries.length - 1) : width;

  const grossPoints = entries.map((item, index) => {
    const x = Number((index * step).toFixed(2));
    const normalized = item.gross / maxVal;
    const y = Number((height - normalized * (height - 6)).toFixed(2));
    return { x, y };
  });

  const netPoints = entries.map((item, index) => {
    const x = Number((index * step).toFixed(2));
    const normalized = item.net / maxVal;
    const y = Number((height - normalized * (height - 6)).toFixed(2));
    return { x, y };
  });

  const grossPath = grossPoints.map((p, idx) => `${idx === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const netPath = netPoints.map((p, idx) => `${idx === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const area = `${grossPath} L${grossPoints[grossPoints.length - 1].x},${height} L${grossPoints[0].x},${height} Z`;

  lineEl.setAttribute("d", grossPath);
  netLineEl.setAttribute("d", netPath);
  areaEl.setAttribute("d", area);
  dotEl.setAttribute("cx", String(grossPoints[grossPoints.length - 1].x));
  dotEl.setAttribute("cy", String(grossPoints[grossPoints.length - 1].y));
  netDotEl.setAttribute("cx", String(netPoints[netPoints.length - 1].x));
  netDotEl.setAttribute("cy", String(netPoints[netPoints.length - 1].y));

  const weekFmt = new Intl.DateTimeFormat("pt-BR", { weekday: "short" });
  labelsEl.innerHTML = entries
    .map((item) => {
      const dt = new Date(`${item.date}T12:00:00`);
      const label = weekFmt.format(dt).replace(".", "").slice(0, 3);
      return `<span>${escapeHtml(label)}</span>`;
    })
    .join("");

  dayListEl.innerHTML = entries.map((item) => {
    const dt = new Date(`${item.date}T12:00:00`);
    const label = dt.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
    return `<div class="spark-day-row"><span>${escapeHtml(label)}</span><span class="gross">Bruto: ${formatCurrency(item.gross)}</span><span class="net">Líquido: ${formatCurrency(item.net)}</span></div>`;
  }).join("");
}

function renderTopProducts() {
  const container = document.getElementById("top-products-list");
  const topProducts = state.stats?.top_products || [];

  if (!topProducts.length) {
    container.innerHTML = '<div class="empty-panel">Sem produtos vendidos no periodo.</div>';
    return;
  }

  const maxAmount = Math.max(...topProducts.map((p) => Number(p.total_amount) || 0), 1);
  const palette = ["", "green", "blue", "", "green"];

  container.innerHTML = topProducts
    .map((product, index) => {
      const amount = Number(product.total_amount) || 0;
      const qty = Number(product.total_quantity) || 0;
      const width = Math.max(8, Math.round((amount / maxAmount) * 100));
      const colorClass = palette[index % palette.length];
      const safeName = escapeHtml(product.name);

      return `
      <div class="bar-row" title="${qty} itens vendidos">
        <span class="bar-label">${safeName}</span>
        <div class="bar-track"><div class="bar-fill ${colorClass}" style="width:${width}%"></div></div>
        <span class="bar-val">${formatCurrency(amount)}</span>
      </div>`;
    })
    .join("");
}

function renderRecentActivity() {
  const container = document.getElementById("recent-activity-list");
  const recentSales = [...state.sales]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 4)
    .map((sale) => ({
      type: "sale",
      timestamp: sale.created_at,
      title: `Venda #${sale.id} — ${sale.items_count || 0} itens`,
      amount: `+${formatCurrency(sale.total)}`,
      amountClass: "pos",
    }));

  const lowStockAlerts = state.products
    .filter((p) => p.stock <= Number(p.min_stock ?? getMeta(p.id).min ?? 10))
    .sort((a, b) => a.stock - b.stock)
    .slice(0, 2)
    .map((product) => ({
      type: "alert",
      timestamp: new Date().toISOString(),
      title: `Alerta: ${product.name} — estoque baixo`,
      amount: `${product.stock} un`,
      amountClass: "neg",
    }));

  const activity = [...recentSales, ...lowStockAlerts]
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 6);

  if (!activity.length) {
    container.innerHTML = '<div class="empty-panel">Sem atividade recente para exibir.</div>';
    return;
  }

  container.innerHTML = activity
    .map((item) => {
      const safeTitle = escapeHtml(item.title);
      const safeTime = formatDate(item.timestamp);
      const safeAmount = escapeHtml(item.amount);
      return `
      <div class="tx-item">
        <div class="tx-dot ${item.type}"></div>
        <div class="tx-info">
          <div class="tx-name">${safeTitle}</div>
          <div class="tx-time">${safeTime}</div>
        </div>
        <div class="tx-amount ${item.amountClass}">${safeAmount}</div>
      </div>`;
    })
    .join("");
}

function renderCriticalStock() {
  const container = document.getElementById("critical-stock-list");
  const criticalProducts = [...state.products]
    .filter((p) => {
      const minStock = Number(p.min_stock ?? getMeta(p.id).min ?? 10);
      return Number(p.stock) <= minStock;
    })
    .sort((a, b) => Number(a.stock) - Number(b.stock))
    .slice(0, 5);

  if (!criticalProducts.length) {
    container.innerHTML = '<div class="empty-panel">Nenhum produto em nível crítico no momento.</div>';
    return;
  }

  container.innerHTML = criticalProducts
    .map((product) => {
      const minStock = Number(product.min_stock ?? getMeta(product.id).min ?? 10);
      const maxStock = Number(product.max_stock ?? getMeta(product.id).max ?? 100);
      const pct = Math.min(100, Math.round((Number(product.stock) / Math.max(maxStock, 1)) * 100));
      const color = Number(product.stock) <= Math.max(1, Math.round(minStock * 0.5)) ? "var(--danger)" : "var(--accent)";
      const safeName = escapeHtml(product.name);
      return `
      <div class="stock-progress">
        <div class="prog-header"><span>${safeName}</span><span>${product.stock} / ${maxStock} un</span></div>
        <div class="prog-track"><div class="prog-fill" style="width:${pct}%;background:${color}"></div></div>
      </div>`;
    })
    .join("");
}

function getActiveChip(groupId) {
  const active = document.querySelector(`#${groupId} .chip.active`);
  return active ? active.textContent.trim().toLowerCase() : "";
}

function renderVendas(filter = "") {
  const chip = getActiveChip("chips-vendas");
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - 7);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const filtered = state.sales.filter((sale) => {
    const saleDate = new Date(sale.created_at);
    const productsLabel = String(sale.products_label || "Sem produto");
    const categoriesLabel = String(sale.categories_label || "Sem categoria");
    const text = `#${sale.id} ${productsLabel} ${categoriesLabel}`;
    const matchesText = !filter || text.includes(filter) || `${sale.items_count}`.includes(filter);

    let matchesChip = true;
    if (chip === "hoje") {
      matchesChip = saleDate.toDateString() === now.toDateString();
    } else if (chip === "esta semana") {
      matchesChip = saleDate >= weekStart;
    } else if (chip === "este mes") {
      matchesChip = saleDate >= monthStart;
    }

    return matchesText && matchesChip;
  });

  const tb = document.getElementById("tb-vendas");
  tb.innerHTML = filtered
    .map(
      (sale) => `
    <tr>
      <td><span style="font-family:'DM Mono',monospace;color:var(--accent)">#${sale.id}</span></td>
      <td style="color:var(--muted);font-family:'DM Mono',monospace;font-size:12px">${formatDate(sale.created_at)}</td>
      <td>${escapeHtml(sale.products_label || "Sem produto")}</td>
      <td>${escapeHtml(sale.categories_label || "Sem categoria")}</td>
      <td style="font-family:'DM Mono',monospace">${sale.items_count || 0}</td>
      <td style="font-family:'DM Mono',monospace;color:var(--success)">${formatCurrency(sale.total)}</td>
      <td><span class="badge ok">Concluida</span></td>
      <td>
        <button class="action-btn" title="Ver detalhes" onclick="verDetalhesVenda(${sale.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </td>
    </tr>`
    )
    .join("");
}

function renderProdutos(filter = "") {
  const tb = document.getElementById("tb-produtos");
  const filtered = state.products.filter((p) => {
    const meta = getMeta(p.id);
    const query = filter.toLowerCase();
    return !query || p.name.toLowerCase().includes(query) || meta.cat.toLowerCase().includes(query);
  });

  tb.innerHTML = filtered
    .map((p) => {
      const meta = getMeta(p.id);
      const custo = typeof p.cost !== "undefined" ? Number(p.cost) : Number(meta.custo);
      const margem = p.price > 0 ? (((Number(p.price) - custo) / Number(p.price)) * 100).toFixed(0) : "0";
      const minStock = Number(p.min_stock ?? meta.min);
      const maxStock = Number(p.max_stock ?? meta.max);
      return `
      <tr>
        <td><strong>${p.name}</strong></td>
        <td style="color:var(--muted)">${meta.cat}</td>
        <td style="font-family:'DM Mono',monospace">${formatCurrency(p.price)}</td>
        <td style="font-family:'DM Mono',monospace;color:var(--muted)">${formatCurrency(custo)}</td>
        <td><span style="font-family:'DM Mono',monospace;color:${margem > 30 ? "var(--success)" : margem > 15 ? "var(--accent)" : "var(--danger)"}">${margem}%</span></td>
        <td>${statusBadge(p.stock, minStock, maxStock)}</td>
        <td style="display:flex;gap:4px">
          <button class="action-btn" title="Editar" onclick="editarProduto(${p.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="action-btn del" title="Excluir" onclick="deleteProduto(${p.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
          </button>
        </td>
      </tr>`;
    })
    .join("");
}

function renderEstoque(filter = "") {
  const chip = getActiveChip("chips-est");
  const query = filter.toLowerCase();

  const filtered = state.products.filter((p) => {
    const meta = getMeta(p.id);
    const minStock = Number(p.min_stock ?? meta.min);
    const maxStock = Number(p.max_stock ?? meta.max);
    const matchesText = !query || p.name.toLowerCase().includes(query);

    let matchesChip = true;
    if (chip === "critico") {
      matchesChip = p.stock <= minStock * 0.5;
    } else if (chip === "normal") {
      matchesChip = p.stock > minStock && p.stock < maxStock * 0.9;
    } else if (chip === "alto") {
      matchesChip = p.stock >= maxStock * 0.9;
    }

    return matchesText && matchesChip;
  });

  const tb = document.getElementById("tb-estoque");
  tb.innerHTML = filtered
    .map((p) => {
      const meta = getMeta(p.id);
      const minStock = Number(p.min_stock ?? meta.min);
      const maxStock = Number(p.max_stock ?? meta.max);
      const pct = Math.min(100, (p.stock / Math.max(maxStock, 1)) * 100).toFixed(0);
      const clr = p.stock <= minStock * 0.5 ? "var(--danger)" : p.stock <= minStock ? "var(--accent)" : "var(--success)";
      return `
      <tr>
        <td>
          <strong>${p.name}</strong>
          <div style="height:3px;background:var(--bg3);margin-top:6px;width:100px"><div style="height:100%;width:${pct}%;background:${clr};transition:width .8s"></div></div>
        </td>
        <td style="color:var(--muted)">${meta.cat}</td>
        <td style="font-family:'DM Mono',monospace;font-size:15px;font-weight:600;color:${clr}">${p.stock} un</td>
        <td style="font-family:'DM Mono',monospace;color:var(--muted)">${minStock} un</td>
        <td style="font-family:'DM Mono',monospace;color:var(--muted)">${maxStock} un</td>
        <td>${statusBadge(p.stock, minStock, maxStock)}</td>
        <td>
          <button class="action-btn" title="Entrada" onclick="selecionarProdutoEntrada(${p.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
        </td>
      </tr>`;
    })
    .join("");
}

function filterVendas() {
  renderVendas(document.getElementById("search-vendas").value);
}

function filterProdutos() {
  renderProdutos(document.getElementById("search-prod").value);
}

function filterEstoque() {
  renderEstoque(document.getElementById("search-est").value);
}

function populateProductSelectors() {
  const saleSelect = document.getElementById("v-produto");
  const stockSelect = document.getElementById("e-produto");

  const options = state.products
    .map((p) => `<option value="${p.id}" data-price="${p.price}">${p.name}</option>`)
    .join("");

  saleSelect.innerHTML = options || "<option value=''>Sem produtos</option>";
  stockSelect.innerHTML = options || "<option value=''>Sem produtos</option>";

  syncSalePrice();
}

function syncSalePrice() {
  const select = document.getElementById("v-produto");
  const selected = select.options[select.selectedIndex];
  if (selected) {
    document.getElementById("v-preco").value = Number(selected.dataset.price || 0).toFixed(2);
  }
}

async function registrarVenda() {
  const productId = Number(document.getElementById("v-produto").value);
  const qty = Number(document.getElementById("v-qty").value || 0);

  if (!productId || qty <= 0) {
    toast("Informe produto e quantidade valida.");
    return;
  }

  try {
    await api("/sales", {
      method: "POST",
      body: JSON.stringify({ items: [{ product_id: productId, quantity: qty }] }),
    });

    closeModal("modal-venda");
    await refreshAll();
    toast("Venda registrada com sucesso.");
  } catch (error) {
    toast(`Falha ao registrar venda: ${error.message}`);
  }
}

async function addProduto() {
  const name = document.getElementById("p-nome").value.trim();
  const price = Number(document.getElementById("p-preco").value || 0);
  const stock = Number(document.getElementById("p-estoque").value || 0);

  if (!name || price <= 0) {
    toast("Informe nome e preco valido.");
    return;
  }

  const cost = Number(document.getElementById("p-custo").value || 0);
  const minStock = Number(document.getElementById("p-min").value || 10);
  const payload = { name, price, cost, stock, min_stock: minStock, max_stock: 100 };
  const metaPayload = {
    cat: document.getElementById("p-cat").value,
    custo: cost,
    min: minStock,
    max: 100,
  };

  try {
    const wasEditing = Boolean(state.editingProductId);
    if (state.editingProductId) {
      await api(`/products/${state.editingProductId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await api("/products", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }

    const editedId = state.editingProductId;
    if (editedId) {
      state.productMeta[editedId] = metaPayload;
      saveProductMeta();
    }

    closeModal("modal-produto");
    resetProductForm();
    await refreshAll();
    if (!editedId) {
      const created = state.products.find((p) => p.name === name);
      if (created) {
        state.productMeta[created.id] = metaPayload;
        saveProductMeta();
        renderProdutos(document.getElementById("search-prod").value || "");
        renderEstoque(document.getElementById("search-est").value || "");
      }
    }
    toast(wasEditing ? "Produto atualizado." : "Produto cadastrado.");
  } catch (error) {
    toast(`Falha ao salvar produto: ${error.message}`);
  }
}

function editarProduto(id) {
  const product = state.products.find((p) => p.id === id);
  if (!product) return;
  const meta = getMeta(id);

  state.editingProductId = id;
  document.querySelector("#modal-produto .modal-title").textContent = "Editar Produto";
  document.getElementById("p-nome").value = product.name;
  document.getElementById("p-cat").value = meta.cat;
  document.getElementById("p-preco").value = Number(product.price).toFixed(2);
  document.getElementById("p-custo").value = Number(typeof product.cost !== "undefined" ? product.cost : meta.custo).toFixed(2);
  document.getElementById("p-estoque").value = product.stock;
  document.getElementById("p-min").value = meta.min;
  openModal("modal-produto");
}

function resetProductForm() {
  state.editingProductId = null;
  document.querySelector("#modal-produto .modal-title").textContent = "Novo Produto";
  document.getElementById("p-nome").value = "";
  document.getElementById("p-preco").value = "";
  document.getElementById("p-custo").value = "";
  document.getElementById("p-estoque").value = "";
  document.getElementById("p-min").value = "";
}

async function deleteProduto(id) {
  const product = state.products.find((p) => p.id === id);
  if (!confirm("Deseja excluir este produto?")) return;

  const ownerPassword = prompt("Informe a mesma senha de login do proprietário para confirmar a exclusão:");
  if (ownerPassword === null) return;
  if (!ownerPassword.trim()) {
    toast("Informe a senha de login do proprietário.");
    return;
  }

  let path = `/products/${id}`;
  if (product && Number(product.stock) > 0) {
    const confirmPermanent = confirm(
      `Este produto ainda possui ${product.stock} unidade(s) em estoque.\n\n` +
      "Deseja confirmar a exclusão PERMANENTE?"
    );
    if (!confirmPermanent) return;
    path = `/products/${id}?force=true`;
  }

  try {
    const result = await api(path, {
      method: "DELETE",
      body: JSON.stringify({ owner_password: ownerPassword.trim() }),
    });
    delete state.productMeta[id];
    saveProductMeta();
    await refreshAll();
    toast(result.message || "Produto removido.");
  } catch (error) {
    toast(`Falha ao excluir: ${error.message}`);
  }
}

function selecionarProdutoEntrada(id) {
  document.getElementById("e-produto").value = String(id);
  openModal("modal-entrada");
}

async function entradaEstoque() {
  const productId = Number(document.getElementById("e-produto").value);
  const qty = Number(document.getElementById("e-qty").value || 0);
  if (!productId || qty <= 0) {
    toast("Informe um produto e quantidade valida.");
    return;
  }

  const product = state.products.find((p) => p.id === productId);
  if (!product) {
    toast("Produto nao encontrado.");
    return;
  }

  try {
    await api(`/products/${productId}`, {
      method: "PUT",
      body: JSON.stringify({ stock: Number(product.stock) + qty }),
    });

    closeModal("modal-entrada");
    document.getElementById("e-qty").value = "";
    await refreshAll();
    toast("Entrada de estoque registrada.");
  } catch (error) {
    toast(`Falha ao registrar entrada: ${error.message}`);
  }
}

async function verDetalhesVenda(saleId) {
  try {
    const data = await api(`/sales/${saleId}`);
    const items = (data.items || []).map((item) => `${item.product_name} x${item.quantity}`).join("\n");
    alert(`Venda #${data.id}\nData: ${formatDate(data.created_at)}\nTotal: ${formatCurrency(data.total)}\n\nItens:\n${items || "Sem itens"}`);
  } catch (error) {
    toast(`Falha ao carregar venda: ${error.message}`);
  }
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function getPeriodoRelatorio() {
  const now = new Date();
  const ano = prompt("Ano do relatório (YYYY):", String(now.getFullYear()));
  if (!ano) return null;

  const mes = prompt("Mês do relatório (1-12):", String(now.getMonth() + 1));
  if (!mes) return null;

  const anoNum = Number(ano);
  const mesNum = Number(mes);

  if (!Number.isInteger(anoNum) || !Number.isInteger(mesNum) || mesNum < 1 || mesNum > 12) {
    toast("Ano/mês inválidos.");
    return null;
  }

  return { ano: anoNum, mes: mesNum };
}

async function baixarArquivoRelatorio(path, fallbackName) {
  const headers = { Authorization: `Bearer ${state.token}` };
  const response = await fetch(`${API_BASE}${path}`, { headers });

  if (!response.ok) {
    const maybeJson = await response.json().catch(() => ({}));
    throw new Error(maybeJson.error || `Erro ${response.status}`);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("content-disposition") || "";
  const match = /filename=([^;]+)/i.exec(contentDisposition);
  const filename = match ? match[1].replace(/\"/g, "").trim() : fallbackName;

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function gerarRelatorioMensal(formato) {
  const periodo = getPeriodoRelatorio();
  if (!periodo) return;

  try {
    const ext = formato === "xlsx" ? "xlsx" : "csv";
    const fallback = `relatorio-mensal-${periodo.ano}-${String(periodo.mes).padStart(2, "0")}.${ext}`;
    await baixarArquivoRelatorio(
      `/sales/reports/monthly?year=${periodo.ano}&month=${periodo.mes}&format=${ext}`,
      fallback
    );
    toast(`Relatório mensal ${ext.toUpperCase()} gerado.`);
  } catch (error) {
    toast(`Falha ao gerar relatório: ${error.message}`);
  }
}

async function compararMesAMes() {
  const periodo = getPeriodoRelatorio();
  if (!periodo) return;

  try {
    const data = await api(`/sales/reports/monthly/compare?year=${periodo.ano}&month=${periodo.mes}`);
    const growth = Number(data.comparison?.growth_percent || 0).toFixed(2);
    const diff = Number(data.comparison?.amount_difference || 0);

    alert(
      `Comparativo Mês a Mês\n\n` +
      `Atual: ${String(data.current?.month).padStart(2, "0")}/${data.current?.year}\n` +
      `Faturamento: ${formatCurrency(data.current?.summary?.total_amount || 0)}\n` +
      `Vendas: ${data.current?.summary?.total_sales || 0}\n\n` +
      `Anterior: ${String(data.previous?.month).padStart(2, "0")}/${data.previous?.year}\n` +
      `Faturamento: ${formatCurrency(data.previous?.summary?.total_amount || 0)}\n` +
      `Vendas: ${data.previous?.summary?.total_sales || 0}\n\n` +
      `Diferença: ${formatCurrency(diff)}\n` +
      `Crescimento: ${growth}%`
    );
  } catch (error) {
    toast(`Falha no comparativo: ${error.message}`);
  }
}

function exportarVendas() {
  downloadJson("vendas.json", state.sales);
  toast("Exportacao de vendas concluida.");
}

function exportarProdutos() {
  const data = state.products.map((p) => ({ ...p, ...getMeta(p.id) }));
  downloadJson("produtos.json", data);
  toast("Exportacao de produtos concluida.");
}

function gerarRelatorioEstoque() {
  const relatorio = state.products.map((p) => {
    const meta = getMeta(p.id);
    return {
      id: p.id,
      nome: p.name,
      estoque: p.stock,
      minimo: meta.min,
      maximo: meta.max,
      status: p.stock <= meta.min ? "baixo" : "normal",
    };
  });
  downloadJson("relatorio-estoque.json", relatorio);
  toast("Relatorio de estoque gerado.");
}

async function clearWorkspaceDataCache() {
  if (state.user?.is_owner === false) {
    toast("Somente o proprietário pode limpar dados.");
    return;
  }

  const confirmAction = confirm(
    "Esta ação vai remover produtos, vendas e análises relacionadas (atividade recente, estoque crítico e meses salvos).\n\nDeseja continuar?"
  );
  if (!confirmAction) return;

  const ownerPassword = prompt("Informe a mesma senha de login do proprietário para confirmar:");
  if (ownerPassword === null) return;
  if (!ownerPassword.trim()) {
    toast("Informe a senha de login do proprietário.");
    return;
  }

  try {
    const result = await api("/products/cache/clear-data", {
      method: "POST",
      body: JSON.stringify({ owner_password: ownerPassword.trim() }),
    });

    // Limpa caches locais relacionados a dados de negócio (preserva dados de usuário/sessão).
    state.productMeta = {};
    saveProductMeta();
    state.sales = [];
    state.products = [];
    state.stats = null;
    state.monthlyStats = null;
    state.monthlySnapshots = [];
    state.employeeAnalytics = [];

    await refreshAll();
    toast(result.message || "Dados operacionais limpos com sucesso.");
  } catch (error) {
    toast(`Falha ao limpar dados: ${error.message}`);
  }
}

