from config import connect

def save_score(username, score, level):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO players(username)
        VALUES (%s)
        ON CONFLICT (username) DO NOTHING
    """, (username,))

    cur.execute("SELECT id FROM players WHERE username=%s", (username,))
    player_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO game_sessions(player_id, score, level_reached)
        VALUES (%s, %s, %s)
    """, (player_id, score, level))

    conn.commit()
    cur.close()
    conn.close()


def get_best(username):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(score)
        FROM game_sessions g
        JOIN players p ON p.id = g.player_id
        WHERE p.username = %s
    """, (username,))

    res = cur.fetchone()[0]

    cur.close()
    conn.close()
    return res if res else 0


def get_top10():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.username, g.score, g.level_reached
        FROM game_sessions g
        JOIN players p ON p.id = g.player_id
        ORDER BY g.score DESC
        LIMIT 10
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data