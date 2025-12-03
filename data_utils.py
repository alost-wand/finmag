import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import uuid

TRANSACTIONS_FILE = "transactions.csv"
DIVISIONS_FILE = "divisions.csv"
RECEIPTS_FOLDER = "receipts"

TRANSACTIONS_COLUMNS = ["id", "datetime", "name", "class", "division", "type", "amount", "description", "receipt_path", "latitude", "longitude"]
DIVISIONS_COLUMNS = ["division", "starting_balance"]


def ensure_receipts_folder():
    Path(RECEIPTS_FOLDER).mkdir(exist_ok=True)


def init_csv_files():
    ensure_receipts_folder()
    
    if not os.path.exists(TRANSACTIONS_FILE):
        df = pd.DataFrame(columns=TRANSACTIONS_COLUMNS)
        df.to_csv(TRANSACTIONS_FILE, index=False)
    else:
        df = pd.read_csv(TRANSACTIONS_FILE)
        if "latitude" not in df.columns:
            df["latitude"] = ""
        if "longitude" not in df.columns:
            df["longitude"] = ""
        df.to_csv(TRANSACTIONS_FILE, index=False)
    
    if not os.path.exists(DIVISIONS_FILE):
        df = pd.DataFrame(columns=DIVISIONS_COLUMNS)
        df.to_csv(DIVISIONS_FILE, index=False)


def load_transactions():
    init_csv_files()
    try:
        df = pd.read_csv(TRANSACTIONS_FILE)
        if df.empty:
            return pd.DataFrame(columns=TRANSACTIONS_COLUMNS)
        for col in ["latitude", "longitude"]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=TRANSACTIONS_COLUMNS)


def save_transactions(df):
    df.to_csv(TRANSACTIONS_FILE, index=False)


def load_divisions():
    init_csv_files()
    try:
        df = pd.read_csv(DIVISIONS_FILE)
        if df.empty:
            return pd.DataFrame(columns=DIVISIONS_COLUMNS)
        return df
    except Exception:
        return pd.DataFrame(columns=DIVISIONS_COLUMNS)


def save_divisions(df):
    df.to_csv(DIVISIONS_FILE, index=False)


def generate_transaction_id():
    return str(uuid.uuid4())[:8].upper()


def division_exists(division_name):
    df = load_divisions()
    return division_name in df["division"].values


def get_division_balance(division_name):
    divisions = load_divisions()
    transactions = load_transactions()
    
    div_row = divisions[divisions["division"] == division_name]
    if div_row.empty:
        return None
    
    starting_bal = div_row["starting_balance"].values[0]
    
    div_transactions = transactions[transactions["division"] == division_name] if not transactions.empty else pd.DataFrame()
    
    if div_transactions.empty:
        credits = 0
        debits = 0
    else:
        credits = div_transactions[div_transactions["type"] == "credit"]["amount"].sum()
        debits = div_transactions[div_transactions["type"] == "debit"]["amount"].sum()
    
    return starting_bal + credits - debits


def add_transaction(name, student_class, division, trans_type, amount, description, receipt_path="", validate_balance=False, latitude="", longitude=""):
    if not division_exists(division):
        return None
    
    if validate_balance and trans_type == "debit":
        current_balance = get_division_balance(division)
        if current_balance is not None and float(amount) > current_balance:
            return "INSUFFICIENT_FUNDS"
    
    df = load_transactions()
    new_row = {
        "id": generate_transaction_id(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "class": student_class,
        "division": division,
        "type": trans_type,
        "amount": float(amount),
        "description": description,
        "receipt_path": receipt_path,
        "latitude": latitude,
        "longitude": longitude
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_transactions(df)
    return new_row["id"]


def update_transaction(trans_id, name, student_class, division, trans_type, amount, description, receipt_path=None, latitude=None, longitude=None):
    df = load_transactions()
    idx = df[df["id"] == trans_id].index
    if len(idx) > 0:
        df.loc[idx[0], "name"] = name
        df.loc[idx[0], "class"] = student_class
        df.loc[idx[0], "division"] = division
        df.loc[idx[0], "type"] = trans_type
        df.loc[idx[0], "amount"] = float(amount)
        df.loc[idx[0], "description"] = description
        if receipt_path is not None:
            df.loc[idx[0], "receipt_path"] = receipt_path
        if latitude is not None:
            df.loc[idx[0], "latitude"] = latitude
        if longitude is not None:
            df.loc[idx[0], "longitude"] = longitude
        save_transactions(df)
        return True
    return False


def delete_transaction(trans_id):
    df = load_transactions()
    initial_len = len(df)
    df = df[df["id"] != trans_id]
    if len(df) < initial_len:
        save_transactions(df)
        return True
    return False


def add_division(division_name, starting_balance):
    df = load_divisions()
    if division_name in df["division"].values:
        return False
    new_row = {
        "division": division_name,
        "starting_balance": float(starting_balance)
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_divisions(df)
    return True


def update_division(division_name, new_starting_balance):
    df = load_divisions()
    idx = df[df["division"] == division_name].index
    if len(idx) > 0:
        df.loc[idx[0], "starting_balance"] = float(new_starting_balance)
        save_divisions(df)
        return True
    return False


def delete_division(division_name):
    df = load_divisions()
    initial_len = len(df)
    df = df[df["division"] != division_name]
    if len(df) < initial_len:
        save_divisions(df)
        return True
    return False


def get_division_list():
    df = load_divisions()
    return df["division"].tolist()


def save_receipt(uploaded_file):
    ensure_receipts_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(RECEIPTS_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath


def calculate_financials():
    transactions = load_transactions()
    divisions = load_divisions()
    
    total_starting_balance = divisions["starting_balance"].sum() if not divisions.empty else 0
    
    if transactions.empty:
        return {
            "total_credited": total_starting_balance,
            "total_spent": 0,
            "remaining_balance": total_starting_balance,
            "credits_added": 0
        }
    
    credits = transactions[transactions["type"] == "credit"]["amount"].sum()
    debits = transactions[transactions["type"] == "debit"]["amount"].sum()
    
    total_credited = total_starting_balance + credits
    remaining_balance = total_credited - debits
    
    return {
        "total_credited": total_credited,
        "total_spent": debits,
        "remaining_balance": remaining_balance,
        "credits_added": credits
    }


def calculate_division_summary():
    transactions = load_transactions()
    divisions = load_divisions()
    
    summary = []
    for _, div_row in divisions.iterrows():
        div_name = div_row["division"]
        starting_bal = div_row["starting_balance"]
        
        div_transactions = transactions[transactions["division"] == div_name] if not transactions.empty else pd.DataFrame()
        
        if div_transactions.empty:
            credits = 0
            debits = 0
        else:
            credits = div_transactions[div_transactions["type"] == "credit"]["amount"].sum()
            debits = div_transactions[div_transactions["type"] == "debit"]["amount"].sum()
        
        total_funds = starting_bal + credits
        remaining = total_funds - debits
        
        summary.append({
            "Division": div_name,
            "Starting Balance": starting_bal,
            "Credits Added": credits,
            "Total Spent": debits,
            "Remaining Balance": remaining
        })
    
    return pd.DataFrame(summary)


def get_division_transactions(division_name):
    transactions = load_transactions()
    if transactions.empty:
        return pd.DataFrame(columns=TRANSACTIONS_COLUMNS)
    return transactions[transactions["division"] == division_name]


def get_division_stats(division_name):
    divisions = load_divisions()
    transactions = load_transactions()
    
    div_row = divisions[divisions["division"] == division_name]
    if div_row.empty:
        return None
    
    starting_bal = div_row["starting_balance"].values[0]
    div_transactions = transactions[transactions["division"] == division_name] if not transactions.empty else pd.DataFrame()
    
    if div_transactions.empty:
        return {
            "starting_balance": starting_bal,
            "credits_added": 0,
            "total_spent": 0,
            "remaining_balance": starting_bal,
            "transaction_count": 0,
            "avg_expense": 0
        }
    
    credits = div_transactions[div_transactions["type"] == "credit"]["amount"].sum()
    debits = div_transactions[div_transactions["type"] == "debit"]["amount"].sum()
    debit_count = len(div_transactions[div_transactions["type"] == "debit"])
    
    return {
        "starting_balance": starting_bal,
        "credits_added": credits,
        "total_spent": debits,
        "remaining_balance": starting_bal + credits - debits,
        "transaction_count": len(div_transactions),
        "avg_expense": debits / debit_count if debit_count > 0 else 0
    }
