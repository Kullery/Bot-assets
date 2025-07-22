import discord
from discord.ext import commands
import asyncio
import json
import random
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
load_dotenv("secrets.env")  # Charge les variables depuis secrets.env

# Configuration des raretés
# Configuration des raretés
class HeroRarity(Enum):
    COMMUN = ("vert", "🟢", 1, "Commun")
    RARE = ("bleu", "🔵", 2, "Rare")
    EPIQUE = ("violet", "🟣", 3, "Epique")
    LEGENDAIRE = ("or", "🟡", 4, "Légendaire")

    def __init__(self, color, emoji, rank, display_name):
        self._color = color
        self._emoji = emoji
        self._rank = rank
        self._display_name = display_name

    @property
    def color(self):
        return self._color

    @property
    def emoji(self):
        return self._emoji

    @property
    def rank(self):
        return self._rank

    @property
    def display_name(self):
        return self._display_name

class ItemRarity(Enum):
    COMMUN = ("gris", "⚪", 1, "Commun")
    RARE = ("bleu", "🔵", 2, "Rare")
    EPIQUE = ("violet", "🟣", 3, "Epique")
    LEGENDAIRE = ("or", "🟡", 4, "Legendaire")
    MYTHIQUE = ("rose", "🩷", 5, "Mythique")
    DIVIN = ("rouge", "🔴", 6, "Divin")
    SUPREME = ("orange", "🟠", 7, "Suprême")

    def __init__(self, color, emoji, rank, display_name):
        self._color = color
        self._emoji = emoji
        self._rank = rank
        self._display_name = display_name

    @property
    def color(self):
        return self._color

    @property
    def emoji(self):
        return self._emoji

    @property
    def rank(self):
        return self._rank

    @property
    def display_name(self):
        return self._display_name

class HeroClass(Enum):
    GLADIATEUR = "Gladiateur"
    MAGE = "Mage"
    VOLEUR = "Voleur"
    PALADIN = "Paladin"
    SAGE = "Sage"
    GENERAL = "Général"
    NECROMANCIEN = "Nécromancien"
    MAITRE_MECA = "Maître Méca"


class EquipSlot(Enum):
    EPEE = "épée"
    CASQUE = "casque"
    ARMURE = "armure"
    CAPE = "cape"
    LIVRE = "livre"
    SCEPTRE = "sceptre"
    BABIOLE = "babiole"
    ROBE = "robe"
    BOUCLIER = "bouclier"
    ARC = "arc"
    
# Définition des emplacements d'équipement par classe
EQUIPMENT_SLOTS_BY_CLASS = {
    HeroClass.GLADIATEUR: ["épée", "épée", "casque", "armure", "babiole", "babiole"],
    HeroClass.MAGE: ["sceptre", "cape", "casque", "robe", "babiole", "robe"],
    HeroClass.VOLEUR: ["épée", "arc", "casque", "armure", "babiole", "babiole"],
    HeroClass.PALADIN: ["épée", "bouclier", "casque", "armure", "babiole", "babiole"],
    HeroClass.SAGE: ["sceptre", "livre", "casque", "robe", "babiole", "babiole"],
    HeroClass.GENERAL: ["épée", "bannière", "casque", "armure", "babiole", "babiole"],
    HeroClass.NECROMANCIEN: ["sceptre", "cape", "casque", "robe", "livre", "babiole"],
    HeroClass.MAITRE_MECA: ["épée", "épée", "casque", "armure", "babiole", "babiole"]
}



@dataclass
class Hero:
    id: int
    name: str
    rarity: HeroRarity
    hero_class: HeroClass
    image: str
    price: int
    description: str = ""
    equipped_items: List[int] = None
    
    def __post_init__(self):
        if self.equipped_items is None:
            self.equipped_items = []

@dataclass
class Item:
    id: int
    name: str
    rarity: ItemRarity
    compatible_classes: List[HeroClass]
    price: int
    image: str
    stats: Dict[str, int]
    description: str = ""

@dataclass
class PlayerData:
    user_id: int
    gold: int = 1000  # or de départ
    emblems: int = 0   # emblèmes de départ
    heroes: List[int] = None
    items: List[int] = None

    def __post_init__(self):
        if self.heroes is None:
            self.heroes = []
        if self.items is None:
            self.items = []

class HeroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Base de données en mémoire (tu peux remplacer par une vraie DB)
        self.heroes_db: Dict[int, Hero] = {}
        self.items_db: Dict[int, Item] = {}
        self.players: Dict[int, PlayerData] = {}
        
        # Charger les données depuis des fichiers JSON
        self.load_data()
    
    def load_data(self):
        """Charge les données depuis des fichiers JSON"""
        # Mapping pour les noms de classes avec accents
        class_mapping = {
            'GÉNÉRAL': 'GENERAL',
            'GLADIATEUR': 'GLADIATEUR',
            'MAGE': 'MAGE',
            'VOLEUR': 'VOLEUR',
            'PALADIN': 'PALADIN',
            'SAGE': 'SAGE',
            'NÉCROMANCIEN': 'NECROMANCIEN',
            'MAÎTRE MÉCA': 'MAITRE_MECA'
        }
        
        try:
            with open('heroes.json', 'r', encoding='utf-8') as f:
                heroes_data = json.load(f)
                for hero_data in heroes_data:
                    # Convertir la string en enum par le nom
                    rarity_name = hero_data['rarity'].upper()
                    hero_rarity = HeroRarity[rarity_name]
                    
                    # Gérer les noms de classes avec accents
                    hero_class_name = hero_data['hero_class'].upper()
                    if hero_class_name in class_mapping:
                        hero_class_name = class_mapping[hero_class_name]
                    hero_class = HeroClass[hero_class_name]
                    
                    hero = Hero(
                        id=hero_data['id'],
                        name=hero_data['name'],
                        rarity=hero_rarity,
                        hero_class=hero_class,
                        image=hero_data['image'],
                        price=hero_data['price'],
                        description=hero_data.get('description', ''),
                        equipped_items=hero_data.get('equipped_items', [])
                    )
                    self.heroes_db[hero.id] = hero
        except FileNotFoundError:
            print("Fichier heroes.json non trouvé")
        except KeyError as e:
            print(f"Erreur de clé dans heroes.json: {e}")
        except Exception as e:
            print(f"Erreur lors du chargement des héros: {e}")
        
        try:
            with open('items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                # Vérifier si items_data est une liste
                if isinstance(items_data, list):
                    for item_data in items_data:
                        # Convertir la string en enum par le nom
                        rarity_name = item_data['rarity'].upper()
                        item_rarity = ItemRarity[rarity_name]
                        
                        # Convertir les classes compatibles
                        compatible_classes = []
                        for class_name in item_data['compatible_classes']:
                            class_name_upper = class_name.upper()
                            if class_name_upper in class_mapping:
                                class_name_upper = class_mapping[class_name_upper]
                            class_enum = HeroClass[class_name_upper]
                            compatible_classes.append(class_enum)
                        
                        item = Item(
                            id=item_data['id'],
                            name=item_data['name'],
                            rarity=item_rarity,
                            compatible_classes=compatible_classes,
                            image=item_data['image'],
                            price=item_data['price'],
                            stats=item_data['stats'],
                            description=item_data.get('description', '')
                        )
                        self.items_db[item.id] = item
        except FileNotFoundError:
            print("Fichier items.json non trouvé")
        except KeyError as e:
            print(f"Erreur de clé dans items.json: {e}")
        except Exception as e:
            print(f"Erreur lors du chargement des items: {e}")
        
        try:
            with open('players.json', 'r', encoding='utf-8') as f:
                players_data = json.load(f)
                for player_data in players_data:
                    player = PlayerData(
                        user_id=player_data['user_id'],
                        gold=player_data['gold'],
                        heroes=player_data['heroes'],
                        items=player_data['items']
                    )
                    self.players[player.user_id] = player
        except FileNotFoundError:
            print("Fichier players.json non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement des joueurs: {e}")
    
    def save_data(self):
        players_data = []
        for player in self.players.values():
            player_dict = asdict(player)
            # Convertir les objets HeroLevel en dictionnaires
            hero_levels_dict = {}
            for hero_id, level_obj in player.hero_levels.items():
                hero_levels_dict[str(hero_id)] = asdict(level_obj)
            player_dict['hero_levels'] = hero_levels_dict
            players_data.append(player_dict)
        
        with open('players.json', 'w', encoding='utf-8') as f:
            json.dump(players_data, f, indent=2, ensure_ascii=False)
    
    def get_player(self, user_id: int) -> PlayerData:
        """Récupère ou crée un joueur"""
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
        return self.players[user_id]
    
    def get_player(self, user_id: int) -> PlayerData:
        """Récupère ou crée un joueur"""
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
        return self.players[user_id]
    
@dataclass
class ChestType:
    name: str
    rarity_distribution: Dict[str, int]
    loot_amount: int
    image: str
    description: str
    price: int = 0  # Prix d'achat du coffre

@dataclass
class LootResult:
    items: List[int] = field(default_factory=list)
    gold: int = 0
    triumph_emblems: int = 0

@dataclass
class HeroLevel:
    level: int = 1
    experience: int = 0
    max_experience: int = 100
    
    def add_experience(self, amount: int) -> bool:
        """Ajoute de l'expérience et retourne True si level up"""
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.max_experience:
            self.experience -= self.max_experience
            self.level += 1
            self.max_experience = int(self.max_experience * 1.5)  # Augmente les requis d'XP
            leveled_up = True
        
        return leveled_up    

bot = HeroBot()

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté !')

@bot.command(name='niveau_heros')
async def hero_level_info(ctx, hero_id: int = None):
    """Affiche les niveaux des héros"""
    player = bot.get_player(ctx.author.id)
    
    if hero_id:
        # Afficher un héros spécifique
        if hero_id not in player.heroes:
            await ctx.send("❌ Vous ne possédez pas ce héros!")
            return
        
        if hero_id not in player.hero_levels:
            player.hero_levels[hero_id] = HeroLevel()
        
        hero = bot.heroes_db[hero_id]
        hero_level = player.hero_levels[hero_id]
        
        embed = discord.Embed(
            title=f"📊 Niveau de {hero.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=hero.image)
        embed.add_field(name="Niveau", value=hero_level.level, inline=True)
        embed.add_field(name="Expérience", value=f"{hero_level.experience}/{hero_level.max_experience}", inline=True)
        embed.add_field(name="Classe", value=hero.hero_class.value, inline=True)
        
        # Barre de progression
        progress = hero_level.experience / hero_level.max_experience
        bar_length = 20
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        embed.add_field(
            name="Progression",
            value=f"`{bar}` {progress*100:.1f}%",
            inline=False
        )
        
    else:
        # Afficher tous les héros
        embed = discord.Embed(
            title=f"📊 Niveaux des héros de {ctx.author.display_name}",
            color=discord.Color.blue()
        )
        
        if not player.heroes:
            embed.description = "Aucun héros possédé"
        else:
            for hero_id in player.heroes:
                hero = bot.heroes_db[hero_id]
                if hero_id not in player.hero_levels:
                    player.hero_levels[hero_id] = HeroLevel()
                
                hero_level = player.hero_levels[hero_id]
                
                embed.add_field(
                    name=f"{hero.rarity.emoji} {hero.name}",
                    value=f"Niveau {hero_level.level}\nXP: {hero_level.experience}/{hero_level.max_experience}",
                    inline=True
                )
    
    await ctx.send(embed=embed)

@bot.command(name='ouvrir_coffre')
async def open_chest(ctx, *, chest_name: str):
    """Ouvre un coffre avec animation"""
    player = bot.get_player(ctx.author.id)
    
    # Vérifier si le joueur a ce coffre
    if chest_name not in player.chests:
        await ctx.send("❌ Vous ne possédez pas ce coffre!")
        return
    
    # Trouver le coffre dans la base de données
    chest = bot.chests_db.get(chest_name)
    if not chest:
        await ctx.send("❌ Coffre introuvable dans la base de données!")
        return
    
    # Retirer le coffre de l'inventaire
    player.chests.remove(chest_name)
    
    # Animation d'ouverture
    embed = discord.Embed(
        title="📦 Ouverture du coffre...",
        description="🔓 Le coffre commence à s'ouvrir...",
        color=discord.Color.orange()
    )
    embed.set_image(url=chest.image)
    
    message = await ctx.send(embed=embed)
    
    # Étapes d'animation
    animations = [
        ("✨ Le coffre brille de mille feux...", discord.Color.yellow()),
        ("💫 Des particules magiques s'échappent...", discord.Color.purple()),
        ("🎆 Le coffre s'ouvre complètement!", discord.Color.gold()),
    ]
    
    for description, color in animations:
        await asyncio.sleep(1.5)
        embed.description = description
        embed.color = color
        await message.edit(embed=embed)
    
    # Générer le loot
    loot = bot.generate_loot(chest)
    
    # Ajouter le loot au joueur
    player.gold += loot.gold
    player.triumph_emblems += loot.triumph_emblems
    player.items.extend(loot.items)
    
    # Affichage des récompenses
    await asyncio.sleep(1)
    
    embed = discord.Embed(
        title="🎁 Récompenses obtenues!",
        description=f"Vous avez ouvert **{chest.name}**",
        color=discord.Color.green()
    )
    
    if loot.gold > 0:
        embed.add_field(name="💰 Pièces", value=f"+{loot.gold}", inline=True)
    
    if loot.triumph_emblems > 0:
        embed.add_field(name="🏆 Emblèmes du Triomphe", value=f"+{loot.triumph_emblems}", inline=True)
    
    if loot.items:
        items_text = []
        for item_id in loot.items:
            item = bot.items_db[item_id]
            items_text.append(f"{item.rarity.emoji} {item.name}")
        
        embed.add_field(
            name="🎒 Items obtenus",
            value="\n".join(items_text),
            inline=False
        )
    
    bot.save_data()
    await message.edit(embed=embed)
    
    embed = discord.Embed(
        title="✅ Coffre acheté!",
        description=f"Vous avez acheté **{chest.name}** pour {chest.price} 💰\nUtilisez `!ouvrir_coffre {chest.name}` pour l'ouvrir!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='mes_coffres')
async def my_chests(ctx):
    """Affiche les coffres du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.chests:
        await ctx.send("❌ Vous n'avez aucun coffre!")
        return
    
    # Compter les coffres par type
    chest_counts = {}
    for chest_name in player.chests:
        chest_counts[chest_name] = chest_counts.get(chest_name, 0) + 1
    
    embed = discord.Embed(
        title=f"📦 Coffres de {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    for chest_name, count in chest_counts.items():
        embed.add_field(
            name=f"📦 {chest_name}",
            value=f"Quantité: {count}",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='profil')
async def profile(ctx):
    """Affiche le profil du joueur"""
    player = bot.get_player(ctx.author.id)
    
    embed = discord.Embed(
        title=f"Profil de {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 Pièces", value=player.gold, inline=True)
    embed.add_field(name="🏆 Emblèmes du Triomphe", value=player.triumph_emblems, inline=True)
    embed.add_field(name="👥 Héros", value=len(player.heroes), inline=True)
    embed.add_field(name="🎒 Items", value=len(player.items), inline=True)
    embed.add_field(name="📦 Coffres", value=len(player.chests), inline=True)
    
    # Niveau moyen des héros
    if player.heroes and player.hero_levels:
        total_level = sum(player.hero_levels.get(h_id, HeroLevel()).level for h_id in player.heroes)
        avg_level = total_level / len(player.heroes)
        embed.add_field(name="📊 Niveau moyen", value=f"{avg_level:.1f}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='acheter')
async def buy(ctx, item_type: str, item_id: int):
    """Achète un héros ou un item"""
    player = bot.get_player(ctx.author.id)
    
    if item_type.lower() == "hero":
        if item_id not in bot.heroes_db:
            await ctx.send("❌ Héros introuvable!")
            return
        
        hero = bot.heroes_db[item_id]
        
        if item_id in player.heroes:
            await ctx.send("❌ Vous possédez déjà ce héros!")
            return
        
        if player.gold < hero.price:
            await ctx.send(f"❌ Pas assez de pièces! Il vous faut {hero.price} pièces.")
            return
        
        player.gold -= hero.price
        player.heroes.append(item_id)
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Achat réussi!",
            description=f"Vous avez acheté {hero.rarity.emoji} **{hero.name}** pour {hero.price} 💰",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    elif item_type.lower() == "item":
        if item_id not in bot.items_db:
            await ctx.send("❌ Item introuvable!")
            return
        
        item = bot.items_db[item_id]
        
        if player.gold < item.price:
            await ctx.send(f"❌ Pas assez de pièces! Il vous faut {item.price} pièces.")
            return
        
        player.gold -= item.price
        player.items.append(item_id)
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Achat réussi!",
            description=f"Vous avez acheté {item.rarity.emoji} **{item.name}** pour {item.price} 💰",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    else:
        await ctx.send("❌ Type invalide. Utilisez `hero` ou `item`")

@bot.command(name='mes_heroes')
async def my_heroes(ctx):
    """Affiche les héros du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.heroes:
        await ctx.send("❌ Vous n'avez aucun héros!")
        return
    
    embed = discord.Embed(
        title=f"👥 Héros de {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    for hero_id in player.heroes:
        hero = bot.heroes_db[hero_id]
        equipped_count = len(hero.equipped_items)
        
        embed.add_field(
            name=f"{hero.rarity.emoji} {hero.name}",
            value=f"Classe: {hero.hero_class.value}\nÉquipement: {equipped_count}/6",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='mes_items')
async def my_items(ctx):
    """Affiche les items du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.items:
        await ctx.send("❌ Vous n'avez aucun item!")
        return
    
    embed = discord.Embed(
        title=f"🎒 Items de {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    for item_id in player.items:
        item = bot.items_db[item_id]
        classes_str = ", ".join([c.value for c in item.compatible_classes])
        stats_str = ", ".join([f"{k}: +{v}" for k, v in item.stats.items()])
        
        embed.add_field(
            name=f"{item.rarity.emoji} {item.name}",
            value=f"Classes: {classes_str}\nStats: {stats_str}",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='équiper')
async def equip_item(ctx, hero_id: int, item_id: int):
    """Équipe un item sur un héros"""
    player = bot.get_player(ctx.author.id)
    
    # Vérifications
    if hero_id not in player.heroes:
        await ctx.send("❌ Vous ne possédez pas ce héros!")
        return
    
    if item_id not in player.items:
        await ctx.send("❌ Vous ne possédez pas cet item!")
        return
    
    hero = bot.heroes_db[hero_id]
    item = bot.items_db[item_id]
    
    # Vérifier la compatibilité de classe
    if hero.hero_class not in item.compatible_classes:
        await ctx.send(f"❌ Cet item n'est pas compatible avec la classe {hero.hero_class.value}!")
        return
    
    # Vérifier si l'item est déjà équipé
    if item_id in hero.equipped_items:
        await ctx.send("❌ Cet item est déjà équipé sur ce héros!")
        return
    
    # Vérifier la limite d'équipement
    if len(hero.equipped_items) >= 6:
        await ctx.send("❌ Ce héros a déjà 6 items équipés!")
        return
    
    # Équiper l'item
    hero.equipped_items.append(item_id)
    bot.save_data()
    
    embed = discord.Embed(
        title="✅ Item équipé!",
        description=f"{item.rarity.emoji} **{item.name}** équipé sur {hero.rarity.emoji} **{hero.name}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='déséquiper')
async def unequip_item(ctx, hero_id: int, item_id: int):
    """Déséquipe un item d'un héros"""
    player = bot.get_player(ctx.author.id)
    
    if hero_id not in player.heroes:
        await ctx.send("❌ Vous ne possédez pas ce héros!")
        return
    
    hero = bot.heroes_db[hero_id]
    
    if item_id not in hero.equipped_items:
        await ctx.send("❌ Cet item n'est pas équipé sur ce héros!")
        return
    
    # Déséquiper l'item
    hero.equipped_items.remove(item_id)
    bot.save_data()
    
    item = bot.items_db[item_id]
    embed = discord.Embed(
        title="✅ Item déséquipé!",
        description=f"{item.rarity.emoji} **{item.name}** déséquipé de {hero.rarity.emoji} **{hero.name}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='détails')
async def hero_details(ctx, hero_id: int):
    """Affiche les détails d'un héros"""
    player = bot.get_player(ctx.author.id)
    
    if hero_id not in player.heroes:
        await ctx.send("❌ Vous ne possédez pas ce héros.")
        return
    
    hero = bot.heroes_db[hero_id]
    
    embed = discord.Embed(
        title=f"{hero.rarity.emoji} {hero.name}",
        description=hero.description,
        color=discord.Color.blue()
    )
    embed.set_image(url=hero.image)
    embed.add_field(name="Classe", value=hero.hero_class.value, inline=True)
    embed.add_field(name="Rareté", value=hero.rarity.name, inline=True)
    embed.add_field(name="Items équipés", value=f"{len(hero.equipped_items)}/6", inline=True)
    
    if hero.equipped_items:
        items_list = []
        for item_id in hero.equipped_items:
            item = bot.items_db[item_id]
            items_list.append(f"{item.rarity.emoji} {item.name}")
        
        embed.add_field(
            name="Équipement",
            value="\n".join(items_list),
            inline=False
        )
    
    await ctx.send(embed=embed)

from discord.ext import commands
from discord.ui import View, Select, Button
from datetime import datetime, timedelta
import discord, random, json

bot = commands.Bot(command_prefix="!")

ITEMS_DU_JOUR = []
DERNIERE_MAJ_ITEMS = None

def maj_items_du_jour():
    global ITEMS_DU_JOUR, DERNIERE_MAJ_ITEMS
    if DERNIERE_MAJ_ITEMS is None or datetime.utcnow() - DERNIERE_MAJ_ITEMS > timedelta(hours=24):
        ITEMS_DU_JOUR = random.sample(list(bot.items_db.values()), k=5)
        DERNIERE_MAJ_ITEMS = datetime.utcnow()

class BoutiqueView(View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.add_item(BoutiqueDropdown(self))

class BoutiqueDropdown(Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="🦸 Héros", value="heros"),
            discord.SelectOption(label="🎁 Coffres", value="coffres"),
            discord.SelectOption(label="🛡️ Items du jour", value="items")
        ]
        super().__init__(placeholder="Choisissez une catégorie", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.user:
            return await interaction.response.send_message("❌ Ce menu n'est pas pour toi.", ephemeral=True)

        maj_items_du_jour()
        selection = self.values[0]

        embed = discord.Embed(color=discord.Color.teal())
        self.parent_view.clear_items()
        self.parent_view.add_item(self)

        if selection == "heros":
            embed.title = "🦸 Héros disponibles"
            for hero in bot.heroes_db.values():
                embed.add_field(name=f"{hero.name}", value=f"Prix : {hero.price} 🏅", inline=False)
                self.parent_view.add_item(AcheterHeroButton(hero))

        elif selection == "coffres":
            with open("chests.json", "r", encoding="utf-8") as f:
                coffres = json.load(f)
            embed.title = "🎁 Coffres disponibles"
            for coffre in coffres:
                embed.add_field(name=coffre["name"], value=f"Prix : 300 🪙", inline=False)
                self.parent_view.add_item(AcheterCoffreButton(coffre))

        elif selection == "items":
            embed.title = "🛡️ Items du jour"
            for item in ITEMS_DU_JOUR:
                embed.add_field(name=item.name, value=f"{item.rarity.emoji} - {item.price} 🪙", inline=False)
                self.parent_view.add_item(AcheterItemButton(item))

        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class AcheterHeroButton(Button):
    def __init__(self, hero):
        super().__init__(label=f"Acheter {hero.name}", style=discord.ButtonStyle.primary)
        self.hero = hero

    async def callback(self, interaction: discord.Interaction):
        player = bot.get_player(interaction.user.id)
        if player.emblems < self.hero.price:
            return await interaction.response.send_message("❌ Pas assez d'emblèmes.", ephemeral=True)
        if self.hero.id in player.heroes:
            return await interaction.response.send_message("❌ Tu possèdes déjà ce héros.", ephemeral=True)

        player.emblems -= self.hero.price
        player.heroes.append(self.hero.id)
        bot.save_data()
        await interaction.response.send_message(f"✅ {self.hero.name} acheté avec succès !", ephemeral=True)

class AcheterCoffreButton(Button):
    def __init__(self, coffre):
        super().__init__(label=f"Acheter {coffre['name']}", style=discord.ButtonStyle.success)
        self.coffre = coffre

    async def callback(self, interaction: discord.Interaction):
        player = bot.get_player(interaction.user.id)
        if player.gold < 300:
            return await interaction.response.send_message("❌ Pas assez d'or.", ephemeral=True)

        player.gold -= 300
        distribution = self.coffre["rarity_distribution"]
        total = sum(distribution.values())
        rarities = list(distribution.keys())
        weights = list(distribution.values())

        def filter_items_by_rarity(rarity_name):
            try:
                rarity_enum = ItemRarity[rarity_name.upper()]
                return [item for item in bot.items_db.values() if item.rarity == rarity_enum]
            except KeyError:
                return []

        items_gagnes = []
        for _ in range(self.coffre["loot_amount"]):
            rarity = random.choices(rarities, weights=weights, k=1)[0]
            candidats = filter_items_by_rarity(rarity)
            if candidats:
                item = random.choice(candidats)
                player.items.append(item.id)
                items_gagnes.append(item)

        bot.save_data()
        await interaction.response.send_message(f"🎉 Tu as obtenu : {', '.join([i.name for i in items_gagnes])}", ephemeral=True)

class AcheterItemButton(Button):
    def __init__(self, item):
        super().__init__(label=f"Acheter {item.name}", style=discord.ButtonStyle.secondary)
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        player = bot.get_player(interaction.user.id)
        if player.gold < self.item.price:
            return await interaction.response.send_message("❌ Pas assez d'or.", ephemeral=True)

        player.gold -= self.item.price
        player.items.append(self.item.id)
        bot.save_data()
        await interaction.response.send_message(f"✅ Tu as acheté **{self.item.name}**.", ephemeral=True)

@bot.command(name="boutique")
async def boutique(ctx):
    maj_items_du_jour()
    embed = discord.Embed(
        title="🏪 Boutique",
        description="Choisissez une catégorie dans le menu ci-dessous.",
        color=discord.Color.teal()
    )
    await ctx.send(embed=embed, view=BoutiqueView(ctx.author))


@bot.command(name='aide')
async def help_command(ctx):
    """Affiche l'aide"""
    embed = discord.Embed(
        title="🆘 Aide - Bot de Collection",
        color=discord.Color.blue()
    )
    
    commands_list = [
        "`!profil` - Affiche votre profil",
        "`!boutique` - Affiche la boutique",
        "`!mes_heroes` - Affiche vos héros",
        "`!mes_items` - Affiche vos items",
        "`!équiper <hero_id> <item_id>` - Équipe un item",
        "`!déséquiper <hero_id> <item_id>` - Déséquipe un item",
        "`!détails <hero_id>` - Détails d'un héros"
    ]
    
    embed.add_field(
        name="Commandes disponibles",
        value="\n".join(commands_list),
        inline=False
    )
    
    await ctx.send(embed=embed)

# Remplace 'YOUR_BOT_TOKEN' par ton token Discord
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    bot.run(token)