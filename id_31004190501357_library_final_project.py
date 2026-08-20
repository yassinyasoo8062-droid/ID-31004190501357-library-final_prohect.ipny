import pandas as pd
import sqlite3


# 1. Read SQLite database


conn = sqlite3.connect("level3_final_project_library.db")

members = pd.read_sql_query("SELECT * FROM members", conn)
books = pd.read_sql_query("SELECT * FROM books", conn)
checkouts = pd.read_sql_query("SELECT * FROM checkouts", conn)



# 2. Read JSON file


book_catalog = pd.read_json(
    "level3_final_project_book_catalog.json"
)


# 3. Read HTML file

event_signup = pd.read_html(
    "level3_final_project_event_signup.html"
)[0]


# TASK 1 - SQL


# Question 1

query1 = """
SELECT
    members.member_id,
    members.first_name,
    members.last_name,
    COUNT(checkouts.checkout_id) AS checkout_count
FROM members
LEFT JOIN checkouts
    ON members.member_id = checkouts.member_id
GROUP BY
    members.member_id,
    members.first_name,
    members.last_name
ORDER BY checkout_count DESC;
"""

result = pd.read_sql_query(query1, conn)
result


# Question 2

query2 = """
SELECT DISTINCT author
FROM books
WHERE author LIKE 'M%';
"""

result2 = pd.read_sql_query(query2, conn)
result2


# Question 3

query3 = """
SELECT
    books.title,
    COUNT(checkouts.checkout_id) AS checkout_count
FROM books
JOIN checkouts
    ON books.book_id = checkouts.book_id
GROUP BY
    books.book_id,
    books.title
ORDER BY checkout_count DESC
LIMIT 5;
"""

result3 = pd.read_sql_query(query3, conn)
result3


# Question 4

query4 = """
SELECT
    members.first_name,
    members.last_name,
    COUNT(checkouts.checkout_id) AS checkout_count
FROM members
JOIN checkouts
    ON members.member_id = checkouts.member_id
GROUP BY
    members.member_id,
    members.first_name,
    members.last_name
ORDER BY checkout_count DESC
LIMIT 10;
"""

result4 = pd.read_sql_query(query4, conn)
result4


# Question 5

query5 = """
SELECT
    member_id,
    first_name,
    last_name,
    grade,
    neighborhood,
    membership_status,
    join_date
FROM members
WHERE LOWER(TRIM(neighborhood)) = 'maadi'
ORDER BY member_id
LIMIT 10 OFFSET 10;
"""

result5 = pd.read_sql_query(query5, conn)
result5


# API vs SCRAPING


"""
API is usually more reliable and structured for getting data.
Scraping is useful when no API is available, but it depends on
the webpage structure and may break if the page changes.
In this project, scraping was suitable for extracting checkout
records from the HTML page.
"""


# TASK 1 - DATA INTEGRATION / MERGE
# 1. Merge checkouts with members

merged = pd.merge(
    checkouts,
    members,
    on="member_id",
    how="left"
)


# 2. Add book details

merged = pd.merge(
    merged,
    book_catalog,
    on="book_id",
    how="left"
)


# 3. Read HTML

event_signup = pd.read_html(
    "level3_final_project_event_signup.html"
)[0]


# 4. Rename columns

event_signup = event_signup.rename(columns={
    "Member ID": "member_id",
    "Book ID": "book_id",
    "Checkout Date": "checkout_date"
})


# 5. Add return_date

event_signup["return_date"] = pd.NA


# 6. Merge HTML data with members

event_signup = pd.merge(
    event_signup,
    members,
    on="member_id",
    how="left"
)


# 7. Merge HTML data with books

event_signup = pd.merge(
    event_signup,
    book_catalog,
    on="book_id",
    how="left"
)


# 8. Add missing checkout_id

event_signup["checkout_id"] = pd.NA


# 9. Make columns identical and in the same order

event_signup = event_signup[merged.columns]


# 10. Combine database checkouts + HTML records

merged = pd.concat(
    [merged, event_signup],
    ignore_index=True
)


# 11. Calculate checkout count for each member

merged["checkout_count"] = (
    merged.groupby("member_id")["book_id"]
    .transform("count")
)


# =========================================================
# SAVE COMBINED DATA BEFORE CLEANING
# =========================================================

merged.to_csv(
    "combined_data.csv",
    index=False
)


# =========================================================
# DATA INTEGRITY CHECKS
# =========================================================

print("Missing Values:")
print(merged.isna().sum())

print("\nDuplicates:")
print(merged.duplicated().sum())

print("\nNeighborhood:")
print(merged["neighborhood"].value_counts(dropna=False))

print("\nMembership Status:")
print(merged["membership_status"].value_counts(dropna=False))


# Check orphan members

orphan_members = merged[
    ~merged["member_id"].isin(members["member_id"])
]

print("\nOrphan member records:")
print(orphan_members)

print("Count:", len(orphan_members))


# Check orphan books

orphan_books = merged[
    ~merged["book_id"].isin(book_catalog["book_id"])
]

print("\nOrphan book records:")
print(orphan_books)

print("Count:", len(orphan_books))


# =========================================================
# TASK 2 - DATA CLEANING
# =========================================================

# 1. Fill missing checkout IDs with new unique IDs

max_id = pd.to_numeric(
    merged["checkout_id"],
    errors="coerce"
).max()

missing = merged["checkout_id"].isna()

merged.loc[missing, "checkout_id"] = range(
    int(max_id) + 1,
    int(max_id) + 1 + missing.sum()
)


# 2. Convert return_date to datetime

merged["return_date"] = pd.to_datetime(
    merged["return_date"],
    errors="coerce"
)


# 3. Restore missing member information

member_cols = [
    "first_name",
    "last_name",
    "grade",
    "neighborhood",
    "membership_status",
    "join_date"
]

member_data = members[
    ["member_id"] + member_cols
]

merged = merged.drop(
    columns=member_cols,
    errors="ignore"
)

merged = merged.merge(
    member_data,
    on="member_id",
    how="left"
)


# 4. Check missing member information

print("\nMissing member information:")
print(merged[member_cols].isna().sum())


# 5. Check duplicates again

print("\nDuplicates after member restoration:")
print(merged.duplicated().sum())


# 6. Standardize membership status

merged["membership_status"] = (
    merged["membership_status"]
    .str.capitalize()
)

print("\nMembership Status after cleaning:")
print(
    merged["membership_status"]
    .value_counts(dropna=False)
)


# 7. Fill missing grades with median

merged["grade"] = merged["grade"].fillna(
    merged["grade"].median()
)

print("\nMissing grades after cleaning:")
print(merged["grade"].isna().sum())


# 8. Standardize neighborhood names

merged["neighborhood"] = (
    merged["neighborhood"]
    .str.strip()
    .str.title()
)

print("\nNeighborhood after cleaning:")
print(
    merged["neighborhood"]
    .value_counts(dropna=False)
)


# 9. Convert join_date to datetime

merged["join_date"] = pd.to_datetime(
    merged["join_date"],
    errors="coerce"
)


# 10. Restore missing publication years

book_years = book_catalog[
    ["book_id", "publication_year"]
]

merged = merged.drop(
    columns=["publication_year"],
    errors="ignore"
)

merged = merged.merge(
    book_years,
    on="book_id",
    how="left"
)


# =========================================================
# FINAL DATA INTEGRITY CHECK
# =========================================================

print("\nFinal Missing Values:")
print(merged.isna().sum())

print("\nFinal Duplicates:")
print(merged.duplicated().sum())


# =========================================================
# SAVE CLEANED DATA
# =========================================================

merged.to_csv(
    "cleaned_library_final_project.csv",
    index=False
)


# =========================================================
# TASK 3 - DATA FAIRNESS
# =========================================================

neighborhood_fairness = (
    merged.groupby("neighborhood")
    .agg(
        checkouts=("checkout_id", "count"),
        members=("member_id", "nunique")
    )
)

neighborhood_fairness["checkouts_per_member"] = (
    neighborhood_fairness["checkouts"] /
    neighborhood_fairness["members"]
)

neighborhood_fairness = (
    neighborhood_fairness
    .sort_values(
        "checkouts_per_member",
        ascending=False
    )
)

print("\nNeighborhood Fairness:")
print(neighborhood_fairness)

# Project tasks completed:
# Task 1 - SQL queries and data integration
# Task 2 - Data cleaning and integrity checks
# Task 3 - Data fairness analysis