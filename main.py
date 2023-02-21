import logging
import os

from global_transferable_entities import scope
from global_transferable_entities.user import User
from state_constructor_parts.action import ActionChangeUserVariableToInput, ActionChangeStage, Action, \
    ActionChangeUserVariable
from bot import Bot
from message_parts.message import Message, MessageKeyboard, MessageKeyboardButton, MessagePicture
from global_transferable_entities.scope import Scope
from state_constructor_parts.filter import IntNumberFilter, DoubleNumberFilter
from state_constructor_parts.stage import Stage
from data_access_layer.google_tables import SheetsClient
from statistics_entities.stage_stats import StageStatsVisitCount
from statistics_entities.user_stats import UserStatsVisitCount, UserStatsCurrentStage
from datetime import datetime

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='log.txt')
    logging.info("Program started")

    # --- Helper methods ---

    def clear_user_variables(user):
        user.set_variable("guests_count", None)
        user.set_variable("drinks_count", None)
        user.set_variable("desserts_count", None)
        user.set_variable("dishes_count", None)
        user.set_variable("order_type", None)

    # --- State constructor ---

    Stage.set_common_statistics([StageStatsVisitCount()])
    User.set_common_statistics([UserStatsVisitCount(),
                                UserStatsCurrentStage()])

    logging.info("Program started")

    _scope = Scope([

        Stage(name="NewUser",
              user_input_actions=[lambda _, user:
                                  ActionChangeStage("AskingForLocation")
                                  if user.get_variable("location") is None
                                  else ActionChangeStage("AskingForWhoTakeOrder")]),

        Stage(name="AskingForLocation",
              message=Message(text="Локация :"),
              user_input_actions=[ActionChangeUserVariableToInput("location"),
                                  ActionChangeUserVariable("weekday", lambda _, __: str(datetime.now().strftime("%A"))),
                                  ActionChangeUserVariable("time", lambda _, __: str(datetime.now().strftime("%H:%M:%S"))),
                                  ActionChangeStage("AskingForWhoTakeOrder")]),

        Stage(name="AskingForWhoTakeOrder",
              message=Message(text=lambda _, user: ("Текущая локация : " + user.get_variable("location") + "\n\n" if user.get_variable("location") is not None else "") + "Заказ забрал курьер?",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(
                                          text="Нет",
                                          actions=[ActionChangeStage("AskingForGuestsCount")]
                                      ),
                                      MessageKeyboardButton(
                                          text="Да",
                                          actions=[ActionChangeStage("AskingForOrderAmount")]
                                      ),
                                      MessageKeyboardButton(
                                          text="Ввести другую локацию",
                                          actions=[ActionChangeStage("AskingForLocation")]
                                      )
                                  ],
                                  is_non_keyboard_input_allowed=False
                              )),
              user_input_actions=[ActionChangeUserVariableToInput("is_order_taken_by_courier"),
                                  Action(action_function=lambda _, user, __, ___: clear_user_variables(user))]),

        Stage(name="AskingForGuestsCount",
              message=Message(text="Кол-во гостей пришедших вместе :",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="0"),
                                      MessageKeyboardButton(text="1"),
                                      MessageKeyboardButton(text="2"),
                                      MessageKeyboardButton(text="3")
                                  ],
                                  is_non_keyboard_input_allowed=True
                              )),
              user_input_filter=IntNumberFilter(not_passed_reason_message="Введите корректное число"),
              user_input_actions=[ActionChangeUserVariableToInput("guests_count"),
                                  ActionChangeStage("AskingForDrinksCount")]),

        Stage(name="AskingForDrinksCount",
              message=Message(text="Кол-во напитков :",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="0"),
                                      MessageKeyboardButton(text="1"),
                                      MessageKeyboardButton(text="2"),
                                      MessageKeyboardButton(text="3")
                                  ],
                                  is_non_keyboard_input_allowed=True
                              )),
              user_input_filter=IntNumberFilter(not_passed_reason_message="Введите корректное число"),
              user_input_actions=[ActionChangeUserVariableToInput("drinks_count"),
                                  ActionChangeStage("AskingForDesertsCount")]),

        Stage(name="AskingForDesertsCount",
              message=Message(text="Кол-во десертов :",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="0"),
                                      MessageKeyboardButton(text="1"),
                                      MessageKeyboardButton(text="2"),
                                      MessageKeyboardButton(text="3")
                                  ],
                                  is_non_keyboard_input_allowed=True
                              )),
              user_input_filter=IntNumberFilter(not_passed_reason_message="Введите корректное число"),
              user_input_actions=[ActionChangeUserVariableToInput("desserts_count"),
                                  ActionChangeStage("AskingForDishesCount")]),

        Stage(name="AskingForDishesCount",
              message=Message(text="Кол-во блюд :",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="0"),
                                      MessageKeyboardButton(text="1"),
                                      MessageKeyboardButton(text="2"),
                                      MessageKeyboardButton(text="3")
                                  ],
                                  is_non_keyboard_input_allowed=True
                              )),
              user_input_filter=IntNumberFilter(not_passed_reason_message="Введите корректное число"),
              user_input_actions=[ActionChangeUserVariableToInput("dishes_count"),
                                  ActionChangeStage("AskingForOrderType")]),

        Stage(name="AskingForOrderType",
              message=Message(text="Заказ с собой или на месте?",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="На месте"),
                                      MessageKeyboardButton(text="С собой"),
                                  ],
                                  is_non_keyboard_input_allowed=False
                              )),
              user_input_actions=[ActionChangeUserVariableToInput("order_type"),
                                  ActionChangeStage("AskingForOrderAmount")]),

        Stage(name="AskingForOrderAmount",
              message=Message(text="Примерная сумма заказа :"),
              user_input_filter=DoubleNumberFilter(not_passed_reason_message="Введите корректное число"),
              user_input_actions=[ActionChangeUserVariableToInput("order_amount"),
                                  ActionChangeStage("FieldResearchSaved")]),

        Stage(name="FieldResearchSaved",
              message=Message(text="Исследование сохранено!"),
              user_input_actions=[lambda _, user: ActionChangeStage("AskingForLocation") if user.get_variable("location") is None else ActionChangeStage("AskingForWhoTakeOrder"),
                                  Action(action_function=lambda scope, user, __, ___: google_sheets.insert_field_research(
                                      user.get_variable("weekday"),
                                      user.get_variable("time"),
                                      scope.try_get_variable("current_research_number", 1),
                                      user.get_variable("location"),
                                      user.get_variable("is_order_taken_by_courier"),
                                      user.get_variable("guests_count"),
                                      user.get_variable("drinks_count"),
                                      user.get_variable("desserts_count"),
                                      user.get_variable("dishes_count"),
                                      user.get_variable("order_type"),
                                      user.get_variable("order_amount"))),
                                  Action(action_function=lambda scope, _, __, ___: scope.set_variable("current_research_number", scope.try_get_variable("current_research_number", 1) + 1))],
              is_gatehouse=True)

    ], main_stage_name="AskingForWord")
    bot = Bot(os.environ['telegram_token'], _scope)
    google_sheets = SheetsClient(os.environ['sheets_token'])

    if os.environ['startup_mode'] == "webhook":
        logging.info("Starting using webhook")
        bot.start_webhook(port=8443,
                          server_ip=os.environ['server_ip'],
                          sertificate_path=os.environ['certificate_path'],
                          key_path=os.environ['key_path'])
    else:
        logging.info("Starting using polling")

        bot.start_polling(poll_interval=2,
                          poll_timeout=1)
