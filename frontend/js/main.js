import * as shared from "./state.js";

window.GestorMei = {
  ...(window.GestorMei || {}),
  ...shared,
};

async function bootstrapApp() {
  await import("./modules/core.js");
  await import("./modules/operations.js");
  await import("./modules/employees.js");
  await import("./modules/bootstrap.js");
}

bootstrapApp().catch((error) => {
  console.error("Falha ao inicializar frontend modular:", error);
});
