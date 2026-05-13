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

  const navUl = document.querySelector("nav.navbar .navbar-nav.ms-auto");

  if (navUl && !document.getElementById("currentUserBadge")) {
    const li = document.createElement("li");
    li.className = "nav-item d-flex align-items-center me-3";
    li.id = "currentUserBadge";

    li.innerHTML = `
      <span class="text-light small">
        ${escapeHtml(user.name)}
        <span class="badge bg-primary">${escapeHtml(user.role)}</span>
      </span>
    `;

    navUl.insertBefore(li, navUl.firstChild);
  }

  const role = user.role;

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

  document.querySelectorAll("a, button").forEach((el) => {
    const text = el.textContent.trim().toLowerCase();
    const href = (el.getAttribute("href") || "").toLowerCase();

    if (
      (text === "add new product" || text === "add product" || href === "add-product.html") &&
      !ADMIN_ROLES.includes(role)
    ) {
      el.style.display = "none";
    }

    if (
      (text === "add new supplier" || text === "add supplier" || href === "add-supplier.html") &&
      !ADMIN_ROLES.includes(role)
    ) {
      el.style.display = "none";
    }

    if (
      (text === "add new order" || text === "add order" || href === "add-order.html") &&
      role === ROLES.INVENTORY_STAFF
    ) {
      el.style.display = "none";
    }
  });
}

// ===============================
// Helper Functions
// ===============================

function escapeHtml(value) {
  if (value === null || value === undefined) return "";

  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

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

function formatDate(dateString) {
  if (!dateString) return "-";

  const [datePart] = String(dateString).split("T");
  const parts = datePart.split("-");

  if (parts.length !== 3) return dateString;

  const year = Number(parts[0]);
  const monthIndex = Number(parts[1]) - 1;
  const day = Number(parts[2]);
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];

  if (
    Number.isNaN(year) ||
    Number.isNaN(monthIndex) ||
    Number.isNaN(day) ||
    monthIndex < 0 ||
    monthIndex >= monthNames.length
  ) {
    return dateString;
  }

  return `${String(day).padStart(2, "0")}-${String(monthIndex + 1).padStart(2, "0")}-${year}`;
}

function toApiDate(dateString) {
  const parts = String(dateString).trim().split("-");

  if (parts.length !== 3) return dateString;

  const [day, month, year] = parts;
  return `${year}-${month}-${day}`;
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
  const role = getCurrentRole();
  return roles.includes(role);
}

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
  const token = getAuthToken();

  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAuth();

    const page = getCurrentPageName();

    if (!PUBLIC_PAGES.includes(page)) {
      window.location.replace("login.html");
    }

    throw new Error("Session expired. Please login again.");
  }

  if (response.status === 403) {
    let detail = "Permission denied for your role.";

    try {
      const data = await response.json();
      if (data.detail) detail = data.detail;
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

  if (response.status === 204) {
    return null;
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
      role: document.getElementById("role").value,
    };

    try {
      await fetchJSON(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });

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
      password: document.getElementById("loginPassword").value,
    };

    try {
      const data = await fetchJSON(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });

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

  const canEditProduct = userHasRole(ROLES.ADMIN, ROLES.BUSINESS_OWNER);

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

      const updateBtn = canEditProduct
        ? `<button class="btn btn-sm btn-outline-primary" onclick="openProductUpdateModal(${Number(product.product_id)})">Update</button>`
        : "";

      const deleteBtn = canEditProduct
        ? `<button class="btn btn-sm btn-outline-danger" onclick="openProductDeleteModal(${Number(product.product_id)})">Delete</button>`
        : "";

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
          <td>
            <div class="d-flex gap-2">
              ${updateBtn}
              ${deleteBtn}
            </div>
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
        <td colspan="8" class="text-danger">
          Products could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
  }
}

function openProductUpdateModal(productId) {
  const product = products.find((p) => Number(p.product_id) === Number(productId));

  if (!product) {
    alert("Product not found.");
    return;
  }

  document.getElementById("updateProductId").value = product.product_id;
  document.getElementById("updateProductNameLabel").textContent = product.product_name;
  document.getElementById("updateProductCategoryLabel").textContent = product.category;
  document.getElementById("updateProductPrice").value = Number(product.price);
  document.getElementById("updateProductStockQuantity").value = Number(product.stock_quantity);
  document.getElementById("updateProductCriticalStockLevel").value =
    Number(product.critical_stock_level);

  document.getElementById("productUpdateError").classList.add("d-none");

  const modalEl = document.getElementById("productUpdateModal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  modal.show();
}

async function saveProductUpdate() {
  const productId = Number(document.getElementById("updateProductId").value);

  const product = products.find((p) => Number(p.product_id) === Number(productId));

  if (!product) {
    alert("Product not found.");
    return;
  }

  const price = Number(document.getElementById("updateProductPrice").value);
  const stockQuantity = Number(document.getElementById("updateProductStockQuantity").value);
  const criticalStockLevel = Number(
    document.getElementById("updateProductCriticalStockLevel").value
  );

  const errorBox = document.getElementById("productUpdateError");

  if (Number.isNaN(price) || price <= 0) {
    errorBox.textContent = "Please enter a valid price.";
    errorBox.classList.remove("d-none");
    return;
  }

  if (Number.isNaN(stockQuantity) || stockQuantity < 0) {
    errorBox.textContent = "Please enter a valid stock quantity.";
    errorBox.classList.remove("d-none");
    return;
  }

  if (Number.isNaN(criticalStockLevel) || criticalStockLevel < 0) {
    errorBox.textContent = "Please enter a valid critical stock level.";
    errorBox.classList.remove("d-none");
    return;
  }

  const payload = {
    product_name: product.product_name,
    category: product.category,
    price: price,
    stock_quantity: stockQuantity,
    critical_stock_level: criticalStockLevel,
  };

  try {
    await fetchJSON(`${API_BASE_URL}/products/${productId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    bootstrap.Modal.getInstance(document.getElementById("productUpdateModal")).hide();

    await loadProductsPage();
    await loadInventoryPage();
    await loadDashboardPage();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("d-none");
  }
}

function openProductDeleteModal(productId) {
  const product = products.find((p) => Number(p.product_id) === Number(productId));

  if (!product) {
    alert("Product not found.");
    return;
  }

  document.getElementById("deleteProductId").value = product.product_id;

  document.getElementById("deleteProductCodeLabel").textContent =
    "P" + String(product.product_id).padStart(3, "0");

  document.getElementById("deleteProductNameLabel").textContent = product.product_name;
  document.getElementById("productDeleteError").classList.add("d-none");

  const modalEl = document.getElementById("productDeleteModal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  modal.show();
}

async function confirmDeleteProduct() {
  const productId = Number(document.getElementById("deleteProductId").value);
  const errorBox = document.getElementById("productDeleteError");

  try {
    await fetchJSON(`${API_BASE_URL}/products/${productId}`, {
      method: "DELETE",
    });

    bootstrap.Modal.getInstance(document.getElementById("productDeleteModal")).hide();

    await loadProductsPage();
    await loadInventoryPage();
    await loadDashboardPage();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("d-none");
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
      critical_stock_level: Number(document.getElementById("criticalStockLevel").value),
    };

    try {
      await fetchJSON(`${API_BASE_URL}/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newProduct),
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

  const canEdit = userHasRole(
    ROLES.ADMIN,
    ROLES.BUSINESS_OWNER,
    ROLES.SALES_MANAGER
  );

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

      const updateBtn = canEdit
        ? `<button class="btn btn-sm btn-outline-primary" onclick="openShippingModal(${Number(order.order_id)}, '${escapeJsString(order.order_status)}', '${escapeJsString(order.tracking_no || "")}', '${escapeJsString(order.shipping_carrier || "")}')">Update</button>`
        : "";

      const deleteBtn = canEdit
        ? `<button class="btn btn-sm btn-outline-danger" onclick="openOrderDeleteModal(${Number(order.order_id)})">Delete</button>`
        : "";

      const tooltip = `${order.customer_email || ""} ${
        order.customer_phone ? "· " + order.customer_phone : ""
      }`;

      ordersTableBody.innerHTML += `
        <tr>
          <td>#${Number(order.order_id)}</td>
          <td title="${escapeHtml(tooltip)}">${escapeHtml(order.customer_name)}</td>
          <td>${escapeHtml(order.product_name)}</td>
          <td>${Number(order.quantity)}</td>
          <td>${formatDate(order.order_date)}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${escapeHtml(order.order_status)}
            </span>
          </td>
          <td>$${Number(order.total_price)}</td>
          <td>${escapeHtml(order.tracking_no || "-")}</td>
          <td>${escapeHtml(order.shipping_carrier || "-")}</td>
          <td>${formatDate(order.estimated_delivery)}</td>
          <td>
            <div class="d-flex gap-2">
              ${updateBtn}
              ${deleteBtn}
            </div>
          </td>
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

  const submitBtn = document.getElementById("modalSubmit");

  if (submitBtn && !submitBtn.dataset.bound) {
    submitBtn.dataset.bound = "1";
    submitBtn.addEventListener("click", saveShippingUpdate);
  }
}

function openShippingModal(orderId, status, tracking, carrier) {
  document.getElementById("modalOrderId").value = orderId;
  document.getElementById("modalOrderIdLabel").textContent = "#" + orderId;

  document.getElementById("modalStatus").value =
    status === "Cancelled" ? "Pending" : status;

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
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    bootstrap.Modal.getInstance(document.getElementById("shippingModal")).hide();

    await loadOrdersPage();
    await loadDashboardPage();
  } catch (error) {
    errBox.textContent = error.message;
    errBox.classList.remove("d-none");
  }
}

function openOrderDeleteModal(orderId) {
  const order = orders.find((o) => Number(o.order_id) === Number(orderId));

  if (!order) {
    alert("Order not found.");
    return;
  }

  document.getElementById("deleteOrderId").value = order.order_id;
  document.getElementById("deleteOrderCodeLabel").textContent = "#" + Number(order.order_id);
  document.getElementById("deleteOrderCustomerLabel").textContent = order.customer_name || "-";
  document.getElementById("deleteOrderProductLabel").textContent = order.product_name || "-";
  document.getElementById("deleteOrderTotalLabel").textContent =
    "$" + Number(order.total_price);

  document.getElementById("orderDeleteError").classList.add("d-none");

  const modalEl = document.getElementById("orderDeleteModal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  modal.show();
}

async function confirmDeleteOrder() {
  const orderId = Number(document.getElementById("deleteOrderId").value);
  const errorBox = document.getElementById("orderDeleteError");

  try {
    await fetchJSON(`${API_BASE_URL}/orders/${orderId}`, {
      method: "DELETE",
    });

    bootstrap.Modal.getInstance(document.getElementById("orderDeleteModal")).hide();

    await loadOrdersPage();
    await loadProductsPage();
    await loadInventoryPage();
    await loadDashboardPage();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("d-none");
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
      const productPrice = Number(String(product.price).replace(',', '.'));
      productSelect.innerHTML += `
        <option value="${product.product_id}" data-price="${productPrice}">
          ${escapeHtml(product.product_name)} - $${productPrice}
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
    const priceRaw = selectedOption?.dataset?.price || "0";
    const price = Number(String(priceRaw).replace(',', '.'));
    const quantity = Number(quantityInput.value || 0);

    if (price > 0 && quantity > 0) {
      totalPriceInput.value = (price * quantity).toFixed(2);
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
      order_date: toApiDate(document.getElementById("orderDate").value),
      order_status: document.getElementById("orderStatus").value,
      total_price: Number(document.getElementById("totalPrice").value),
    };

    try {
      await fetchJSON(`${API_BASE_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newOrder),
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

      const canDraft = userHasRole(
        ROLES.ADMIN,
        ROLES.BUSINESS_OWNER,
        ROLES.INVENTORY_STAFF
      );

      const draftBtn =
        stockStatus === "Critical" && canDraft
          ? `<button class="btn btn-sm btn-outline-warning" onclick="openDraftEmailModal(${Number(item.product_id)})">Draft Email</button>`
          : "";

      inventoryTableBody.innerHTML += `
        <tr>
          <td>${escapeHtml(item.product_name)}</td>
          <td>${Number(item.current_stock)}</td>
          <td>${Number(item.critical_level)}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${stockStatus}
            </span>
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

  const modal = window.bootstrap
    ? bootstrap.Modal.getOrCreateInstance(modalEl)
    : null;

  document.getElementById("emailTo").textContent = "Loading...";
  document.getElementById("emailSubject").textContent = "Loading...";
  document.getElementById("emailBody").textContent =
    "Generating draft from AI service...";
  document.getElementById("emailDraftError").classList.add("d-none");

  const mailLink = document.getElementById("emailDraftMailLink");
  if (mailLink) {
    mailLink.href = "#";
    mailLink.classList.add("disabled");
    mailLink.setAttribute("aria-disabled", "true");
  }

  if (modal) {
    modal.show();
  } else {
    modalEl.classList.add("show");
    modalEl.style.display = "block";
    modalEl.removeAttribute("aria-hidden");
    modalEl.setAttribute("aria-modal", "true");
    modalEl.setAttribute("role", "dialog");
  }

  try {
    const data = await fetchJSON(
      `${API_BASE_URL}/inventory/products/${productId}/draft-supplier-email`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }
    );

    document.getElementById("emailTo").textContent = data.recipient;
    document.getElementById("emailSubject").textContent = data.subject;
    document.getElementById("emailBody").textContent = data.body;

    if (mailLink) {
      const params = new URLSearchParams({
        subject: data.subject,
        body: data.body,
      });

      mailLink.href = `mailto:${encodeURIComponent(data.recipient)}?${params.toString()}`;
      mailLink.classList.remove("disabled");
      mailLink.removeAttribute("aria-disabled");
    }
  } catch (error) {
    const err = document.getElementById("emailDraftError");
    err.textContent = error.message;
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

    document.getElementById("dashboardDailySummary").textContent =
      dashboardData.ai_brief ||
      `Today: ${dashboardData.today_orders} orders received, ${dashboardData.pending_orders} pending, ${dashboardData.preparing_orders} in preparation, ${dashboardData.completed_orders} completed.`;

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

  async function askAI(question) {
    aiAnswerText.textContent = "Thinking...";
    aiAnswerBox.classList.remove("d-none");

    try {
      const data = await fetchJSON(`${API_BASE_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });

      let text = data.reply || "(empty response)";

      if (data.used_tools && data.used_tools.length) {
        text += `\n\n[tools used: ${data.used_tools.join(", ")}]`;
      }

      aiAnswerText.textContent = text;
    } catch (error) {
      aiAnswerText.textContent = "AI error: " + error.message;
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
// Suppliers Page
// ===============================

async function loadSuppliersPage() {
  const tbody = document.getElementById("suppliersTableBody");

  if (!tbody) return;

  const canEditSupplier = userHasRole(ROLES.ADMIN, ROLES.BUSINESS_OWNER);

  try {
    const suppliers = await fetchSuppliers();

    if (!suppliers.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-muted text-center">
            No suppliers found.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = "";

    suppliers.forEach((supplier) => {
      const productsHtml =
        supplier.products
          .map(
            (product) =>
              `<span class="badge bg-light text-dark me-1 mb-1">
                ${escapeHtml(product.product_name)} (${Number(product.stock_quantity)})
              </span>`
          )
          .join(" ") || `<span class="text-muted">No products</span>`;

      const updateBtn = canEditSupplier
        ? `<button class="btn btn-sm btn-outline-primary" onclick="openSupplierUpdateModal(${Number(supplier.supplier_id)})">Update</button>`
        : "";

      const deleteBtn = canEditSupplier
        ? `<button class="btn btn-sm btn-outline-danger" onclick="openSupplierDeleteModal(${Number(supplier.supplier_id)})">Delete</button>`
        : "";

      tbody.innerHTML += `
        <tr>
          <td>${Number(supplier.supplier_id)}</td>
          <td>${escapeHtml(supplier.name)}</td>
          <td>
            <a href="mailto:${escapeHtml(supplier.email)}">
              ${escapeHtml(supplier.email)}
            </a>
          </td>
          <td>${escapeHtml(supplier.phone || "-")}</td>
          <td>${productsHtml}</td>
          <td>
            <div class="d-flex gap-2">
              ${updateBtn}
              ${deleteBtn}
            </div>
          </td>
        </tr>
      `;
    });
  } catch (error) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-danger">
          Suppliers could not be loaded: ${escapeHtml(error.message)}
        </td>
      </tr>
    `;
  }
}

function updateSupplierSelectedProductsView() {
  const selectedProductsBox = document.getElementById("updateSelectedSupplierProducts");
  const selectedProductsList = document.getElementById("updateSelectedSupplierProductsList");

  if (!selectedProductsBox || !selectedProductsList) return;

  const checkedProducts = document.querySelectorAll(".update-supplier-product-checkbox:checked");

  selectedProductsList.innerHTML = "";

  if (!checkedProducts.length) {
    selectedProductsBox.classList.add("d-none");
    return;
  }

  selectedProductsBox.classList.remove("d-none");

  checkedProducts.forEach((checkbox) => {
    selectedProductsList.innerHTML += `
      <span class="badge bg-primary selected-product-badge">
        ${escapeHtml(checkbox.dataset.productName)}
      </span>
    `;
  });
}

async function renderSupplierUpdateProductCheckboxes(selectedProductIds = []) {
  const productsCheckboxList = document.getElementById("updateSupplierProductsCheckboxList");

  if (!productsCheckboxList) return;

  try {
    await fetchProducts();

    productsCheckboxList.innerHTML = "";

    if (!products.length) {
      productsCheckboxList.innerHTML = `
        <p class="text-muted mb-0">
          No products found.
        </p>
      `;
      return;
    }

    products.forEach((product) => {
      const isChecked = selectedProductIds.includes(Number(product.product_id));

      productsCheckboxList.innerHTML += `
        <label class="product-checkbox-item">
          <input
            type="checkbox"
            class="form-check-input update-supplier-product-checkbox"
            value="${Number(product.product_id)}"
            data-product-name="${escapeHtml(product.product_name)}"
            ${isChecked ? "checked" : ""}
          />

          <div>
            <div class="fw-semibold">
              ${escapeHtml(product.product_name)}
            </div>
            <div class="text-muted small">
              Stock: ${Number(product.stock_quantity)}
            </div>
          </div>
        </label>
      `;
    });

    document.querySelectorAll(".update-supplier-product-checkbox").forEach((checkbox) => {
      checkbox.addEventListener("change", updateSupplierSelectedProductsView);
    });

    updateSupplierSelectedProductsView();
  } catch (error) {
    productsCheckboxList.innerHTML = `
      <p class="text-danger mb-0">
        Products could not be loaded.
      </p>
    `;
  }
}

async function openSupplierUpdateModal(supplierId) {
  try {
    const supplier = await fetchJSON(`${API_BASE_URL}/suppliers/${supplierId}`);

    document.getElementById("updateSupplierId").value = supplier.supplier_id;

    document.getElementById("updateSupplierIdLabel").textContent =
      "#" + Number(supplier.supplier_id);

    document.getElementById("updateSupplierNameLabel").textContent =
      supplier.name;

    document.getElementById("updateSupplierEmail").value =
      supplier.email || "";

    document.getElementById("updateSupplierPhone").value =
      supplier.phone || "";

    document.getElementById("supplierUpdateError").classList.add("d-none");

    const selectedProductIds = supplier.products.map((product) =>
      Number(product.product_id)
    );

    await renderSupplierUpdateProductCheckboxes(selectedProductIds);

    const modalEl = document.getElementById("supplierUpdateModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    modal.show();
  } catch (error) {
    alert(error.message);
  }
}

async function saveSupplierUpdate() {
  const supplierId = Number(document.getElementById("updateSupplierId").value);
  const supplierName = document.getElementById("updateSupplierNameLabel").textContent.trim();
  const supplierEmail = document.getElementById("updateSupplierEmail").value.trim();
  const supplierPhone = document.getElementById("updateSupplierPhone").value.trim();
  const errorBox = document.getElementById("supplierUpdateError");

  const selectedProductIds = Array.from(
    document.querySelectorAll(".update-supplier-product-checkbox:checked")
  ).map((checkbox) => Number(checkbox.value));

  if (!supplierEmail) {
    errorBox.textContent = "Supplier email is required.";
    errorBox.classList.remove("d-none");
    return;
  }

  const payload = {
    name: supplierName,
    email: supplierEmail,
    phone: supplierPhone,
    product_ids: selectedProductIds,
  };

  try {
    await fetchJSON(`${API_BASE_URL}/suppliers/${supplierId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    bootstrap.Modal.getInstance(document.getElementById("supplierUpdateModal")).hide();

    await loadSuppliersPage();
    await loadInventoryPage();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("d-none");
  }
}

async function openSupplierDeleteModal(supplierId) {
  try {
    const supplier = await fetchJSON(`${API_BASE_URL}/suppliers/${supplierId}`);

    document.getElementById("deleteSupplierId").value = supplier.supplier_id;

    document.getElementById("deleteSupplierIdLabel").textContent =
      "#" + Number(supplier.supplier_id);

    document.getElementById("deleteSupplierNameLabel").textContent =
      supplier.name;

    document.getElementById("deleteSupplierEmailLabel").textContent =
      supplier.email || "-";

    document.getElementById("supplierDeleteError").classList.add("d-none");

    const modalEl = document.getElementById("supplierDeleteModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    modal.show();
  } catch (error) {
    alert(error.message);
  }
}

async function confirmDeleteSupplier() {
  const supplierId = Number(document.getElementById("deleteSupplierId").value);
  const errorBox = document.getElementById("supplierDeleteError");

  try {
    await fetchJSON(`${API_BASE_URL}/suppliers/${supplierId}`, {
      method: "DELETE",
    });

    bootstrap.Modal.getInstance(document.getElementById("supplierDeleteModal")).hide();

    await loadSuppliersPage();
    await loadInventoryPage();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("d-none");
  }
}

// ===============================
// Add Supplier Form Page
// ===============================

async function loadAddSupplierPage() {
  const addSupplierForm = document.getElementById("addSupplierForm");
  const supplierSuccessMessage = document.getElementById("supplierSuccessMessage");
  const productsCheckboxList = document.getElementById("supplierProductsCheckboxList");
  const selectedProductsBox = document.getElementById("selectedSupplierProducts");
  const selectedProductsList = document.getElementById("selectedSupplierProductsList");

  if (!addSupplierForm) return;

  function updateSelectedProductsView() {
    const checkedProducts = document.querySelectorAll(".supplier-product-checkbox:checked");

    selectedProductsList.innerHTML = "";

    if (!checkedProducts.length) {
      selectedProductsBox.classList.add("d-none");
      return;
    }

    selectedProductsBox.classList.remove("d-none");

    checkedProducts.forEach((checkbox) => {
      selectedProductsList.innerHTML += `
        <span class="badge bg-primary selected-product-badge">
          ${escapeHtml(checkbox.dataset.productName)}
        </span>
      `;
    });
  }

  try {
    await fetchProducts();

    productsCheckboxList.innerHTML = "";

    if (!products.length) {
      productsCheckboxList.innerHTML = `
        <p class="text-muted mb-0">
          No products found.
        </p>
      `;
    } else {
      products.forEach((product) => {
        productsCheckboxList.innerHTML += `
          <label class="product-checkbox-item">
            <input
              type="checkbox"
              class="form-check-input supplier-product-checkbox"
              value="${Number(product.product_id)}"
              data-product-name="${escapeHtml(product.product_name)}"
            />

            <div>
              <div class="fw-semibold">
                ${escapeHtml(product.product_name)}
              </div>
              <div class="text-muted small">
                Stock: ${Number(product.stock_quantity)}
              </div>
            </div>
          </label>
        `;
      });
    }

    document.querySelectorAll(".supplier-product-checkbox").forEach((checkbox) => {
      checkbox.addEventListener("change", updateSelectedProductsView);
    });
  } catch (error) {
    productsCheckboxList.innerHTML = `
      <p class="text-danger mb-0">
        Products could not be loaded.
      </p>
    `;
  }

  addSupplierForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const selectedProductIds = Array.from(
      document.querySelectorAll(".supplier-product-checkbox:checked")
    ).map((checkbox) => Number(checkbox.value));

    const newSupplier = {
      name: document.getElementById("supplierName").value.trim(),
      email: document.getElementById("supplierEmail").value.trim(),
      phone: document.getElementById("supplierPhone").value.trim(),
      product_ids: selectedProductIds,
    };

    try {
      await fetchJSON(`${API_BASE_URL}/suppliers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newSupplier),
      });

      showMessage(
        supplierSuccessMessage,
        "Supplier added successfully. Redirecting to suppliers page...",
        "success"
      );

      addSupplierForm.reset();
      updateSelectedProductsView();

      setTimeout(function () {
        window.location.href = "suppliers.html";
      }, 1000);
    } catch (error) {
      showMessage(supplierSuccessMessage, error.message, "danger");
    }
  });
}

// ===============================
// Page Loader
// ===============================

document.addEventListener("DOMContentLoaded", function () {
  enforceLogin();
  setupLogoutButton();
  applyRoleUI();

  const productUpdateSaveButton = document.getElementById("productUpdateSaveButton");

  if (productUpdateSaveButton && typeof saveProductUpdate === "function") {
    productUpdateSaveButton.addEventListener("click", saveProductUpdate);
  }

  const productDeleteConfirmButton = document.getElementById("productDeleteConfirmButton");

  if (productDeleteConfirmButton && typeof confirmDeleteProduct === "function") {
    productDeleteConfirmButton.addEventListener("click", confirmDeleteProduct);
  }

  const orderDeleteConfirmButton = document.getElementById("orderDeleteConfirmButton");

  if (orderDeleteConfirmButton && typeof confirmDeleteOrder === "function") {
    orderDeleteConfirmButton.addEventListener("click", confirmDeleteOrder);
  }

  const supplierUpdateSaveButton = document.getElementById("supplierUpdateSaveButton");

  if (supplierUpdateSaveButton && typeof saveSupplierUpdate === "function") {
    supplierUpdateSaveButton.addEventListener("click", saveSupplierUpdate);
  }

  const supplierDeleteConfirmButton = document.getElementById("supplierDeleteConfirmButton");

  if (supplierDeleteConfirmButton && typeof confirmDeleteSupplier === "function") {
    supplierDeleteConfirmButton.addEventListener("click", confirmDeleteSupplier);
  }

  loadRegisterPage();
  loadLoginPage();
  loadProductsPage();
  loadAddProductPage();
  loadOrdersPage();
  loadAddOrderPage();
  loadInventoryPage();
  loadDashboardPage();
  loadSuppliersPage();
  loadAddSupplierPage();
  loadAIAssistantPage();
});
