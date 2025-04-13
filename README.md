# Minecraft Bank System (EssenceBank)

**Essence Bank** — это телеграм бот для Minecraft, добавляющий полноценную банковскую систему с переводами, криптовалютой (Эссенция) и комиссиями. Игроки могут хранить средства, переводить деньги друг другу, обменивать валюту и участвовать в экономике сервера.

## 🔹 Основные возможности

- 💰 **Личные счета** у каждого игрока.
- 🔄 **Переводы между игроками** с настраиваемой комиссией.
- ₿ **Криптовалюта Эссенция** с динамическим курсом (зависит от спроса).
- 🏦 **Банковский счет сервера** (накопление комиссий, резервы).
- 📊 **Экономическая система** с инфляцией/дефляцией.


## 📊 Эссенция (Криптовалюта)

- Курс Эссенции зависит от спроса и предложения на сервере.
- Можно обменивать на внутриигровую валюту (Ары).
- Комиссия за обмен взимается в пользу банка.

## 📋 Команды

Основные команды бота

- /start - Запустить бота
- /help - посмотреть все доступные команды


##  📥 Установка

1. Клонируйте репозиторий:\
`git clone https://github.com/sBag834/my_test` \
`cd my_test`
2. Установите зависимости:\
`pip install -r requirements.txt`
3. Создайте файл `.env` в корневом каталоге проекта и добавьте параметры подключения к базе данных и токены для ботов:\
`DB_HOST=`\
`DB_NAME=`\
`DB_USER=`\
`DB_PASSWORD=`
`BOT_TOKEN=`\
`DS_BOT_TOKEN=`

4. Запустите приложение:\
`python main_1.py`

##  💾 Требования к базе данных

- Таблица "users"
```sql
-- Создание таблицы для хранения данных пользователей

CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telegram_id` varchar(255) NOT NULL,
  `nickname` varchar(255) NOT NULL,
  `balance` decimal(10,2) DEFAULT 0.00,
  `balance_ar` decimal(15,2) NOT NULL DEFAULT 0.00,
  `is_admin` tinyint(1) DEFAULT 0,
  `is_verified` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `telegram_id` (`telegram_id`),
  UNIQUE KEY `nickname` (`nickname`),
  CONSTRAINT `chk_balance` CHECK (`balance` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```


- Таблица "transactions"
```sql
-- Создание таблицы для хранения транзакций

CREATE TABLE `transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `currency` enum('es','ar') NOT NULL DEFAULT 'es',
  `is_bank_operation` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `receiver_id` (`receiver_id`),
  KEY `idx_transactions_user` (`sender_id`,`receiver_id`),
  KEY `idx_transactions_time` (`timestamp`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

