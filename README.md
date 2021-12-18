# Yatube

## Yatube – соц. сеть с публикацией сообщений в тематических группах и ведения дневников.
Стек: Python 3, Django, PostgreSQL, gunicorn, nginx, Яндекс.Облако (Ubuntu 18.04), pytest.
Разработан по классической MVT архитектуре. Используется пагинация постов и кеширование. 
Регистрация реализована с верификацией данных, сменой и восстановлением пароля через почту.

##Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/RomanGrbr/Yatube.git
```

```
cd Yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```