async function fetchEmployeeAnalytics(showToast = false) {
  // Funcionário vinculado pode operar no mesmo banco, mas a aba analítica fica para o proprietário.
  if (state.user?.is_owner === false) {
    state.employeeAnalytics = [];
    state.employees = [];
    return;
  }

  try {
    const days = [7, 30, 90].includes(Number(state.employeeAnalyticsDays)) ? Number(state.employeeAnalyticsDays) : 30;
    const [employeesData, analyticsData] = await Promise.all([
      api("/employees"),
      api(`/employees/analytics?days=${days}`),
    ]);
    state.employees = employeesData.employees || [];
    state.employeeAnalytics = analyticsData.employees || [];
    if (showToast) toast("Análise por funcionário atualizada.");
  } catch (error) {
    state.employees = [];
    state.employeeAnalytics = [];
    if (showToast) toast(`Falha ao carregar análise: ${error.message}`);
  }
}

function syncEmployeePeriodChips() {
  const chips = document.querySelectorAll("#chips-func .chip");
  chips.forEach((chip) => {
    const days = Number(chip.getAttribute("data-days") || 30);
    chip.classList.toggle("active", days === Number(state.employeeAnalyticsDays));
  });
}

async function setEmployeeAnalyticsDays(days, el) {
  if (![7, 30, 90].includes(Number(days))) return;
  state.employeeAnalyticsDays = Number(days);
  localStorage.setItem("gestormei_employee_days", String(state.employeeAnalyticsDays));
  if (el) {
    document.querySelectorAll("#chips-func .chip").forEach((chip) => chip.classList.remove("active"));
    el.classList.add("active");
  }
  await fetchEmployeeAnalytics(false);
  renderFuncionarios();
}

function renderFuncionarios() {
  const tb = document.getElementById("tb-funcionarios");
  if (!tb) return;
  const searchQuery = (document.getElementById("employee-search")?.value || "").trim().toLowerCase();

  if (state.user?.is_owner === false) {
    tb.innerHTML = '<tr><td colspan="6" style="color:var(--muted)">Apenas o proprietário visualiza esta análise.</td></tr>';
    return;
  }

  if (!state.employeeAnalytics.length) {
    tb.innerHTML = '<tr><td colspan="6" style="color:var(--muted)">Nenhum funcionário vinculado ou sem vendas no período.</td></tr>';
    return;
  }

  const employeeEmailById = {};
  state.employees.forEach((emp) => {
    employeeEmailById[emp.id] = emp.email;
  });
  if (state.user) {
    employeeEmailById[state.user.account_owner_id || state.user.id] = state.user.email;
  }

  const rows = state.employeeAnalytics
    .map((row) => {
      const isOwnerRow = Number(row.employee_id) === Number(state.user?.account_owner_id || state.user?.id);
      const rowName = String(row.employee_name || `Funcionário #${row.employee_id}`);
      const rowEmail = String(employeeEmailById[row.employee_id] || "-");
      const matchesSearch = !searchQuery
        || rowName.toLowerCase().includes(searchQuery)
        || rowEmail.toLowerCase().includes(searchQuery);
      if (!matchesSearch) return "";

      const actionCell = isOwnerRow
        ? '<span style="color:var(--muted)">Proprietário</span>'
        : `<button class="action-btn del" title="Desvincular" onclick="desvincularFuncionario(${row.employee_id})">Desvincular</button>`;
      return `
      <tr>
        <td><strong>${escapeHtml(rowName)}</strong></td>
        <td style="color:var(--muted)">${escapeHtml(rowEmail)}</td>
        <td style="font-family:'DM Mono',monospace">${Number(row.sales_count || 0)}</td>
        <td style="font-family:'DM Mono',monospace">${formatCurrency(row.gross_total || 0)}</td>
        <td style="font-family:'DM Mono',monospace">${formatCurrency(row.net_total || 0)}</td>
        <td>${actionCell}</td>
      </tr>`;
    })
    .join("");

  if (!rows.trim()) {
    tb.innerHTML = '<tr><td colspan="6" style="color:var(--muted)">Nenhum funcionário encontrado com esse filtro.</td></tr>';
    return;
  }

  tb.innerHTML = rows;
}

async function vincularFuncionario() {
  if (state.user?.is_owner === false) {
    toast("Somente o proprietário pode vincular funcionários.");
    return;
  }

  const emailInput = document.getElementById("employee-email");
  const email = (emailInput?.value || "").trim().toLowerCase();
  if (!email) {
    toast("Informe o e-mail do funcionário.");
    return;
  }

  const suggestedName = prompt("Nome do funcionário (opcional, usado ao criar conta automática):", "") || "";
  const suggestedPhone = prompt("Telefone do funcionário (opcional):", "") || "";

  try {
    const response = await api("/employees/link", {
      method: "POST",
      body: JSON.stringify({ email, name: suggestedName, phone: suggestedPhone }),
    });
    if (emailInput) emailInput.value = "";
    await fetchEmployeeAnalytics(false);
    renderFuncionarios();
    if (response.generated_password) {
      alert(`Funcionário criado automaticamente.\n\nSenha temporária: ${response.generated_password}`);
    }
    toast(response.message || "Funcionário vinculado.");
  } catch (error) {
    toast(`Falha ao vincular: ${error.message}`);
  }
}

async function desvincularFuncionario(employeeId) {
  if (state.user?.is_owner === false) {
    toast("Somente o proprietário pode desvincular funcionários.");
    return;
  }

  if (!confirm("Deseja desvincular este funcionário do seu banco compartilhado?")) return;

  try {
    const response = await api(`/employees/unlink/${employeeId}`, { method: "POST" });
    await fetchEmployeeAnalytics(false);
    renderFuncionarios();
    toast(response.message || "Funcionário desvinculado.");
  } catch (error) {
    toast(`Falha ao desvincular: ${error.message}`);
  }
}

