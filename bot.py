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
from discord.ui import View, Select, Button
from datetime import datetime, timedelta, timezone
load_dotenv("secrets.env")  # Charge les variables depuis secrets.env

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

#Puissance des héros et items par rareté
PUISSANCE_HEROS = {
    HeroRarity.COMMUN: 100,
    HeroRarity.RARE: 200,
    HeroRarity.EPIQUE: 300,
    HeroRarity.LEGENDAIRE: 500
}
PUISSANCE_ITEM = {
    ItemRarity.COMMUN: 20,
    ItemRarity.RARE: 50,
    ItemRarity.EPIQUE: 80,
    ItemRarity.LEGENDAIRE: 100,
    ItemRarity.MYTHIQUE: 120,
    ItemRarity.SUPREME: 200
}

def get_color_from_hex(hex_color):
    """Convertit une couleur hex en discord.Color"""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return discord.Color(int(hex_color, 16))

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
    def get_puissance(self) -> int:
        return PUISSANCE_ITEM.get(self.rarity, 0)
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
    color: str = "#5865F2"
    def calculer_puissance(self, items_db: Dict[int, Item]) -> int:
        puissance = PUISSANCE_HEROS.get(self.rarity, 0)
        for item_id in self.equipped_items:
            item = items_db.get(item_id)
            if item:
                puissance += PUISSANCE_ITEM.get(item.rarity, 0)
        return puissance
    
    def __post_init__(self):
        if self.equipped_items is None:
            self.equipped_items = []
@dataclass
class PlayerData:
    user_id: int
    gold: int = 1000
    emblems: int = 0
    heroes: List[int] = None
    items: List[int] = None
    chests: List[str] = None
    hero_levels: Dict[int, 'HeroLevel'] = None  

    def __post_init__(self):
        if self.heroes is None:
            self.heroes = []
        if self.items is None:
            self.items = []
        if self.chests is None:
            self.chests = []
        if self.hero_levels is None:
            self.hero_levels = {}
@dataclass
class ChestType:
    name: str
    rarity_distribution: Dict[str, int]
    loot_amount: int
    image: str
    description: str
    price: int = 0
    color: str = "#5865F2"
@dataclass
class LootResult:
    items: List[int] = field(default_factory=list)
    gold: int = 0
    emblems: int = 0
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

ITEMS_DU_JOUR = []
DERNIERE_MAJ_ITEMS = None
ITEMS_DU_JOUR_PATH = "items_du_jour.json"

def sauvegarder_items_du_jour():
    """Sauvegarde les items du jour dans le fichier JSON"""
    try:
        item_ids = [item.id for item in ITEMS_DU_JOUR]
        derniere_maj_str = DERNIERE_MAJ_ITEMS.isoformat() if DERNIERE_MAJ_ITEMS else None
        data = {
            'items_ids': item_ids,  # clé corrigée ici, c'était 'items_du_jour' dans ta version, mieux garder 'items_ids'
            'derniere_maj': derniere_maj_str
        }
        with open(ITEMS_DU_JOUR_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des items du jour: {e}")

def maj_items_du_jour(bot):
    """Met à jour la liste des items du jour, en rechargeant depuis fichier ou générant"""
    global ITEMS_DU_JOUR, DERNIERE_MAJ_ITEMS

    if os.path.exists(ITEMS_DU_JOUR_PATH):
        try:
            with open(ITEMS_DU_JOUR_PATH, "r", encoding='utf-8') as f:
                data = json.load(f)

            timestamp = data.get("derniere_maj")
            if timestamp:
                DERNIERE_MAJ_ITEMS = datetime.fromisoformat(timestamp)

            if DERNIERE_MAJ_ITEMS and datetime.now(timezone.utc) - DERNIERE_MAJ_ITEMS < timedelta(hours=24):
                item_ids = data.get("items_ids", [])
                ITEMS_DU_JOUR = [bot.items_db[i] for i in item_ids if i in bot.items_db]
                return  # Garder les mêmes items, moins de 24h écoulées
        except Exception as e:
            print(f"Erreur lors du chargement des items du jour: {e}")

    # Générer de nouveaux items
    items_disponibles = list(bot.items_db.values())
    k = min(5, len(items_disponibles))
    ITEMS_DU_JOUR = random.sample(items_disponibles, k=k) if k > 0 else []
    DERNIERE_MAJ_ITEMS = datetime.now(timezone.utc)
    sauvegarder_items_du_jour()

class HeroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Bases de données en mémoire
        self.heroes_db: Dict[int, Hero] = {}
        self.items_db: Dict[int, Item] = {}
        self.players: Dict[int, PlayerData] = {}
        self.chests_db: Dict[str, ChestType] = {}
        
        # Chargement des données JSON
        self.load_data()
    
    def load_data(self):
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
        
        # Chargement des héros
        try:
            with open('heroes.json', 'r', encoding='utf-8') as f:
                heroes_data = json.load(f)
                for hero_data in heroes_data:
                    rarity_name = hero_data['rarity'].upper()
                    hero_rarity = HeroRarity[rarity_name]

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
                        equipped_items=hero_data.get('equipped_items', []),
                        color=hero_data.get('color', '#5865F2')
                    )
                    self.heroes_db[hero.id] = hero
        except FileNotFoundError:
            print("Fichier heroes.json non trouvé")
        except KeyError as e:
            print(f"Erreur de clé dans heroes.json: {e}")
        except Exception as e:
            print(f"Erreur lors du chargement des héros: {e}")

        # Chargement des items
        try:
            with open('items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                if isinstance(items_data, list):
                    for item_data in items_data:
                        rarity_name = item_data['rarity'].upper()
                        item_rarity = ItemRarity[rarity_name]

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

        # Chargement des joueurs
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

        # Chargement des coffres
        try:
            with open('chests.json', 'r', encoding='utf-8') as f:
                chests_data = json.load(f)
                for chest_data in chests_data:
                    chest = ChestType(
                        name=chest_data['name'],
                        rarity_distribution=chest_data['rarity_distribution'],
                        loot_amount=chest_data['loot_amount'],
                        image=chest_data['image'],
                        description=chest_data['description'],
                        price=chest_data.get('price', 300),
                        color=chest_data.get('color', '#5865F2')
                    )
                    self.chests_db[chest.name] = chest
        except FileNotFoundError:
            print("Fichier chests.json non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement des coffres: {e}")

        # Mise à jour des items du jour après chargement
        maj_items_du_jour(self)
    
    def save_data(self):
        players_data = []
        for player in self.players.values():
            player_dict = asdict(player)
            # Conversion des hero_levels en dicts
            hero_levels_dict = {}
            for hero_id, level_obj in player.hero_levels.items():
                hero_levels_dict[str(hero_id)] = asdict(level_obj)
            player_dict['hero_levels'] = hero_levels_dict
            players_data.append(player_dict)
        
        with open('players.json', 'w', encoding='utf-8') as f:
            json.dump(players_data, f, indent=2, ensure_ascii=False)
        sauvegarder_items_du_jour()
    
    def get_player(self, user_id: int) -> PlayerData:
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
        return self.players[user_id]
    
    def generate_loot(self, chest: ChestType) -> 'LootResult':
        loot = LootResult()
        
        for _ in range(chest.loot_amount):
            rarities = list(chest.rarity_distribution.keys())
            weights = list(chest.rarity_distribution.values())
            selected_rarity = random.choices(rarities, weights=weights, k=1)[0]
            
            try:
                rarity_enum = ItemRarity[selected_rarity.upper()]
                available_items = [item for item in self.items_db.values() if item.rarity == rarity_enum]
                if available_items:
                    selected_item = random.choice(available_items)
                    loot.items.append(selected_item.id)
            except KeyError:
                continue
        
        loot.gold = random.randint(50, 200)
        return loot

# Création de l'instance globale du bot
bot = HeroBot()

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté !')

@bot.command(name='lvl_heros')
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

@bot.command(name='open')
async def open_chest(ctx, *, chest_name: str):
    """Ouvre un coffre avec animation"""
    player = bot.get_player(ctx.author.id)
    
    # Vérifier si le joueur a ce coffre
    if chest_name not in player.chests:
        await ctx.send("❌ Vous ne possédez pas ce coffre !")
        return
    
    # Trouver le coffre dans la base de données
    chest = bot.chests_db.get(chest_name)
    if not chest:
        await ctx.send("❌ Coffre introuvable dans la base de données !")
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
    player.emblems += loot.emblems
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
    
    if loot.emblems > 0:
        embed.add_field(name="🏆 Emblèmes du Triomphe", value=f"+{loot.emblems}", inline=True)
    
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
        title="✅ Coffre acheté !",
        description=f"Vous avez acheté **{chest.name}** pour {chest.price} 💰\nUtilisez `!ouvrir_coffre {chest.name}` pour l'ouvrir!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='chests')
async def my_chests(ctx):
    """Affiche les coffres du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.chests:
        await ctx.send("❌ Vous n'avez aucun coffre !")
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
    # Ressources
    embed.add_field(
        name="💰 Ressources", 
        value=f"Pièces: {player.gold} 🪙\nEmblèmes: {player.emblems} 🏆", 
        inline=False
    )
    # Collection
    embed.add_field(
        name="🎒 Collection", 
        value=f"Héros: {len(player.heroes)} 👥\nItems: {len(player.items)} ⚔️\nCoffres: {len(player.chests)} 📦", 
        inline=False
    )

    # Niveau moyen des héros
    if player.heroes and player.hero_levels:
        total_level = sum(player.hero_levels.get(h_id, HeroLevel()).level for h_id in player.heroes)
        avg_level = total_level / len(player.heroes)
        embed.add_field(name="📊 Niveau moyen", value=f"{avg_level:.1f}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='buy')
async def buy(ctx, item_type: str, item_id: int):
    """Achète un héros ou un item"""
    player = bot.get_player(ctx.author.id)
    
    if item_type.lower() == "hero":
        if item_id not in bot.heroes_db:
            await ctx.send("❌ Héros introuvable.")
            return
        
        hero = bot.heroes_db[item_id]
        
        if item_id in player.heroes:
            await ctx.send("❌ Vous possédez déjà ce héros.")
            return
        
        if player.gold < hero.price:
            await ctx.send(f"❌ Pas assez d'argent ! Il vous faut {hero.price} pièces.")
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
            await ctx.send("❌ Item introuvable.")
            return
        
        item = bot.items_db[item_id]
        
        if player.gold < item.price:
            await ctx.send(f"❌ Pas assez d'argent ! Il vous faut {item.price} pièces.")
            return
        
        player.gold -= item.price
        player.items.append(item_id)
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Achat réussi !",
            description=f"Vous avez acheté {item.rarity.emoji} **{item.name}** pour {item.price} 💰",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    else:
        await ctx.send("❌ Type invalide. Utilisez `hero` ou `item`")

@bot.command(name='heros')
async def my_heroes(ctx):
    """Affiche les héros du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.heroes:
        await ctx.send("❌ Vous n'avez aucun héros recruté pour le moment.")
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

@bot.command(name='items')
async def my_items(ctx):
    """Affiche les items du joueur"""
    player = bot.get_player(ctx.author.id)
    
    if not player.items:
        await ctx.send("❌ Vous n'avez aucun item pour le moment.")
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

@bot.command(name='equip')
async def equip_item(ctx, hero_id: int, item_id: int):
    """Équipe un item sur un héros"""
    player = bot.get_player(ctx.author.id)
    
    # Vérifications
    if hero_id not in player.heroes:
        await ctx.send("❌ Vous ne possédez pas ce héros.")
        return
    
    if item_id not in player.items:
        await ctx.send("❌ Vous ne possédez pas cet item.")
        return
    
    hero = bot.heroes_db[hero_id]
    item = bot.items_db[item_id]
    
    # Vérifier la compatibilité de classe
    if hero.hero_class not in item.compatible_classes:
        await ctx.send(f"❌ Cet item n'est pas compatible avec la classe {hero.hero_class.value}.")
        return
    
    # Vérifier si l'item est déjà équipé
    if item_id in hero.equipped_items:
        await ctx.send("❌ Cet item est déjà équipé sur ce héros.")
        return
    
    # Vérifier la limite d'équipement
    if len(hero.equipped_items) >= 6:
        await ctx.send("❌ Ce héros a déjà 6 items équipés.")
        return
    
    # Équiper l'item
    hero.equipped_items.append(item_id)
    bot.save_data()
    
    embed = discord.Embed(
        title="✅ Item équipé !",
        description=f"{item.rarity.emoji} **{item.name}** équipé sur {hero.rarity.emoji} **{hero.name}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='unequip')
async def unequip_item(ctx, hero_id: int, item_id: int):
    """Déséquipe un item d'un héros"""
    player = bot.get_player(ctx.author.id)
    
    if hero_id not in player.heroes:
        await ctx.send("❌ Vous ne possédez pas ce héros.")
        return
    
    hero = bot.heroes_db[hero_id]
    
    if item_id not in hero.equipped_items:
        await ctx.send("❌ Cet item n'est pas équipé sur ce héros.")
        return
    
    # Déséquiper l'item
    hero.equipped_items.remove(item_id)
    bot.save_data()
    
    item = bot.items_db[item_id]
    embed = discord.Embed(
        title="✅ Item déséquipé !",
        description=f"{item.rarity.emoji} **{item.name}** déséquipé de {hero.rarity.emoji} **{hero.name}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='info')
async def hero_details(ctx, *, hero_name: str):
    """Affiche les détails d'un héros possédé par le joueur, en utilisant son nom"""
    player = bot.get_player(ctx.author.id)

    # Recherche d'un héros correspondant par nom (insensible à la casse)
    hero_id = None
    for pid in player.heroes:
        hero = bot.heroes_db.get(pid)
        if hero and hero.name.lower() == hero_name.lower():
            hero_id = pid
            break

    if hero_id is None:
        await ctx.send("❌ Vous ne possédez pas ce héros (vérifie l'orthographe).")
        return

    hero = bot.heroes_db[hero_id]

    try:
        couleur = int(hero.color.lstrip("#"), 16)
    except AttributeError:
        couleur = 0x3498db  # couleur par défaut si pas de champ 'color'

    embed = discord.Embed(
        title=f"{hero.rarity.emoji} {hero.name}",
        description=hero.description,
        color=couleur
    )
    embed.set_image(url=hero.image)
    embed.add_field(name="Classe", value=hero.hero_class.value, inline=True)
    embed.add_field(name="Rareté", value=hero.rarity.name, inline=True)
    embed.add_field(name="Items équipés", value=f"{len(hero.equipped_items)}/6", inline=True)

    puissance = hero.calculer_puissance(bot.items_db)
    embed.add_field(name="Puissance", value=f"{puissance} ⚡", inline=False)

    if hero.equipped_items:
        items_list = []
        for item_id in hero.equipped_items:
            item = bot.items_db[item_id]
            items_list.append(f"{item.rarity.emoji} {item.name}")
        embed.add_field(name="Équipement", value="\n".join(items_list), inline=False)

    await ctx.send(embed=embed)

class BoutiqueView(View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.current_page = "heros"
        self.hero_index = 0
        self.chest_index = 0
        self.refresh_buttons()

    def refresh_buttons(self):
        self.clear_items()
        self.add_item(NavigationButton("🦸 Héros", "heros"))
        self.add_item(NavigationButton("🎁 Coffres", "coffres"))
        self.add_item(NavigationButton("🛡️ Items du jour", "items"))

        if self.current_page == "heros" and len(bot.heroes_db) > 1:
            self.add_item(PaginationButton("⬅️", -1, "heros"))
            self.add_item(PaginationButton("➡️", 1, "heros"))
        elif self.current_page == "coffres" and len(bot.chests_db) > 1:
            self.add_item(PaginationButton("⬅️", -1, "coffres"))
            self.add_item(PaginationButton("➡️", 1, "coffres"))

    async def create_page_embed(self):
        if self.current_page == "heros":
            heroes_list = list(bot.heroes_db.values())
            if heroes_list:
                self.hero_index = min(self.hero_index, len(heroes_list) - 1)
                hero = heroes_list[self.hero_index]
                
                # Créez l'embed AVEC la couleur personnalisée du héros
                embed = discord.Embed(
                    title="🦸 Héros disponibles",
                    color=get_color_from_hex(hero.color)
                )
                
                embed.set_image(url=hero.image)
                embed.add_field(name="Nom", value=hero.name, inline=True)
                embed.add_field(name="Classe", value=hero.hero_class.value, inline=True)
                embed.add_field(name="Prix", value=f"{hero.price} 🏅", inline=True)
                embed.add_field(name="Rareté", value=f"{hero.rarity.emoji} {hero.rarity.display_name}", inline=True)
                if hero.description:
                    embed.add_field(name="Description", value=hero.description, inline=False)
                embed.set_footer(text=f"Héros {self.hero_index + 1}/{len(heroes_list)}")
            else:
                embed = discord.Embed(
                    title="🦸 Héros disponibles",
                    description="Aucun héros disponible",
                    color=discord.Color.red()
                )

        elif self.current_page == "coffres":
            chests_list = list(bot.chests_db.values())
            if chests_list:
                self.chest_index = min(self.chest_index, len(chests_list) - 1)
                chest = chests_list[self.chest_index]
                
                # Créez l'embed AVEC la couleur personnalisée du coffre
                embed = discord.Embed(
                    title="🎁 Coffres disponibles",
                    color=get_color_from_hex(chest.color)
                )
                
                embed.add_field(
                    name=f"📦 {chest.name}",
                    value=f"Prix: {chest.price} 🪙\n{chest.description}",
                    inline=False
                )
                if hasattr(chest, 'image') and chest.image:
                    embed.set_thumbnail(url=chest.image)
                embed.set_footer(text=f"Coffre {self.chest_index + 1}/{len(chests_list)}")
            else:
                embed = discord.Embed(
                    title="🎁 Coffres disponibles",
                    description="Aucun coffre disponible",
                    color=discord.Color.red()
                )

        elif self.current_page == "items":
            embed = discord.Embed(
                title="🛡️ Items du jour",
                color=discord.Color.teal()
            )
            maj_items_du_jour(bot)
            if ITEMS_DU_JOUR:
                for item in ITEMS_DU_JOUR:
                    stats_str = ", ".join([f"{k}: +{v}" for k, v in item.stats.items()])
                    embed.add_field(
                        name=f"{item.rarity.emoji} {item.name}",
                        value=f"Prix: {item.price} 🪙\nStats: {stats_str}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="Aucun item",
                    value="Aucun item disponible aujourd'hui",
                    inline=False
                )
        
        else:
            # Cas par défaut au cas où
            embed = discord.Embed(
                title="❌ Page inconnue",
                color=discord.Color.red()
            )

        return embed

class NavigationButton(Button):
    def __init__(self, label: str, page: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.user:
            return await interaction.response.send_message("❌ Ce menu n'est pas pour toi.", ephemeral=True)

        self.view.current_page = self.page
        self.view.hero_index = 0
        self.view.chest_index = 0
        self.view.refresh_buttons()
        embed = await self.view.create_page_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

class PaginationButton(Button):
    def __init__(self, emoji: str, direction: int, target_page: str):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.primary)
        self.direction = direction
        self.target_page = target_page

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.user:
            return await interaction.response.send_message("❌ Ce menu n'est pas pour toi.", ephemeral=True)

        if self.target_page == "heros":
            heroes_list = list(bot.heroes_db.values())
            self.view.hero_index = (self.view.hero_index + self.direction) % len(heroes_list)
        elif self.target_page == "coffres":
            chests_list = list(bot.chests_db.values())
            self.view.chest_index = (self.view.chest_index + self.direction) % len(chests_list)

        self.view.refresh_buttons()
        embed = await self.view.create_page_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

@bot.command(name="shop")
async def shop(ctx):
    print("Héros dans heroes_db :")
    for hero_id, hero in bot.heroes_db.items():
        print(f"- {hero_id}: {hero.name}")
    maj_items_du_jour(bot)
    print("Héros filtrés pour boutique :")
    for hero in heroes_to_show:
        print(f"- {hero.id}: {hero.name}")
    view = BoutiqueView(ctx.author)
    embed = await view.create_page_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name='aide')
async def help_command(ctx):
    """Affiche l'aide"""
    embed = discord.Embed(
        title="🆘 Aide - Bot de Collection",
        color=discord.Color.blue()
    )

    commands_list = [
        "`!profil` - Affiche votre profil",
        "`!shop` - Affiche la boutique",
        "`!buy <item>` - Acheter un item/coffre/héros" 
        "`!heros` - Affiche vos héros",
        "`!items` - Affiche vos items",
        "`!equip <hero_id> <item_id>` - Équipe un item",
        "`!unequip <hero_id> <item_id>` - Déséquipe un item",
        "`!info <hero_id>` - Détails d'un héros",
        "`!open <nom du coffre>` - Ouvrir un coffre spécifique",   
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
