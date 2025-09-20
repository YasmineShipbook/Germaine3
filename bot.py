import discord
from discord.ext import commands, tasks
from meteofrance_api import MeteoFranceClient
from datetime import datetime
import os

# === CONFIGURATION ===
TOKEN = os.environ["TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
LAT, LON = 48.8566, 2.3522
CITY_NAME = "Jarlaheim"

# === INTENTS ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Fonction météo avec embed par jour et conseils uniques ===
def get_week_weather_embeds(lat=LAT, lon=LON, city_name=CITY_NAME):
    client = MeteoFranceClient()
    forecast = client.get_forecast(lat, lon)
    daily = forecast.daily_forecast

    jours_fr = {
        "Mon": "Lun",
        "Tue": "Mar",
        "Wed": "Mer",
        "Thu": "Jeu",
        "Fri": "Ven",
        "Sat": "Sam",
        "Sun": "Dim"
    }

    emojis = {
        "Soleil": "☀️",
        "Eclaircies": "🌤️",
        "Nuageux": "☁️",
        "Très nuageux": "🌥️",
        "Pluie": "🌧️",
        "Pluie faible": "🌦️",
        "Pluies éparses": "🌦️",
        "Averses": "🌧️",
        "Orages": "⛈️",
        "Neige": "❄️",
        "Brouillard": "🌫️"
    }

    couleurs = {
        "Soleil": 0xFFD700,
        "Eclaircies": 0xFFFACD,
        "Nuageux": 0xC0C0C0,
        "Très nuageux": 0xA9A9A9,
        "Pluie": 0x1E90FF,
        "Pluie faible": 0x87CEFA,
        "Pluies éparses": 0x87CEFA,
        "Averses": 0x1E90FF,
        "Orages": 0x8A2BE2,
        "Neige": 0xADD8E6,
        "Brouillard": 0x696969
    }

    embeds = []
    conseils = set()  # Set pour éviter les doublons

    for day in daily[:7]:
        dt = datetime.fromtimestamp(day["dt"])
        day_eng = dt.strftime("%a")
        day_fr = jours_fr[day_eng]
        date_str = f"{day_fr} {dt.strftime('%d/%m')}"

        tmin = day["T"]["min"]
        tmax = day["T"]["max"]
        desc = day["weather12H"]["desc"]
        emoji = emojis.get(desc, "🌍")
        couleur = couleurs.get(desc, 0x1E90FF)

        # Ajouter conseils uniques
        if "Pluie" in desc or "Averses" in desc:
            conseils.add("🌂 N'oubliez pas votre parapluie !")
        elif "Soleil" in desc:
            conseils.add("😎 Profitez du soleil !")

        # Embed individuel pour chaque jour
        embed = discord.Embed(
            title=f"{date_str} - {city_name}",
            description=f"{emoji} {desc}\nTempératures: {tmin:.1f}°C → {tmax:.1f}°C",
            color=couleur
        )
        embeds.append(embed)

    # Embed final pour les conseils si non vide
    if conseils:
        embed_conseils = discord.Embed(
            title="Conseils météo 🌦️",
            description="\n".join(conseils),
            color=0xFFD700
        )
        embeds.append(embed_conseils)

    return embeds

# === Tâche automatique dimanche 20h ===
@tasks.loop(hours=1)
async def weekly_weather():
    now = datetime.now()
    if now.weekday() == 6 and now.hour == 20:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embeds = get_week_weather_embeds(lat=LAT, lon=LON, city_name=CITY_NAME)
            for embed in embeds:
                await channel.send(embed=embed)

# === Événement quand le bot démarre ===
@bot.event
async def on_ready():
    print(f"{bot.user} est connecté ✅")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot météo Météo-France activé !")
    weekly_weather.start()

# === Commande manuelle ===
@bot.command()
async def meteo(ctx):
    embeds = get_week_weather_embeds(lat=LAT, lon=LON, city_name=CITY_NAME)
    for embed in embeds:
        await ctx.send(embed=embed)

# === Lancement du bot ===
bot.run(TOKEN)
