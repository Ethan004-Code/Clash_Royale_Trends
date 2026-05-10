from flask import Flask, render_template
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
from collections import Counter
import os

app = Flask(__name__)

# *Helper function to parse list strings from CSV*
def parse_list(x):
    x = str(x).strip("[]")  # Ensure it's a string
    if x == "":  # Empty string
        return []
    return [int(i.strip()) for i in x.split(",")]  # Build a list of integers

@app.route("/")
def home():
    try:
       
        # Necessary imports to run visualizations and pandas analysis
        # Data is loaded from CSV files

        # LOAD DATA
        df = pd.read_csv("Data/battle_data.csv")
        print(f"Loaded {len(df)} rows from battle_data.csv")  # Debug: show data size

        # Create mapping from card IDs to names
        id_to_name = {}
        with open("Data/cards_info.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                card_id = int(row[0])
                name = row[1]
                id_to_name[card_id] = name

        print(f"Loaded {len(id_to_name)} card mappings")  # Debug: show mappings

        # CLEAN DATA
        # Remove header rows that might be duplicated
        df = df[df["player1 win"] != "player1 win"]
        df = df[df["player2 win"] != "player2 win"]
        print(f"After cleaning: {len(df)} rows")  # Debug: show cleaned data size

        # *Top Used decks analysis*
        # Initialize counters for deck usage and wins
        deck_counter = Counter()
        deck_wins = Counter()
        deck_display_lookup = {}  # Dictionary for deck names and labels

        rows = df.to_dict("records")

        for row in rows:
            for player in ["player1", "player2"]:
                # Parse the three types of cards: Evo, Champions, Normal
                evo = parse_list(row.get(f"{player} evo", ""))
                champions = parse_list(row.get(f"{player} hero/champion", ""))
                normal_cards = parse_list(row.get(f"{player} normal", ""))

                # Order: First two Evo, third Champion, rest Normal
                ordered_deck = evo + champions + normal_cards

                if len(ordered_deck) == 0:
                    continue

                # Use sorted tuple as key to count identical decks regardless of order
                deck_key = tuple(sorted(ordered_deck))

                deck_counter[deck_key] += 1

                # Count wins for this deck
                if str(row.get(f"{player} win", "")).lower() == "true":
                    deck_wins[deck_key] += 1

                # Create labeled deck for display
                labeled_deck = []
                for idx, card_id in enumerate(ordered_deck):
                    name = id_to_name.get(int(card_id), str(card_id))

                    if idx < 2:
                        labeled_deck.append(f"{name} (Evo)")
                    elif idx == 2:
                        labeled_deck.append(f"{name} (Champion)")
                    else:
                        labeled_deck.append(name)

                # Store the display version if not already present
                if deck_key not in deck_display_lookup:
                    deck_display_lookup[deck_key] = labeled_deck

        print(f"Found {len(deck_counter)} unique decks")  # Debug: show unique decks

        # BUILD TABLE
        # Get top 10 most common decks
        table_data = []
        for i, (deck, count) in enumerate(deck_counter.most_common(10), start=1):
            wins = deck_wins[deck]
            losses = count - wins
            win_rate = (wins / count) * 100 if count > 0 else 0

            table_data.append({
                "Deck": f"Deck {i}",
                "Cards": ", ".join(deck_display_lookup.get(deck, [])),
                "Total Games": count,
                "Wins": wins,
                "Losses": losses,
                "Win Rate": f"{win_rate:.1f}%"
            })

        if len(table_data) == 0:
            return "No data found. Check your CSV files."

        df_table = pd.DataFrame(table_data)
        print(f"Top decks table created with {len(df_table)} entries")  # Debug: show table size

        # CREATE STATIC FOLDER
        os.makedirs("static", exist_ok=True)

        # --- BAR CHART ---
        # Create wins vs losses bar chart
        x = np.arange(len(df_table))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar(x - width / 2, df_table["Wins"], width, label="Wins")
        plt.bar(x + width / 2, df_table["Losses"], width, label="Losses")
        plt.xticks(x, df_table["Deck"])
        plt.xlabel("DECKS")
        plt.ylabel("MATCHES")
        plt.title("Wins vs Losses for Top Decks")
        plt.legend()
        plt.tight_layout()
        plt.savefig("static/wins_losses_chart.png")
        plt.close()
        print("Bar chart saved as wins_losses_chart.png")  # Debug: confirm chart saved

        # --- PIE CHARTS ---
        # Create individual pie charts for each deck
        fig, axes = plt.subplots(2, 5, figsize=(18, 8))

        for i, ax in enumerate(axes.flatten()):
            if i >= len(df_table):
                ax.axis("off")
                continue

            wins = df_table.iloc[i]["Wins"]
            losses = df_table.iloc[i]["Losses"]

            ax.pie([wins, losses], labels=["W", "L"], autopct="%1.1f%%")
            ax.set_title(df_table.iloc[i]["Deck"])

        plt.tight_layout()
        plt.savefig("static/pie_charts.png")
        plt.close()
        print("Pie charts saved as pie_charts.png")  # Debug: confirm charts saved

        # KEY METRICS
        # Find deck with highest win rate
        highest_idx = df_table["Win Rate"].str.replace("%", "").astype(float).idxmax()

        # Load custom insights from file
        insights = []
        try:
            with open("insights.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        insights.append(line)
        except FileNotFoundError:
            insights = ["insights.txt not found. Add your notes there."]

        # Render the template with all data
        return render_template(
            "index.html",
            title="Clash Royale Deck Analysis",
            total_matches=len(df),
            most_used_card=df_table.iloc[0]["Deck"],
            highest_winrate=df_table.loc[highest_idx, "Win Rate"],
            plot_url="wins_losses_chart.png",
            pie_url="pie_charts.png",
            decks=table_data,
            insights=insights
        )

    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)