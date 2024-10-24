import logging
import requests
import telebot
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '7672158475:AAE0sfKYxJwH4GwqpdgAwzDwB658FHIahMQ'
bot = telebot.TeleBot(TOKEN)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
b_findinn = KeyboardButton('/findinn')
b_findreport = KeyboardButton('/findreport')
b_findbank = KeyboardButton('/findbank')
keyboard.add(b_findinn, b_findreport, b_findbank)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет! Используйте кнопки ниже для поиска информации о компании или кредита.', reply_markup=keyboard)

@bot.message_handler(commands=['findinn'])
def find_inn(message):
    args = message.text.split()
    if len(args) > 1:
        inn = args[1]
        url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party'
        headers = {"Authorization": "Token f3ef15e2586892e81d99aeec0e208208c38da19d"}
        data = {"query": inn}
        response = requests.post(url, headers=headers, json=data)
        logging.info(f'Запрос к API: {response.request.url}, Данные: {data}, Статус код: {response.status_code}')
        if response.status_code == 200:
            suggestions = response.json().get('suggestions', [])
            if suggestions:
                company = suggestions[0]['data']
                subject_type = 'Индивидуальый предприниматель' if len(inn) == 12 else 'Юридическое лицо'
                company_info = (
                    f"Название: {company.get('name', {}).get('full_with_opf', 'Неизвестно')}\n"
                    f"ИНН: {company.get('inn', 'Неизвестно')}\n"
                    f"КПП: {company.get('kpp', 'Неизвестно')}\n"
                    f"ОГРН: {company.get('ogrn', 'Неизвестно')}\n"
                    f"ОКВЭД: {company.get('okved', 'Неизвестно')}\n"
                    f"Адрес: {company.get('address', {}).get('value', 'Неизвестно')}\n"
                    f"Тип: {subject_type}\n"
                )
                if subject_type == 'Юридическое лицо':
                    management = company.get('management', {})
                    director_name = management.get('name', 'Неизвестно')
                    director_post = management.get('post', 'Неизвестно')
                    company_info += (
                        f"Руководитель: {director_name}\n"
                        f"Должность: {director_post}"
                    )
                bot.reply_to(message, company_info)
            else:
                bot.reply_to(message, 'Компания или ИП не найдены.')
        else:
            bot.reply_to(message, f'Ошибка при обращении к API: {response.status_code} - {response.text}')
    else:
        bot.reply_to(message, 'Пожалуйста, укажите ИНН.')

@bot.message_handler(commands=['findreport'])
def find_report(message):
    args = message.text.split()
    if len(args) > 2:
        inn = args[1]
        year = args[2]
        url = f'https://api.checko.ru/v2/finances?key=fan6vCH2mQWcNru6&inn={inn}'

        response = requests.get(url)

        if response.status_code == 200:
            report_data = response.json()
            year_data = report_data.get('data', {}).get(year, None)
            if year_data:
                keys = ['1100', '1200', '1230', '1240', '1250', '1260', '1300', '1400', '1500', '1510', '1520', '1530',
                        '1540', '1550', '1600', '1700', '2110', '2400']
                values = {key: int(year_data.get(key, 0)) for key in keys}
                k_pokr = values['1200'] / (values['1510'] + values['1520'] + values['1550'])
                prk_pokr = (values['1230'] + values['1240'] + values['1250'] + values['1260']) / (
                        values['1510'] + values['1520'] + values['1550'])
                abs_pokr = (values['1240'] + values['1250']) / (values['1510'] + values['1520'] + values['1550'])

                if values['1200'] or values['1100'] != 0:
                    k_avtonom = (values['1300'] + values['1530'] + values['1540']) / (values['1200'] + values['1100'])
                else:
                    k_avtonom = 0
                score_result = (k_pokr * 30 + prk_pokr * 20 + abs_pokr * 30 + k_avtonom * 20)
                rent_posib = (values['2400'] / values['2110']) * 100
                report_info = f'Финансовая отчетность для ИНН {inn} за {year}:\n'
                report_info += f'Выручка: {values["2110"]}\n'
                report_info += f'Прибыль: {values["2400"]}\n'
                report_info += f'Рентабельность: {rent_posib:.2f}\n'
                report_info += f'Cкоринг: {score_result:.2f}\n'

                if score_result <= 60:
                    rating_message = 'Кредит в ближайшее время не удастся получить.'
                elif score_result <= 100:
                    rating_message = 'Кредит возможно получить под поручительство.'
                else:
                    rating_message = 'У вас отличный рейтинг! Рассмотрите предложения /findbank'

                report_info += f'{rating_message}'
                bot.reply_to(message, report_info)
            else:
                bot.reply_to(message, f'Нет данных за год {year} для ИНН {inn}.')
        else:
            bot.reply_to(message, f'Ошибка при обращении к API: {response.status_code} - {response.text}')
    else:
        bot.reply_to(message, 'Пожалуйста, укажите ИНН и год отчетности.')

text1 = "Сбербанк, Альфабанк, ГПБ, ВТБ, ПСБ, ТСБ, Совкомбанк, Солидарность, МСП, Абсолют, ТКБ"
text2 = "Казань, Зенит, Сбербанк, Альфабанк, ГПБ, Металл"
set1 = set(text1.lower().split(", "))
set2 = set(text2.lower().split(", "))

@bot.message_handler(commands=['findbank'])
def find_suitable_bank(message):
    bot.send_message(message.chat.id, "Введите сумму кредита (в рублях) и срок кредита (в месяцах) через запятую:")
    bot.register_next_step_handler(message, process_credit_and_duration)

def process_credit_and_duration(message):
    try:
        credit_amount, contract_duration = map(float, message.text.split(','))
        suitable_banks = set()
        if credit_amount <= 10000000:
            suitable_banks.update(set1)
        if contract_duration <= 36:
            suitable_banks.update(set2)
        if contract_duration > 36:
            intersecting_banks = suitable_banks.intersection(set2)
            final_banks = suitable_banks - intersecting_banks
        else:
            final_banks = suitable_banks
        if final_banks:
            response = "Подходящие банки для получения кредита:\n" + "\n".join(bank.capitalize() for bank in final_banks)
        else:
            response = "Подходящих банков не найдено."
        bot.send_message(message.chat.id, response)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите сумму кредита и срок кредита через запятую, например: `1000000, 12`.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}. Пожалуйста, попробуйте еще раз.")

def main():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()

