import streamlit as st
import anthropic
import pandas as pd
import re
import os
from dotenv import load_dotenv
from database import get_schema, run_query

load_dotenv()

st.set_page_config(
    page_title="SQL Query Assistant",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #0d0f12; }
    .stApp { background-color: #0d0f12; color: #e8e6e0; }
    .block-container { padding-top: 2rem; }
    .sql-box {
        background: #161a1f;
        border: 1px solid rgba(200,245,160,0.2);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        color: #c8f5a0;
        white-space: pre-wrap;
        margin: 0.5rem 0 1rem;
    }
    .explanation-box {
        background: #161a1f;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-size: 15px;
        color: #b0b3b8;
        margin-bottom: 1rem;
    }
    .stTextArea textarea {
        background-color: #161a1f !important;
        color: #e8e6e0 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        font-size: 15px !important;
    }
    .stButton button {
        background-color: #c8f5a0 !important;
        color: #0d0f12 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.5rem 2rem !important;
    }
    .stButton button:hover { background-color: #d4f8b0 !important; }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    h1, h2, h3 { color: #e8e6e0 !important; }
    .stExpander { background: #161a1f; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 8px; }
    label { color: #7a7d82 !important; font-size: 13px !important; }
    .tag {
        display: inline-block;
        background: rgba(200,245,160,0.08);
        border: 1px solid rgba(200,245,160,0.2);
        color: #c8f5a0;
        border-radius: 4px;
        padding: 2px 10px;
        font-size: 12px;
        font-family: monospace;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("### 🔍 SQL Query Assistant")
st.markdown("<p style='color:#7a7d82; margin-top:-0.5rem; margin-bottom:2rem;'>Ask a question in plain English — get a SQL query and results instantly.</p>", unsafe_allow_html=True)

# Load schema once
@st.cache_data
def load_schema():
    return get_schema()

with st.spinner("Loading database..."):
    schema, tables = load_schema()

# Table metadata
TABLE_INFO = {
    "Categories": {
        "desc": "Product categories like Beverages, Seafood, Dairy.",
        "columns": {
            "CategoryID": "Unique category identifier",
            "CategoryName": "Name of the category",
            "Description": "What kinds of products belong here",
        }
    },
    "Customers": {
        "desc": "Companies and individuals who place orders.",
        "columns": {
            "CustomerID": "5-letter unique customer code",
            "CompanyName": "Name of the customer's company",
            "ContactName": "Primary contact person",
            "Country": "Country where the customer is based",
            "City": "City of the customer",
        }
    },
    "Employees": {
        "desc": "Staff who manage and process orders.",
        "columns": {
            "EmployeeID": "Unique employee identifier",
            "FirstName": "Employee's first name",
            "LastName": "Employee's last name",
            "Title": "Job title",
            "ReportsTo": "EmployeeID of their manager",
            "Country": "Country where employee works",
        }
    },
    "Orders": {
        "desc": "Every order placed by customers, with dates and shipping info.",
        "columns": {
            "OrderID": "Unique order identifier",
            "CustomerID": "Who placed the order",
            "EmployeeID": "Who processed the order",
            "OrderDate": "When the order was placed",
            "ShippedDate": "When the order was shipped",
            "ShipCountry": "Destination country",
        }
    },
    "Order Details": {
        "desc": "Line items within each order — products, quantities, and prices.",
        "columns": {
            "OrderID": "Which order this line belongs to",
            "ProductID": "Which product was ordered",
            "UnitPrice": "Price per unit at time of order",
            "Quantity": "Number of units ordered",
            "Discount": "Discount applied (0.0 to 1.0)",
        }
    },
    "Products": {
        "desc": "All products available for sale, with pricing and stock info.",
        "columns": {
            "ProductID": "Unique product identifier",
            "ProductName": "Name of the product",
            "SupplierID": "Who supplies this product",
            "CategoryID": "Which category it belongs to",
            "UnitPrice": "Current selling price",
            "UnitsInStock": "Current inventory count",
            "Discontinued": "1 if no longer sold, 0 if active",
        }
    },
    "Suppliers": {
        "desc": "Vendors who supply products to Northwind.",
        "columns": {
            "SupplierID": "Unique supplier identifier",
            "CompanyName": "Supplier's company name",
            "ContactName": "Primary contact",
            "Country": "Country of the supplier",
        }
    },
    "Shippers": {
        "desc": "Shipping companies used to deliver orders.",
        "columns": {
            "ShipperID": "Unique shipper identifier",
            "CompanyName": "Name of the shipping company",
            "Phone": "Contact phone number",
        }
    },
    "Regions": {
        "desc": "Geographic sales regions.",
        "columns": {
            "RegionID": "Unique region identifier",
            "RegionDescription": "Name of the region",
        }
    },
    "Territories": {
        "desc": "Sales territories within each region.",
        "columns": {
            "TerritoryID": "Unique territory identifier",
            "TerritoryDescription": "Name of the territory",
            "RegionID": "Which region this territory belongs to",
        }
    },
    "EmployeeTerritories": {
        "desc": "Maps which employees cover which sales territories.",
        "columns": {
            "EmployeeID": "The employee",
            "TerritoryID": "The territory they cover",
        }
    },
    "CustomerDemographics": {
        "desc": "Customer type classifications (mostly unused in this dataset).",
        "columns": {
            "CustomerTypeID": "Type identifier",
            "CustomerDesc": "Description of the customer type",
        }
    },
    "CustomerCustomerDemo": {
        "desc": "Links customers to their demographic types.",
        "columns": {
            "CustomerID": "The customer",
            "CustomerTypeID": "Their demographic type",
        }
    },
}

# Sidebar — schema explorer
with st.sidebar:
    st.markdown("#### 📋 Database Tables")
    st.markdown("<p style='color:#7a7d82; font-size:13px;'>Northwind sample — click any table to explore</p>", unsafe_allow_html=True)
    st.markdown("")

    for table in tables:
        info = TABLE_INFO.get(table, {})
        desc = info.get("desc", "")
        columns_info = info.get("columns", {})

        with st.expander(f"**{table}**"):
            if desc:
                st.markdown(f"<p style='color:#7a7d82; font-size:12px; margin-bottom:8px;'>{desc}</p>", unsafe_allow_html=True)
            if columns_info:
                st.markdown("<p style='color:#c8f5a0; font-size:11px; letter-spacing:0.08em; margin-bottom:4px;'>COLUMNS</p>", unsafe_allow_html=True)
                for col, col_desc in columns_info.items():
                    st.markdown(
                        f"<div style='margin-bottom:4px;'>"
                        f"<span style='font-family:monospace; font-size:12px; color:#e8e6e0;'>{col}</span>"
                        f"<span style='font-size:11px; color:#7a7d82;'> — {col_desc}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("<p style='color:#7a7d82; font-size:12px;'>No metadata available.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 💡 Try asking...")
    examples = [
        "Who are the top 5 customers by total orders?",
        "Which products have never been ordered?",
        "What is the total revenue by country?",
        "Show me all employees and their managers",
        "Which supplier provides the most products?",
    ]
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state["prefill"] = ex

# Main input
prefill = st.session_state.get("prefill", "")
question = st.text_area(
    "Your question",
    value=prefill,
    placeholder="e.g. Who are the top 10 customers by number of orders?",
    height=80
)

col1, col2 = st.columns([1, 5])
with col1:
    submit = st.button("Generate SQL →")

if submit and question.strip():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("API key not found. Make sure your .env file has ANTHROPIC_API_KEY set.")
        st.stop()

    client = anthropic.Anthropic(api_key=api_key)

    with st.spinner("Generating query..."):
        prompt = f"""You are an expert SQL assistant. The user is querying a SQLite database with this schema:

{schema}

The user asked: "{question}"

Respond with:
1. A valid SQLite SQL query that answers the question
2. A plain-English explanation of what the query does (2-3 sentences max, no technical jargon)

Format your response EXACTLY like this:
SQL:
<the sql query here>

EXPLANATION:
<the explanation here>

Rules:
- Use only tables and columns that exist in the schema above
- SQLite syntax only (no TOP, use LIMIT instead)
- Keep the query readable with proper formatting
- If the question can't be answered with the available data, say so in the explanation and return a simple valid query as a placeholder
"""

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text

    # Parse response
    sql_match = re.search(r"SQL:\s*(.*?)(?=EXPLANATION:|$)", raw, re.DOTALL)
    exp_match = re.search(r"EXPLANATION:\s*(.*)", raw, re.DOTALL)

    sql = sql_match.group(1).strip().strip("```sql").strip("```").strip() if sql_match else ""
    explanation = exp_match.group(1).strip() if exp_match else ""

    if sql:
        st.markdown("#### Generated SQL")
        st.markdown(f"<div class='sql-box'>{sql}</div>", unsafe_allow_html=True)

        if explanation:
            st.markdown("#### What this query does")
            st.markdown(f"<div class='explanation-box'>{explanation}</div>", unsafe_allow_html=True)

        st.markdown("#### Results")
        try:
            columns, rows = run_query(sql)
            if rows:
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, use_container_width=True)
                st.markdown(f"<p style='color:#7a7d82; font-size:13px;'>{len(rows)} row(s) returned</p>", unsafe_allow_html=True)
            else:
                st.info("Query ran successfully but returned no results.")
        except Exception as e:
            st.error(f"Query error: {e}")
            st.markdown("<p style='color:#7a7d82; font-size:13px;'>The generated SQL had an issue. Try rephrasing your question.</p>", unsafe_allow_html=True)

elif submit and not question.strip():
    st.warning("Please enter a question first.")
