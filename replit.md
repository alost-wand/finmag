# Finance Management Web App

## Overview
A public-facing, one-admin Finance Management Web Application built with Streamlit for a school farewell event. Uses local CSV files for persistent data storage. Currency: Emirati Dirhams (AED).

## Current State
Fully functional with enhanced features including geolocation tracking, receipt image display, and division-specific analytics.

## Project Structure
```
/
├── app.py              # Main Streamlit application
├── data_utils.py       # CSV data operations and utilities
├── transactions.csv    # Transaction ledger (auto-created)
├── divisions.csv       # Divisions data (auto-created)
├── receipts/           # Uploaded receipt files
└── .streamlit/
    └── config.toml     # Streamlit configuration
```

## Data Schema

### transactions.csv
| Column | Description |
|--------|-------------|
| id | Unique transaction ID (8-char UUID) |
| datetime | Transaction timestamp |
| name | Student/source name |
| class | Student class or category |
| division | Associated division |
| type | "credit" or "debit" |
| amount | Transaction amount (AED) |
| description | Transaction details |
| receipt_path | Path to uploaded receipt file |
| latitude | Geolocation latitude (fraud prevention) |
| longitude | Geolocation longitude (fraud prevention) |

### divisions.csv
| Column | Description |
|--------|-------------|
| division | Division name (unique) |
| starting_balance | Initial balance for division (AED) |

## User Roles

### Public Access (Default)
- View Dashboard with financial summaries and last 5 transactions
- Submit expense forms (debit transactions only) with geolocation capture
- View Transaction Log with receipt images displayed inline
- View Stats & Analytics with interactive charts
- View Division Analytics with individual division graphs

### Admin Access (100% Full Control)
- All public features
- Add credits to divisions
- Edit/delete any transaction
- Create/update/delete divisions
- Manual expense recording
- View geolocation data for fraud prevention
- Access to all hidden/confidential data

## Features

### Public Pages
1. **Home Dashboard**: Total Credited, Total Spent, Remaining Balance, Division Summary, Charts, Last 5 Transactions (all in AED)
2. **Submit Expense**: Form with balance validation, receipt upload, and automatic geolocation capture
3. **Transaction Log**: Shows all transactions with receipt images inline for full transparency
4. **Stats & Analytics**: Pie charts, bar charts, spending trends (all in AED)
5. **Division Analytics**: Dropdown selector to view individual division usage with detailed graphs

### Admin Features
1. **Admin Login**: Password-protected with session state
2. **Admin Dashboard**: Overview with quick action buttons (100% access)
3. **Manage Transactions**: Edit/delete any transaction, view location data
4. **Manage Divisions**: CRUD for divisions and starting balances
5. **Add Credit/Expense**: Manual entries with validation
6. **Location Data & Fraud Detection**: Interactive map visualization, cluster detection, location analysis charts (admin only)

## Security & Privacy
- Admin password is set via `SESSION_SECRET` environment variable
- Balance validation prevents overdrawing divisions
- Warning displayed if using default password
- Session-based authentication via Streamlit session state
- Geolocation data stored in CSV but NOT displayed publicly (admin-only access)
- Location data used for fraud prevention purposes

## Currency
All amounts displayed in Emirati Dirhams (AED)

## Running the Application
```bash
streamlit run app.py --server.port 5000
```

## Recent Changes
- December 2025: Enhanced features
  - Receipt images displayed inline in Transaction Log for full transparency
  - Geolocation capture during expense submission (browser-based)
  - Latitude/longitude stored in CSV for fraud prevention
  - Location data visible only to admin users
  - Division Analytics page with dropdown selector for individual division graphs
  - Currency changed to AED (Emirati Dirhams) throughout the app
  - Admin has 100% access to all features and data
  - Location Data & Fraud Detection page with:
    - Interactive world map showing expense submission locations
    - Location analysis charts (by division, timeline)
    - Cluster detection table to identify suspicious patterns
    - Google Maps integration for individual transaction lookup
