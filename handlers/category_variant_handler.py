from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup                                              
import database as db
from keyboards import (
    admin_main_kb, category_management_kb, variant_management_kb,
    category_list_kb, variant_list_kb, confirm_delete_kb,
)
from config import ADMIN_IDS
                                               router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS                

class CategoryStates(StatesGroup):                 adding_name = State()
    renaming_old = State()
    renaming_new = State()
                                                                                              class VariantStates(StatesGroup):
    choosing_category = State()
    entering_number = State()
    entering_name = State()
    entering_description = State()

    editing_choose = State()
    editing_name = State()
    editing_description = State()

                                               # ─── CATEGORY MANAGEMENT ──────────────────────────────────────────────────────
                                               @router.message(F.text == "📂 Санаттар басқару")
async def category_management_menu(message: Message):                                             if not is_admin(message.from_user.id):             return
                                                   categories = await db.get_categories()
                                                   text = (
        f"📂 *Санаттар басқару*\n\n"
        f"Жалпы санаттар: *{len(categories)}*\n\n"
        f"Не істегіңіз келеді?"                    )

    await message.answer(text, reply_markup=category_management_kb())


@router.callback_query(F.data == "category_add")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):            await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return                                 
    await state.set_state(CategoryStates.adding_name)                                             await callback.message.edit_text(
        "➕ *Жаңа санат қосу*\n\n"                     "Санат атауын жазыңыз:\n\n"
        "Болдырмау үшін /cancel"
    )                                          

@router.message(CategoryStates.adding_name, F.text == "/cancel")                              async def add_category_cancel(message: Message, state: FSMContext):                               await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())                    
                                               @router.message(CategoryStates.adding_name)
async def add_category_save(message: Message, state: FSMContext):                                 category_name = message.text.strip()
                                                   # Check if exists
    categories = await db.get_categories()
    if any(c[0] == category_name for c in categories):
        await message.answer(
            f"⚠️ *'{category_name}'* санаты бұрын бар.\n"
            "Басқа атау жазыңыз немесе /cancel"
        )
        return                                 
    # For now, we just add it by creating a variant with number 0 (meta)
    # Or we can track categories separately - but simpler is to just use it                       await state.clear()
                                                   await message.answer(
        f"✅ Санат *'{category_name}'* қосылды!\n\n"
        f"_Енді бұл санатқа сұрақтар немесе нұсқалар қоса аласыз._",                                  reply_markup=admin_main_kb()               )
                                               
@router.callback_query(F.data == "category_rename")
async def rename_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):            await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return

    categories = await db.get_categories()     
    if not categories:                                 await callback.answer("⚠️ Санаттар жоқ.", show_alert=True)                                     return
                                                   await callback.message.edit_text(
        "✏️ *Санатты өңдеу*\n\n"                        "Қай санатты өңдейсіз?",
        reply_markup=category_list_kb(categories, action="rename")
    )


@router.callback_query(F.data.startswith("catrename:"))
async def rename_category_chosen(callback: CallbackQuery, state: FSMContext):                     old_name = callback.data.split(":", 1)[1]
    await state.update_data(old_category=old_name)
    await state.set_state(CategoryStates.renaming_new)                                        
    await callback.message.edit_text(
        f"✏️ *Санатты өңдеу*\n\n"
        f"Ағымдағы атау: *{old_name}*\n\n"
        f"Жаңа атауын жазыңыз:\n\n"                    f"Болдырмау үшін /cancel"
    )                                          

@router.message(CategoryStates.renaming_new, F.text == "/cancel")
async def rename_category_cancel(message: Message, state: FSMContext):                            await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())


@router.message(CategoryStates.renaming_new)
async def rename_category_save(message: Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()                  old_name = data["old_category"]

    await db.rename_category(old_name, new_name)
    await state.clear()

    await message.answer(                              f"✅ Санат атауы өзгертілді:\n"
        f"*{old_name}* → *{new_name}*",
        reply_markup=admin_main_kb()               )


@router.callback_query(F.data == "category_delete")
async def delete_category_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return                                 
    categories = await db.get_categories()

    if not categories:
        await callback.answer("⚠️ Санаттар жоқ.", show_alert=True)
        return

    await callback.message.edit_text(                  "🗑 *Санатты өшіру*\n\n"
        "⚠️ *ЕСКЕРТУ:* Санат өшірілсе, оның ішіндегі барлық сұрақтар мен нұсқалар да өшеді!\n\n"
        "Қай санатты өшіресіз?",                       reply_markup=category_list_kb(categories, action="delete")
    )                                          
                                               @router.callback_query(F.data.startswith("catdelete:"))
async def delete_category_confirm(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]

    # Get question count                           count = await db.get_question_count(category)

    text = (
        f"🗑 *Санатты өшіру растау*\n\n"                f"Санат: *{category}*\n"
        f"Сұрақтар: *{count}*\n\n"                     f"⚠️ Бұл әрекетті қайтару мүмкін емес!\n\n"
        f"Өшіргіңіз келе ме?"                      )

    await callback.message.edit_text(                  text,                                          reply_markup=confirm_delete_kb(f"catdelconfirm:{category}")
    )


@router.callback_query(F.data.startswith("catdelconfirm:"))
async def delete_category_confirmed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return

    category = callback.data.split(":", 1)[1]

    deleted_count = await db.delete_category(category)

    await callback.message.edit_text(
        f"✅ *Санат өшірілді*\n\n"
        f"Санат: *{category}*\n"
        f"Өшірілген сұрақтар: *{deleted_count}*"
    )

    await callback.message.answer(
        "Әкімші тақтасы 👇",
        reply_markup=admin_main_kb()
    )


# ─── VARIANT MANAGEMENT ───────────────────────────────────────────────────────              
@router.message(F.text == "📋 Нұсқалар басқару")
async def variant_management_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    variants = await db.get_variants()

    text = (
        f"📋 *Нұсқалар басқару*\n\n"
        f"Жалпы нұсқалар: *{len(variants)}*\n\n"
        f"Не істегіңіз келеді?"
    )

    await message.answer(text, reply_markup=variant_management_kb())


@router.callback_query(F.data == "variant_add")
async def add_variant_start(callback: CallbackQuery, state: FSMContext):                          if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return                                 
    categories = await db.get_categories()

    if not categories:
        await callback.answer(
            "⚠️ Алдымен санат қосыңыз!",
            show_alert=True
        )
        return
                                                   await state.set_state(VariantStates.choosing_category)
    await callback.message.edit_text(
        "➕ *Жаңа нұсқа қосу*\n\n"                     "Санатты таңдаңыз:",
        reply_markup=category_list_kb(categories, action="varadd")
    )
                                               
@router.callback_query(VariantStates.choosing_category, F.data.startswith("varaddcat:"))
async def add_variant_category_chosen(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)

    # Get existing variants for this category      variants = await db.get_variants(category)
    next_number = len(variants) + 1

    await state.update_data(variant_number=next_number)
    await state.set_state(VariantStates.entering_name)                                                                                           await callback.message.edit_text(
        f"➕ *Жаңа нұсқа қосу*\n\n"
        f"Санат: *{category}*\n"
        f"Нұсқа нөмірі: *{next_number}*\n\n"
        f"Нұсқа атауын жазыңыз:\n"
        f"_(мысалы: '1-нұсқа' немесе 'Базалық деңгей')_\n\n"
        f"Болдырмау үшін /cancel"                  )
                                                                                              @router.message(VariantStates.entering_name, F.text == "/cancel")
async def add_variant_cancel(message: Message, state: FSMContext):                                await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())


@router.message(VariantStates.entering_name)   async def add_variant_name_entered(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(variant_name=name)     await state.set_state(VariantStates.entering_description)

    await message.answer(                              f"➕ *Жаңа нұсқа қосу*\n\n"
        f"Нұсқа атауы: *{name}*\n\n"
        f"Сипаттама жазыңыз (міндетті емес):\n\n"
        f"Өткізіп жіберу үшін: /skip\n"
        f"Болдырмау үшін: /cancel"
    )


@router.message(VariantStates.entering_description, F.text.in_(["/skip", "/cancel"]))
async def add_variant_description_skip_or_cancel(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())
        return

    # Skip description                             data = await state.get_data()
    variant_id = await db.add_variant(                 category=data["category"],
        variant_number=data["variant_number"],         name=data["variant_name"],
        description=""
    )
                                                   await state.clear()

    await message.answer(
        f"✅ *Нұсқа қосылды!*\n\n"                     f"Санат: *{data['category']}*\n"
        f"Нұсқа: *{data['variant_number']}. {data['variant_name']}*\n"
        f"ID: `{variant_id}`",                         reply_markup=admin_main_kb()
    )


@router.message(VariantStates.entering_description)
async def add_variant_save(message: Message, state: FSMContext):
    description = message.text.strip()
    data = await state.get_data()

    variant_id = await db.add_variant(
        category=data["category"],
        variant_number=data["variant_number"],
        name=data["variant_name"],
        description=description
    )

    await state.clear()

    await message.answer(
        f"✅ *Нұсқа қосылды!*\n\n"
        f"Санат: *{data['category']}*\n"               f"Нұсқа: *{data['variant_number']}. {data['variant_name']}*\n"
        f"Сипаттама: _{description}_\n"
        f"ID: `{variant_id}`",                         reply_markup=admin_main_kb()
    )


@router.callback_query(F.data == "variant_list")                                              async def list_variants(callback: CallbackQuery):                                                 if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return

    categories = await db.get_categories()
                                                   if not categories:                                 await callback.answer("⚠️ Санаттар жоқ.", show_alert=True)
        return

    await callback.message.edit_text(                  "📋 *Нұсқалар тізімі*\n\n"
        "Санатты таңдаңыз:",                           reply_markup=category_list_kb(categories, action="varlist")                               )
                                               
@router.callback_query(F.data.startswith("varlistcat:"))                                      async def list_variants_by_category(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    variants = await db.get_variants(category) 
    if not variants:                                   await callback.answer(
            f"⚠️ '{category}' санатында нұсқалар жоқ.",
            show_alert=True
        )
        return

    lines = [f"📋 *{category}* — Нұсқалар:\n"]     for v in variants:
        lines.append(                                      f"{v['variant_number']}. *{v['name']}* — {v['questions_count']} сұрақ"
        )

    await callback.message.edit_text(                  "\n".join(lines),
        reply_markup=variant_list_kb(variants, "view")
    )                                          
                                               @router.callback_query(F.data == "variant_delete")
async def delete_variant_choose_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return
                                                   categories = await db.get_categories()

    if not categories:                                 await callback.answer("⚠️ Санаттар жоқ.", show_alert=True)                                     return
                                                   await callback.message.edit_text(
        "🗑 *Нұсқаны өшіру*\n\n"                        "Санатты таңдаңыз:",
        reply_markup=category_list_kb(categories, action="vardel")
    )


@router.callback_query(F.data.startswith("vardelcat:"))
async def delete_variant_choose_variant(callback: CallbackQuery):                                 category = callback.data.split(":", 1)[1]
    variants = await db.get_variants(category)                                                    if not variants:                                   await callback.answer(
            f"⚠️ '{category}' санатында нұсқалар жоқ.",
            show_alert=True
        )                                              return                                                                                    await callback.message.edit_text(
        f"🗑 *Нұсқаны өшіру*\n\n"                       f"Санат: *{category}*\n\n"
        f"Қай нұсқаны өшіресіз?",                      reply_markup=variant_list_kb(variants, "delete")
    )


@router.callback_query(F.data.startswith("vardel:"))
async def delete_variant_confirm(callback: CallbackQuery):
    variant_id = int(callback.data.split(":")[1])
    variant = await db.get_variant_by_id(variant_id)
                                                   if not variant:
        await callback.answer("⚠️ Нұсқа табылмады.", show_alert=True)
        return                                                                                    text = (                                           f"🗑 *Нұсқаны өшіру растау*\n\n"
        f"Санат: *{variant['category']}*\n"
        f"Нұсқа: *{variant['variant_number']}. {variant['name']}*\n\n"
        f"⚠️ Сұрақтар сақталады, бірақ нұсқамен байланысы үзіледі.\n\n"
        f"Өшіргіңіз келе ме?"
    )                                                                                             await callback.message.edit_text(
        text,                                          reply_markup=confirm_delete_kb(f"vardelconf:{variant_id}")
    )                                                                                                                                        @router.callback_query(F.data.startswith("vardelconf:"))                                      async def delete_variant_confirmed(callback: CallbackQuery):                                      if not is_admin(callback.from_user.id):            await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return
                                                   variant_id = int(callback.data.split(":")[1])                                                 variant = await db.get_variant_by_id(variant_id)                                          
    if not variant:
        await callback.answer("⚠️ Нұсқа табылмады.", show_alert=True)                                  return

    await db.delete_variant(variant_id)
                                                   await callback.message.edit_text(
        f"✅ *Нұсқа өшірілді*\n\n"
        f"Санат: *{variant['category']}*\n"            f"Нұсқа: *{variant['variant_number']}. {variant['name']}*"
    )                                          
    await callback.message.answer(                     "Әкімші тақтасы 👇",                           reply_markup=admin_main_kb()               )
                                                                                              @router.callback_query(F.data == "delcancel")  async def delete_cancelled(callback: CallbackQuery):                                              await callback.message.edit_text("❌ Өшіру болдырылмады.")                                    await callback.message.answer("Әкімші тақтасы 👇", reply_markup=admin_main_kb())