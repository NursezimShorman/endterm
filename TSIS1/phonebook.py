import json
from connect import connect

conn = connect()
cur = conn.cursor()

def export_json(cur):
    cur.execute("""
        SELECT c.name, c.email, p.phone
        FROM contacts c
        LEFT JOIN phones p ON c.id = p.contact_id
    """)

    data = cur.fetchall()

    with open("contacts.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Saved to contacts.json")


while True:
    print("\n1. Add contact")
    print("2. Search")
    print("3. Add phone")
    print("4. Exit")
    print("5. Move to group")
    print("6. Export JSON")

    choice = input("Choose: ")

    if choice == "1":
        name = input("Name: ")
        cur.execute("INSERT INTO contacts(name) VALUES (%s)", (name,))
        conn.commit()

    elif choice == "2":
        q = input("Search: ")
        cur.execute("SELECT * FROM search_contacts(%s)", (q,))
        for row in cur.fetchall():
            print(row)

    elif choice == "3":
        name = input("Name: ")
        phone = input("Phone: ")
        t = input("Type (home/work/mobile): ")

        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, t))
        conn.commit()

    elif choice == "4":
        break

    elif choice == "5":
        name = input("Name: ")
        group = input("Group: ")

        cur.execute("CALL move_to_group(%s, %s)", (name, group))
        conn.commit()

    elif choice == "6":
        export_json(cur)