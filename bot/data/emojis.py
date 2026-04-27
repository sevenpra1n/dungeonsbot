"""Centralized emoji constants for all main bot modules.

All values use Telegram custom emoji tags with confirmed IDs.
"""

# ── Inventory ──────────────────────────────────────────────────────────────
E_INV_HEADER  = '<tg-emoji emoji-id="5854908544712707500">📦</tg-emoji>'   # инвентарь — заголовок

E_MAT_WOOD    = '<tg-emoji emoji-id="5449918202718985124">🌳</tg-emoji>'   # древесина
E_MAT_STONE   = '<tg-emoji emoji-id="5433955200849159326">🪨</tg-emoji>'   # камень
E_MAT_FOOD    = '<tg-emoji emoji-id="6284888960644682300">🥕</tg-emoji>'   # еда
E_MAT_COPPER  = '<tg-emoji emoji-id="6278264420267201893">🔶</tg-emoji>'   # медь
E_MAT_IRON    = '<tg-emoji emoji-id="6278216436892570592">⛰️</tg-emoji>'   # железо
E_MAT_GOLD    = '<tg-emoji emoji-id="6280721566762277148">🥇</tg-emoji>'   # золото
E_MAT_STEEL   = '<tg-emoji emoji-id="6280349132968168995">🌋</tg-emoji>'   # сталь
E_MAT_AMETHYST = '<tg-emoji emoji-id="5341757074936193080">🤩</tg-emoji>'  # аметист
E_MAT_GEM     = '<tg-emoji emoji-id="5429387443000341439">🎁</tg-emoji>'   # самоцвет

# ── Components ─────────────────────────────────────────────────────────────
E_COMP_HEADER = '<tg-emoji emoji-id="5398095118735521227">⚙️</tg-emoji>'   # компоненты — заголовок
E_COMP_BOX    = '<tg-emoji emoji-id="5278540791336165644">📦</tg-emoji>'   # компоненты — ящик

E_RARITY_STAR      = '<tg-emoji emoji-id="5395855331945392566">🌟</tg-emoji>'  # маркер редкости (общий)
E_RARITY_ICON      = '<tg-emoji emoji-id="5377561928065372080">🔠</tg-emoji>'  # иконка редкости
E_RARITY_COMMON    = '<tg-emoji emoji-id="5395855331945392566">🌟</tg-emoji>'  # обычная
E_RARITY_RARE      = '<tg-emoji emoji-id="5395316601312548706">🌟</tg-emoji>'  # редкая
E_RARITY_EPIC      = '<tg-emoji emoji-id="5395550054259921224">🌟</tg-emoji>'  # эпическая
E_RARITY_LEGENDARY = '<tg-emoji emoji-id="5395487888903280719">🌟</tg-emoji>'  # легендарная
E_RARITY_MYTHIC    = '<tg-emoji emoji-id="5395620513198410698">🌟</tg-emoji>'  # мифическая

# ── Rating leagues ─────────────────────────────────────────────────────────
E_LEAGUE_NEWBIE      = '<tg-emoji emoji-id="6334498641822090737">🎗️</tg-emoji>'  # Новичковая
E_LEAGUE_SILVER      = '<tg-emoji emoji-id="5395855331945392566">🌟</tg-emoji>'   # Серебряная
E_LEAGUE_AMATEUR     = '<tg-emoji emoji-id="5395316601312548706">🌟</tg-emoji>'   # Любительская
E_LEAGUE_ADVANCED    = '<tg-emoji emoji-id="5334746438473651565">📕</tg-emoji>'   # Продвинутая
E_LEAGUE_CHOSEN      = '<tg-emoji emoji-id="5427140724132963665">🎁</tg-emoji>'   # Избранная
E_LEAGUE_PRO         = '<tg-emoji emoji-id="5427011475682130336">🎁</tg-emoji>'   # Профессиональная
E_LEAGUE_ESPORTS     = '<tg-emoji emoji-id="5427098087992617834">🎁</tg-emoji>'   # Киберспортивная
E_LEAGUE_WORLD       = '<tg-emoji emoji-id="5427277836668928138">🎁</tg-emoji>'   # Мировая
E_LEAGUE_POINTS      = '<tg-emoji emoji-id="5264816030068274765">⭐️</tg-emoji>'  # очки лиги

# ── Profile UI ─────────────────────────────────────────────────────────────
E_PROFILE   = '<tg-emoji emoji-id="5275979556308674886">👤</tg-emoji>'   # заголовок профиля
E_HASHTAG   = '<tg-emoji emoji-id="5354857360844152098">#️⃣</tg-emoji>'  # никнейм
E_STAR      = '<tg-emoji emoji-id="5206476089127372379">⭐️</tg-emoji>'  # звезда (уровень)
E_CRYSTALS  = '<tg-emoji emoji-id="5354902509540370798">💎</tg-emoji>'   # кристаллы
E_CIRCLE    = '<tg-emoji emoji-id="5357471466919056181">🔘</tg-emoji>'   # кружок (уровень)
E_HP        = '<tg-emoji emoji-id="5267283746477861842">❤️</tg-emoji>'   # здоровье

# ── Rating UI ──────────────────────────────────────────────────────────────
E_TROPHY    = '<tg-emoji emoji-id="5312315739842026755">🏆</tg-emoji>'   # трофей / победы
E_YELLOW    = '<tg-emoji emoji-id="5906800644525660990">🟡</tg-emoji>'   # желтый маркер (нейтрально)
E_RED       = '<tg-emoji emoji-id="5907027122446145395">🔴</tg-emoji>'   # красный маркер (опасность)

# ── Friends UI ─────────────────────────────────────────────────────────────
E_FRIENDS   = '<tg-emoji emoji-id="5298668674532538341">👥</tg-emoji>'   # заголовок друзей
E_GIFT      = '<tg-emoji emoji-id="5936138290519349485">🎁</tg-emoji>'   # игрок в списке (1 место)
E_GIFT2     = '<tg-emoji emoji-id="6021412890496473421">🎁</tg-emoji>'   # игрок в списке (2 место)
E_GIFT3     = '<tg-emoji emoji-id="6001349144046737619">🎁</tg-emoji>'   # игрок в списке (3 место)

# ── Chest UI ───────────────────────────────────────────────────────────────
E_CHEST     = '<tg-emoji emoji-id="6334602442591700514">📦</tg-emoji>'   # сундук (общий / заголовок)
E_CHEST_WOOD   = '<tg-emoji emoji-id="5854908544712707500">📦</tg-emoji>'   # деревянный сундук
E_CHEST_STEEL  = '<tg-emoji emoji-id="5201888948091129713">🔩</tg-emoji>'   # стальной сундук
E_CHEST_GOLD   = '<tg-emoji emoji-id="5276111746812112286">🌟</tg-emoji>'   # золотой сундук
E_CHEST_DIVINE = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'   # всевышний сундук
E_GEAR      = '<tg-emoji emoji-id="5339081812821957844">⚙️</tg-emoji>'   # шестерёнка (анимация открытия)
E_REWARD    = '<tg-emoji emoji-id="5427140724132963665">🎁</tg-emoji>'   # награда из сундука

# ── Indicators ────────────────────────────────────────────────────────────
E_GREEN     = '<tg-emoji emoji-id="5906852613629941703">🟢</tg-emoji>'   # зелёный (успех)
E_MARKER    = '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>'   # маркер строки
E_DIVIDER   = '<tg-emoji emoji-id="5265000876870761765">🔖</tg-emoji>'   # разделитель
E_PLUS      = '<tg-emoji emoji-id="5397916757333654639">➕</tg-emoji>'   # плюс (очки за победу)
E_MINUS     = '<tg-emoji emoji-id="5019523782004441717">❌</tg-emoji>'   # минус (очки за поражение)

# ── Likes & notifications ──────────────────────────────────────────────────
E_LIKE_HEART = '<tg-emoji emoji-id="5355174247826217637">❤️</tg-emoji>'  # сердце (лайк)
E_LIKE_THUMB = '<tg-emoji emoji-id="5357585094573838761">👍</tg-emoji>'  # палец вверх (лайк)

# ── Misc ───────────────────────────────────────────────────────────────────
E_CALENDAR  = '<tg-emoji emoji-id="5427055572111356481">🗓</tg-emoji>'   # редкость (ярлык)
E_CLIPBOARD = '<tg-emoji emoji-id="6334391113020868435">📋</tg-emoji>'   # количество (ярлык)
E_ATK       = '<tg-emoji emoji-id="5408935401442267103">⚔️</tg-emoji>'   # сила / атака
E_COINS     = '<tg-emoji emoji-id="5215420556089776398">👛</tg-emoji>'   # монеты
E_TICKET    = '<tg-emoji emoji-id="5334675412599480338">📕</tg-emoji>'   # билет рейда
E_LOCK      = '<tg-emoji emoji-id="6034962180875490251">🔓</tg-emoji>'   # замок (никнейм)
E_SQ        = '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>'   # квадратный маркер
E_DOT       = '<tg-emoji emoji-id="5321440402157353076">🔸</tg-emoji>'   # оранжевая точка
E_EXP_DOT   = '<tg-emoji emoji-id="5321440402157353076">🔸</tg-emoji>'   # точка (опыт)
E_EXP       = '<tg-emoji emoji-id="5336829549151823064">📕</tg-emoji>'   # опыт (ярлык)

# ── MarkdownV2 emoji (parse_mode="MarkdownV2") ─────────────────────────────
# Format: ![fallback](tg://emoji?id=ID)

# Inventory header & line marker
MD_INV_HEADER   = '![📦](tg://emoji?id=5854908544712707500)'
MD_CLIPBOARD    = '![📋](tg://emoji?id=6334391113020868435)'
MD_MARKER       = '![▫️](tg://emoji?id=5267324424113124134)'
MD_GREEN        = '![🟢](tg://emoji?id=5906852613629941703)'

# Materials (inventory lines)
MD_MAT_WOOD     = '![🌳](tg://emoji?id=5449918202718985124)'
MD_MAT_STONE    = '![🪨](tg://emoji?id=5433955200849159326)'
MD_MAT_FOOD     = '![🥕](tg://emoji?id=6284888960644682300)'
MD_MAT_COPPER   = '![🔶](tg://emoji?id=6278264420267201893)'
MD_MAT_IRON     = '![⛰️](tg://emoji?id=6278216436892570592)'
MD_MAT_GOLD     = '![🥇](tg://emoji?id=6280721566762277148)'
MD_MAT_STEEL    = '![🌋](tg://emoji?id=6280349132968168995)'
MD_MAT_AMETHYST = '![🤩](tg://emoji?id=5341757074936193080)'
MD_MAT_GEM      = '![🎁](tg://emoji?id=5429387443000341439)'

# Chests
MD_CHEST        = '![📦](tg://emoji?id=6334602442591700514)'
MD_CHEST_WOOD   = '![📦](tg://emoji?id=5854908544712707500)'
MD_CHEST_STEEL  = '![🔩](tg://emoji?id=5201888948091129713)'
MD_CHEST_GOLD   = '![🌟](tg://emoji?id=5276111746812112286)'
MD_CHEST_DIVINE = '![👑](tg://emoji?id=5217822164362739968)'

# Rarity (drop level)
MD_RARITY_COMMON  = '![🌟](tg://emoji?id=5395855331945392566)'
MD_RARITY_RARE    = '![🌟](tg://emoji?id=5395316601312548706)'
MD_RARITY_EPIC    = '![🌟](tg://emoji?id=5395550054259921224)'
MD_RARITY_MYTHIC  = '![🌟](tg://emoji?id=5395620513198410698)'

# Settings
MD_SETTINGS = '![⚙️](tg://emoji?id=5398095118735521227)'
MD_INFO     = '![ℹ️](tg://emoji?id=5377561928065372080)'
MD_CHECK    = '![✅](tg://emoji?id=5368324170671202286)'
MD_CROSS    = '![❌](tg://emoji?id=5019523782004441717)'
