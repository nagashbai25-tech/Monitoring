# MiniBlog

Учебный мини-блог на Flask с полным путём до сервера и мониторингом:

```
git push → CI (ruff, pytest, проверка конфигов) → образ в GHCR → Ansible → сервер
                                                                    │
                       Prometheus + Grafana следят за приложением, базой, nginx и сервером
```

## Стек

| Что | Чем |
|---|---|
| Приложение | Flask + Flask-SQLAlchemy, запуск через gunicorn |
| База | PostgreSQL 16 |
| Веб-сервер | nginx (reverse proxy, статика) |
| Метрики | Prometheus, `prometheus-flask-exporter`, node-exporter, cAdvisor, postgres-exporter, nginx-exporter |
| Дашборды | Grafana (дашборды и источник данных создаются автоматически) |
| CI | GitHub Actions: линтер, тесты, проверка конфигов Prometheus, сборка и push образа в GHCR |
| CD | Ansible |

## Структура

```
.
├── front/                          # приложение (app.py, templates, tests, Dockerfile)
├── nginx/
│   ├── nginx.conf                  # локально: HTTP -> HTTPS
│   └── nginx.production.conf       # прод: HTTP на 80
├── monitoring/
│   ├── prometheus/                 # prometheus.yml (кого опрашивать) и alerts.yml (правила)
│   └── grafana/
│       ├── provisioning/           # автонастройка источника данных и загрузки дашбордов
│       └── dashboards/             # готовые дашборды (JSON)
├── ansible/                        # плейбук деплоя на сервер
├── docs/MONITORING.md              # как работает мониторинг, подробно
├── docker-compose.yml              # локально: приложение (build из исходников)
├── docker-compose.product.yml      # прод: приложение (образ из GHCR)
├── docker-compose.monitoring.yml   # мониторинг, подключается вторым файлом
├── Makefile                        # короткие команды
├── scripts/gen-certs.sh            # самоподписанный сертификат для локального HTTPS
└── .env.example                    # шаблон переменных окружения
```

## Быстрый старт (локально)

Нужны Docker и Docker Compose v2.

```bash
make setup      # создаст .env из шаблона и самоподписанный сертификат
nano .env       # впиши db_password и grafana_admin_password (любые, без символов @ : / # %)
make up         # соберёт приложение и запустит всё
```

Через минуту всё доступно:

| Что | Адрес |
|---|---|
| Блог | https://localhost:4433 (браузер предупредит о сертификате, это нормально) |
| Grafana | http://localhost:3000 (логин и пароль из `.env`) |
| Prometheus | http://localhost:9090 (раздел Status → Targets: все цели должны быть UP) |

Дашборды лежат в Grafana в папке **MiniBlog**. Чтобы графики ожили, походи по блогу, создай пару постов и комментариев.

`make help` покажет остальные команды (`make logs`, `make down`, `make test`).

## Тесты и линтер

```bash
pip install -r front/requirements-dev.txt
make test
make lint
```

## CI

`.github/workflows/CI.yml` запускается на каждый push и pull request:

1. **test**: `ruff check`, `ruff format --check`, `pytest`.
2. **monitoring-config**: `promtool check config` проверяет конфиг Prometheus и правила алертов, дашборды проверяются как JSON.
3. **docker**: сборка образа из `front/`. При push в `main` образ публикуется в `ghcr.io/<владелец>/miniblog` с тегами `latest` и `sha-<коммит>`.

Если твой логин GitHub отличается от `nagashbai25-tech`, поправь имя образа в `docker-compose.product.yml`.

## Деплой на сервер (Ansible)

На сервере нет исходников и сборки: только Docker, compose-файлы, конфиги и `.env`.

1. Убедись, что `ssh пользователь@IP` заходит по ключу, а у пользователя работает `sudo`.
   Для автоматизации удобен sudo без пароля:
   `echo "ПОЛЬЗОВАТЕЛЬ ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ansible` (на сервере).
2. На своём компьютере:
   ```bash
   pip install ansible
   ansible-galaxy collection install community.docker
   ```
3. Поправь `ansible/inventory.ini` (IP и пользователь).
4. Создай зашифрованный файл с секретами (образец в `ansible/group_vars/prod/vault.yml.example`):
   ```bash
   cd ansible
   ansible-vault create group_vars/prod/vault.yml
   ```
5. Проверка связи и деплой:
   ```bash
   ansible prod -m ping
   ansible-playbook deploy.yml --ask-vault-pass
   ```
6. Повтори запуск: во второй раз почти всё должно быть `ok`, это идемпотентность.

После деплоя:
- блог: `http://IP_сервера`
- Grafana: `http://IP_сервера:3000`
- Prometheus наружу не открыт (только localhost сервера). Доступ через SSH-туннель:
  `ssh -L 9090:localhost:9090 пользователь@IP`, затем http://localhost:9090

Если пакет в GHCR приватный, добавь в vault `vault_ghcr_user` и `vault_ghcr_token`, или сделай пакет публичным.

## Подробнее про мониторинг

См. [docs/MONITORING.md](docs/MONITORING.md): как всё устроено, что означает каждый график и алерт, как проверить алерты и добавить свою метрику.
