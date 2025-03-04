#!/usr/bin/env bash


curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Устанавливаем зависимости
make install

# Создаём таблицы в базе
psql -a -d $DATABASE_URL -f database.sql
