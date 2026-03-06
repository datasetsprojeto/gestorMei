function openModal(id) {
  if (id === "modal-venda" || id === "modal-entrada") {
    populateProductSelectors();
  }
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
  if (id === "modal-produto") {
    resetProductForm();
  }
}

document.querySelectorAll(".modal-overlay").forEach((overlay) => {
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      overlay.classList.remove("open");
    }
  });
});

function setChip(el, groupId) {
  document.querySelectorAll(`#${groupId} .chip`).forEach((chip) => chip.classList.remove("active"));
  el.classList.add("active");
  if (groupId === "chips-vendas") {
    filterVendas();
  }
  if (groupId === "chips-est") {
    filterEstoque();
  }
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

document.getElementById("v-produto").addEventListener("change", syncSalePrice);
document.getElementById("login-pass").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doLogin();
});
document.getElementById("register-phone").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doRegister();
});

if (state.token) {
  showApp();
  refreshAll().catch((error) => {
    toast(`Sessao expirada: ${error.message}`);
    doLogout();
  });
}


