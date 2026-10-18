
import streamlit as st
import pandas as pd
import sqlite3

from database import (
    create_tables,
    connect_db,
    delete_customer,
    delete_policy,
    delete_claim
)
from risk_model import estimate_risk

create_tables()

st.set_page_config(
    page_title="InsureTrack AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
        color: #1f2937;
    }
    [data-testid="stSidebar"] {
        background-color: #e8eef8;
    }
    [data-testid="stSidebar"] * {
        color: #1f2937 !important;
    }
    h1, h2, h3, p, label {
        color: #1f2937 !important;
    }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dce4f0;
        padding: 18px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: #17365d !important;
    }
    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #17365d;
        color: #ffffff !important;
        border-radius: 8px;
        border: none;
        padding: 8px 18px;
    }
    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #28558a;
        color: #ffffff !important;
    }
    [data-testid="stDataFrame"] {
        background-color: #ffffff;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ InsureTrack AI")
st.caption("Smart Insurance Management with AI-Based Risk Estimation")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a section",
    [
        "Dashboard",
        "Customer Registration",
        "Health Insurance",
        "Vehicle Insurance",
        "Life Insurance",
        "Policy Management",
        "AI Risk Estimation",
        "Claims Management"
    ]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.header("Insurance Dashboard")
    st.markdown(
        """
        Welcome to **InsureTrack AI** — a smart insurance
        management demonstration built with Python, Streamlit,
        SQLite, Pandas, and scikit-learn.

        Use the sidebar to register customers, create insurance
        policies, manage claims, and explore the AI demo.
        """
    )

    st.divider()
    conn = connect_db()

    customers_count = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM customers", conn
    ).iloc[0]["total"]

    policies_count = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM policies", conn
    ).iloc[0]["total"]

    claims_count = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM claims WHERE status = 'Pending'",
        conn
    ).iloc[0]["total"]

    policy_data = pd.read_sql_query(
        """
        SELECT insurance_type,
               COUNT(*) AS total,
               SUM(premium) AS total_premium
        FROM policies
        GROUP BY insurance_type
        """,
        conn
    )
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", int(customers_count))
    col2.metric("Total Policies", int(policies_count))
    col3.metric("Pending Claims", int(claims_count))

    st.subheader("Number of Policies by Insurance Type")

    if policy_data.empty:
        st.info("No insurance policies registered yet.")
    else:
        st.bar_chart(
            policy_data.set_index("insurance_type")[["total"]]
        )

        st.subheader("Total Annual Premium by Insurance Type")
        premium_data = policy_data.set_index("insurance_type")[
            ["total_premium"]
        ]
        st.bar_chart(premium_data)

        st.subheader("Premium Summary")
        st.dataframe(
            policy_data[
                ["insurance_type", "total", "total_premium"]
            ].rename(
                columns={
                    "insurance_type": "Insurance Type",
                    "total": "Number of Policies",
                    "total_premium": "Total Annual Premium (₹)"
                }
            ),
            use_container_width=True
        )


# ---------------- CUSTOMER REGISTRATION ----------------
elif page == "Customer Registration":
    st.header("Customer Registration")

    with st.form("customer_form"):
        name = st.text_input("Full Name")

        age = st.number_input(
            "Age", min_value=18, max_value=100, value=25
        )

        gender = st.selectbox(
            "Gender",
            ["Male", "Female", "Other", "Prefer not to say"]
        )

        contact = st.text_input(
            "Contact Number",
            max_chars=15,
            placeholder="Enter contact number"
        )

        email = st.text_input("Email Address")

        submitted = st.form_submit_button("Register Customer")

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email.")
        elif not contact.strip():
            st.error("Please enter a contact number.")
        else:
            conn = None
            try:
                conn = connect_db()
                conn.execute(
                    """
                    INSERT INTO customers
                    (name, age, gender, contact, email)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name.strip(),
                        age,
                        gender,
                        contact.strip(),
                        email.strip()
                    )
                )
                conn.commit()
                st.success(
                    f"Customer {name.strip()} registered successfully!"
                )
                st.rerun()

            except sqlite3.IntegrityError:
                st.error("This email is already registered.")

            finally:
                if conn:
                    conn.close()

    conn = connect_db()
    customers = pd.read_sql_query(
        "SELECT * FROM customers ORDER BY customer_id DESC",
        conn
    )
    conn.close()

    st.subheader("Search Customers")
    search_query = st.text_input(
        "Search by name, email, or contact number",
        key="customer_search"
    )

    if search_query.strip():
        customers = customers[
            customers["name"].str.contains(
                search_query, case=False, na=False
            )
            | customers["email"].str.contains(
                search_query, case=False, na=False
            )
            | customers["contact"].astype(str).str.contains(
                search_query, case=False, na=False
            )
        ]

    st.subheader("Registered Customers")
    st.dataframe(customers, use_container_width=True)

    if not customers.empty:
        st.subheader("Delete Customer")

        customer_options = {
            f"{row['name']} ({row['email']}) - ID {row['customer_id']}":
            int(row["customer_id"])
            for _, row in customers.iterrows()
        }

        selected_customer = st.selectbox(
            "Select customer to delete",
            list(customer_options.keys()),
            key="delete_customer_select"
        )

        confirm_delete = st.checkbox(
            "I understand that deleting this customer also deletes "
            "their policies and claims.",
            key="confirm_delete_customer"
        )

        if st.button(
            "🗑️ Delete Customer",
            key="delete_customer_button"
        ):
            if confirm_delete:
                delete_customer(customer_options[selected_customer])
                st.success("Customer and related records deleted.")
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

# ---------------- INSURANCE POLICY REGISTRATION ----------------
elif page in [
    "Health Insurance",
    "Vehicle Insurance",
    "Life Insurance"
]:
    st.header(f"{page} Policy Registration")
    insurance_type = page.replace(" Insurance", "")

    conn = connect_db()
    customers = pd.read_sql_query(
        "SELECT customer_id, name, email FROM customers",
        conn
    )
    conn.close()

    if customers.empty:
        st.warning(
            "Please register a customer before creating an insurance policy."
        )
    else:
        customer_options = {
            f"{row['name']} ({row['email']})": int(row["customer_id"])
            for _, row in customers.iterrows()
        }

        with st.form("policy_form"):
            selected_customer = st.selectbox(
                "Select Customer", list(customer_options.keys())
            )
            premium = st.number_input(
                "Annual Premium (₹)",
                min_value=100.0,
                max_value=1000000.0,
                value=5000.0,
                step=500.0
            )
            submitted = st.form_submit_button("Create Insurance Policy")

        if submitted:
            conn = connect_db()
            conn.execute(
                """
                INSERT INTO policies
                    (customer_id, insurance_type, premium, status)
                VALUES (?, ?, ?, 'Active')
                """,
                (customer_options[selected_customer], insurance_type, premium)
            )
            conn.commit()
            conn.close()
            st.success(
                f"{insurance_type} insurance policy created successfully!"
            )

    conn = connect_db()
    policies = pd.read_sql_query(
        """
        SELECT p.policy_id, c.name, p.insurance_type,
               p.premium, p.status
        FROM policies p
        JOIN customers c ON p.customer_id = c.customer_id
        ORDER BY p.policy_id DESC
        """,
        conn
    )
    conn.close()

    st.subheader("Registered Insurance Policies")
    st.dataframe(policies, use_container_width=True)

# ---------------- POLICY MANAGEMENT ----------------
elif page == "Policy Management":
    st.header("📋 Policy Management")

    conn = connect_db()
    policies = pd.read_sql_query(
        """
        SELECT p.policy_id, c.name, c.email,
               p.insurance_type, p.premium, p.status
        FROM policies p
        JOIN customers c ON p.customer_id = c.customer_id
        ORDER BY p.policy_id DESC
        """,
        conn
    )
    conn.close()

    if policies.empty:
        st.info("No insurance policies found.")
    else:
        st.subheader("All Insurance Policies")
        st.dataframe(policies, use_container_width=True)

        st.subheader("Delete Insurance Policy")
        policy_delete_options = {
            f"Policy #{row['policy_id']} - {row['name']} "
            f"({row['insurance_type']})": int(row["policy_id"])
            for _, row in policies.iterrows()
        }

        selected_policy_delete = st.selectbox(
            "Select policy to delete",
            list(policy_delete_options.keys()),
            key="delete_policy_select"
        )

        confirm_policy_delete = st.checkbox(
            "I understand that deleting this policy also deletes its claims.",
            key="confirm_delete_policy"
        )

        if st.button("🗑️ Delete Policy", key="delete_policy_button"):
            if confirm_policy_delete:
                delete_policy(policy_delete_options[selected_policy_delete])
                st.success("Policy and related claims deleted.")
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

        st.subheader("Update Policy Status")
        policy_options = {
            f"Policy #{row['policy_id']} - {row['name']} "
            f"({row['insurance_type']})": int(row["policy_id"])
            for _, row in policies.iterrows()
        }

        with st.form("update_policy_form"):
            selected_policy = st.selectbox(
                "Select Policy", list(policy_options.keys())
            )
            new_status = st.selectbox("New Status", ["Active", "Inactive"])
            update_submitted = st.form_submit_button("Update Policy")

        if update_submitted:
            conn = connect_db()
            conn.execute(
                "UPDATE policies SET status = ? WHERE policy_id = ?",
                (new_status, policy_options[selected_policy])
            )
            conn.commit()
            conn.close()
            st.success("Policy status updated successfully!")
            st.rerun()

# ---------------- AI RISK ESTIMATION ----------------
elif page == "AI Risk Estimation":
    st.header("🤖 AI-Based Risk Estimation")
    st.info(
        "Educational demonstration using synthetic data only. "
        "This is not a real insurance risk assessment."
    )

    st.subheader("Enter Sample Details")
    age = st.number_input(
        "Age", min_value=18, max_value=100, value=25, step=1
    )
    insurance_type = st.selectbox(
        "Insurance Type", ["Health", "Vehicle", "Life"]
    )
    type_mapping = {"Health": 0, "Vehicle": 1, "Life": 2}

    if st.button("Estimate Demonstration Risk"):
        risk = estimate_risk(age, type_mapping[insurance_type])
        st.subheader("Demonstration Result")

        if risk == "Low":
            st.success(f"Sample model category: {risk}")
        elif risk == "Medium":
            st.warning(f"Sample model category: {risk}")
        else:
            st.error(f"Sample model category: {risk}")

        st.caption(
            "This result comes from a small, artificial training dataset. "
            "It is not a reliable prediction of a person's actual risk."
        )

# ---------------- CLAIMS MANAGEMENT ----------------
elif page == "Claims Management":
    st.header("Claims Management")

    conn = connect_db()
    policies = pd.read_sql_query(
        """
        SELECT p.policy_id, c.name, p.insurance_type
        FROM policies p
        JOIN customers c ON p.customer_id = c.customer_id
        ORDER BY p.policy_id DESC
        """,
        conn
    )
    conn.close()

    if policies.empty:
        st.warning("Please register a customer and create a policy first.")
    else:
        policy_options = {
            f"Policy #{row['policy_id']} - {row['name']} "
            f"({row['insurance_type']})": int(row["policy_id"])
            for _, row in policies.iterrows()
        }

        with st.form("claim_form"):
            selected_policy = st.selectbox(
                "Select Insurance Policy", list(policy_options.keys())
            )
            claim_amount = st.number_input(
                "Claim Amount (₹)",
                min_value=1.0,
                max_value=10000000.0,
                value=1000.0,
                step=500.0
            )
            submitted = st.form_submit_button("Register Claim")

        if submitted:
            policy_id = policy_options[selected_policy]
            conn = connect_db()
            result = conn.execute(
                "SELECT customer_id FROM policies WHERE policy_id = ?",
                (policy_id,)
            ).fetchone()

            if result:
                conn.execute(
                    """
                    INSERT INTO claims
                        (customer_id, policy_id, claim_amount, status)
                    VALUES (?, ?, ?, 'Pending')
                    """,
                    (result[0], policy_id, claim_amount)
                )
                conn.commit()
                st.success("Claim registered successfully!")
            conn.close()
            st.rerun()

    # Load claims independently, even if there are no policies
    conn = connect_db()
    claims = pd.read_sql_query(
        """
        SELECT cl.claim_id, c.name, cl.policy_id,
               cl.claim_amount, cl.status
        FROM claims cl
        JOIN customers c ON cl.customer_id = c.customer_id
        ORDER BY cl.claim_id DESC
        """,
        conn
    )
    conn.close()

    st.subheader("Registered Claims")

    if claims.empty:
        st.info("No claims have been registered yet.")
    else:
        st.dataframe(claims, use_container_width=True)

        st.subheader("Delete Claim")
        claim_delete_options = {
            f"Claim #{row['claim_id']} - {row['name']} "
            f"(₹{row['claim_amount']})": int(row["claim_id"])
            for _, row in claims.iterrows()
        }

        selected_claim_delete = st.selectbox(
            "Select claim to delete",
            list(claim_delete_options.keys()),
            key="delete_claim_select"
        )

        confirm_claim_delete = st.checkbox(
            "I confirm that I want to permanently delete this claim.",
            key="confirm_delete_claim"
        )

        if st.button("🗑️ Delete Claim", key="delete_claim_button"):
            if confirm_claim_delete:
                delete_claim(claim_delete_options[selected_claim_delete])
                st.success("Claim deleted successfully.")
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

        st.subheader("Update Claim Status")
        claim_options = {
            f"Claim #{row['claim_id']} - {row['name']}": int(row["claim_id"])
            for _, row in claims.iterrows()
        }

        with st.form("update_claim_form"):
            selected_claim = st.selectbox(
                "Select Claim", list(claim_options.keys())
            )
            new_status = st.selectbox(
                "New Status", ["Pending", "Approved", "Rejected"]
            )
            update_submitted = st.form_submit_button("Update Status")

        if update_submitted:
            conn = connect_db()
            conn.execute(
                "UPDATE claims SET status = ? WHERE claim_id = ?",
                (new_status, claim_options[selected_claim])
            )
            conn.commit()
            conn.close()
            st.success("Claim status updated successfully!")
            st.rerun()
