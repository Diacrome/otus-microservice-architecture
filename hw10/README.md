## Домашнее задание №2

### Запуск

Проверить что в minikube есть ingress:

`minikube addons enable ingress`

Из папки hw10 применить команду

```
kubectl apply -f . &&
kubectl apply -f ./secrets -n hw10 &&
helm repo add bitnami https://charts.bitnami.com/bitnami &&
helm install service bitnami/postgresql -n hw10 -f ./helm/values.yaml &&
kubectl apply -f ./config -n hw10 &&
kubectl apply -f ./python_app -n hw10
```

Для проверки CRUD выполнить команду:

`newman run ./test/hw10.postman_collection.json`

### Задание 
Цель:
В этом ДЗ вы создадите простейший RESTful CRUD.

Сделать простейший RESTful CRUD по созданию, удалению, просмотру и обновлению пользователей.
Пример API  - https://app.swaggerhub.com/apis/otus55/users/1.0.0

Добавить базу данных для приложения.

Конфигурация приложения должна хранится в Configmaps.

Доступы к БД должны храниться в Secrets.

Первоначальные миграции должны быть оформлены в качестве Job-ы, если это требуется.

Ingress-ы должны также вести на url arch.homework/ (как и в прошлом задании)

На выходе должны быть предоставлена

ссылка на директорию в github, где находится директория с манифестами кубернетеса
инструкция по запуску приложения.

команда установки БД из helm, вместе с файлом values.yaml.

команда применения первоначальных миграций

команда kubectl apply -f, которая запускает в правильном порядке манифесты кубернетеса

Postman коллекция, в которой будут представлены примеры запросов к сервису на создание, получение, изменение и удаление пользователя. Важно: в postman коллекции использовать базовый url - arch.homework.

Задание со звездочкой:

+5 балла за шаблонизацию приложения в helm чартах

### Код
В папке `python_docker_code` исходный код приложения
