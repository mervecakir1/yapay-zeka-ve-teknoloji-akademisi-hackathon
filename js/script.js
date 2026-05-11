const API_BASE_URL = "http://127.0.0.1:8000";

let products = [];
let orders = [];
let inventory = [];

// ===============================
// Helper Functions
// ===============================

function getStatusClass(status) {
  if (status === "Pending") return "status-pending";
  if (status === "Preparing") return "status-preparing";
  if (status === "Completed") return "status-completed";
  if (status === "Cancelled") return "status-cancelled";
  if (status === "Critical") return "status-critical";
  return "status-normal";
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);

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
      const data = await fetchJSON(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(newUser)
      });

      localStorage.setItem("loggedInUser", JSON.stringify(data.user));

      showMessage(
        registerSuccessMessage,
        "Account created successfully. Redirecting to dashboard...",
        "success"
      );

      registerForm.reset();

      setTimeout(function () {
        window.location.href = "dashboard.html";
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
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(loginData)
      });

      localStorage.setItem("loggedInUser", JSON.stringify(data.user));

      showMessage(
        loginMessage,
        "Login successful. Redirecting to dashboard...",
        "success"
      );

      // Most reliable redirect for Live Server
      setTimeout(function () {
        window.location.replace("http://127.0.0.1:5500/dashboard.html");
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
          <td>${product.product_name}</td>
          <td>${product.category}</td>
          <td>$${product.price}</td>
          <td>${product.stock_quantity}</td>
          <td>${product.critical_stock_level}</td>
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

      ordersTableBody.innerHTML += `
        <tr>
          <td>#${order.order_id}</td>
          <td>${order.customer_name}</td>
          <td>${order.product_name}</td>
          <td>${order.quantity}</td>
          <td>${order.order_date}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${order.order_status}
            </span>
          </td>
          <td>$${order.total_price}</td>
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
        <td colspan="7" class="text-danger">
          Orders could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
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

      inventoryTableBody.innerHTML += `
        <tr>
          <td>${item.product_name}</td>
          <td>${item.current_stock}</td>
          <td>${item.critical_level}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${stockStatus}
            </span>
          </td>
          <td>${suggestion}</td>
        </tr>
      `;
    });

    document.getElementById("inventoryTotalProducts").textContent = inventory.length;
    document.getElementById("inventoryCriticalProducts").textContent = criticalCount;
    document.getElementById("inventoryNormalProducts").textContent = normalCount;
  } catch (error) {
    inventoryTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-danger">
          Inventory could not be loaded. Please make sure the backend is running.
        </td>
      </tr>
    `;
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

    document.getElementById("dashboardDailySummary").innerHTML = `
      Today, the business received <strong>${dashboardData.today_orders} orders</strong>. 
      <strong>${dashboardData.pending_orders} orders</strong> are pending, 
      <strong>${dashboardData.preparing_orders} orders</strong> are preparing, and 
      <strong>${dashboardData.completed_orders} orders</strong> have been completed.
    `;

    document.getElementById("dashboardStockAlert").textContent =
      `${dashboardData.low_stock_products} products are below the critical stock level and should be restocked soon.`;

    const recentOrdersBody = document.getElementById("dashboardRecentOrdersBody");
    recentOrdersBody.innerHTML = "";

    const recentOrders = orders.slice(0, 5);

    recentOrders.forEach((order) => {
      const statusClass = getStatusClass(order.order_status);

      recentOrdersBody.innerHTML += `
        <tr>
          <td>#${order.order_id}</td>
          <td>${order.customer_name}</td>
          <td>${order.product_name}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${order.order_status}
            </span>
          </td>
          <td>$${order.total_price}</td>
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
      const response = await fetch("http://127.0.0.1:8001/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
      });

      const data = await response.json();
      aiAnswerText.textContent = data.answer;
    } catch (error) {
      aiAnswerText.textContent = "AI service is not running. Please start the AI agent.";
    }
  }

  aiAssistantForm.addEventListener("submit", function (event) {
    event.preventDefault();
    askAI(aiQuestionInput.value.trim());
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

document.addEventListener("DOMContentLoaded", function () {
  loadRegisterPage();
  loadLoginPage();
  loadProductsPage();
  loadAddProductPage();
  loadOrdersPage();
  loadAddOrderPage();
  loadInventoryPage();
  loadDashboardPage();
  loadAIAssistantPage();
});