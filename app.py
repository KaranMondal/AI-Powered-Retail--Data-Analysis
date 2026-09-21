from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


COLORS = {
    "forest": "#22D3B6",
    "terracotta": "#FF6B5E",
    "gold": "#FBBF24",
    "sage": "#A3E635",
    "ink": "#203A35",
    "cream": "#F5F7F4",
    "night": "#111827",
    "panel": "#1F2937",
    "text": "#E5E7EB",
    "muted": "#A7B0BE",
}


st.set_page_config(
    page_title="Retail Intelligence",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).with_name("Online Retail.xlsx")


@st.cache_data
def load_analysis_data():
    raw_df = pd.read_excel(DATA_FILE)
    data = raw_df.copy()
    data["InvoiceNo"] = data["InvoiceNo"].astype(str).str.strip()
    data["StockCode"] = data["StockCode"].astype(str).str.strip()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce")
    data["UnitPrice"] = pd.to_numeric(data["UnitPrice"], errors="coerce")
    data = data.drop_duplicates().copy()
    data["IsCancelled"] = data["InvoiceNo"].str.startswith("C")
    data["IsReturned"] = data["Quantity"] < 0
    returns_df = data[data["IsCancelled"] | data["IsReturned"]].copy()

    required_columns = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country",
    ]
    data = data.dropna(subset=required_columns).copy()
    non_product_codes = {
        "POST", "DOT", "M", "MANUAL", "D", "DISCOUNT",
        "AMAZONFEE", "BANK CHARGES", "CRUK", "S",
    }
    data["StockCodeUpper"] = data["StockCode"].str.upper()
    data = data[
        (~data["IsCancelled"])
        & (~data["IsReturned"])
        & (data["Quantity"] > 0)
        & (data["UnitPrice"] > 0)
        & (~data["StockCodeUpper"].isin(non_product_codes))
    ].copy()
    data["Revenue"] = data["Quantity"] * data["UnitPrice"]

    category_rules = {
        "Bags and Accessories": r"BAG|PURSE|WALLET|SCARF|HAT|GLOVE|JEWEL|RING",
        "Home and Kitchen": r"CAKE|CUP|MUG|KITCHEN|JAR|BOWL|PLATE|TEA|FRAME|DOORMAT|T-LIGHT|LIGHT|HOLDER",
        "Decorations and Gifts": r"HEART|ORNAMENT|BUNTING|CHRISTMAS|DECORATION|CANDLE|SIGN",
        "Toys and Crafts": r"TOY|GAME|DOLL|PUZZLE|GLIDER|PAINT|KITE",
        "Stationery and Packaging": r"PAPER|PENCIL|PEN|NOTEBOOK|CARD|TISSUE|CAKE CASE|ENVELOPE",
        "Garden and Outdoor": r"GARDEN|PLANT|FLOWER|PICNIC",
    }
    category_data = data.copy()
    category_data["Category"] = "Other / Unclassified"
    descriptions = category_data["Description"].fillna("").str.upper()
    for category, pattern in category_rules.items():
        matches = descriptions.str.contains(pattern, regex=True, na=False)
        category_data.loc[
            (category_data["Category"] == "Other / Unclassified") & matches,
            "Category",
        ] = category

    monthly_sales = (
        data.assign(Month=data["InvoiceDate"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
    )
    monthly_sales["AOV"] = monthly_sales["Revenue"] / monthly_sales["Orders"]

    country_sales = (
        data.groupby("Country", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    product_sales = (
        data.groupby(["StockCode", "Description"], as_index=False)
        .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    category_sales = (
        category_data.groupby("Category", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Products=("StockCode", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    category_sales["Share"] = category_sales["Revenue"] / category_sales["Revenue"].sum()

    reference_date = data["InvoiceDate"].max().normalize()
    rfm = (
        data.groupby("CustomerID", as_index=False)
        .agg(
            LastPurchase=("InvoiceDate", "max"),
            FirstPurchase=("InvoiceDate", "min"),
            Frequency=("InvoiceNo", "nunique"),
            MonetaryValue=("Revenue", "sum"),
            ItemsPurchased=("Quantity", "sum"),
            Country=("Country", lambda values: values.mode().iat[0]),
        )
    )
    rfm["Recency"] = (reference_date - rfm["LastPurchase"].dt.normalize()).dt.days
    rfm["AOV"] = rfm["MonetaryValue"] / rfm["Frequency"]
    rfm["R_Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["MonetaryValue"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def segment(row):
        if row.R_Score >= 4 and row.F_Score >= 4 and row.M_Score >= 4:
            return "Champions"
        if row.R_Score >= 3 and row.F_Score >= 4:
            return "Loyal Customers"
        if row.M_Score >= 4 and row.F_Score <= 3:
            return "Big Spenders"
        if row.R_Score >= 4 and row.F_Score <= 2:
            return "New Customers"
        if row.R_Score <= 2 and row.M_Score >= 3:
            return "At Risk"
        if row.R_Score <= 2 and row.F_Score <= 2:
            return "Lost Customers"
        return "Developing Customers"

    rfm["Segment"] = rfm.apply(segment, axis=1)
    return {
        "raw": raw_df,
        "sales": data,
        "returns": returns_df,
        "monthly": monthly_sales,
        "countries": country_sales,
        "products": product_sales,
        "categories": category_sales,
        "category_data": category_data,
        "rfm": rfm,
        "reference_date": reference_date,
    }


def money(value):
    return f"GBP {value:,.0f}"


def style_chart(fig, height=320):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="Arial"),
        margin=dict(l=10, r=10, t=12, b=10),
        hoverlabel=dict(bgcolor=COLORS["forest"], font_color="#FFFFFF"),
        xaxis=dict(gridcolor="#374151", zerolinecolor="#4B5563"),
        yaxis=dict(gridcolor="#374151", zerolinecolor="#4B5563"),
    )
    return fig


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #111827; color: #e5e7eb !important; }
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, label { color: #cbd5e1 !important; }
        [data-testid="stSidebar"] { background: #0B1220; }
        [data-testid="stSidebar"] * { color: #e5e7eb !important; }
        h1, h2, h3 { color: #f8fafc; letter-spacing: 0; }
        [data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2, [data-testid="stAppViewContainer"] h3 { color: #f8fafc !important; }
        [data-testid="stMetric"] { background: linear-gradient(145deg, #243247, #1b2638); border: 1px solid #3b4d66; border-left: 4px solid #22d3b6; border-radius: 10px; padding: .9rem 1rem; min-height: 88px; box-shadow: 0 8px 20px rgba(0, 0, 0, .18); }
        [data-testid="stMetric"]:hover { border-color: #60a5fa; transform: translateY(-2px); transition: transform .18s ease, border-color .18s ease; }
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div { color: #f8fafc; font-size: 1.35rem; line-height: 1.15; white-space: normal !important; overflow: visible !important; overflow-wrap: anywhere; word-break: normal; text-overflow: clip !important; }
        [data-testid="stMetricLabel"] { color: #a7b0be !important; }
        [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] { border-left-color: #ff6b5e; }
        [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] { border-left-color: #fbbf24; }
        [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"] { border-left-color: #a3e635; }
        [data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stMetric"] { border-left-color: #60a5fa; }
        .hero { padding: 1.35rem 1.5rem; background: linear-gradient(120deg, #164e63, #3f2438); border-radius: 10px; margin-bottom: 1.2rem; border: 1px solid #256b83; box-shadow: 0 10px 28px rgba(0, 0, 0, .22); }
        .hero h1 { margin: 0; font-size: 2.2rem; }
        .hero p { margin: .35rem 0 0; color: #d1d5db; }
        .profile-card { padding: 1rem; background: linear-gradient(145deg, #243247, #1b2638); border-left: 5px solid #ff6b5e; border-radius: 10px; box-shadow: 0 8px 20px rgba(0, 0, 0, .18); }
        .insight-card { padding: .8rem 1rem; background: #1f2937; border-radius: 10px; border: 1px solid #3b4d66; border-top: 3px solid #fbbf24; min-height: 88px; box-shadow: 0 8px 20px rgba(0, 0, 0, .16); }
        [data-testid="stDataFrame"], [data-testid="stExpander"] { border-color: #3b4d66; background: #1f2937; }
        [data-baseweb="select"], [data-baseweb="input"] { background: #1f2937; border-color: #475569; }
        small { color: #a7b0be; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def business_overview(analysis):
    sales = analysis["sales"]
    returns = analysis["returns"]
    with st.sidebar:
        st.markdown("### Overview filters")
        country_options = analysis["countries"]["Country"].tolist()
        selected_countries = st.multiselect("Markets", country_options, placeholder="All markets")
        category_options = analysis["categories"]["Category"].tolist() if "Category" in analysis["categories"] else analysis["category_data"]["Category"].drop_duplicates().sort_values().tolist()
        selected_categories = st.multiselect("Categories", category_options, placeholder="All categories")

    filtered_sales = sales.copy()
    if selected_countries:
        filtered_sales = filtered_sales[filtered_sales["Country"].isin(selected_countries)]
    if selected_categories:
        filtered_sales = analysis["category_data"].loc[filtered_sales.index]
        filtered_sales = filtered_sales[filtered_sales["Category"].isin(selected_categories)]

    total_revenue = filtered_sales["Revenue"].sum()
    return_value = (returns["Quantity"].abs() * returns["UnitPrice"].abs()).sum()
    return_rate = return_value / (total_revenue + return_value) if total_revenue else 0
    orders = filtered_sales["InvoiceNo"].nunique()

    scope_label = "All qualifying sales" if not selected_countries and not selected_categories else "Filtered view"
    st.markdown(f'<div class="hero"><h1>Retail Intelligence</h1><p>Executive view of revenue, demand, product performance, and customer value. <strong>{scope_label}</strong></p></div>', unsafe_allow_html=True)
    first, second, third, fourth, fifth = st.columns(5)
    first.metric("Revenue", money(total_revenue))
    second.metric("Identifiable customers", f"{filtered_sales['CustomerID'].nunique():,}")
    third.metric("Average order value", money(total_revenue / orders))
    fourth.metric("Qualifying orders", f"{orders:,}")
    fifth.metric("Return / exception rate", f"{return_rate:.1%}")
    st.caption("Return / exception rate uses absolute value from cancelled or negative-quantity records and may include operational adjustments.")

    november_revenue = analysis["monthly"].loc[analysis["monthly"]["Month"].dt.month == 11, "Revenue"].sum()
    uk_share = analysis["countries"].iloc[0]["Revenue"] / analysis["sales"]["Revenue"].sum()
    named_categories = analysis["categories"][analysis["categories"]["Category"] != "Other / Unclassified"]
    category_leaders = named_categories.head(2)["Revenue"].sum() / analysis["categories"]["Revenue"].sum()
    st.subheader("Signals worth acting on")
    signal_one, signal_two, signal_three = st.columns(3)
    with signal_one:
        st.markdown(f'<div class="insight-card"><strong>Peak season</strong><br><span style="font-size:1.35rem;color:#ff6b5e">{money(november_revenue)}</span><br><small>November revenue sets the planning benchmark.</small></div>', unsafe_allow_html=True)
    with signal_two:
        st.markdown(f'<div class="insight-card"><strong>Market concentration</strong><br><span style="font-size:1.35rem;color:#22d3b6">{uk_share:.1%} UK share</span><br><small>International growth needs deliberate market selection.</small></div>', unsafe_allow_html=True)
    with signal_three:
        st.markdown(f'<div class="insight-card"><strong>Category concentration</strong><br><span style="font-size:1.35rem;color:#fbbf24">{category_leaders:.1%} in top 2</span><br><small>Home, kitchen, decor, and gifts lead identifiable revenue.</small></div>', unsafe_allow_html=True)

    monthly = (
        filtered_sales.assign(Month=filtered_sales["InvoiceDate"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
    )
    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Revenue trend")
        fig = px.line(monthly, x="Month", y="Revenue", markers=True, template="simple_white")
        fig.update_traces(line_color=COLORS["terracotta"], hovertemplate="%{x|%b %Y}<br>Revenue: GBP %{y:,.0f}<extra></extra>")
        fig.update_layout(xaxis_title=None, yaxis_title="Revenue (GBP)")
        style_chart(fig, 315)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.subheader("Revenue by country")
        countries = filtered_sales.groupby("Country", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=True).tail(10)
        fig = px.bar(countries, x="Revenue", y="Country", orientation="h", template="simple_white", color_discrete_sequence=[COLORS["forest"]])
        fig.update_layout(xaxis_title="Revenue (GBP)", yaxis_title=None)
        style_chart(fig, 315)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if not countries.empty:
            st.caption(f"Top market in this view: {countries.iloc[-1]['Country']}.")

    left, right = st.columns(2)
    with left:
        st.subheader("Top products by revenue")
        products = filtered_sales.groupby(["StockCode", "Description"], as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=True).tail(10)
        products["Product"] = products["Description"].str.slice(0, 38)
        fig = px.bar(products, x="Revenue", y="Product", orientation="h", template="simple_white", color_discrete_sequence=[COLORS["gold"]])
        fig.update_layout(xaxis_title="Revenue (GBP)", yaxis_title=None)
        style_chart(fig, 370)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.subheader("Category contribution")
        categories = filtered_sales.assign(Category=analysis["category_data"].loc[filtered_sales.index, "Category"]).groupby("Category", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
        fig = px.pie(categories, names="Category", values="Revenue", hole=0.56, template="simple_white", color_discrete_sequence=[COLORS["forest"], COLORS["terracotta"], COLORS["gold"], COLORS["sage"], "#9C6B4F", "#6D8B8A", "#D9C5A1"])
        fig.update_layout(legend_title=None)
        style_chart(fig, 370)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Categories are estimated from product descriptions; the unclassified group is intentionally retained.")

    with st.expander("Open the supporting rankings"):
        table_left, table_right = st.columns(2)
        with table_left:
            st.markdown("**Top markets**")
            market_table = filtered_sales.groupby("Country", as_index=False).agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("Revenue", ascending=False).head(10)
            st.dataframe(market_table.style.format({"Revenue": "GBP {:,.0f}", "Orders": "{:,.0f}"}), hide_index=True, use_container_width=True)
        with table_right:
            st.markdown("**Top products**")
            product_table = filtered_sales.groupby("Description", as_index=False).agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("Revenue", ascending=False).head(10)
            st.dataframe(product_table.style.format({"Revenue": "GBP {:,.0f}", "Orders": "{:,.0f}"}), hide_index=True, use_container_width=True)

    st.subheader("Revenue leakage to investigate")
    exception_left, exception_right = st.columns(2)
    with exception_left:
        st.metric("Cancellation / exception value", money(return_value))
        st.caption("Calculated from absolute quantity x unit price across cancelled and negative-quantity records.")
    with exception_right:
        st.metric("Exception rows retained", f"{len(returns):,}")
        st.caption("Operational fees and manual adjustments are mixed into this pool and need separate classification.")


def recommendation(segment):
    recommendations = {
        "Champions": "Protect this relationship with VIP access, early product releases, and loyalty benefits. Avoid unnecessary blanket discounts.",
        "Loyal Customers": "Increase basket size with bundles, complementary recommendations, and progression toward a VIP tier.",
        "Big Spenders": "Build purchase frequency through replenishment reminders, tailored recommendations, and account-level outreach.",
        "New Customers": "Guide the second purchase with onboarding emails, product education, and a relevant follow-up offer.",
        "At Risk": "Launch a targeted win-back campaign, prioritizing customers with high historical value and personalized products.",
        "Lost Customers": "Use low-cost reactivation campaigns and focus spend on the highest-value customers in this segment.",
        "Developing Customers": "Nurture toward repeat behavior with post-purchase follow-up and cross-sell recommendations.",
    }
    return recommendations[segment]


def customer_rfm_page(analysis):
    st.markdown('<div class="hero"><h1>Customer RFM Lens</h1><p>Explore individual customer value and turn behavioral signals into action.</p></div>', unsafe_allow_html=True)
    rfm = analysis["rfm"].copy()
    segment_snapshot = rfm.groupby("Segment", as_index=False).agg(Customers=("CustomerID", "nunique"), Revenue=("MonetaryValue", "sum")).sort_values("Revenue", ascending=False)
    snapshot_left, snapshot_right = st.columns([1, 1.3])
    with snapshot_left:
        st.subheader("Customer portfolio")
        st.metric("Revenue represented", money(rfm["MonetaryValue"].sum()))
        st.caption(f"{len(rfm):,} identifiable customers scored against {analysis['reference_date'].date()}.")
    with snapshot_right:
        fig = px.bar(segment_snapshot.sort_values("Revenue"), x="Revenue", y="Segment", orientation="h", template="simple_white", color_discrete_sequence=[COLORS["terracotta"]])
        fig.update_layout(xaxis_title="Revenue (GBP)", yaxis_title=None)
        style_chart(fig, 210)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Open the full RFM segment scorecard"):
        scorecard = segment_snapshot.copy()
        scorecard["Revenue share"] = scorecard["Revenue"] / scorecard["Revenue"].sum()
        st.dataframe(scorecard.style.format({"Revenue": "GBP {:,.0f}", "Revenue share": "{:.1%}", "Customers": "{:,.0f}"}), hide_index=True, use_container_width=True)

    query = st.text_input("Search customer ID", placeholder="Type a customer ID, for example 14646")
    if query.strip():
        filtered = rfm[rfm["CustomerID"].astype(str).str.contains(query.strip(), case=False, na=False)]
    else:
        filtered = rfm.sort_values("MonetaryValue", ascending=False)
    if filtered.empty:
        st.warning("No matching customer was found.")
        return

    selected_id = st.selectbox("Select customer", filtered["CustomerID"].astype(str).tolist())
    customer = rfm[rfm["CustomerID"].astype(str) == selected_id].iloc[0]
    segment = customer["Segment"]
    st.markdown(f'<div class="profile-card"><h3>{segment}</h3><p>{recommendation(segment)}</p></div>', unsafe_allow_html=True)

    first, second, third, fourth = st.columns(4)
    first.metric("Customer", selected_id)
    second.metric("Total revenue", money(customer["MonetaryValue"]))
    third.metric("AOV", money(customer["AOV"]))
    fourth.metric("Orders", f"{int(customer['Frequency']):,}")

    st.subheader("Customer profile")
    profile_left, profile_right = st.columns(2)
    with profile_left:
        st.write(f"**Country:** {customer['Country']}")
        st.write(f"**First purchase:** {customer['FirstPurchase'].date()}")
        st.write(f"**Last purchase:** {customer['LastPurchase'].date()}")
        st.write(f"**Recency:** {int(customer['Recency'])} days")
    with profile_right:
        st.write(f"**RFM score:** {customer['R_Score']}{customer['F_Score']}{customer['M_Score']}")
        st.write(f"**Items purchased:** {int(customer['ItemsPurchased']):,}" if "ItemsPurchased" in customer else "**Segment:** " + segment)
        st.write(f"**Frequency score:** {customer['F_Score']}/5")
        st.write(f"**Monetary score:** {customer['M_Score']}/5")

    customer_sales = analysis["sales"][analysis["sales"]["CustomerID"].astype(str) == selected_id].copy()
    product_chart = customer_sales.groupby("Description", as_index=False)["Revenue"].sum().nlargest(8, "Revenue").sort_values("Revenue")
    category_data = customer_sales.copy()
    category_data["Category"] = "Other / Unclassified"
    patterns = {
        "Bags and Accessories": r"BAG|PURSE|WALLET|SCARF|HAT|GLOVE|JEWEL|RING",
        "Home and Kitchen": r"CAKE|CUP|MUG|KITCHEN|JAR|BOWL|PLATE|TEA|FRAME|DOORMAT|T-LIGHT|LIGHT|HOLDER",
        "Decorations and Gifts": r"HEART|ORNAMENT|BUNTING|CHRISTMAS|DECORATION|CANDLE|SIGN",
        "Toys and Crafts": r"TOY|GAME|DOLL|PUZZLE|GLIDER|PAINT|KITE",
        "Stationery and Packaging": r"PAPER|PENCIL|PEN|NOTEBOOK|CARD|TISSUE|CAKE CASE|ENVELOPE",
        "Garden and Outdoor": r"GARDEN|PLANT|FLOWER|PICNIC",
    }
    descriptions = category_data["Description"].fillna("").str.upper()
    for category, pattern in patterns.items():
        category_data.loc[(category_data["Category"] == "Other / Unclassified") & descriptions.str.contains(pattern, regex=True, na=False), "Category"] = category
    category_chart = category_data.groupby("Category", as_index=False)["Revenue"].sum().sort_values("Revenue")

    left, right = st.columns(2)
    with left:
        st.subheader("Top products purchased")
        product_chart["Description"] = product_chart["Description"].str.slice(0, 34)
        fig = px.bar(product_chart, x="Revenue", y="Description", orientation="h", template="simple_white", color_discrete_sequence=[COLORS["gold"]])
        fig.update_layout(xaxis_title="Revenue (GBP)", yaxis_title=None)
        style_chart(fig, 330)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.subheader("Categories purchased")
        fig = px.pie(category_chart, names="Category", values="Revenue", hole=0.55, template="simple_white", color_discrete_sequence=[COLORS["forest"], COLORS["terracotta"], COLORS["gold"], COLORS["sage"], "#9C6B4F", "#6D8B8A", "#D9C5A1"])
        fig.update_layout(legend_title=None)
        style_chart(fig, 330)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    history = customer_sales.assign(Month=customer_sales["InvoiceDate"].dt.to_period("M").dt.to_timestamp()).groupby("Month", as_index=False)["Revenue"].sum()
    st.subheader("Customer purchase rhythm")
    fig = px.area(history, x="Month", y="Revenue", template="simple_white", color_discrete_sequence=[COLORS["sage"]])
    fig.update_layout(xaxis_title=None, yaxis_title="Revenue (GBP)")
    style_chart(fig, 260)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


inject_styles()
analysis = load_analysis_data()
with st.sidebar:
    st.markdown("## Retail Intelligence")
    page = st.radio("Navigate", ["Business overview", "Customer RFM analysis"])
    st.divider()
    st.caption("Source: Online Retail.xlsx")
    st.caption(f"Data through {analysis['reference_date'].date()}")

if page == "Business overview":
    business_overview(analysis)
else:
    customer_rfm_page(analysis)