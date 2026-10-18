
import sqlite3

DB_NAME = "insurance.db"



def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Customer records
  
    # Customer records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT,
            contact TEXT,
            email TEXT NOT NULL UNIQUE
        )
    """)

    # Add new columns to existing databases
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]

    if "gender" not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN gender TEXT")

    if "contact" not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN contact TEXT")


    # Insurance policies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            insurance_type TEXT NOT NULL,
            premium REAL NOT NULL,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        )
    """)

    # Insurance claims
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            policy_id INTEGER NOT NULL,
            claim_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),
            FOREIGN KEY (policy_id)
                REFERENCES policies(policy_id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Insurance database created successfully!")


def delete_claim(claim_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM claims WHERE claim_id = ?",
        (claim_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted


def delete_policy(policy_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Delete related claims first
    cursor.execute(
        "DELETE FROM claims WHERE policy_id = ?",
        (policy_id,)
    )

    cursor.execute(
        "DELETE FROM policies WHERE policy_id = ?",
        (policy_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted


def delete_customer(customer_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Delete the customer's claims first
    cursor.execute(
        "DELETE FROM claims WHERE customer_id = ?",
        (customer_id,)
    )

    # Then delete the customer's policies
    cursor.execute(
        "DELETE FROM policies WHERE customer_id = ?",
        (customer_id,)
    )

    # Finally delete the customer
    cursor.execute(
        "DELETE FROM customers WHERE customer_id = ?",
        (customer_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted
