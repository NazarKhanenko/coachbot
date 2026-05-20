"""Admin-only command handlers for athlete management."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from services.athlete_service import AthleteService

admin_router = Router()


def setup_admin_handlers(router: Router, athlete_service: AthleteService):
    """Register admin handlers with the router."""

    @router.message(Command("add_athlete"))
    async def cmd_add_athlete(message: Message):
        """Add a new athlete: /add_athlete USER_ID DAYS"""
        if message.from_user.id != config.ADMIN_ID:
            await message.answer("⛔ Admin only command.")
            return

        args = message.text.split()
        if len(args) != 3:
            await message.answer(
                "Usage: /add_athlete USER_ID DAYS\n"
                "Example: /add_athlete 123456789 30"
            )
            return

        try:
            user_id = int(args[1])
            days = int(args[2])
        except ValueError:
            await message.answer("❌ USER_ID and DAYS must be integers.")
            return

        athlete = athlete_service.add_athlete(
            telegram_id=user_id,
            username=f"user_{user_id}",
            coach_id=config.ADMIN_ID,
            days=days,
        )

        await message.answer(
            f"✅ Athlete added!\n"
            f"User ID: {athlete.telegram_id}\n"
            f"Subscription: {days} days\n"
            f"Expires: {athlete.subscription_expires_at.strftime('%Y-%m-%d %H:%M')}"
        )

    @router.message(Command("remove_athlete"))
    async def cmd_remove_athlete(message: Message):
        """Remove an athlete: /remove_athlete USER_ID"""
        if message.from_user.id != config.ADMIN_ID:
            await message.answer("⛔ Admin only command.")
            return

        args = message.text.split()
        if len(args) != 2:
            await message.answer("Usage: /remove_athlete USER_ID")
            return

        try:
            user_id = int(args[1])
        except ValueError:
            await message.answer("❌ USER_ID must be an integer.")
            return

        if athlete_service.remove_athlete(user_id):
            await message.answer(f"✅ Athlete {user_id} removed (deactivated).")
        else:
            await message.answer(f"❌ Athlete {user_id} not found.")

    @router.message(Command("list_athletes"))
    async def cmd_list_athletes(message: Message):
        """List all athletes with their status."""
        if message.from_user.id != config.ADMIN_ID:
            await message.answer("⛔ Admin only command.")
            return

        athletes = athlete_service.list_athletes()

        if not athletes:
            await message.answer("📭 No athletes registered yet.")
            return

        lines = ["📋 **Athletes:**", ""]
        for athlete in athletes:
            status = "🟢 Active" if athlete.active else "🔴 Inactive"
            days = athlete.days_remaining()
            
            if athlete.subscription_expires_at:
                expires = athlete.subscription_expires_at.strftime("%Y-%m-%d")
            else:
                expires = "N/A"

            lines.append(
                f"• ID: `{athlete.telegram_id}`\n"
                f"  Status: {status}\n"
                f"  Days left: {days}\n"
                f"  Expires: {expires}\n"
            )

        await message.answer("\n".join(lines), parse_mode="Markdown")
