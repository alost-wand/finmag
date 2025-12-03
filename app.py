import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from data_utils import (init_csv_files, load_transactions, load_divisions,
                        add_transaction, update_transaction,
                        delete_transaction, add_division, update_division,
                        delete_division, get_division_list, save_receipt,
                        calculate_financials, calculate_division_summary,
                        division_exists, get_division_balance,
                        get_division_transactions, get_division_stats)

st.set_page_config(page_title="Finance Management",
                   page_icon="💰",
                   layout="wide",
                   initial_sidebar_state="expanded")

init_csv_files()

ADMIN_PASSWORD = "archbox"
ADMIN_PASSWORD_SET = bool(ADMIN_PASSWORD)
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = "admin123"

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "location_captured" not in st.session_state:
    st.session_state.location_captured = False
if "latitude" not in st.session_state:
    st.session_state.latitude = ""
if "longitude" not in st.session_state:
    st.session_state.longitude = ""


def format_currency(amount):
    return f"AED {amount:,.2f}"


def get_location_component():
    location_js = """
    (function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    return position.coords.latitude + ',' + position.coords.longitude;
                },
                function(error) {
                    return 'error:' + error.message;
                },
                {enableHighAccuracy: true, timeout: 10000}
            );
        }
        return 'unavailable';
    })();
    """
    return location_js


def render_sidebar():
    with st.sidebar:
        st.title("💰 Finance Manager")
        st.divider()

        st.subheader("📊 Public Pages")
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        if st.button("📝 Submit Expense", use_container_width=True):
            st.session_state.current_page = "Submit Expense"
            st.rerun()
        if st.button("📋 Transaction Log", use_container_width=True):
            st.session_state.current_page = "Transaction Log"
            st.rerun()
        if st.button("📈 Stats & Analytics", use_container_width=True):
            st.session_state.current_page = "Stats & Analytics"
            st.rerun()
        if st.button("📊 Division Analytics", use_container_width=True):
            st.session_state.current_page = "Division Analytics"
            st.rerun()

        st.divider()

        if st.session_state.is_admin:
            st.subheader("🔐 Admin Pages")
            if st.button("⚙️ Admin Dashboard", use_container_width=True):
                st.session_state.current_page = "Admin Dashboard"
                st.rerun()
            if st.button("📊 Manage Transactions", use_container_width=True):
                st.session_state.current_page = "Manage Transactions"
                st.rerun()
            if st.button("🏢 Manage Divisions", use_container_width=True):
                st.session_state.current_page = "Manage Divisions"
                st.rerun()
            if st.button("💳 Add Credit/Expense", use_container_width=True):
                st.session_state.current_page = "Add Credit/Expense"
                st.rerun()
            if st.button("📍 Location Data", use_container_width=True):
                st.session_state.current_page = "Location Data"
                st.rerun()
            st.divider()
            if st.button("🚪 Logout",
                         use_container_width=True,
                         type="secondary"):
                st.session_state.is_admin = False
                st.session_state.current_page = "Dashboard"
                st.rerun()
        else:
            if st.button("🔑 Admin Login", use_container_width=True):
                st.session_state.current_page = "Admin Login"
                st.rerun()


def render_dashboard():
    st.title("🏠 Finance Dashboard")
    st.markdown("---")

    financials = calculate_financials()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="💰 Total Credited",
                  value=format_currency(financials["total_credited"]),
                  help="Starting balances + all credits added")

    with col2:
        st.metric(label="💸 Total Spent",
                  value=format_currency(financials["total_spent"]),
                  help="Sum of all debit transactions")

    with col3:
        st.metric(label="💵 Remaining Balance",
                  value=format_currency(financials["remaining_balance"]),
                  delta=format_currency(financials["remaining_balance"] -
                                        financials["total_credited"]),
                  help="Available funds")

    with col4:
        st.metric(label="➕ Credits Added",
                  value=format_currency(financials["credits_added"]),
                  help="Additional credits beyond starting balance")

    st.markdown("---")
    st.subheader("📊 Division-wise Summary")

    division_summary = calculate_division_summary()

    if division_summary.empty:
        st.info(
            "No divisions have been created yet. An admin needs to add divisions first."
        )
    else:
        display_summary = division_summary.copy()
        for col in [
                "Starting Balance", "Credits Added", "Total Spent",
                "Remaining Balance"
        ]:
            if col in display_summary.columns:
                display_summary[col] = display_summary[col].apply(
                    format_currency)

        st.dataframe(display_summary,
                     use_container_width=True,
                     hide_index=True)

        divisions = load_divisions()
        transactions = load_transactions()

        if not divisions.empty:
            col1, col2 = st.columns(2)

            with col1:
                summary_data = calculate_division_summary()
                if not summary_data.empty:
                    fig = px.pie(summary_data,
                                 values="Remaining Balance",
                                 names="Division",
                                 title="Remaining Balance by Division")
                    fig.update_traces(textposition='inside',
                                      textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                if not transactions.empty:
                    div_spending = transactions[
                        transactions["type"] == "debit"].groupby(
                            "division")["amount"].sum().reset_index()
                    if not div_spending.empty:
                        fig = px.bar(div_spending,
                                     x="division",
                                     y="amount",
                                     title="Spending by Division (AED)",
                                     labels={
                                         "division": "Division",
                                         "amount": "Amount Spent (AED)"
                                     })
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No spending recorded yet.")
                else:
                    st.info("No transactions recorded yet.")

    st.markdown("---")
    st.subheader("📋 Last 5 Transactions")

    transactions = load_transactions()
    if not transactions.empty:
        recent = transactions.sort_values("datetime", ascending=False).head(5)
        display_df = recent.copy()
        display_df["amount"] = display_df["amount"].apply(format_currency)
        st.dataframe(display_df[[
            "id", "datetime", "name", "division", "type", "amount",
            "description"
        ]],
                     use_container_width=True,
                     hide_index=True)
    else:
        st.info("No transactions recorded yet.")


def render_submit_expense():
    st.title("📝 Submit Expense")
    st.markdown(
        "Submit a new expense request. This will be recorded as a debit transaction."
    )
    st.markdown("---")

    divisions = get_division_list()

    if not divisions:
        st.warning(
            "⚠️ No divisions available. Please contact an administrator to add divisions first."
        )
        return

    selected_division = st.selectbox("Select Division to view balance",
                                     options=divisions,
                                     key="preview_div")
    current_balance = get_division_balance(selected_division)
    if current_balance is not None:
        st.info(
            f"💰 Available balance for {selected_division}: {format_currency(current_balance)}"
        )

    st.markdown("### 📍 Location Capture")
    st.markdown(
        "Your location will be captured for encryption and  security purposes.please allow location access when propmted"
    )

    loc_result = streamlit_js_eval(js_expressions="""
        new Promise((resolve) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve(pos.coords.latitude + ',' + pos.coords.longitude),
                    (err) => resolve('error:' + err.message),
                    {enableHighAccuracy: true, timeout: 10000}
                );
            } else {
                resolve('unavailable');
            }
        })
        """,
                                   key="get_location")

    latitude = ""
    longitude = ""

    if loc_result:
        if loc_result.startswith('error:') or loc_result == 'unavailable':
            st.warning(
                "📍 Location could not be captured. Submission will proceed without location data."
            )
        else:
            parts = loc_result.split(',')
            if len(parts) == 2:
                latitude = parts[0]
                longitude = parts[1]
                st.success("📍 Location captured successfully!")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            student_name = st.text_input("Student Name *",
                                         placeholder="Enter student name")
            student_class = st.text_input(
                "Class *", placeholder="e.g., 10th Grade, Class A")
            division = st.selectbox("Division *", options=divisions)

        with col2:
            amount = st.number_input("Amount (AED) *",
                                     min_value=0.01,
                                     step=0.01,
                                     format="%.2f")
            description = st.text_area("Description *",
                                       placeholder="Describe the expense...")
            receipt = st.file_uploader("Upload Receipt (optional)",
                                       type=["jpg", "jpeg", "png", "pdf"])

        submitted = st.form_submit_button("Submit Expense",
                                          use_container_width=True,
                                          type="primary")

        if submitted:
            if not student_name or not student_class or not description:
                st.error("Please fill in all required fields.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                receipt_path = ""
                if receipt:
                    receipt_path = save_receipt(receipt)

                trans_id = add_transaction(name=student_name,
                                           student_class=student_class,
                                           division=division,
                                           trans_type="debit",
                                           amount=amount,
                                           description=description,
                                           receipt_path=receipt_path,
                                           validate_balance=True,
                                           latitude=latitude,
                                           longitude=longitude)

                if trans_id is None:
                    st.error(
                        "❌ Division does not exist. Please select a valid division."
                    )
                elif trans_id == "INSUFFICIENT_FUNDS":
                    st.error(
                        "❌ Insufficient funds in this division. Please check the available balance."
                    )
                else:
                    st.success(
                        f"✅ Expense submitted successfully! Transaction ID: {trans_id}"
                    )
                    st.balloons()


def render_transaction_log():
    st.title("📋 Transaction Log")
    st.markdown(
        "View all recorded transactions with receipt images for full transparency."
    )
    st.markdown("---")

    transactions = load_transactions()

    if transactions.empty:
        st.info("No transactions recorded yet.")
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        type_filter = st.selectbox("Filter by Type",
                                   ["All", "credit", "debit"])

    with col2:
        divisions = ["All"] + get_division_list()
        division_filter = st.selectbox("Filter by Division", divisions)

    with col3:
        students = ["All"] + sorted(transactions["name"].unique().tolist())
        student_filter = st.selectbox("Filter by Student", students)

    with col4:
        sort_by = st.selectbox("Sort by",
                               ["datetime", "amount", "name", "division"])

    with col5:
        sort_order = st.selectbox("Sort Order", ["Descending", "Ascending"])

    filtered_df = transactions.copy()

    if type_filter != "All":
        filtered_df = filtered_df[filtered_df["type"] == type_filter]

    if division_filter != "All":
        filtered_df = filtered_df[filtered_df["division"] == division_filter]

    if student_filter != "All":
        filtered_df = filtered_df[filtered_df["name"] == student_filter]

    ascending = sort_order == "Ascending"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    st.markdown(
        f"**Showing {len(filtered_df)} of {len(transactions)} transactions**")

    st.markdown("---")
    st.subheader("📄 Transaction Details with Receipts")

    for idx, row in filtered_df.iterrows():
        with st.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                type_color = "🟢" if row["type"] == "credit" else "🔴"
                st.markdown(f"### {type_color} {row['id']} - {row['name']}")
                st.markdown(f"**Date:** {row['datetime']}")
                st.markdown(
                    f"**Class:** {row['class']} | **Division:** {row['division']}"
                )
                st.markdown(
                    f"**Type:** {row['type'].upper()} | **Amount:** {format_currency(row['amount'])}"
                )
                st.markdown(f"**Description:** {row['description']}")

            with col2:
                receipt_path = row.get("receipt_path", "")
                if receipt_path and str(receipt_path).strip(
                ) and os.path.exists(str(receipt_path)):
                    if str(receipt_path).lower().endswith(
                        ('.jpg', '.jpeg', '.png')):
                        st.image(receipt_path,
                                 caption="Receipt",
                                 use_container_width=True)
                    else:
                        st.markdown(
                            f"📄 **Receipt file:** `{os.path.basename(receipt_path)}`"
                        )
                        st.info("PDF receipt attached")
                else:
                    st.markdown("📷 *No receipt uploaded*")

            st.markdown("---")


def render_division_analytics():
    st.title("📊 Division Analytics")
    st.markdown("View detailed analytics for each division individually.")
    st.markdown("---")

    divisions = get_division_list()

    if not divisions:
        st.info(
            "No divisions available. An admin needs to create divisions first."
        )
        return

    selected_division = st.selectbox("🏢 Select Division to Analyze",
                                     options=divisions,
                                     key="division_analytics_selector")

    st.markdown("---")

    stats = get_division_stats(selected_division)

    if stats is None:
        st.error("Division not found.")
        return

    st.subheader(f"📈 {selected_division} - Financial Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Starting Balance",
                  format_currency(stats["starting_balance"]))
    with col2:
        st.metric("Credits Added", format_currency(stats["credits_added"]))
    with col3:
        st.metric("Total Spent", format_currency(stats["total_spent"]))
    with col4:
        st.metric("Remaining Balance",
                  format_currency(stats["remaining_balance"]))

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Transactions", stats["transaction_count"])
    with col2:
        st.metric("Average Expense", format_currency(stats["avg_expense"]))

    st.markdown("---")

    div_transactions = get_division_transactions(selected_division)

    if div_transactions.empty:
        st.info(f"No transactions recorded for {selected_division} yet.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Budget Allocation")
        total_funds = stats["starting_balance"] + stats["credits_added"]
        spent = stats["total_spent"]
        remaining = stats["remaining_balance"]

        fig = go.Figure(data=[
            go.Pie(labels=["Spent", "Remaining"],
                   values=[spent, remaining],
                   hole=0.5,
                   marker_colors=["#e74c3c", "#2ecc71"])
        ])
        fig.update_layout(title=f"Budget Usage - {selected_division}",
                          annotations=[
                              dict(text=f"{(spent/total_funds*100):.1f}%"
                                   if total_funds > 0 else "0%",
                                   x=0.5,
                                   y=0.5,
                                   font_size=20,
                                   showarrow=False)
                          ])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Credits vs Debits")
        credits = div_transactions[div_transactions["type"] ==
                                   "credit"]["amount"].sum()
        debits = div_transactions[div_transactions["type"] ==
                                  "debit"]["amount"].sum()

        fig = px.bar(x=["Credits", "Debits"],
                     y=[credits, debits],
                     color=["Credits", "Debits"],
                     color_discrete_map={
                         "Credits": "#2ecc71",
                         "Debits": "#e74c3c"
                     })
        fig.update_layout(title=f"Transaction Types - {selected_division}",
                          xaxis_title="Type",
                          yaxis_title="Amount (AED)",
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Transaction Timeline")
    div_transactions["date"] = pd.to_datetime(
        div_transactions["datetime"]).dt.date
    daily = div_transactions.groupby(["date",
                                      "type"])["amount"].sum().reset_index()

    if not daily.empty:
        fig = px.line(daily,
                      x="date",
                      y="amount",
                      color="type",
                      color_discrete_map={
                          "credit": "#2ecc71",
                          "debit": "#e74c3c"
                      },
                      markers=True)
        fig.update_layout(xaxis_title="Date",
                          yaxis_title="Amount (AED)",
                          title=f"Daily Transactions - {selected_division}")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("👥 Top Spenders")
    debits_df = div_transactions[div_transactions["type"] == "debit"]
    if not debits_df.empty:
        top_spenders = debits_df.groupby("name")["amount"].sum().sort_values(
            ascending=False).head(5).reset_index()
        fig = px.bar(top_spenders,
                     x="name",
                     y="amount",
                     title=f"Top 5 Spenders - {selected_division}")
        fig.update_layout(xaxis_title="Student",
                          yaxis_title="Amount Spent (AED)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Recent Transactions")
    recent = div_transactions.sort_values("datetime", ascending=False).head(10)
    display_df = recent.copy()
    display_df["amount"] = display_df["amount"].apply(format_currency)
    st.dataframe(
        display_df[["id", "datetime", "name", "type", "amount",
                    "description"]],
        use_container_width=True,
        hide_index=True)


def render_stats():
    st.title("📈 Stats & Analytics")
    st.markdown("Visual insights into financial data.")
    st.markdown("---")

    transactions = load_transactions()
    divisions = load_divisions()

    if transactions.empty and divisions.empty:
        st.info(
            "No data available for analytics. Add divisions and transactions to see charts."
        )
        return

    financials = calculate_financials()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Credited",
                  format_currency(financials["total_credited"]))
    with col2:
        st.metric("Total Spent", format_currency(financials["total_spent"]))
    with col3:
        utilization = (financials["total_spent"] /
                       financials["total_credited"] *
                       100) if financials["total_credited"] > 0 else 0
        st.metric("Budget Utilization", f"{utilization:.1f}%")

    st.markdown("---")

    if not transactions.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Expense Distribution by Division")
            debits = transactions[transactions["type"] == "debit"]
            if not debits.empty:
                div_spending = debits.groupby(
                    "division")["amount"].sum().reset_index()
                fig = px.pie(div_spending,
                             values="amount",
                             names="division",
                             hole=0.4)
                fig.update_traces(textposition='inside',
                                  textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expenses recorded yet.")

        with col2:
            st.subheader("Credits vs Debits (AED)")
            type_totals = transactions.groupby(
                "type")["amount"].sum().reset_index()
            fig = px.bar(type_totals,
                         x="type",
                         y="amount",
                         color="type",
                         color_discrete_map={
                             "credit": "#2ecc71",
                             "debit": "#e74c3c"
                         })
            fig.update_layout(showlegend=False, yaxis_title="Amount (AED)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Transaction Timeline")
        transactions["date"] = pd.to_datetime(transactions["datetime"]).dt.date
        daily_summary = transactions.groupby(["date", "type"
                                              ])["amount"].sum().reset_index()

        if not daily_summary.empty:
            fig = px.line(daily_summary,
                          x="date",
                          y="amount",
                          color="type",
                          color_discrete_map={
                              "credit": "#2ecc71",
                              "debit": "#e74c3c"
                          },
                          markers=True)
            fig.update_layout(xaxis_title="Date", yaxis_title="Amount (AED)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top Spenders")
        top_spenders = debits.groupby("name")["amount"].sum().sort_values(
            ascending=False).head(10).reset_index()
        if not top_spenders.empty:
            fig = px.bar(top_spenders, x="name", y="amount", title="")
            fig.update_layout(xaxis_title="Student",
                              yaxis_title="Total Spent (AED)")
            st.plotly_chart(fig, use_container_width=True)

    if not divisions.empty:
        st.subheader("Division Balances Overview (AED)")
        summary = calculate_division_summary()
        if not summary.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(name="Starting Balance",
                       x=summary["Division"],
                       y=summary["Starting Balance"],
                       marker_color="#3498db"))
            fig.add_trace(
                go.Bar(name="Total Spent",
                       x=summary["Division"],
                       y=summary["Total Spent"],
                       marker_color="#e74c3c"))
            fig.add_trace(
                go.Bar(name="Remaining Balance",
                       x=summary["Division"],
                       y=summary["Remaining Balance"],
                       marker_color="#2ecc71"))
            fig.update_layout(barmode="group", yaxis_title="Amount (AED)")
            st.plotly_chart(fig, use_container_width=True)


def render_admin_login():
    st.title("🔑 Admin Login")
    st.markdown("Enter the admin password to access management features.")
    st.markdown("---")

    if not ADMIN_PASSWORD_SET:
        st.warning(
            "⚠️ Security Warning: Admin password is using default value. Please set the SESSION_SECRET environment variable for production use."
        )

    if st.session_state.is_admin:
        st.success("You are already logged in as admin.")
        if st.button("Go to Admin Dashboard"):
            st.session_state.current_page = "Admin Dashboard"
            st.rerun()
        return

    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login",
                                          use_container_width=True,
                                          type="primary")

        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.session_state.current_page = "Admin Dashboard"
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")


def render_admin_dashboard():
    if not st.session_state.is_admin:
        st.error("Access denied. Please login as admin.")
        return

    st.title("⚙️ Admin Dashboard")
    st.markdown(
        "Central hub for all administrative tasks. You have **100% access** to all features."
    )
    st.markdown("---")

    financials = calculate_financials()
    transactions = load_transactions()
    divisions = load_divisions()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Total Balance",
                  format_currency(financials["remaining_balance"]))
    with col2:
        st.metric("📊 Total Transactions", len(transactions))
    with col3:
        st.metric("🏢 Total Divisions", len(divisions))
    with col4:
        credits = len(transactions[transactions["type"] ==
                                   "credit"]) if not transactions.empty else 0
        debits = len(transactions[transactions["type"] ==
                                  "debit"]) if not transactions.empty else 0
        st.metric("Credits / Debits", f"{credits} / {debits}")

    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 📊 Manage Transactions")
        st.markdown("Edit or delete any transaction in the ledger.")
        if st.button("Open Transaction Manager", key="btn_trans"):
            st.session_state.current_page = "Manage Transactions"
            st.rerun()

    with col2:
        st.markdown("### 🏢 Manage Divisions")
        st.markdown("Create, update, or remove divisions.")
        if st.button("Open Division Manager", key="btn_div"):
            st.session_state.current_page = "Manage Divisions"
            st.rerun()

    with col3:
        st.markdown("### 💳 Add Credit/Expense")
        st.markdown("Manually add credits or expenses.")
        if st.button("Open Credit/Expense Form", key="btn_credit"):
            st.session_state.current_page = "Add Credit/Expense"
            st.rerun()

    with col4:
        st.markdown("### 📍 Location Data")
        st.markdown("View geolocation data for fraud prevention.")
        if st.button("View Location Data", key="btn_location"):
            st.session_state.current_page = "Location Data"
            st.rerun()

    st.markdown("---")
    st.subheader("Recent Transactions")

    if not transactions.empty:
        recent = transactions.sort_values("datetime", ascending=False).head(5)
        display_df = recent.copy()
        display_df["amount"] = display_df["amount"].apply(format_currency)
        st.dataframe(display_df[[
            "id", "datetime", "name", "division", "type", "amount",
            "description"
        ]],
                     use_container_width=True,
                     hide_index=True)
    else:
        st.info("No transactions yet.")


def render_location_data():
    if not st.session_state.is_admin:
        st.error("Access denied. Please login as admin.")
        return

    st.title("📍 Location Data & Fraud Detection (Admin Only)")
    st.markdown(
        "View geolocation data and map visualization for fraud prevention.")
    st.markdown("---")

    st.warning(
        "⚠️ This data is confidential and should only be used for fraud prevention purposes."
    )

    transactions = load_transactions()

    if transactions.empty:
        st.info("No transactions recorded yet.")
        return

    has_location = transactions[(transactions["latitude"].notna())
                                & (transactions["latitude"] != "") &
                                (transactions["longitude"].notna()) &
                                (transactions["longitude"] != "")]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(transactions))
    with col2:
        st.metric("With Location Data", len(has_location))
    with col3:
        coverage = (len(has_location) / len(transactions) *
                    100) if len(transactions) > 0 else 0
        st.metric("Location Coverage", f"{coverage:.1f}%")

    st.markdown("---")

    if not has_location.empty:
        st.subheader("🗺️ Expense Submission Locations - Street View Map")
        st.markdown(
            "Interactive street-level map showing exact locations where expenses were submitted. Zoom in to see streets, buildings, and landmarks for fraud detection."
        )

        map_df = has_location.copy()
        map_df["lat"] = pd.to_numeric(map_df["latitude"], errors='coerce')
        map_df["lon"] = pd.to_numeric(map_df["longitude"], errors='coerce')
        map_df = map_df.dropna(subset=["lat", "lon"])

        if not map_df.empty:
            center_lat = map_df["lat"].mean()
            center_lon = map_df["lon"].mean()

            m = folium.Map(location=[center_lat, center_lon],
                           zoom_start=12,
                           tiles='OpenStreetMap')

            marker_cluster = MarkerCluster().add_to(m)

            division_colors = {
                div: color
                for div, color in zip(map_df["division"].unique(), [
                    'red', 'blue', 'green', 'purple', 'orange', 'darkred',
                    'lightred', 'beige', 'darkblue', 'darkgreen'
                ])
            }

            for _, row in map_df.iterrows():
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; min-width: 200px;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">Transaction Details</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 4px 0;"><b>ID:</b></td><td>{row['id']}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Student:</b></td><td>{row['name']}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Class:</b></td><td>{row['class']}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Division:</b></td><td>{row['division']}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Amount:</b></td><td>{format_currency(row['amount'])}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Date:</b></td><td>{row['datetime']}</td></tr>
                        <tr><td style="padding: 4px 0;"><b>Coordinates:</b></td><td>{row['lat']:.6f}, {row['lon']:.6f}</td></tr>
                    </table>
                    <div style="margin-top: 10px;">
                        <a href="https://www.google.com/maps?q={row['lat']},{row['lon']}" target="_blank" 
                           style="background: #4285f4; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">
                           View on Google Maps
                        </a>
                    </div>
                </div>
                """

                color = division_colors.get(row['division'], 'gray')

                folium.Marker(
                    location=[row['lat'], row['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row['name']} - {format_currency(row['amount'])}",
                    icon=folium.Icon(color=color, icon='money',
                                     prefix='fa')).add_to(marker_cluster)

            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background: white; 
                        padding: 10px; border-radius: 5px; border: 2px solid gray; font-size: 12px;">
                <b>Division Colors:</b><br>
            """
            for div, color in division_colors.items():
                legend_html += f'<i class="fa fa-map-marker" style="color:{color}"></i> {div}<br>'
            legend_html += "</div>"
            m.get_root().html.add_child(folium.Element(legend_html))

            st_folium(m, width=None, height=500, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Location Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Submissions by Division (with location)**")
                div_counts = map_df.groupby("division").size().reset_index(
                    name="count")
                fig_div = px.pie(div_counts,
                                 values="count",
                                 names="division",
                                 title="Distribution by Division")
                st.plotly_chart(fig_div, use_container_width=True)

            with col2:
                st.markdown("**Submission Timeline**")
                map_df["date"] = pd.to_datetime(map_df["datetime"]).dt.date
                daily_counts = map_df.groupby("date").size().reset_index(
                    name="count")
                fig_timeline = px.bar(daily_counts,
                                      x="date",
                                      y="count",
                                      title="Daily Submissions with Location")
                fig_timeline.update_layout(xaxis_title="Date",
                                           yaxis_title="Count")
                st.plotly_chart(fig_timeline, use_container_width=True)

            st.markdown("---")
            st.subheader("🔍 Cluster Detection")
            st.markdown(
                "Transactions from similar locations may indicate coordinated submissions."
            )

            unique_locations = map_df.groupby(["lat", "lon"]).agg({
                "id":
                "count",
                "name":
                lambda x: ", ".join(x.unique()[:3]) +
                ("..." if len(x.unique()) > 3 else ""),
                "amount":
                "sum"
            }).reset_index()
            unique_locations.columns = [
                "Latitude", "Longitude", "Transaction Count", "Students",
                "Total Amount"
            ]
            unique_locations["Total Amount"] = unique_locations[
                "Total Amount"].apply(format_currency)
            unique_locations = unique_locations.sort_values(
                "Transaction Count", ascending=False)

            if len(unique_locations) > 0:
                st.dataframe(unique_locations,
                             use_container_width=True,
                             hide_index=True)
        else:
            st.info("Location data could not be parsed for mapping.")

    st.markdown("---")
    st.subheader("📋 All Transactions with Location Data")

    if has_location.empty:
        st.info("No transactions have location data yet.")
    else:
        display_df = has_location.copy()
        display_df["amount"] = display_df["amount"].apply(format_currency)
        display_df["coordinates"] = display_df.apply(
            lambda x: f"{x['latitude']}, {x['longitude']}"
            if x['latitude'] and x['longitude'] else "N/A",
            axis=1)

        st.dataframe(display_df[[
            "id", "datetime", "name", "division", "amount", "latitude",
            "longitude", "coordinates"
        ]],
                     use_container_width=True,
                     hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Search by Transaction ID")

    trans_ids = transactions["id"].tolist()
    selected_id = st.selectbox("Select Transaction", trans_ids)

    if selected_id:
        trans = transactions[transactions["id"] == selected_id].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Transaction ID:** {trans['id']}")
            st.markdown(f"**Student:** {trans['name']}")
            st.markdown(f"**Class:** {trans['class']}")
            st.markdown(f"**Division:** {trans['division']}")
            st.markdown(f"**Amount:** {format_currency(trans['amount'])}")

        with col2:
            st.markdown(f"**Date/Time:** {trans['datetime']}")
            lat = trans.get('latitude', '')
            lon = trans.get('longitude', '')
            if lat and lon and str(lat).strip() and str(lon).strip():
                st.markdown(f"**Latitude:** {lat}")
                st.markdown(f"**Longitude:** {lon}")
                st.markdown(
                    f"[View on Google Maps](https://www.google.com/maps?q={lat},{lon})"
                )
            else:
                st.markdown("**Location:** Not captured")


def render_manage_transactions():
    if not st.session_state.is_admin:
        st.error("Access denied. Please login as admin.")
        return

    st.title("📊 Manage Transactions")
    st.markdown(
        "Edit or delete transactions from the ledger. Admin has full access to all transaction data."
    )
    st.markdown("---")

    transactions = load_transactions()

    if transactions.empty:
        st.info("No transactions to manage.")
        return

    divisions = get_division_list()

    st.subheader("Edit Transaction")

    trans_ids = transactions["id"].tolist()
    selected_id = st.selectbox("Select Transaction ID to Edit/Delete",
                               trans_ids)

    if selected_id:
        trans_row = transactions[transactions["id"] == selected_id].iloc[0]

        st.markdown("#### Current Location Data (Read Only)")
        lat = trans_row.get('latitude', '')
        lon = trans_row.get('longitude', '')
        if lat and lon and str(lat).strip() and str(lon).strip():
            st.info(f"📍 Coordinates: {lat}, {lon}")
        else:
            st.info("📍 No location data captured for this transaction")

        with st.form("edit_transaction"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Student Name", value=trans_row["name"])
                student_class = st.text_input("Class",
                                              value=trans_row["class"])
                div_index = divisions.index(
                    trans_row["division"]
                ) if trans_row["division"] in divisions else 0
                division = st.selectbox("Division",
                                        options=divisions,
                                        index=div_index)

            with col2:
                trans_type = st.selectbox(
                    "Type",
                    options=["credit", "debit"],
                    index=0 if trans_row["type"] == "credit" else 1)
                amount = st.number_input("Amount (AED)",
                                         value=float(trans_row["amount"]),
                                         min_value=0.01,
                                         step=0.01)
                description = st.text_area("Description",
                                           value=trans_row["description"])

            col1, col2 = st.columns(2)
            with col1:
                update_btn = st.form_submit_button("Update Transaction",
                                                   use_container_width=True,
                                                   type="primary")
            with col2:
                delete_btn = st.form_submit_button("Delete Transaction",
                                                   use_container_width=True,
                                                   type="secondary")

            if update_btn:
                success = update_transaction(selected_id, name, student_class,
                                             division, trans_type, amount,
                                             description)
                if success:
                    st.success("✅ Transaction updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update transaction.")

            if delete_btn:
                success = delete_transaction(selected_id)
                if success:
                    st.success("✅ Transaction deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete transaction.")

    st.markdown("---")
    st.subheader("All Transactions")

    display_df = transactions.copy()
    display_df["amount"] = display_df["amount"].apply(format_currency)
    st.dataframe(display_df[[
        "id", "datetime", "name", "class", "division", "type", "amount",
        "description"
    ]],
                 use_container_width=True,
                 hide_index=True)


def render_manage_divisions():
    if not st.session_state.is_admin:
        st.error("Access denied. Please login as admin.")
        return

    st.title("🏢 Manage Divisions")
    st.markdown(
        "Create, update, or delete divisions and their starting balances.")
    st.markdown("---")

    divisions = load_divisions()

    st.subheader("Add New Division")

    with st.form("add_division"):
        col1, col2 = st.columns(2)

        with col1:
            new_div_name = st.text_input("Division Name",
                                         placeholder="e.g., Food, Decorations")

        with col2:
            new_starting_bal = st.number_input("Starting Balance (AED)",
                                               min_value=0.0,
                                               step=100.0,
                                               format="%.2f")

        submitted = st.form_submit_button("Add Division",
                                          use_container_width=True,
                                          type="primary")

        if submitted:
            if not new_div_name:
                st.error("Please enter a division name.")
            else:
                success = add_division(new_div_name, new_starting_bal)
                if success:
                    st.success(
                        f"✅ Division '{new_div_name}' added with starting balance {format_currency(new_starting_bal)}!"
                    )
                    st.rerun()
                else:
                    st.error(
                        "❌ Division already exists or could not be added.")

    if not divisions.empty:
        st.markdown("---")
        st.subheader("Edit/Delete Existing Divisions")

        div_names = divisions["division"].tolist()
        selected_div = st.selectbox("Select Division to Edit/Delete",
                                    div_names)

        if selected_div:
            div_row = divisions[divisions["division"] == selected_div].iloc[0]
            current_balance = get_division_balance(selected_div)

            st.info(
                f"Current remaining balance for {selected_div}: {format_currency(current_balance) if current_balance else 'N/A'}"
            )

            with st.form("edit_division"):
                new_balance = st.number_input("New Starting Balance (AED)",
                                              value=float(
                                                  div_row["starting_balance"]),
                                              min_value=0.0,
                                              step=100.0,
                                              format="%.2f")

                col1, col2 = st.columns(2)
                with col1:
                    update_btn = st.form_submit_button(
                        "Update Starting Balance",
                        use_container_width=True,
                        type="primary")
                with col2:
                    delete_btn = st.form_submit_button(
                        "Delete Division",
                        use_container_width=True,
                        type="secondary")

                if update_btn:
                    success = update_division(selected_div, new_balance)
                    if success:
                        st.success(
                            f"✅ Updated {selected_div} starting balance to {format_currency(new_balance)}!"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Failed to update division.")

                if delete_btn:
                    success = delete_division(selected_div)
                    if success:
                        st.success(f"✅ Division '{selected_div}' deleted!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete division.")

        st.markdown("---")
        st.subheader("Current Divisions")

        summary = calculate_division_summary()
        if not summary.empty:
            display_summary = summary.copy()
            for col in [
                    "Starting Balance", "Credits Added", "Total Spent",
                    "Remaining Balance"
            ]:
                if col in display_summary.columns:
                    display_summary[col] = display_summary[col].apply(
                        format_currency)
            st.dataframe(display_summary,
                         use_container_width=True,
                         hide_index=True)


def render_add_credit_expense():
    if not st.session_state.is_admin:
        st.error("Access denied. Please login as admin.")
        return

    st.title("💳 Add Credit/Expense")
    st.markdown(
        "Manually add credits or expenses to any division. Admin has full control."
    )
    st.markdown("---")

    divisions = get_division_list()

    if not divisions:
        st.warning("No divisions available. Please create divisions first.")
        return

    selected_div = st.selectbox("Select Division", options=divisions)
    current_balance = get_division_balance(selected_div)
    if current_balance is not None:
        st.info(
            f"Current balance for {selected_div}: {format_currency(current_balance)}"
        )

    tab1, tab2 = st.tabs(["➕ Add Credit", "➖ Add Expense"])

    with tab1:
        st.subheader("Add Credit to Division")

        with st.form("add_credit"):
            col1, col2 = st.columns(2)

            with col1:
                credit_source = st.text_input(
                    "Credit Source *", placeholder="e.g., Sponsor, Donation")
                credit_class = st.text_input("Category",
                                             value="Admin Credit",
                                             placeholder="e.g., Sponsorship")

            with col2:
                credit_amount = st.number_input("Amount (AED) *",
                                                min_value=0.01,
                                                step=0.01,
                                                format="%.2f",
                                                key="credit_amount")
                credit_desc = st.text_area(
                    "Description *",
                    placeholder="Describe the credit source...")

            submitted = st.form_submit_button("Add Credit",
                                              use_container_width=True,
                                              type="primary")

            if submitted:
                if not credit_source or not credit_desc:
                    st.error("Please fill in all required fields.")
                elif credit_amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    trans_id = add_transaction(name=credit_source,
                                               student_class=credit_class,
                                               division=selected_div,
                                               trans_type="credit",
                                               amount=credit_amount,
                                               description=credit_desc)
                    if trans_id:
                        st.success(
                            f"✅ Credit of {format_currency(credit_amount)} added to {selected_div}! Transaction ID: {trans_id}"
                        )
                        st.balloons()
                    else:
                        st.error("❌ Failed to add credit.")

    with tab2:
        st.subheader("Add Expense (Admin Entry)")

        with st.form("add_expense"):
            col1, col2 = st.columns(2)

            with col1:
                expense_name = st.text_input(
                    "Name *", placeholder="Enter name for this expense")
                expense_class = st.text_input(
                    "Category",
                    value="Admin Expense",
                    placeholder="e.g., Venue, Supplies")

            with col2:
                expense_amount = st.number_input("Amount (AED) *",
                                                 min_value=0.01,
                                                 step=0.01,
                                                 format="%.2f",
                                                 key="expense_amount")
                expense_desc = st.text_area(
                    "Description *", placeholder="Describe the expense...")

            expense_receipt = st.file_uploader(
                "Upload Receipt (optional)",
                type=["jpg", "jpeg", "png", "pdf"],
                key="admin_receipt")

            submitted = st.form_submit_button("Add Expense",
                                              use_container_width=True,
                                              type="primary")

            if submitted:
                if not expense_name or not expense_desc:
                    st.error("Please fill in all required fields.")
                elif expense_amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    receipt_path = ""
                    if expense_receipt:
                        receipt_path = save_receipt(expense_receipt)

                    trans_id = add_transaction(name=expense_name,
                                               student_class=expense_class,
                                               division=selected_div,
                                               trans_type="debit",
                                               amount=expense_amount,
                                               description=expense_desc,
                                               receipt_path=receipt_path,
                                               validate_balance=False)
                    if trans_id:
                        st.success(
                            f"✅ Expense of {format_currency(expense_amount)} added to {selected_div}! Transaction ID: {trans_id}"
                        )
                    else:
                        st.error("❌ Failed to add expense.")


def main():
    render_sidebar()

    page = st.session_state.current_page

    if page == "Dashboard":
        render_dashboard()
    elif page == "Submit Expense":
        render_submit_expense()
    elif page == "Transaction Log":
        render_transaction_log()
    elif page == "Stats & Analytics":
        render_stats()
    elif page == "Division Analytics":
        render_division_analytics()
    elif page == "Admin Login":
        render_admin_login()
    elif page == "Admin Dashboard":
        render_admin_dashboard()
    elif page == "Manage Transactions":
        render_manage_transactions()
    elif page == "Manage Divisions":
        render_manage_divisions()
    elif page == "Add Credit/Expense":
        render_add_credit_expense()
    elif page == "Location Data":
        render_location_data()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
