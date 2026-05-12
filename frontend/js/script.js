const API_BASE_URL = "http://127.0.0.1:8000";

let products = [];
let orders = [];
let inventory = [];

// ===============================
// Auth Guard
// ===============================

const PUBLIC_PAGES = ["", "/", "index.html", "login.html", "register.html"];

function getCurrentPageName() {
  const path = window.location.pathname;
  const fileName = path.split("/").pop().toLowerCase();
  return fileName || "index.html";
}

function enforceLogin() {
  const page = getCurrentPageName();
  if (PUBLIC_PAGES.includes(page)) return;

  const token = localStorage.getItem("authToken");
  if (!token) {
    window.location.replace("login.html");
  }
}

function setupLogoutButton() {
  document.querySelectorAll("a").forEach((a) => {
    if (a.textContent.trim().toLowerCase() === "logout") {
      a.addEventListener("click", function (event) {
        event.preventDefault();
        clearAuth();
        window.location.replace("login.html");
      });
    }
  });
}

function applyRoleUI() {
  const user = getCurrentUser();
  if (!user) return;

  // Navbar'a "Kullanıcı (Role)" rozeti ekle
  const navUl = document.querySelector("nav.navbar .navbar-nav.ms-auto");
  if (navUl && !document.getElementById("currentUserBadge")) {
    const li = document.createElement("li");
    li.className = "nav-item d-flex align-items-center me-3";
    li.id = "currentUserBadge";
    li.innerHTML = `<span class="text-light small">${escapeHtml(user.name)} <span class="badge bg-primary">${escapeHtml(user.role)}</span></span>`;
    navUl.insertBefore(li, navUl.firstChild);
  }

  const role = user.role;

  // Login linkleri:
  //  - Navbar içindekiler → "Logout" yap (tek logout butonu burası)
  //  - Navbar dışındakiler (hero section vb.) → gizle
  document.querySelectorAll("a").forEach((a) => {
    const text = a.textContent.trim().toLowerCase();
    const href = (a.getAttribute("href") || "").toLowerCase();
    if (text === "login" && href.endsWith("login.html")) {
      const insideNav = a.closest("nav") !== null;
      if (insideNav) {
        a.textContent = "Logout";
        a.addEventListener("click", function (event) {
          event.preventDefault();
          clearAuth();
          window.location.replace("login.html");
        });
      } else {
        a.style.display = "none";
      }
    }
  });

  // Add Product butonunu Admin/Business Owner dışındakilere gizle
  document.querySelectorAll("a, button").forEach((el) => {
    const text = el.textContent.trim().toLowerCase();
    const href = (el.getAttribute("href") || "").toLowerCase();

    if ((text === "add new product" || text === "add product" || href === "add-product.html")
        && !ADMIN_ROLES.includes(role)) {
      el.style.display = "none";
    }
    if ((text === "add new order" || text === "add order" || href === "add-order.html")
        && role === ROLES.INVENTORY_STAFF) {
      el.style.display = "none";
    }
  });
}

// ===============================
// Helper Functions
// ===============================

// HTML escape — kullanıcı verisini innerHTML içine basarken XSS engelleme.
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// JS string-literal escape — onclick="fn('${...}')" gibi inline handler argümanları için.
function escapeJsString(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/</g, "\\u003c");
}

function getStatusClass(status) {
  if (status === "Pending") return "status-pending";
  if (status === "Preparing") return "status-preparing";
  if (status === "Completed") return "status-completed";
  if (status === "Cancelled") return "status-cancelled";
  if (status === "Critical") return "status-critical";
  return "status-normal";
}

function getAuthToken() {
  return localStorage.getItem("authToken");
}

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem("loggedInUser") || "null");
  } catch {
    return null;
  }
}

function getCurrentRole() {
  const user = getCurrentUser();
  return user ? user.role : null;
}

function userHasRole(...roles) {
  const r = getCurrentRole();
  return roles.includes(r);
}

// Role grupları (backend'le uyumlu)
const ROLES = {
  ADMIN: "Admin",
  BUSINESS_OWNER: "Business Owner",
  SALES_MANAGER: "Sales Manager",
  INVENTORY_STAFF: "Inventory Staff",
};
const ADMIN_ROLES = [ROLES.ADMIN, ROLES.BUSINESS_OWNER];

function clearAuth() {
  localStorage.removeItem("authToken");
  localStorage.removeItem("loggedInUser");
}

async function fetchJSON(url, options = {}) {
  // Token varsa her isteğe Authorization header ekle
  const token = getAuthToken();
  const headers = {
    ...(options.headers || {}),
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
  };
  const response = await fetch(url, { ...options, headers });

  // 401 → token expired / yok → temizle ve login'e yönlendir
  if (response.status === 401) {
    clearAuth();
    const page = getCurrentPageName();
    if (!PUBLIC_PAGES.includes(page)) {
      window.location.replace("login.html");
    }
    throw new Error("Session expired. Please login again.");
  }

  // 403 → role yetkisiz → hata mesajıyla yönlendirme yok
  if (response.status === 403) {
    let detail = "Permission denied for your role.";
    try {
      const d = await response.json();
      if (d.detail) detail = d.detail;
    } catch {}
    throw new Error(detail);
  }

  if (!response.ok) {
    let errorMessage = "An error occurred.";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      errorMessage = "Server error.";
    }
    throw new Error(errorMessage);
  }

  return await response.json();
}

function showMessage(element, message, type = "success") {
  if (!element) return;

  element.classList.remove("d-none", "alert-success", "alert-danger", "alert-warning");
  element.classList.add(`alert-${type}`);
  element.textContent = message;
}

// ===============================
// API Functions
// ===============================

async function fetchProducts() {
  products = await fetchJSON(`${API_BASE_URL}/products`);
  return products;
}

async function fetchOrders() {
  orders = await fetchJSON(`${API_BASE_URL}/orders`);
  return orders;
}

async function fetchInventory() {
  inventory = await fetchJSON(`${API_BASE_URL}/inventory`);
  return inventory;
}

async function fetchDashboard() {
  return await fetchJSON(`${API_BASE_URL}/dashboard`);
}

async function fetchSuppliers() {
  return await fetchJSON(`${API_BASE_URL}/suppliers`);
}

// ===============================
// Register Page
// ===============================

function loadRegisterPage() {
  const registerForm = document.getElementById("registerForm");
  const registerSuccessMessage = document.getElementById("registerSuccessMessage");

  if (!registerForm) return;

  registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const newUser = {
      name: document.getElementById("fullName").value.trim(),
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
      role: document.getElementById("role").value
    };

    try {
      await fetchJSON(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });

      // Token vermiyoruz; kullanıcı login sayfasında giriş yapacak
      showMessage(
        registerSuccessMessage,
        "Account created successfully. Redirecting to login...",
        "success"
      );
      registerForm.reset();

      setTimeout(function () {
        window.location.href = "login.html";
      }, 1000);
    } catch (error) {
      showMessage(registerSuccessMessage, error.message, "danger");
    }
  });
}
// ===============================
// Login Page
// ===============================

function loadLoginPage() {
  const loginForm = document.getElementById("loginForm");
  const loginMessage = document.getElementById("loginMessage");

  if (!loginForm) return;

  loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const loginData = {
      email: document.getElementById("loginEmail").value.trim(),
      password: document.getElementById("loginPassword").value
    };

    try {
      const data = await fetchJSON(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });

      // JWT token + user objesini localStorage'a kaydet
      localStorage.setItem("authToken", data.access_token);
      localStorage.setItem("loggedInUser", JSON.stringify(data.user));

      showMessage(loginMessage, "Login successful. Redirecting...", "success");

      setTimeout(function () {
        window.location.replace("dashboard.html");
      }, 500);
    } catch (error) {
      showMessage(loginMessage, error.message, "danger");
    }
  });
}

// ===============================
// Products Page
// ===============================

async function loadProductsPage() {
  const productsTableBody = document.getElementById("productsTableBody");

  if (!productsTableBody) return;

  try {
    await fetchProducts();

    let criticalCount = 0;
    let normalCount = 0;

    productsTableBody.innerHTML = "";

    products.forEach((product) => {
      const stockStatus =
        product.stock_quantity <= product.critical_stock_level
          ? "Critical"
          : "Normal";

      if (stockStatus === "Critical") {
        criticalCount++;
      } else {
        normalCount++;
      }

      const statusClass = getStatusClass(stockStatus);

      productsTableBody.innerHTML += `
        <tr>
          <td>P${String(product.product_id).padStart(3, "0")}</td>
          <td>${escapeHtml(product.product_name)}</td>
          <td>${escapeHtml(product.category)}</td>
          <td>$${Number(product.price)}</td>
          <td>${Number(product.stock_quantity)}</td>
          <td>${Number(product.critical_stock_level)}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${stockStatus}
            </span>
          </td>
        </tr>
      `;
    });

    document.getElementById("totalProducts").textContent = products.length;
    document.getElementById("normalStockProducts").textContent = normalCount;
    document.getElementById("criticalStockProducts").textContent = criticalCount;
  } catch (error) {
    productsTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-danger">
          Products could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
  }
}

// ===============================
// Add Product Form Page
// ===============================

function loadAddProductPage() {
  const addProductForm = document.getElementById("addProductForm");
  const productSuccessMessage = document.getElementById("productSuccessMessage");

  if (!addProductForm) return;

  addProductForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const newProduct = {
      product_name: document.getElementById("productName").value.trim(),
      category: document.getElementById("category").value,
      price: Number(document.getElementById("price").value),
      stock_quantity: Number(document.getElementById("stockQuantity").value),
      critical_stock_level: Number(document.getElementById("criticalStockLevel").value)
    };

    try {
      await fetchJSON(`${API_BASE_URL}/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(newProduct)
      });

      showMessage(
        productSuccessMessage,
        "Product added successfully. The product is saved to the database.",
        "success"
      );

      addProductForm.reset();

      setTimeout(function () {
        window.location.href = "products.html";
      }, 1000);
    } catch (error) {
      showMessage(productSuccessMessage, error.message, "danger");
    }
  });
}

// ===============================
// Orders Page
// ===============================

async function loadOrdersPage() {
  const ordersTableBody = document.getElementById("ordersTableBody");

  if (!ordersTableBody) return;

  // Sales Manager + Admin/Business Owner shipping update yapabilir
  const canEdit = userHasRole(ROLES.ADMIN, ROLES.BUSINESS_OWNER, ROLES.SALES_MANAGER);

  try {
    await fetchOrders();

    let pendingCount = 0;
    let preparingCount = 0;
    let completedCount = 0;

    ordersTableBody.innerHTML = "";

    orders.forEach((order) => {
      if (order.order_status === "Pending") pendingCount++;
      if (order.order_status === "Preparing") preparingCount++;
      if (order.order_status === "Completed") completedCount++;

      const statusClass = getStatusClass(order.order_status);
      // onclick handler argümanları JS string olarak yorumlanır — single/double quote ve
      // <script> içeren kullanıcı verisi enjeksiyonu için escapeJsString gerekli.
      const editBtn = canEdit
        ? `<button class="btn btn-sm btn-outline-primary" onclick="openShippingModal(${Number(order.order_id)}, '${escapeJsString(order.order_status)}', '${escapeJsString(order.tracking_no || "")}', '${escapeJsString(order.shipping_carrier || "")}')">Update</button>`
        : "";
      const tooltip = `${order.customer_email || ""} ${order.customer_phone ? "· " + order.customer_phone : ""}`;

      ordersTableBody.innerHTML += `
        <tr>
          <td>#${Number(order.order_id)}</td>
          <td title="${escapeHtml(tooltip)}">${escapeHtml(order.customer_name)}</td>
          <td>${escapeHtml(order.product_name)}</td>
          <td>${Number(order.quantity)}</td>
          <td>${escapeHtml(order.order_date)}</td>
          <td>
            <span class="status-badge ${statusClass}">${escapeHtml(order.order_status)}</span>
          </td>
          <td>$${Number(order.total_price)}</td>
          <td>${escapeHtml(order.tracking_no || "-")}</td>
          <td>${escapeHtml(order.shipping_carrier || "-")}</td>
          <td>${escapeHtml(order.estimated_delivery || "-")}</td>
          <td>${editBtn}</td>
        </tr>
      `;
    });

    document.getElementById("totalOrders").textContent = orders.length;
    document.getElementById("pendingOrders").textContent = pendingCount;
    document.getElementById("preparingOrders").textContent = preparingCount;
    document.getElementById("completedOrders").textContent = completedCount;
  } catch (error) {
    ordersTableBody.innerHTML = `
      <tr>
        <td colspan="11" class="text-danger">
          Orders could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
  }

  // Modal save handler
  const submitBtn = document.getElementById("modalSubmit");
  if (submitBtn && !submitBtn.dataset.bound) {
    submitBtn.dataset.bound = "1";
    submitBtn.addEventListener("click", saveShippingUpdate);
  }
}

function openShippingModal(orderId, status, tracking, carrier) {
  document.getElementById("modalOrderId").value = orderId;
  document.getElementById("modalOrderIdLabel").textContent = "#" + orderId;
  document.getElementById("modalStatus").value = status === "Cancelled" ? "Pending" : status;
  document.getElementById("modalTracking").value = tracking;
  document.getElementById("modalCarrier").value = carrier;
  document.getElementById("shippingModalError").classList.add("d-none");
  const modalEl = document.getElementById("shippingModal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
}

async function saveShippingUpdate() {
  const orderId = document.getElementById("modalOrderId").value;
  const payload = {
    order_status: document.getElementById("modalStatus").value,
    tracking_no: document.getElementById("modalTracking").value.trim() || null,
    shipping_carrier: document.getElementById("modalCarrier").value.trim() || null,
  };
  const errBox = document.getElementById("shippingModalError");
  try {
    await fetchJSON(`${API_BASE_URL}/orders/${orderId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    bootstrap.Modal.getInstance(document.getElementById("shippingModal")).hide();
    await loadOrdersPage();
  } catch (e) {
    errBox.textContent = e.message;
    errBox.classList.remove("d-none");
  }
}

// ===============================
// Add Order Form Page
// ===============================

async function loadAddOrderPage() {
  const addOrderForm = document.getElementById("addOrderForm");
  const orderSuccessMessage = document.getElementById("orderSuccessMessage");
  const productSelect = document.getElementById("orderProductId");
  const quantityInput = document.getElementById("quantity");
  const totalPriceInput = document.getElementById("totalPrice");

  if (!addOrderForm) return;

  try {
    await fetchProducts();

    productSelect.innerHTML = `
      <option selected disabled value="">Select product</option>
    `;

    products.forEach((product) => {
      productSelect.innerHTML += `
        <option value="${product.product_id}" data-price="${product.price}">
          ${product.product_name} - $${product.price}
        </option>
      `;
    });
  } catch (error) {
    productSelect.innerHTML = `
      <option selected disabled value="">Products could not be loaded</option>
    `;
  }

  function updateTotalPrice() {
    const selectedOption = productSelect.options[productSelect.selectedIndex];
    const price = Number(selectedOption?.dataset?.price || 0);
    const quantity = Number(quantityInput.value || 0);

    if (price > 0 && quantity > 0) {
      totalPriceInput.value = price * quantity;
    }
  }

  productSelect.addEventListener("change", updateTotalPrice);
  quantityInput.addEventListener("input", updateTotalPrice);

  addOrderForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const newOrder = {
      customer_name: document.getElementById("customerName").value.trim(),
      customer_email: document.getElementById("customerEmail").value.trim(),
      customer_phone: document.getElementById("customerPhone").value.trim(),
      product_id: Number(document.getElementById("orderProductId").value),
      quantity: Number(document.getElementById("quantity").value),
      order_date: document.getElementById("orderDate").value,
      order_status: document.getElementById("orderStatus").value,
      total_price: Number(document.getElementById("totalPrice").value)
    };

    try {
      await fetchJSON(`${API_BASE_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(newOrder)
      });

      showMessage(
        orderSuccessMessage,
        "Order added successfully. The order is saved to the database.",
        "success"
      );

      addOrderForm.reset();

      setTimeout(function () {
        window.location.href = "orders.html";
      }, 1000);
    } catch (error) {
      showMessage(orderSuccessMessage, error.message, "danger");
    }
  });
}

// ===============================
// Inventory Page
// ===============================

async function loadInventoryPage() {
  const inventoryTableBody = document.getElementById("inventoryTableBody");

  if (!inventoryTableBody) return;

  try {
    await fetchInventory();

    let criticalCount = 0;
    let normalCount = 0;

    inventoryTableBody.innerHTML = "";

    inventory.forEach((item) => {
      const stockStatus =
        item.current_stock <= item.critical_level ? "Critical" : "Normal";

      if (stockStatus === "Critical") {
        criticalCount++;
      } else {
        normalCount++;
      }

      const statusClass = getStatusClass(stockStatus);

      const suggestion =
        stockStatus === "Critical"
          ? `Restock at least ${item.critical_level * 2} units soon.`
          : "Stock level is sufficient.";

      // Draft Email butonu sadece kritik stoktaki ürünlere ve yetkili role
      const canDraft = userHasRole(ROLES.ADMIN, ROLES.BUSINESS_OWNER, ROLES.INVENTORY_STAFF);
      const draftBtn = (stockStatus === "Critical" && canDraft)
        ? `<button class="btn btn-sm btn-outline-warning" onclick="openDraftEmailModal(${Number(item.product_id)})">Draft Email</button>`
        : "";

      inventoryTableBody.innerHTML += `
        <tr>
          <td>${escapeHtml(item.product_name)}</td>
          <td>${Number(item.current_stock)}</td>
          <td>${Number(item.critical_level)}</td>
          <td>
            <span class="status-badge ${statusClass}">${stockStatus}</span>
          </td>
          <td>${escapeHtml(suggestion)}</td>
          <td>${draftBtn}</td>
        </tr>
      `;
    });

    document.getElementById("inventoryTotalProducts").textContent = inventory.length;
    document.getElementById("inventoryCriticalProducts").textContent = criticalCount;
    document.getElementById("inventoryNormalProducts").textContent = normalCount;
  } catch (error) {
    inventoryTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-danger">
          Inventory could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
  }
}

async function openDraftEmailModal(productId) {
  const modalEl = document.getElementById("emailDraftModal");
  if (!modalEl) return;
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  document.getElementById("emailTo").textContent = "Loading...";
  document.getElementById("emailSubject").textContent = "Loading...";
  document.getElementById("emailBody").textContent = "Generating draft from AI service...";
  document.getElementById("emailDraftError").classList.add("d-none");
  modal.show();
  try {
    const data = await fetchJSON(`${API_BASE_URL}/inventory/products/${productId}/draft-supplier-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    document.getElementById("emailTo").textContent = data.recipient;
    document.getElementById("emailSubject").textContent = data.subject;
    document.getElementById("emailBody").textContent = data.body;
  } catch (e) {
    const err = document.getElementById("emailDraftError");
    err.textContent = e.message;
    err.classList.remove("d-none");
  }
}

// ===============================
// Dashboard Page
// ===============================

async function loadDashboardPage() {
  const dashboardTotalProducts = document.getElementById("dashboardTotalProducts");

  if (!dashboardTotalProducts) return;

  try {
    const dashboardData = await fetchDashboard();
    await fetchOrders();

    document.getElementById("dashboardTotalProducts").textContent =
      dashboardData.total_products;

    document.getElementById("dashboardTotalOrders").textContent =
      dashboardData.total_orders;

    document.getElementById("dashboardPendingOrders").textContent =
      dashboardData.pending_orders;

    document.getElementById("dashboardLowStockProducts").textContent =
      dashboardData.low_stock_products;

    // AI-generated brief from backend (Gemini if AI_ENABLED=true, rule-based fallback otherwise)
    document.getElementById("dashboardDailySummary").textContent =
      dashboardData.ai_brief || `Today: ${dashboardData.today_orders} orders received, ${dashboardData.pending_orders} pending, ${dashboardData.preparing_orders} in preparation, ${dashboardData.completed_orders} completed.`;

    document.getElementById("dashboardStockAlert").textContent =
      `${dashboardData.low_stock_products} products are below the critical stock level and should be restocked soon.`;

    const recentOrdersBody = document.getElementById("dashboardRecentOrdersBody");
    recentOrdersBody.innerHTML = "";

    const recentOrders = orders.slice(0, 5);

    recentOrders.forEach((order) => {
      const statusClass = getStatusClass(order.order_status);

      recentOrdersBody.innerHTML += `
        <tr>
          <td>#${Number(order.order_id)}</td>
          <td>${escapeHtml(order.customer_name)}</td>
          <td>${escapeHtml(order.product_name)}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${escapeHtml(order.order_status)}
            </span>
          </td>
          <td>$${Number(order.total_price)}</td>
        </tr>
      `;
    });
  } catch (error) {
    document.getElementById("dashboardDailySummary").textContent =
      "Dashboard data could not be loaded. Please make sure the backend is running.";
  }
}

// ===============================
// AI Assistant Page
// ===============================

async function loadAIAssistantPage() {
  const aiAssistantForm = document.getElementById("aiAssistantForm");
  const aiQuestionInput = document.getElementById("aiQuestion");
  const aiAnswerBox = document.getElementById("aiAnswerBox");
  const aiAnswerText = document.getElementById("aiAnswerText");
  const exampleQuestions = document.querySelectorAll(".example-question");

  if (!aiAssistantForm) return;

  // Backend AI agent'a istek atan helper
  async function askAI(question) {
    aiAnswerText.textContent = "Thinking...";
    aiAnswerBox.classList.remove("d-none");
    try {
      const data = await fetchJSON(`${API_BASE_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),  // customer_id opsiyonel
      });
      let text = data.reply || "(empty response)";
      if (data.used_tools && data.used_tools.length) {
        text += `\n\n[tools used: ${data.used_tools.join(", ")}]`;
      }
      aiAnswerText.textContent = text;
    } catch (e) {
      aiAnswerText.textContent = "AI error: " + e.message;
    }
  }

  aiAssistantForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const question = aiQuestionInput.value.trim();
    if (!question) return;
    askAI(question);
  });

  exampleQuestions.forEach((button) => {
    button.addEventListener("click", function () {
      aiQuestionInput.value = button.textContent.trim();
      askAI(aiQuestionInput.value);
    });
  });
}

// ===============================
// Page Loader
// ===============================

async function loadSuppliersPage() {
  const tbody = document.getElementById("suppliersTableBody");
  if (!tbody) return;
  try {
    const suppliers = await fetchSuppliers();
    if (!suppliers.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-muted text-center">No suppliers found.</td></tr>`;
      return;
    }
    tbody.innerHTML = "";
    suppliers.forEach((s) => {
      const productsHtml = s.products
        .map((p) => `<span class="badge bg-light text-dark me-1 mb-1">${escapeHtml(p.product_name)} (${Number(p.stock_quantity)})</span>`)
        .join(" ") || `<span class="text-muted">No products</span>`;
      tbody.innerHTML += `
        <tr>
          <td>${Number(s.supplier_id)}</td>
          <td>${escapeHtml(s.name)}</td>
          <td><a href="mailto:${escapeHtml(s.email)}">${escapeHtml(s.email)}</a></td>
          <td>${escapeHtml(s.phone || "-")}</td>
          <td>${productsHtml}</td>
        </tr>
      `;
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-danger">Suppliers could not be loaded: ${escapeHtml(e.message)}</td></tr>`;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  enforceLogin();
  setupLogoutButton();
  applyRoleUI();
  loadRegisterPage();
  loadLoginPage();
  loadProductsPage();
  loadAddProductPage();
  loadOrdersPage();
  loadAddOrderPage();
  loadInventoryPage();
  loadDashboardPage();
  loadSuppliersPage();
  loadAIAssistantPage();
});