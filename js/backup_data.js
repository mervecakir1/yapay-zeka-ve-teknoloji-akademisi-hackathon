// ===============================
// Product Mock Data
// ===============================

const products = [
  {
    product_id: "P001",
    product_name: "Handmade Soap",
    category: "Personal Care",
    price: 7,
    stock_quantity: 35,
    critical_stock_level: 15
  },
  {
    product_id: "P002",
    product_name: "Natural Olive Oil",
    category: "Food",
    price: 18,
    stock_quantity: 8,
    critical_stock_level: 10
  },
  {
    product_id: "P003",
    product_name: "Organic Honey",
    category: "Food",
    price: 12,
    stock_quantity: 5,
    critical_stock_level: 10
  },
  {
    product_id: "P004",
    product_name: "Handmade Candle",
    category: "Home Decoration",
    price: 9,
    stock_quantity: 22,
    critical_stock_level: 8
  },
  {
    product_id: "P005",
    product_name: "Ceramic Coffee Cup",
    category: "Home & Kitchen",
    price: 16,
    stock_quantity: 18,
    critical_stock_level: 10
  },
  {
    product_id: "P006",
    product_name: "Natural Lip Balm",
    category: "Cosmetics",
    price: 6,
    stock_quantity: 40,
    critical_stock_level: 15
  },
  {
    product_id: "P007",
    product_name: "Handmade Bracelet",
    category: "Accessories",
    price: 14,
    stock_quantity: 12,
    critical_stock_level: 10
  },
  {
    product_id: "P008",
    product_name: "Knitted Scarf",
    category: "Textile",
    price: 20,
    stock_quantity: 9,
    critical_stock_level: 12
  },
  {
    product_id: "P009",
    product_name: "Organic Herbal Tea",
    category: "Beverage",
    price: 8,
    stock_quantity: 6,
    critical_stock_level: 12
  },
  {
    product_id: "P010",
    product_name: "Handmade Necklace",
    category: "Accessories",
    price: 19,
    stock_quantity: 25,
    critical_stock_level: 10
  },
  {
    product_id: "P011",
    product_name: "Natural Face Cream",
    category: "Cosmetics",
    price: 15,
    stock_quantity: 14,
    critical_stock_level: 10
  },
  {
    product_id: "P012",
    product_name: "Decorative Pillow Cover",
    category: "Home Textile",
    price: 13,
    stock_quantity: 30,
    critical_stock_level: 12
  },
  {
    product_id: "P013",
    product_name: "Handmade Tote Bag",
    category: "Fashion",
    price: 22,
    stock_quantity: 11,
    critical_stock_level: 10
  },
  {
    product_id: "P014",
    product_name: "Organic Jam",
    category: "Food",
    price: 9,
    stock_quantity: 7,
    critical_stock_level: 10
  },
  {
    product_id: "P015",
    product_name: "Lavender Room Spray",
    category: "Home Fragrance",
    price: 10,
    stock_quantity: 28,
    critical_stock_level: 12
  },
  {
    product_id: "P016",
    product_name: "Handmade Hair Clip",
    category: "Accessories",
    price: 5,
    stock_quantity: 45,
    critical_stock_level: 15
  },
  {
    product_id: "P017",
    product_name: "Ceramic Plate",
    category: "Home & Kitchen",
    price: 24,
    stock_quantity: 10,
    critical_stock_level: 10
  },
  {
    product_id: "P018",
    product_name: "Natural Body Lotion",
    category: "Cosmetics",
    price: 13,
    stock_quantity: 16,
    critical_stock_level: 10
  },
  {
    product_id: "P019",
    product_name: "Handmade Keychain",
    category: "Accessories",
    price: 4,
    stock_quantity: 50,
    critical_stock_level: 20
  },
  {
    product_id: "P020",
    product_name: "Organic Dried Fruit Box",
    category: "Food",
    price: 17,
    stock_quantity: 6,
    critical_stock_level: 10
  },
  {
    product_id: "P021",
    product_name: "Macrame Wall Hanging",
    category: "Home Decoration",
    price: 28,
    stock_quantity: 13,
    critical_stock_level: 8
  },
  {
    product_id: "P022",
    product_name: "Handmade Earrings",
    category: "Accessories",
    price: 11,
    stock_quantity: 32,
    critical_stock_level: 12
  },
  {
    product_id: "P023",
    product_name: "Natural Shampoo Bar",
    category: "Personal Care",
    price: 9,
    stock_quantity: 17,
    critical_stock_level: 10
  },
  {
    product_id: "P024",
    product_name: "Organic Tomato Paste",
    category: "Food",
    price: 14,
    stock_quantity: 4,
    critical_stock_level: 10
  },
  {
    product_id: "P025",
    product_name: "Handmade Baby Blanket",
    category: "Baby Products",
    price: 35,
    stock_quantity: 8,
    critical_stock_level: 8
  },
  {
    product_id: "P026",
    product_name: "Embroidered Table Runner",
    category: "Home Textile",
    price: 26,
    stock_quantity: 15,
    critical_stock_level: 10
  },
  {
    product_id: "P027",
    product_name: "Natural Facial Serum",
    category: "Cosmetics",
    price: 21,
    stock_quantity: 9,
    critical_stock_level: 10
  },
  {
    product_id: "P028",
    product_name: "Handmade Wallet",
    category: "Fashion",
    price: 18,
    stock_quantity: 23,
    critical_stock_level: 10
  },
  {
    product_id: "P029",
    product_name: "Ceramic Vase",
    category: "Home Decoration",
    price: 32,
    stock_quantity: 7,
    critical_stock_level: 8
  },
  {
    product_id: "P030",
    product_name: "Organic Spice Set",
    category: "Food",
    price: 16,
    stock_quantity: 19,
    critical_stock_level: 12
  },
  {
    product_id: "P031",
    product_name: "Handmade Notebook",
    category: "Stationery",
    price: 10,
    stock_quantity: 34,
    critical_stock_level: 15
  },
  {
    product_id: "P032",
    product_name: "Soy Wax Candle Set",
    category: "Home Fragrance",
    price: 25,
    stock_quantity: 6,
    critical_stock_level: 10
  },
  {
    product_id: "P033",
    product_name: "Crochet Bag",
    category: "Fashion",
    price: 30,
    stock_quantity: 12,
    critical_stock_level: 10
  },
  {
    product_id: "P034",
    product_name: "Natural Hand Cream",
    category: "Cosmetics",
    price: 8,
    stock_quantity: 26,
    critical_stock_level: 12
  },
  {
    product_id: "P035",
    product_name: "Handmade Wooden Tray",
    category: "Home & Kitchen",
    price: 27,
    stock_quantity: 9,
    critical_stock_level: 10
  },
  {
    product_id: "P036",
    product_name: "Organic Fig Jam",
    category: "Food",
    price: 11,
    stock_quantity: 5,
    critical_stock_level: 10
  },
  {
    product_id: "P037",
    product_name: "Knitted Cardigan",
    category: "Textile",
    price: 45,
    stock_quantity: 4,
    critical_stock_level: 6
  },
  {
    product_id: "P038",
    product_name: "Handmade Bookmark",
    category: "Stationery",
    price: 3,
    stock_quantity: 60,
    critical_stock_level: 20
  },
  {
    product_id: "P039",
    product_name: "Natural Bath Salt",
    category: "Personal Care",
    price: 12,
    stock_quantity: 14,
    critical_stock_level: 10
  },
  {
    product_id: "P040",
    product_name: "Personalized Gift Box",
    category: "Gift Products",
    price: 38,
    stock_quantity: 7,
    critical_stock_level: 8
  }
];


// ===============================
// Order Mock Data
// ===============================

const orders = [
  {
    order_id: 128,
    customer_name: "Emma Johnson",
    product_name: "Natural Olive Oil",
    quantity: 3,
    order_date: "2026-05-09",
    order_status: "Preparing",
    total_price: 54
  },
  {
    order_id: 127,
    customer_name: "Olivia Smith",
    product_name: "Handmade Soap",
    quantity: 5,
    order_date: "2026-05-09",
    order_status: "Completed",
    total_price: 35
  },
  {
    order_id: 126,
    customer_name: "Sophia Brown",
    product_name: "Organic Honey",
    quantity: 2,
    order_date: "2026-05-08",
    order_status: "Pending",
    total_price: 24
  },
  {
    order_id: 125,
    customer_name: "Ava Miller",
    product_name: "Handmade Candle",
    quantity: 4,
    order_date: "2026-05-08",
    order_status: "Preparing",
    total_price: 36
  },
  {
    order_id: 124,
    customer_name: "Isabella Wilson",
    product_name: "Ceramic Coffee Cup",
    quantity: 2,
    order_date: "2026-05-08",
    order_status: "Completed",
    total_price: 32
  },
  {
    order_id: 123,
    customer_name: "Mia Davis",
    product_name: "Natural Lip Balm",
    quantity: 6,
    order_date: "2026-05-07",
    order_status: "Pending",
    total_price: 36
  },
  {
    order_id: 122,
    customer_name: "Charlotte Moore",
    product_name: "Handmade Bracelet",
    quantity: 1,
    order_date: "2026-05-07",
    order_status: "Completed",
    total_price: 14
  },
  {
    order_id: 121,
    customer_name: "Amelia Taylor",
    product_name: "Knitted Scarf",
    quantity: 2,
    order_date: "2026-05-07",
    order_status: "Preparing",
    total_price: 40
  },
  {
    order_id: 120,
    customer_name: "Harper Anderson",
    product_name: "Organic Herbal Tea",
    quantity: 3,
    order_date: "2026-05-06",
    order_status: "Cancelled",
    total_price: 24
  },
  {
    order_id: 119,
    customer_name: "Evelyn Thomas",
    product_name: "Handmade Necklace",
    quantity: 1,
    order_date: "2026-05-06",
    order_status: "Completed",
    total_price: 19
  },
  {
    order_id: 118,
    customer_name: "Abigail Jackson",
    product_name: "Natural Face Cream",
    quantity: 2,
    order_date: "2026-05-06",
    order_status: "Preparing",
    total_price: 30
  },
  {
    order_id: 117,
    customer_name: "Emily White",
    product_name: "Decorative Pillow Cover",
    quantity: 2,
    order_date: "2026-05-05",
    order_status: "Pending",
    total_price: 26
  },
  {
    order_id: 116,
    customer_name: "Elizabeth Harris",
    product_name: "Handmade Tote Bag",
    quantity: 1,
    order_date: "2026-05-05",
    order_status: "Completed",
    total_price: 22
  },
  {
    order_id: 115,
    customer_name: "Sofia Martin",
    product_name: "Organic Jam",
    quantity: 4,
    order_date: "2026-05-05",
    order_status: "Preparing",
    total_price: 36
  },
  {
    order_id: 114,
    customer_name: "Avery Thompson",
    product_name: "Lavender Room Spray",
    quantity: 3,
    order_date: "2026-05-04",
    order_status: "Completed",
    total_price: 30
  },
  {
    order_id: 113,
    customer_name: "Ella Garcia",
    product_name: "Handmade Hair Clip",
    quantity: 8,
    order_date: "2026-05-04",
    order_status: "Pending",
    total_price: 40
  },
  {
    order_id: 112,
    customer_name: "Scarlett Martinez",
    product_name: "Ceramic Plate",
    quantity: 2,
    order_date: "2026-05-04",
    order_status: "Completed",
    total_price: 48
  },
  {
    order_id: 111,
    customer_name: "Grace Robinson",
    product_name: "Natural Body Lotion",
    quantity: 3,
    order_date: "2026-05-03",
    order_status: "Preparing",
    total_price: 39
  },
  {
    order_id: 110,
    customer_name: "Lily Clark",
    product_name: "Handmade Keychain",
    quantity: 10,
    order_date: "2026-05-03",
    order_status: "Completed",
    total_price: 40
  },
  {
    order_id: 109,
    customer_name: "Chloe Lewis",
    product_name: "Organic Dried Fruit Box",
    quantity: 2,
    order_date: "2026-05-03",
    order_status: "Pending",
    total_price: 34
  }
];