from aiogram import Router, Dispatcher

dp = Dispatcher()
router = Router()
dp.include_router(router)
