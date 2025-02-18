from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from app.core.config import settings
from app.services.subscription import SubscriptionService
from datetime import datetime
from dateutil.relativedelta import relativedelta
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.bot.keyboards.user_keyboard import get_configuration_keyboard, get_admin_keyboard, get_start_keyboard, get_cancel_keyboard
from app.services.vpn import VPNService
import asyncio

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_extend_id = State()
    waiting_for_extend_months = State()
    waiting_for_block_id = State()

@router.callback_query(F.data == "userinfo")
async def request_user_info(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды.")
        return

    await callback.message.edit_text(
        "Пожалуйста, отправьте Telegram ID пользователя:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_user_id)

@router.message(AdminStates.waiting_for_user_id)
async def process_user_info(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        telegram_id = int(message.text)
        
        service = SubscriptionService()
        user = await service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"Пользователь с telegram_id {telegram_id} не найден.")
            return

        user_info_text = (
            f"ID: {user.id}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"Username: {user.username}\n"
            f"Subscription End: {user.subscription_end}\n"
            f"Status: {user.status}\n"
            f"Server ID: {user.server_id}\n"
        )
        await message.answer(user_info_text, reply_markup=get_configuration_keyboard())
        
    except ValueError:
        await message.answer("Неверный формат ID. Пожалуйста, отправьте числовой ID.")
    finally:
        await state.clear()

@router.callback_query(F.data == "extend_user")
async def request_extend_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды.")
        return

    await callback.message.edit_text(
        "Пожалуйста, отправьте Telegram ID пользователя для продления подписки:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_extend_id)

@router.message(AdminStates.waiting_for_extend_id)
async def process_extend_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        telegram_id = int(message.text)
        await state.update_data(telegram_id=telegram_id)
        await message.answer(
            "Теперь отправьте количество месяцев для продления:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_extend_months)
    except ValueError:
        await message.answer(
            "Неверный формат ID. Пожалуйста, отправьте числовой ID.",
            reply_markup=get_cancel_keyboard()
        )

@router.message(AdminStates.waiting_for_extend_months)
async def process_extend_months(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        months = int(message.text)
        if months <= 0 or months > 12:
            await message.answer("Пожалуйста, введите число месяцев от 1 до 12.")
            return
            
        data = await state.get_data()
        telegram_id = data.get('telegram_id')
        if not telegram_id:
            await message.answer("Произошла ошибка. Пожалуйста, начните процесс заново.")
            await state.clear()
            return

        service = SubscriptionService()
        user = await service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"Пользователь с telegram_id {telegram_id} не найден.")
            return

        # Проверка статуса пользователя
        if user.status == "blocked":
            await message.answer("❌ Невозможно продлить подписку заблокированному пользователю.")
            return

        current_expiration = user.subscription_end if user.subscription_end else datetime.now().date()
        new_expiration = current_expiration + relativedelta(months=months)

        from app.database.repositories.user_repo import UserRepository
        user_repo = UserRepository(service.db)
        success = user_repo.update_subscription(telegram_id, new_expiration)

        if success:
            try:
                # Синхронизация с VPN API
                await asyncio.to_thread(VPNService.syns_user, user)
                await message.answer(
                    f"✅ Подписка пользователя {telegram_id} продлена до {new_expiration.strftime('%d-%m-%Y')}.",
                    reply_markup=get_configuration_keyboard()
                )
            except Exception as e:
                print(f"Error syncing with VPN: {e}")
                await message.answer(
                    "⚠️ Подписка продлена, но возникла ошибка синхронизации с VPN.",
                    reply_markup=get_configuration_keyboard()
                )
        else:
            await message.answer("❌ Ошибка при продлении подписки.")

    except Exception as e:
        await message.answer("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")
        print(f"Error in process_extend_months: {e}")
    finally:
        await state.clear()

@router.callback_query(F.data == "block_user")
async def request_block_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды.")
        return

    await callback.message.edit_text(
        "Пожалуйста, отправьте Telegram ID пользователя для блокировки:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_block_id)

@router.message(AdminStates.waiting_for_block_id)
async def process_block_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        telegram_id = int(message.text)
        
        service = SubscriptionService()
        user = await service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"Пользователь с telegram_id {telegram_id} не найден.")
            return

        # Проверка текущего статуса
        if user.status == "blocked":
            await message.answer("❌ Пользователь уже заблокирован.")
            return

        user.status = "blocked"
        service.db.commit()
        
        try:
            # Синхронизация с VPN API
            await asyncio.to_thread(VPNService.syns_user, user)
            await message.answer(
                f"✅ Пользователь {telegram_id} заблокирован.", 
                reply_markup=get_configuration_keyboard()
            )
        except Exception as e:
            print(f"Error syncing with VPN: {e}")
            await message.answer(
                "⚠️ Пользователь заблокирован, но возникла ошибка синхронизации с VPN.",
                reply_markup=get_configuration_keyboard()
            )
        
    except ValueError:
        await message.answer("Неверный формат ID. Пожалуйста, отправьте числовой ID.")
    finally:
        await state.clear()

async def return_to_main_menu(message: Message, user_id: int):
    service = SubscriptionService()
    status = await service.get_subscription_status(user_id)
    if user_id in settings.ADMIN_IDS:
        text, keyboard = get_admin_keyboard(status)
    else:
        text, keyboard = get_start_keyboard(status)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await return_to_main_menu(message, message.from_user.id)
    await message.answer("Действие отменено.")

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await callback.answer("Действие отменено")
        await return_to_main_menu(callback.message, callback.from_user.id) 