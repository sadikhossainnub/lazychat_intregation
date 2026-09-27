# LazyChat Integration for ERPNext

A production-ready Frappe/ERPNext custom application to seamlessly integrate **LazyChat AI** with **ERPNext v16+**. 

It handles bidirectional integration:
1. **Real-time & Bulk Product Synchronization** from ERPNext to LazyChat AI Catalog.
2. **Automated 10-Minute Order Fetching** from LazyChat AI into ERPNext `Sales Order`, `Customer`, `Contact`, and `Address`.

---

## 🌟 Key Features

### 1. Direct API Product Sync (`createOrUpdate`)
- **Instant Sync:** Whenever an `Item` is saved or updated in ERPNext (`on_update` hook), the system automatically updates/creates the corresponding **`LazyChat Product`** record and pushes the payload directly to LazyChat API (`POST https://app.lazychat.io/api/v1/products/createOrUpdate`).
- **Bulk Product Export:** Dedicated desk button in **LazyChat Settings** and **LazyChat Product List View** to import/push all active ERPNext items in one click.

### 2. Dedicated `LazyChat Product` DocType
- Tracks real-time sync status for every product:
  - 🟢 **Synced**: Successfully pushed to LazyChat.
  - 🟠 **Pending**: Queued for sync.
  - 🔴 **Failed**: Error details captured in `sync_error` field.
- **Item Master Connection:** Embedded connection link and status indicator directly on ERPNext's standard `Item Master` form view.

### 3. 10-Minute Automated Order Polling & Ingestion
- **10-Minute Cron Scheduler:** Frappe background scheduler calls LazyChat Order API (`POST https://app.lazychat.io/api/v1/orders` with `{"page": 1}`) every 10 minutes.
- **Manual Order Fetch Button:** On-demand **"Fetch Orders from LazyChat"** button in **LazyChat Settings** form.
- **Duplicate Prevention:** Checks `po_no` against LazyChat `invoice_number` / Order ID to ensure zero duplicate Sales Orders.

### 4. Smart Customer, Contact & Address Auto-Creation
- **Phone Lookup First:** Matches existing ERPNext `Contact Phone` to reuse existing customers.
- **Auto-Creation:** If not found, creates:
  - **`Customer`** (Assigned to non-group `Customer Group`, e.g., `Individual`).
  - **`Contact`** (Linked to Customer with mobile phone number).
  - **`Address`** (Shipping Address with auto-detected `city` and `country`).

### 5. Template Item to Variant Item Auto-Resolution
- Automatically maps LazyChat order variation IDs and size attributes (e.g. `TP00166` template with size `40`) to active ERPNext child variant items (e.g. `TP00166-40-PRG`), preventing template item validation errors.

### 6. Sales Order Configuration
- Auto-assigns mandatory fields:
  - `sales_type`: `"LazyChat"`
  - `po_no`: LazyChat Invoice Number (e.g. `INV-000001`)
  - Linked `contact_person`, `customer_address`, `shipping_address_name`.

---

## 🚀 Installation Guide

Run the following commands inside your Frappe Bench directory:

```bash
cd /path/to/frappe-bench

# Fetch the repository
bench get-app https://github.com/sadikhossainnub/lazychat_intregation.git --branch version-16

# Install on your site
bench --site your-site-name install-app lazychat_intregation

# Run migration
bench --site your-site-name migrate

# Enable scheduler (if not already enabled)
bench --site your-site-name enable-scheduler

# Clear site cache
bench --site your-site-name clear-cache
```

---

## ⚙️ Configuration Setup

1. Open **ERPNext Desk** and search for **LazyChat Settings**.
2. Fill in the required fields:
   - **LazyChat Shop Token:** Enter your `YOUR_SHOP_TOKEN` provided by LazyChat.
   - **Enable 10-Minute Auto Order Fetch:** Check to enable background polling.
   - **Fetch Orders API URL:** `https://app.lazychat.io/api/v1/orders`
   - **ERPNext Defaults:** Select default `Company`, `Customer Group`, `Price List`, `Warehouse`, and `Currency`.
3. Click **Save**.

---

## 📖 Usage & Workflows

### Initial Product Sync
To push your existing ERPNext Item Master catalog to LazyChat:
- Open **LazyChat Settings** ➡️ Click **"Sync All Products to LazyChat"**.
- Or open **LazyChat Product List** ➡️ Click **"Import / Sync Items from ERPNext"**.

### Daily Operations
- **Product Updates:** Saving any Item in ERPNext automatically updates LazyChat in real-time.
- **Orders:** Orders placed on LazyChat AI are automatically fetched every 10 minutes into ERPNext Sales Orders. Click **"Fetch Orders from LazyChat"** in **LazyChat Settings** anytime for immediate sync.

---

## 🛠️ DocType Overview

| DocType | Type | Description |
| :--- | :--- | :--- |
| **`LazyChat Settings`** | Single | Manages API tokens, endpoints, polling options, and default ERPNext parameters. |
| **`LazyChat Product`** | Master | Stores product sync status, SKU, price, image, and last sync timestamp. |
| **`Item Master`** (Extended) | Master | Displays real-time LazyChat status indicator and direct navigation link. |
| **`Sales Order`** (Extended) | Transaction | Stores fetched LazyChat orders with `po_no`, `sales_type = "LazyChat"`, linked customer, contact, and address. |

---

## 📜 License

MIT License. See [LICENSE](license.txt) for details.
