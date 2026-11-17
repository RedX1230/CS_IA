import sqlite3
conn=sqlite3.connect('test_database.db')
cur=conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            name varchar(255), 
            score INTEGER)''')
conn.commit()
def add_user():
    name = input("Enter name: ")
    id= int(input("Enter user ID: "))
    score= int(input("Enter a score: "))
    cur.execute(
        """INSERT INTO users (id,name,score) VALUES (?,?,?)""",
        (id,name,score,)
    )
    conn.commit()
def view_user():
    cur.execute("""SELECT * FROM users""")
    records=cur.fetchall()
    for row in records:
        print(row)
def search_user():
    id=int(input("Enter ID to search:"))
    cur.execute(
        """SELECT * FROM users WHERE id=?""",
        (id,)
    )
    record=cur.fetchone()
    if record:
        print(record)
    else:
        print("User not found")
    conn.commit()
def update_user():
    id= int(input("Enter user ID to change:"))
    score=int(input("Enter score"))
    cur.execute(
        """UPDATE users SET score=? WHERE id=?""",
        (score,id)
    )
    conn.commit()
def delete_user():
    id= int(input("Enter user ID to change:"))
while True:
    question=input("What would you like to do: add user,search user, view databse or update score ")
    if question=="add user":
        add_user()
    elif question=="view database":
        view_user()
    elif question=="search user":
        search_user()
    elif question=="update score":
        update_user()
    else:
        exit
        conn.commit()
