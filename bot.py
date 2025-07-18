import discord
from discord.ext import commands
import json
import random
from enum import Enum
from dataclasses import dataclass, asdict
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
    coins: int = 1000
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
                        coins=player_data['coins'],
                        heroes=player_data['heroes'],
                        items=player_data['items']
                    )
                    self.players[player.user_id] = player
        except FileNotFoundError:
            print("Fichier players.json non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement des joueurs: {e}")
    
    def save_data(self):
        """Sauvegarde les données dans des fichiers JSON"""
        players_data = []
        for player in self.players.values():
            players_data.append(asdict(player))
        
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

bot = HeroBot()

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté !')

@bot.command(name='profil')
async def profile(ctx):
    """Affiche le profil du joueur"""
    player = bot.get_player(ctx.author.id)
    
    embed = discord.Embed(
        title=f"Profil de {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 Pièces", value=player.coins, inline=True)
    embed.add_field(name="👥 Héros", value=len(player.heroes), inline=True)
    embed.add_field(name="🎒 Items", value=len(player.items), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='boutique')
async def shop(ctx, category: str = "heroes"):
    """Affiche la boutique"""
    if category.lower() == "heroes":
        embed = discord.Embed(
            title="🏪 Boutique - Héros",
            description="Utilisez `!acheter hero <id>` pour acheter un héros",
            color=discord.Color.green()
        )
        
        for hero in bot.heroes_db.values():
            embed.add_field(
                name=f"{hero.rarity.emoji} {hero.name} (ID: {hero.id})",
                value=f"Classe: {hero.hero_class.value}\nPrix: {hero.price} 💰\n{hero.description}",
                inline=False
            )
    
    elif category.lower() == "items":
        embed = discord.Embed(
            title="🏪 Boutique - Items",
            description="Utilisez `!acheter item <id>` pour acheter un item",
            color=discord.Color.green()
        )
        
        for item in bot.items_db.values():
            classes_str = ", ".join([c.value for c in item.compatible_classes])
            stats_str = ", ".join([f"{k}: +{v}" for k, v in item.stats.items()])
            
            embed.add_field(
                name=f"{item.rarity.emoji} {item.name} (ID: {item.id})",
                value=f"Classes: {classes_str}\nStats: {stats_str}\nPrix: {item.price} 💰",
                inline=False
            )
    
    else:
        embed = discord.Embed(
            title="❌ Erreur",
            description="Catégorie invalide. Utilisez `heroes` ou `items`",
            color=discord.Color.red()
        )
    
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
        
        if player.coins < hero.price:
            await ctx.send(f"❌ Pas assez de pièces! Il vous faut {hero.price} pièces.")
            return
        
        player.coins -= hero.price
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
        
        if player.coins < item.price:
            await ctx.send(f"❌ Pas assez de pièces! Il vous faut {item.price} pièces.")
            return
        
        player.coins -= item.price
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
    embed.add_field(name="Rareté", value=hero.rarity, inline=True)
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

@bot.command(name='aide')
async def help_command(ctx):
    """Affiche l'aide"""
    embed = discord.Embed(
        title="🆘 Aide - Bot de Collection",
        color=discord.Color.blue()
    )
    
    commands_list = [
        "`!profil` - Affiche votre profil",
        "`!boutique [heroes/items]` - Affiche la boutique",
        "`!acheter <hero/item> <id>` - Achète un héros ou item",
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