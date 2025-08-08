# app.py
import streamlit as st
import sqlite3
import random
import time
from datetime import datetime
from PIL import Image
import os

# ---------- Konfiguration ----------
DB_PATH = "casino.db"
st.set_page_config(page_title="Klaus' Casino", layout="centered", initial_sidebar_state="expanded")

# ---------- Styles ----------
st.markdown("""
<style>
/* Card-like container */
.block {
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(250,250,255,0.98));
  margin-bottom: 16px;
}
.big-title {
  font-size: 26px;
  font-weight: 700;
}
.small {
  color: #666;
  font-size: 14px;
}
.center {
  text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------- DB Helpers ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            points INTEGER,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            game TEXT,
            bet INTEGER,
            delta INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, points FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(username, start_points=1000):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, points, created_at) VALUES (?, ?, ?)",
              (username, start_points, now))
    conn.commit()
    conn.close()

def update_points(username, delta):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username = ?", (delta, username))
    conn.commit()
    conn.close()

def set_points(username, points):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = ? WHERE username = ?", (points, username))
    conn.commit()
    conn.close()

def record_play(username, game, bet, delta):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO plays (username, game, bet, delta, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, game, bet, delta, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def top_leaderboard(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- Init ----------
init_db()

# ---------- Session: Login / User ----------
if "username" not in st.session_state:
    st.session_state["username"] = ""

st.sidebar.image(None, width=1)  # spacing

st.sidebar.markdown("## Spieler-Login")
username = st.sidebar.text_input("Benutzername", value=st.session_state.get("username",""))
if st.sidebar.button("Einloggen / neues Konto"):
    username = username.strip()
    if username == "":
        st.sidebar.error("Bitte gib einen Namen ein.")
    else:
        if not get_user(username):
            create_user(username, start_points=1000)
            st.sidebar.success(f"Neues Konto für {username} (Start: 1000 Punkte).")
        else:
            st.sidebar.info(f"Willkommen zurück, {username}!")
        st.session_state["username"] = username
        st.experimental_rerun()

if st.session_state.get("username"):
    cur_user = get_user(st.session_state["username"])
    if cur_user:
        _, cur_points = cur_user
    else:
        cur_points = 0
else:
    cur_points = 0

# ---------- Layout ----------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.markdown('<div class="big-title center">🎰 Klaus\' Casino</div>', unsafe_allow_html=True)
st.markdown(f'<p class="small center">Spiele: Würfel, Münzwurf, Slotmaschine, Bombenzahl, Greifautomat — Punkte werden gespeichert.</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Sidebar: Navigation ----------
games = ["Startseite", "Würfeln", "Münzwurf", "Slotmaschine", "Bombenzahl", "Greifautomat", "Leaderboard", "Statistiken"]
page = st.sidebar.radio("Menu", games)

# Helper: show wallet & quick actions
def wallet_card():
    st.sidebar.markdown("### Wallet")
    if st.session_state.get("username"):
        st.sidebar.markdown(f"**{st.session_state['username']}**")
        st.sidebar.markdown(f"**Punkte:** {cur_points}")
        if st.sidebar.button("+ 500 Punkte (Tausch)"):
            update_points(st.session_state["username"], 500)
            st.experimental_rerun()
    else:
        st.sidebar.info("Bitte einloggen, um zu spielen.")

wallet_card()

# ---------- Game Utilities ----------
def play_result(username, game, bet, delta, message):
    if username:
        update_points(username, delta)
        record_play(username, game, bet, delta)
        st.success(message)
        st.balloons()

# ---------- Pages ----------
if page == "Startseite":
    st.markdown("## Willkommen")
    st.markdown("Wähle links ein Spiel aus. Du startest mit 1000 Punkten beim ersten Login. Jeder Spielzug wird in der Datenbank gespeichert.")
    st.markdown("---")
    st.markdown("### Schnellstart")
    st.markdown("1. Einloggen (links)\n2. Spiel auswählen\n3. Einsatz wählen und spielen")
    st.image(None)  # placeholder for visual

elif page == "Würfeln":
    st.header("🎲 Würfeln")
    st.markdown("Wette auf die Augenzahl (1–6). Treffer: 4× Einsatz, sonst Einsatz verloren.")
    with st.form("dice_form"):
        bet = st.number_input("Einsatz", min_value=1, max_value=100000, value=10, step=1)
        guess = st.selectbox("Auf welche Zahl setzt du?", [1,2,3,4,5,6])
        submitted = st.form_submit_button("Würfeln")
    if submitted:
        if not st.session_state.get("username"):
            st.error("Bitte zuerst einloggen.")
        else:
            if bet > cur_points:
                st.error("Nicht genug Punkte.")
            else:
                rolled = random.randint(1,6)
                st.info(f"Die Kugel zeigt: **{rolled}**")
                if rolled == guess:
                    win = bet * 4
                    play_result(st.session_state["username"], "Würfeln", bet, win, f"Glückwunsch! Du gewinnst {win} Punkte.")
                else:
                    play_result(st.session_state["username"], "Würfeln", bet, -bet, f"Schade — du verlierst {bet} Punkte.")

elif page == "Münzwurf":
    st.header("🪙 Münzwurf")
    st.markdown("Wette auf Kopf oder Zahl. Treffer: 2× Einsatz.")
    with st.form("coin_form"):
        bet = st.number_input("Einsatz", min_value=1, value=10, step=1, key="coin_bet")
        choice = st.radio("Wähle", ["Kopf", "Zahl"])
        submitted = st.form_submit_button("Werfen")
    if submitted:
        if not st.session_state.get("username"):
            st.error("Bitte zuerst einloggen.")
        else:
            if bet > cur_points:
                st.error("Nicht genug Punkte.")
            else:
                flip = random.choice(["Kopf","Zahl"])
                st.info(f"Ergebnis: **{flip}**")
                if flip == choice:
                    win = bet * 2
                    play_result(st.session_state["username"], "Münzwurf", bet, win, f"Treffer! Du gewinnst {win} Punkte.")
                else:
                    play_result(st.session_state["username"], "Münzwurf", bet, -bet, f"Verloren — {bet} Punkte weg.")

elif page == "Slotmaschine":
    st.header("🎰 Slotmaschine")
    st.markdown("Drehe 3 Symbole. Dreier-Kombos bringen hohe Gewinne.")
    symbols = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
    with st.form("slot_form"):
        bet = st.number_input("Einsatz", min_value=1, value=20, step=1, key="slot_bet")
        submitted = st.form_submit_button("Drehen")
    if submitted:
        if not st.session_state.get("username"):
            st.error("Bitte zuerst einloggen.")
        else:
            if bet > cur_points:
                st.error("Nicht genug Punkte.")
            else:
                reels = [random.choice(symbols) for _ in range(3)]
                st.markdown("### " + " | ".join(reels))
                # simple payout rules
                if reels[0] == reels[1] == reels[2]:
                    mult = {"🍒":10, "🍋":5, "🔔":8, "⭐":12, "7️⃣":25}[reels[0]]
                    win = bet * mult
                    play_result(st.session_state["username"], "Slotmaschine", bet, win, f"Jackpot! {reels[0]} x3 — Du gewinnst {win} Punkte.")
                elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
                    win = bet * 2
                    play_result(st.session_state["username"], "Slotmaschine", bet, win, f"Zweite Reihe! Du gewinnst {win} Punkte.")
                else:
                    play_result(st.session_state["username"], "Slotmaschine", bet, -bet, f"Kein Glück — du verlierst {bet} Punkte.")

elif page == "Bombenzahl":
    st.header("💣 Bombenzahl (Zahlenraten)")
    st.markdown("Rate die Zufallszahl zwischen 1 und 20. Richtige Zahl -> hoher Gewinn. Falsche Zahl -> Einsatz weg.")
    with st.form("bomb_form"):
        bet = st.number_input("Einsatz", min_value=1, value=15, step=1, key="bomb_bet")
        guess = st.slider("Dein Tipp", 1, 20, 10)
        submitted = st.form_submit_button("Raten")
    if submitted:
        if not st.session_state.get("username"):
            st.error("Bitte zuerst einloggen.")
        else:
            if bet > cur_points:
                st.error("Nicht genug Punkte.")
            else:
                secret = random.randint(1,20)
                st.info(f"Die geheime Zahl ist **{secret}**")
                if guess == secret:
                    win = bet * 10
                    play_result(st.session_state["username"], "Bombenzahl", bet, win, f"Treffer! Du gewinnst {win} Punkte.")
                else:
                    # close guess bonus
                    if abs(guess - secret) <= 2:
                        partial = int(bet * 0.5)
                        play_result(st.session_state["username"], "Bombenzahl", bet, -bet + partial, f"Knapp vorbei! Du bekommst {partial} zurück.")
                    else:
                        play_result(st.session_state["username"], "Bombenzahl", bet, -bet, f"Falsch — du verlierst {bet} Punkte.")

elif page == "Greifautomat":
    st.header("🕹️ Greifautomat (Glücksgriff)")
    st.markdown("Versuche dein Glück: verschiedene Preise mit unterschiedlichen Wahrscheinlichkeiten.")
    prizes = [
        ("Nichts", 0, 0.5),
        ("Kleiner Preis", 50, 0.3),
        ("Mittlerer Preis", 150, 0.15),
        ("Großer Preis", 500, 0.045),
        ("Super-Jackpot", 2000, 0.005)
    ]
    with st.form("claw_form"):
        bet = st.number_input("Einsatz", min_value=1, value=25, step=1, key="claw_bet")
        submitted = st.form_submit_button("Greifen")
    if submitted:
        if not st.session_state.get("username"):
            st.error("Bitte zuerst einloggen.")
        else:
            if bet > cur_points:
                st.error("Nicht genug Punkte.")
            else:
                r = random.random()
                cum = 0.0
                result = None
                for name, value, prob in prizes:
                    cum += prob
                    if r <= cum:
                        result = (name, value)
                        break
                if result is None:
                    result = ("Nichts", 0)
                name, value = result
                # payout: prize value minus bet (so you always risk bet)
                delta = value - bet
                record_play(st.session_state["username"], "Greifautomat", bet, delta)
                update_points(st.session_state["username"], delta)
                if value > 0:
                    st.success(f"Gewonnen: {name} — Netto {delta} Punkte.")
                    st.balloons()
                else:
                    st.info(f"Nichts gewonnen — du verlierst {bet} Punkte.")

elif page == "Leaderboard":
    st.header("🏆 Leaderboard")
    rows = top_leaderboard(10)
    if rows:
        st.table([{"Platz": i+1, "Spieler": r[0], "Punkte": r[1]} for i,r in enumerate(rows)])
    else:
        st.info("Noch keine Spieler.")

elif page == "Statistiken":
    st.header("📊 Statistiken")
    st.markdown("Letzte Spielzüge (letzte 10)")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, game, bet, delta, timestamp FROM plays ORDER BY id DESC LIMIT 10")
    recent = c.fetchall()
    conn.close()
    if recent:
        for row in recent:
            st.write(f"{row[4][:19]} — **{row[0]}** spielte *{row[1]}* (Einsatz {row[2]}) → Delta {row[3]}")
    else:
        st.info("Noch keine Spielzüge.")

# ---------- Footer ----------
st.sidebar.markdown("---")
st.sidebar.markdown("Kleine Hinweise:")
st.sidebar.markdown("- Lokal gespeichert (sqlite `casino.db`).\n- Backup: `cp casino.db casino_backup.db`")
