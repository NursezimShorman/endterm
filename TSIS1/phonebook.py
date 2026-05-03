import json
import csv
from connect import connect

conn = connect()
cur = conn.cursor()

# ---------------- ADD CONTACT ----------------
def add_contact():
    name = input("Name: ")
    email = input("Email: ")
    birthday = input("Birthday (YYYY-MM-DD): ")
    group = input("Group: ")

    cur.execute("SELECT id FROM groups WHERE name=%s", (group,))
    g = cur.fetchone()

    if not g:
        cur.execute("INSERT INTO groups(name) VALUES (%s) RETURNING id", (group,))
        group_id = cur.fetchone()[0]
    else:
        group_id = g[0]

    cur.execute("""
        INSERT INTO contacts(name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s)
    """, (name, email, birthday, group_id))

    conn.commit()
    print("Added")

# ---------------- EXPORT JSON ----------------
def export_json():
    cur.execute("""
        SELECT c.name, c.email, c.birthday, g.name, p.phone, p.type
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
    """)

    rows = cur.fetchall()
    result = {}

    for name, email, birthday, group, phone, t in rows:
        if name not in result:
            result[name] = {
                "name": name,
                "email": email,
                "birthday": str(birthday),
                "group": group,
                "phones": []
            }

        if phone:
            result[name]["phones"].append({
                "number": phone,
                "type": t
            })

    with open("contacts.json", "w") as f:
        json.dump(list(result.values()), f, indent=4)

    print("Exported")

# ---------------- IMPORT JSON ----------------
def import_json():
    with open("contacts.json", "r") as f:
        data = json.load(f)

    for c in data:
        name = c["name"]

        cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
        existing = cur.fetchone()

        if existing:
            choice = input(f"{name} exists. skip/overwrite? ")
            if choice == "skip":
                continue
            else:
                cur.execute("DELETE FROM contacts WHERE name=%s", (name,))

        group = c.get("group", "Other")

        cur.execute("SELECT id FROM groups WHERE name=%s", (group,))
        g = cur.fetchone()

        if not g:
            cur.execute("INSERT INTO groups(name) VALUES (%s) RETURNING id", (group,))
            group_id = cur.fetchone()[0]
        else:
            group_id = g[0]

        cur.execute("""
            INSERT INTO contacts(name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (name, c["email"], c["birthday"], group_id))

        cid = cur.fetchone()[0]

        for p in c["phones"]:
            cur.execute("""
                INSERT INTO phones(contact_id, phone, type)
                VALUES (%s, %s, %s)
            """, (cid, p["number"], p["type"]))

    conn.commit()
    print("Imported")

# ---------------- FILTER ----------------
def filter_by_group():
    group = input("Group: ")

    cur.execute("""
        SELECT c.name, c.email
        FROM contacts c
        JOIN groups g ON c.group_id = g.id
        WHERE g.name = %s
    """, (group,))

    for row in cur.fetchall():
        print(row)

# ---------------- SORT ----------------
def sort_contacts():
    field = input("Sort by (name/birthday/date_added): ")

    cur.execute(f"SELECT name, email FROM contacts ORDER BY {field}")

    for row in cur.fetchall():
        print(row)

# ---------------- PAGINATION ----------------
def paginate():
    limit = 2
    offset = 0

    while True:
        cur.execute("""
            SELECT name, email FROM contacts
            LIMIT %s OFFSET %s
        """, (limit, offset))

        rows = cur.fetchall()

        if not rows:
            print("No more")
            break

        for r in rows:
            print(r)

        cmd = input("next / prev / quit: ")

        if cmd == "next":
            offset += limit
        elif cmd == "prev":
            offset = max(0, offset - limit)
        else:
            break

# ---------------- MENU ----------------
while True:
    print("\n1 Add")
    print("2 Search")
    print("3 Add phone")
    print("4 Exit")
    print("5 Move group")
    print("6 Export JSON")
    print("7 Import JSON")
    print("8 Filter group")
    print("9 Sort")
    print("10 Pagination")

    ch = input("Choose: ")

    if ch == "1":
        add_contact()

    elif ch == "2":
        q = input("Search: ")
        cur.execute("SELECT * FROM search_contacts(%s)", (q,))
        print(cur.fetchall())

    elif ch == "3":
        name = input("Name: ")
        phone = input("Phone: ")
        t = input("Type: ")
        cur.execute("CALL add_phone(%s,%s,%s)", (name, phone, t))
        conn.commit()

    elif ch == "4":
        break

    elif ch == "5":
        name = input("Name: ")
        group = input("Group: ")
        cur.execute("CALL move_to_group(%s,%s)", (name, group))
        conn.commit()

    elif ch == "6":
        export_json()

    elif ch == "7":
        import_json()

    elif ch == "8":
        filter_by_group()

    elif ch == "9":
        sort_contacts()

    elif ch == "10":
        paginate()
