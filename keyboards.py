from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,                                 )
from aiogram.utils.keyboard import InlineKeyboardBuilder
                                               
def main_menu_kb() -> ReplyKeyboardMarkup:         return ReplyKeyboardMarkup(                        keyboard=[
            [KeyboardButton(text="🎯 Тест бастау"), KeyboardButton(text="📚 ҰБТ режимі")],
            [KeyboardButton(text="📊 Статистика"),   KeyboardButton(text="🏆 Рейтинг")],
            [KeyboardButton(text="💡 Сұрақ ұсыну"), KeyboardButton(text="💬 Кері байланыс")],
            [KeyboardButton(text="⚙️ Баптаулар"),   KeyboardButton(text="ℹ️ Туралы")],                  ],
        resize_keyboard=True,
    )                                          

def categories_kb(categories: list[tuple]) -> InlineKeyboardMarkup:
    """categories = [(name, count), ...]"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Барлығы", callback_data="cat:all")                                    for name, cnt in categories:
        builder.button(text=f"{name} ({cnt})", callback_data=f"cat:{name}")
    builder.adjust(1)
    return builder.as_markup()                                                                
def answer_kb(q_index: int, question: dict = None) -> InlineKeyboardMarkup:                       """Generate answer keyboard based on available options."""
    builder = InlineKeyboardBuilder()
                                                   # Default to A,B,C,D if no question provided
    letters = ["A", "B", "C", "D"]
                                                   if question:
        # Add E,F if they exist
        if question.get('option_e'):
            letters.append("E")                        if question.get('option_f'):
            letters.append("F")

    for letter in letters:                             builder.button(text=letter, callback_data=f"ans:{q_index}:{letter}")
                                                   # Check if multiple correct answers
    has_multiple = question and question.get('correct') and ',' in question['correct']

    if has_multiple:
        # Add confirm button                           builder.button(text="✅ Растау", callback_data=f"confirm_ans:{q_index}")

        # Adjust layout: letters in rows, confirm below
        cols = 4 if len(letters) <= 4 else 3           builder.adjust(cols, 1)
    else:
        # Adjust layout: 4 columns if <= 4, 3 columns if > 4
        cols = 4 if len(letters) <= 4 else 3           builder.adjust(cols)
                                                   return builder.as_markup()


def admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Кезектегі сұрақтар"), KeyboardButton(text="➕ Сұрақ қосу")],                                                        [KeyboardButton(text="🗑 Сұрақ өшіру"),         KeyboardButton(text="⚙️ Баптаулар")],
            [KeyboardButton(text="📚 ҰБТ басқару"),         KeyboardButton(text="📩 Хат жіберу")],
            [KeyboardButton(text="📊 Жіберу тарихы"),       KeyboardButton(text="📊 Бот статистикасы")],
            [KeyboardButton(text="🔙 Шығу")],
        ],
        resize_keyboard=True,                      )

                                               def delete_confirm_kb(question_id: int) -> InlineKeyboardMarkup:                                  builder = InlineKeyboardBuilder()
    builder.button(text="✅ Иә, өшір", callback_data=f"delconfirm:{question_id}")
    builder.button(text="❌ Жоқ, қалдыр", callback_data="delcancel")
    builder.adjust(2)                              return builder.as_markup()


def approve_reject_kb(pending_id: int) -> InlineKeyboardMarkup:                                   builder = InlineKeyboardBuilder()
    builder.button(text="✅ Бекіту", callback_data=f"approve:{pending_id}")
    builder.button(text="❌ Қабылдамау", callback_data=f"reject:{pending_id}")
    builder.adjust(2)
    return builder.as_markup()


def difficulty_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Жеңіл",   callback_data="diff:easy")                                  builder.button(text="🟡 Орташа",  callback_data="diff:medium")                                builder.button(text="🔴 Қиын",    callback_data="diff:hard")
    builder.adjust(3)
    return builder.as_markup()


def submit_category_kb(categories: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"submit_cat:{cat}")
    builder.adjust(2)
    return builder.as_markup()                 

def remove_kb():
    return ReplyKeyboardRemove()


# ═══ SETTINGS KEYBOARDS (v1.2) ═══════════════════════════════════════════════

def settings_menu_kb() -> InlineKeyboardMarkup:
    """Admin settings menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Глобалды баптаулар", callback_data="show_global_settings")
    builder.button(text="📂 Санаттар басқару", callback_data="show_category_mgmt")
    builder.button(text="📋 Нұсқалар басқару", callback_data="show_variant_mgmt")                 builder.adjust(1)
    return builder.as_markup()

                                               def global_settings_kb() -> InlineKeyboardMarkup:                                                 """Global settings edit menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Сұрақтар саны", callback_data="gsetting:questions_count")             builder.button(text="⏱ Уақыт лимиті", callback_data="gsetting:time_limit")
    builder.button(text="🔢 Макс жауап опциялары", callback_data="gsetting:max_options")          builder.button(text="✅ Макс дұрыс жауаптар", callback_data="gsetting:max_correct")           builder.button(text="🎲 Shuffle режимі", callback_data="gsetting:shuffle")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")                             builder.adjust(1)
    return builder.as_markup()


def user_settings_kb() -> InlineKeyboardMarkup:    """User personal settings menu."""
    builder = InlineKeyboardBuilder()              builder.button(text="📝 Сұрақтар саны", callback_data="usetting:questions_count")             builder.button(text="⏱ Уақыт лимиті", callback_data="usetting:time_limit")                    builder.button(text="🎲 Shuffle режимі", callback_data="usetting:shuffle")                    builder.adjust(1)
    return builder.as_markup()


def questions_count_kb(scope: str) -> InlineKeyboardMarkup:
    """Questions count selector. scope: 'global' or 'user'"""
    builder = InlineKeyboardBuilder()
    prefix = "gset:qcount" if scope == "global" else "uset:qcount"

    for count in [5, 10, 15, 20, 25]:
        builder.button(text=str(count), callback_data=f"{prefix}:{count}")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")                             builder.adjust(5, 1)
    return builder.as_markup()                 
                                               def time_limit_kb(scope: str) -> InlineKeyboardMarkup:                                            """Time limit selector. scope: 'global' or 'user'"""
    builder = InlineKeyboardBuilder()
    prefix = "gset:tlimit" if scope == "global" else "uset:tlimit"

    builder.button(text="10с", callback_data=f"{prefix}:10")
    builder.button(text="30с", callback_data=f"{prefix}:30")
    builder.button(text="60с", callback_data=f"{prefix}:60")
    builder.button(text="∞", callback_data=f"{prefix}:0")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(4, 1)
    return builder.as_markup()                 
                                               def max_options_kb() -> InlineKeyboardMarkup:
    """Max answer options selector (admin only)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="4", callback_data="gset:maxopt:4")
    builder.button(text="5", callback_data="gset:maxopt:5")
    builder.button(text="6", callback_data="gset:maxopt:6")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(3, 1)
    return builder.as_markup()

                                               def max_correct_kb() -> InlineKeyboardMarkup:
    """Max correct answers selector (admin only)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="1", callback_data="gset:maxcorr:1")
    builder.button(text="2", callback_data="gset:maxcorr:2")
    builder.button(text="3", callback_data="gset:maxcorr:3")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(3, 1)                           return builder.as_markup()
                                               
# ═══ CATEGORY & VARIANT MANAGEMENT ════════════════════════════════════════════
                                               def category_management_kb() -> InlineKeyboardMarkup:
    """Category management menu."""
    builder = InlineKeyboardBuilder()              builder.button(text="➕ Санат қосу", callback_data="category_add")                            builder.button(text="✏️ Санат өңдеу", callback_data="category_rename")
    builder.button(text="🗑 Санат өшіру", callback_data="category_delete")                         builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(1)
    return builder.as_markup()                 

def variant_management_kb() -> InlineKeyboardMarkup:                                              """Variant management menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Нұсқа қосу", callback_data="variant_add")
    builder.button(text="📋 Нұсқалар тізімі", callback_data="variant_list")
    builder.button(text="🗑 Нұсқа өшіру", callback_data="variant_delete")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")                             builder.adjust(1)
    return builder.as_markup()                 
                                               def category_list_kb(categories: list[tuple], action: str) -> InlineKeyboardMarkup:
    """Category selector. action: 'rename', 'delete', 'varadd', 'varlist', 'vardel'"""            builder = InlineKeyboardBuilder()

    action_map = {                                     "rename": "catrename",
        "delete": "catdelete",
        "varadd": "varaddcat",                         "varlist": "varlistcat",
        "vardel": "vardelcat",
    }
    prefix = action_map.get(action, "cat")     
    for name, count in categories:
        builder.button(text=f"{name} ({count})", callback_data=f"{prefix}:{name}")            
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(2, 1)
    return builder.as_markup()
                                               
def variant_list_kb(variants: list[dict], action: str) -> InlineKeyboardMarkup:
    """Variant selector. action: 'view', 'delete'"""
    builder = InlineKeyboardBuilder()          
    if action == "delete":
        for v in variants:
            builder.button(                                    text=f"{v['variant_number']}. {v['name']}",
                callback_data=f"vardel:{v['id']}"
            )                                      else:  # view
        for v in variants:
            builder.button(
                text=f"{v['variant_number']}. {v['name']} ({v['questions_count']})",
                callback_data=f"varview:{v['id']}"
            )
                                                   builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(1)
    return builder.as_markup()

                                               def confirm_delete_kb(confirm_data: str) -> InlineKeyboardMarkup:
    """Confirm deletion."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Иә, өшір", callback_data=confirm_data)
    builder.button(text="❌ Жоқ", callback_data="delcancel")
    builder.adjust(2)                              return builder.as_markup()


def shuffle_settings_kb(scope: str) -> InlineKeyboardMarkup:
    """Shuffle settings toggle. scope: 'global' or 'user'"""
    builder = InlineKeyboardBuilder()              prefix = "gshuffle" if scope == "global" else "ushuffle"
                                                   builder.button(text="🎲 Сұрақтар араластыру", callback_data=f"{prefix}:questions")
    builder.button(text="🔀 Жауаптар араластыру", callback_data=f"{prefix}:answers")
    builder.button(text="🔙 Артқа", callback_data="back_to_settings")
    builder.adjust(1)
    return builder.as_markup()
                                               
def shuffle_toggle_kb(scope: str, setting: str, current: bool) -> InlineKeyboardMarkup:
    """Toggle shuffle on/off. scope: 'global'/'user', setting: 'questions'/'answers'"""
    builder = InlineKeyboardBuilder()
    prefix = "gshtoggle" if scope == "global" else "ushtoggle"

    on_text = "✅ Қосулы" if current else "⚪️ Қосулы"                                             off_text = "⚪️ Өшірулі" if current else "✅ Өшірулі"

    builder.button(text=on_text, callback_data=f"{prefix}:{setting}:1")
    builder.button(text=off_text, callback_data=f"{prefix}:{setting}:0")
    builder.button(text="🔙 Артқа", callback_data=f"back_shuffle:{scope}")
    builder.adjust(2, 1)                           return builder.as_markup()
                                               
# ═══ ҰБТ РЕЖИМІ KEYBOARDS ═══════════════════════════════════════════════════                
def ubt_mode_kb() -> InlineKeyboardMarkup:
    """UBT mode selection (full or short)."""
    builder = InlineKeyboardBuilder()              builder.button(text="📝 Толық тест (180 мин)", callback_data="ubt_mode:full")                 builder.button(text="⚡ Қысқартылған (60 мин)", callback_data="ubt_mode:short")
    builder.adjust(1)
    return builder.as_markup()


def ubt_subjects_kb(subjects: list[dict], exclude: list[int]) -> InlineKeyboardMarkup:
    """Elective subjects selection keyboard."""
    builder = InlineKeyboardBuilder()

    for subj in subjects:
        if subj["id"] not in exclude and not subj.get("is_mandatory"):
            builder.button(text=subj["name"], callback_data=f"ubt_elective:{subj['id']}")

    builder.adjust(1)
    return builder.as_markup()                 

def ubt_electives_kb(subjects: list[dict]) -> InlineKeyboardMarkup:
    """Simple elective subjects list."""
    builder = InlineKeyboardBuilder()          
    for subj in subjects:
        if not subj.get("is_mandatory"):                   builder.button(text=subj["name"], callback_data=f"ubt_el:{subj['id']}")           
    builder.adjust(2)                              return builder.as_markup()

                                               # ═══ FEEDBACK KEYBOARDS ════════════════════════════════════════════════════

def feedback_type_kb() -> InlineKeyboardMarkup:    """Feedback type selection."""
    builder = InlineKeyboardBuilder()              builder.button(text="💡 Ұсыныс", callback_data="feedback:suggestion")
    builder.button(text="📋 Шағым", callback_data="feedback:complaint")
    builder.button(text="🐛 Қате туралы", callback_data="feedback:bug")
    builder.button(text="📞 Әкімшімен байланысу", callback_data="feedback:contact")
    builder.adjust(1)
    return builder.as_markup()                 
                                               # ═══ BROADCAST KEYBOARDS ═══════════════════════════════════════════════════

def broadcast_type_kb() -> InlineKeyboardMarkup:                                                  """Broadcast message type selection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Мәтін", callback_data="bcast_type:text")
    builder.button(text="🖼 Сурет", callback_data="bcast_type:photo")
    builder.button(text="🎥 Видео", callback_data="bcast_type:video")
    builder.button(text="📄 Файл", callback_data="bcast_type:document")
    builder.adjust(2)                              return builder.as_markup()


def broadcast_target_kb() -> InlineKeyboardMarkup:
    """Broadcast target audience selection."""     builder = InlineKeyboardBuilder()
    builder.button(text="👥 Барлығына", callback_data="bcast_target:all")
    builder.button(text="✅ Белсенділерге (7 күн)", callback_data="bcast_target:active")
    builder.adjust(1)
    return builder.as_markup()


# ═══ UBT ADMIN KEYBOARDS ═══════════════════════════════════════════════════
                                               def ubt_admin_kb() -> InlineKeyboardMarkup:
    """UBT admin management menu."""               builder = InlineKeyboardBuilder()
    builder.button(text="📋 Пәндер тізімі", callback_data="ubt_list")                             builder.button(text="➕ Таңдау пәні қосу", callback_data="ubt_add")
    builder.button(text="🗑 Пәнді өшіру", callback_data="ubt_delete")
    builder.adjust(1)
    return builder.as_markup()

                                               def ubt_subject_list_kb(subjects: list[dict], action: str = "view") -> InlineKeyboardMarkup:
    """UBT subjects list keyboard."""              builder = InlineKeyboardBuilder()
                                                   if action == "delete":
        for s in subjects:
            if not s.get('is_mandatory'):  # Only electives can be deleted                                    builder.button(text=f"🗑 {s['name']}", callback_data=f"ubt_del:{s['id']}")
    else:
        # Just show list
        pass
                                                   builder.button(text="🔙 Артқа", callback_data="ubt_back")                                     builder.adjust(1)
    return builder.as_markup()

                                               def question_type_kb() -> InlineKeyboardMarkup:
    """Question type selection for UBT subjects."""
    builder = InlineKeyboardBuilder()              builder.button(text="📝 single (1 балл)", callback_data="qtype:single")                       builder.button(text="📖 context (2 балл)", callback_data="qtype:context")
    builder.button(text="🔗 matching (2 балл)", callback_data="qtype:matching")                   builder.button(text="✅ multiple (2 балл)", callback_data="qtype:multiple")
    builder.adjust(1)
    return builder.as_markup()                 

# ═══ ҰБТ ADMIN KEYBOARDS ═══════════════════════════════════════════════════                 
def ubt_admin_main_kb() -> ReplyKeyboardMarkup:
    """UBT admin main menu."""                     return ReplyKeyboardMarkup(
        keyboard=[                                         [KeyboardButton(text="🎓 Міндетті пәндер"), KeyboardButton(text="📋 Таңдау пәндері")],
            [KeyboardButton(text="➕ Пән қосу"), KeyboardButton(text="📊 ҰБТ статистика")],
            [KeyboardButton(text="🔙 Админ панель")],
        ],
        resize_keyboard=True,                      )

                                               def ubt_subject_list_kb(subjects: list[dict]) -> InlineKeyboardMarkup:
    """List of elective subjects."""
    builder = InlineKeyboardBuilder()          
    for s in subjects:
        builder.button(text=f"{s['name']}", callback_data=f"ubt_subj:{s['id']}")              
    builder.adjust(1)
    return builder.as_markup()
                                               
def ubt_question_type_kb() -> InlineKeyboardMarkup:
    """Question type selection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Бір дұрыс жауап", callback_data="ubtq_type:simple")
    builder.button(text="💬 Контекст бойынша", callback_data="ubtq_type:context")
    builder.button(text="🔗 Сәйкестік", callback_data="ubtq_type:matching")
    builder.button(text="✅ Бірнеше дұрыс", callback_data="ubtq_type:multiple")
    builder.adjust(1)
    return builder.as_markup()